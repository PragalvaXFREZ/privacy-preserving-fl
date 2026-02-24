"""
NVFlare custom Executor for client-side federated training.

Each client:
1. Receives the global model from the server.
2. Trains on its local (private) data partition for a configurable
   number of epochs.
3. Applies differential-privacy noise to the *body* (feature extractor)
   gradient updates.
4. Encrypts the *head* (classifier) weights using CKKS homomorphic
   encryption.
5. Returns the mixed plaintext/ciphertext update to the server.
"""

from __future__ import annotations

import logging
import os
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader

from nvflare.apis.dxo import DXO, DataKind, MetaKey, from_shareable
from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import ReturnCode
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable, make_reply
from nvflare.apis.signal import Signal

from .densenet_square import DenseNetSquare
from .dp_noise import DPNoise
from .selective_he import SelectiveHE

logger = logging.getLogger(__name__)

# Simulator uses generic site names (site-1, site-2, ...).
# Map them to the actual client data directory names.
SITE_NAME_MAP = {
    "site-1": "trauma_center",
    "site-2": "pulmonology_clinic",
    "site-3": "general_hospital",
}


class FedLearnTrainer(Executor):
    """Client-side executor for Privacy-Preserving Federated Learning.

    Handles two tasks:

    * ``"train"`` -- local SGD training followed by DP + HE post-processing.
    * ``"validate"`` -- evaluation on a held-out local validation set.

    Args:
        local_epochs: Number of local SGD epochs per FL round.
        lr: Learning rate for SGD.
        dp_epsilon: Per-round DP epsilon.
        dp_delta: DP delta parameter.
        batch_size: Mini-batch size for training and validation.
        max_grad_norm: DP gradient clipping norm.
        data_root: Root directory containing local client data.
    """

    def __init__(
        self,
        local_epochs: int = 1,
        lr: float = 0.01,
        dp_epsilon: float = 1.0,
        dp_delta: float = 1e-5,
        batch_size: int = 32,
        max_grad_norm: float = 1.0,
        data_root: str = "/app/data",
    ) -> None:
        super().__init__()

        self.local_epochs = local_epochs
        self.lr = lr
        self.batch_size = batch_size
        self.data_root = data_root

        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Model
        self.model = DenseNetSquare(num_classes=14, pretrained=False)
        self.model.to(self.device)

        # Optimizer and loss
        self.optimizer = torch.optim.SGD(
            self.model.parameters(), lr=lr, momentum=0.9
        )
        self.criterion = nn.BCELoss()

        # Privacy modules
        self.dp = DPNoise(
            epsilon=dp_epsilon,
            delta=dp_delta,
            sensitivity=1.0,
            max_grad_norm=max_grad_norm,
        )
        self.he = SelectiveHE()

        # Data loaders (lazy-initialised on first execute call)
        self._train_loader: Optional[DataLoader] = None
        self._val_loader: Optional[DataLoader] = None

    # ------------------------------------------------------------------
    # NVFlare Executor entry point
    # ------------------------------------------------------------------

    def execute(
        self,
        task_name: str,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """Dispatch to the correct handler based on *task_name*."""
        try:
            if task_name == "train":
                return self._handle_train(shareable, fl_ctx, abort_signal)
            elif task_name == "validate":
                return self._handle_validate(shareable, fl_ctx, abort_signal)
            elif task_name == "submit_model":
                return self._handle_submit_model(shareable, fl_ctx, abort_signal)
            else:
                logger.warning(f"Unknown task: {task_name}")
                return make_reply(ReturnCode.TASK_UNKNOWN)
        except Exception as e:
            logger.error(f"Error executing task '{task_name}': {e}", exc_info=True)
            return make_reply(ReturnCode.EXECUTION_EXCEPTION)

    # ------------------------------------------------------------------
    # Task handlers
    # ------------------------------------------------------------------

    def _handle_train(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """Receive global model, train locally, return DP + HE update."""

        # -- 1. Extract global weights from shareable ----------------
        dxo = from_shareable(shareable)
        global_weights = dxo.data

        # Separate body (plaintext) and head (possibly encrypted)
        body_weights: Dict[str, Any] = {}
        head_weights_raw: Dict[str, Any] = {}

        for k, v in global_weights.items():
            if k.startswith("classifier."):
                head_weights_raw[k] = v
            else:
                body_weights[k] = v

        # -- 2. Load global weights into local model -----------------
        # Body: always plaintext tensors
        body_tensors = OrderedDict()
        for k, v in body_weights.items():
            if isinstance(v, torch.Tensor):
                body_tensors[k] = v
            else:
                body_tensors[k] = torch.tensor(v, dtype=torch.float32)

        # Head: may be encrypted bytes or plain tensors
        head_tensors = OrderedDict()
        head_is_encrypted = False
        for k, v in head_weights_raw.items():
            if isinstance(v, bytes):
                head_is_encrypted = True
                break
            elif isinstance(v, torch.Tensor):
                head_tensors[k] = v
            else:
                head_tensors[k] = torch.tensor(v, dtype=torch.float32)

        if head_is_encrypted:
            # Register shapes from the current model head before decrypting
            self.he.register_shapes(self.model.get_head_state_dict())
            head_tensors = self.he.decrypt_head(head_weights_raw)

        # Load into model
        if body_tensors:
            self.model.load_body_state_dict(body_tensors)
        if head_tensors:
            self.model.load_head_state_dict(head_tensors)

        # -- 3. Local training ---------------------------------------
        self._ensure_data_loaders(fl_ctx)
        total_loss = 0.0
        num_samples = 0

        for epoch in range(self.local_epochs):
            if abort_signal.triggered:
                return make_reply(ReturnCode.TASK_ABORTED)
            epoch_loss, epoch_samples = self._train_one_epoch(
                self._train_loader, abort_signal
            )
            total_loss += epoch_loss
            num_samples = epoch_samples  # last epoch sample count

        avg_loss = total_loss / max(self.local_epochs, 1)

        # -- 4. Compute validation AUC -------------------------------
        val_loss, val_auc = self._validate(self._val_loader)

        # -- 5. Prepare update: DP on body, HE on head ---------------
        # Compute the *delta* (update - original global) for the body
        body_update = self.model.get_body_state_dict()
        body_update_dp = self.dp.apply(body_update)

        # Encrypt the head
        head_update = self.model.get_head_state_dict()
        he_start = time.time()
        head_encrypted = self.he.encrypt_head(head_update)
        he_elapsed_ms = (time.time() - he_start) * 1000

        # -- 6. Package into shareable --------------------------------
        combined_weights: Dict[str, Any] = {}
        combined_weights.update(body_update_dp)
        combined_weights.update(head_encrypted)

        out_dxo = DXO(
            data_kind=DataKind.WEIGHTS,
            data=combined_weights,
            meta={
                MetaKey.NUM_STEPS_CURRENT_ROUND: num_samples,
                "local_loss": float(avg_loss),
                "local_auc": float(val_auc),
                "num_samples": num_samples,
                "encryption_overhead_ms": he_elapsed_ms,
            },
        )
        return out_dxo.to_shareable()

    def _handle_validate(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """Load global model and run validation, returning metrics."""

        dxo = from_shareable(shareable)
        global_weights = dxo.data

        # Load all weights (assume plaintext for validation broadcast)
        model_sd = OrderedDict()
        for k, v in global_weights.items():
            if isinstance(v, torch.Tensor):
                model_sd[k] = v
            elif isinstance(v, bytes):
                # Encrypted head -- decrypt
                self.he.register_shapes(self.model.get_head_state_dict())
                shape = self.he.get_shapes().get(k)
                if shape is not None:
                    model_sd[k] = self.he.decrypt_tensor(v, tuple(shape))
            else:
                model_sd[k] = torch.tensor(v, dtype=torch.float32)

        self.model.load_state_dict(model_sd, strict=False)
        self._ensure_data_loaders(fl_ctx)
        val_loss, val_auc = self._validate(self._val_loader)

        out_dxo = DXO(
            data_kind=DataKind.METRICS,
            data={"val_loss": float(val_loss), "val_auc": float(val_auc)},
        )
        return out_dxo.to_shareable()

    def _handle_submit_model(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """Return the current local model weights."""
        model_weights = OrderedDict(
            (k, v.cpu()) for k, v in self.model.state_dict().items()
        )
        out_dxo = DXO(data_kind=DataKind.WEIGHTS, data=model_weights)
        return out_dxo.to_shareable()

    # ------------------------------------------------------------------
    # Training / validation loops
    # ------------------------------------------------------------------

    def _train_one_epoch(
        self,
        dataloader: Optional[DataLoader],
        abort_signal: Signal,
    ) -> tuple[float, int]:
        """Standard PyTorch training loop for one epoch.

        Args:
            dataloader: Training data loader.
            abort_signal: NVFlare abort signal.

        Returns:
            Tuple of (total_loss, num_samples).
        """
        self.model.train()
        running_loss = 0.0
        total_samples = 0

        if dataloader is None:
            logger.warning("No training dataloader available; skipping epoch.")
            return 0.0, 0

        for batch_idx, (images, labels) in enumerate(dataloader):
            if abort_signal.triggered:
                break

            images = images.to(self.device)
            labels = labels.to(self.device).float()

            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            batch_size = images.size(0)
            running_loss += loss.item() * batch_size
            total_samples += batch_size

        return running_loss, total_samples

    def _validate(
        self, dataloader: Optional[DataLoader]
    ) -> tuple[float, float]:
        """Compute validation loss and per-class mean AUC.

        Args:
            dataloader: Validation data loader.

        Returns:
            Tuple of (avg_loss, mean_auc).  AUC is 0.0 if it cannot
            be computed (e.g. single-class columns).
        """
        self.model.eval()

        if dataloader is None:
            logger.warning("No validation dataloader available.")
            return 0.0, 0.0

        all_preds = []
        all_labels = []
        running_loss = 0.0
        total_samples = 0

        with torch.no_grad():
            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device).float()

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                batch_size = images.size(0)
                running_loss += loss.item() * batch_size
                total_samples += batch_size

                all_preds.append(outputs.cpu().numpy())
                all_labels.append(labels.cpu().numpy())

        avg_loss = running_loss / max(total_samples, 1)

        # Compute mean AUC across all 14 pathology columns
        try:
            preds = np.concatenate(all_preds, axis=0)
            labels = np.concatenate(all_labels, axis=0)
            aucs = []
            for col in range(labels.shape[1]):
                if len(np.unique(labels[:, col])) > 1:
                    aucs.append(roc_auc_score(labels[:, col], preds[:, col]))
            mean_auc = float(np.mean(aucs)) if aucs else 0.0
        except Exception:
            mean_auc = 0.0

        return avg_loss, mean_auc

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _ensure_data_loaders(self, fl_ctx: FLContext) -> None:
        """Lazily initialise train and validation data loaders.

        The data is expected at ``<data_root>/<client_name>/`` with
        ``train/`` and ``val/`` subdirectories, or a CSV manifest.

        If no data is found, the loaders remain ``None`` and training
        will be skipped gracefully.
        """
        if self._train_loader is not None:
            return

        client_name = fl_ctx.get_identity_name()
        # Map simulator site names to actual client data directories
        client_name = SITE_NAME_MAP.get(client_name, client_name)
        client_data_dir = os.path.join(self.data_root, client_name)

        if not os.path.isdir(client_data_dir):
            logger.warning(
                f"Data directory not found: {client_data_dir}. "
                "Training will produce zero updates."
            )
            return

        try:
            from data.data_splitter import ChestXrayDataset
            from torchvision import transforms
            num_workers = int(os.getenv("DATALOADER_NUM_WORKERS", "0"))
            pin_memory = torch.cuda.is_available()

            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ])

            train_csv = os.path.join(client_data_dir, "train.csv")
            val_csv = os.path.join(client_data_dir, "val.csv")
            image_dir = os.path.join(client_data_dir, "images")

            if os.path.exists(train_csv) and os.path.isdir(image_dir):
                train_ds = ChestXrayDataset(
                    csv_path=train_csv,
                    image_dir=image_dir,
                    transform=transform,
                )
                self._train_loader = DataLoader(
                    train_ds,
                    batch_size=self.batch_size,
                    shuffle=True,
                    num_workers=num_workers,
                    pin_memory=pin_memory,
                )

            if os.path.exists(val_csv) and os.path.isdir(image_dir):
                val_ds = ChestXrayDataset(
                    csv_path=val_csv,
                    image_dir=image_dir,
                    transform=transform,
                )
                self._val_loader = DataLoader(
                    val_ds,
                    batch_size=self.batch_size,
                    shuffle=False,
                    num_workers=num_workers,
                    pin_memory=pin_memory,
                )

            logger.info(
                f"Loaded data for client '{client_name}': "
                f"train={len(self._train_loader.dataset) if self._train_loader else 0}, "
                f"val={len(self._val_loader.dataset) if self._val_loader else 0}"
            )
        except Exception as e:
            logger.error(f"Failed to load data for '{client_name}': {e}")
