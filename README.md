# Privacy-Preserving Federated Learning for Healthcare

**SLAY DIPUN**

A full-stack system for Privacy-Preserving Federated Learning to detect thoracic pathologies from Chest X-rays. Multiple simulated hospitals collaboratively train a DenseNet-121 model without sharing raw patient data, using Zero-Trust principles, Homomorphic Encryption (TenSEAL/CKKS), and Geometric Median aggregation for Byzantine resilience.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)     → localhost:3000              │
│  Login, Dashboard, Training Monitor, Inference           │
├──────────────────────────────────────────────────────────┤
│  Backend (FastAPI)         → localhost:8000               │
│  REST API, JWT Auth, ML Inference                        │
├──────────────────────────────────────────────────────────┤
│  Database (PostgreSQL 16)  → localhost:5432               │
│  Users, Clients, Rounds, Metrics, Inference Logs         │
├──────────────────────────────────────────────────────────┤
│  FL Pipeline (NVFlare)     → localhost:8002               │
│  3 Hospital Clients, GeomMedian Aggregator, TenSEAL HE  │
└──────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Recharts, shadcn/ui |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, JWT Auth |
| Database | PostgreSQL 16 |
| FL Engine | NVIDIA NVFlare, PyTorch, TenSEAL (CKKS), Geometric Median |
| Infra | Docker, Docker Compose |

---

## Quick Start (Docker — Easiest)

```bash
# 1. Clone the repo
git clone <repo-url>
cd project

# 2. Start everything (Postgres + Backend + Frontend + FL services)
docker compose up --build

# 3. Open the dashboard
#    → http://localhost:3000
```

Default credentials (seeded automatically):
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@fedlearn.health` | `admin123` |
| Doctor | `doctor@fedlearn.health` | `doctor123` |

---

## Local Development Setup

If you want to run services individually for development (hot reload, debugging, etc.):

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or use Docker just for Postgres)

### 1. Start PostgreSQL

Option A — Docker (recommended):
```bash
docker compose up postgres -d
```

Option B — Local Postgres:
```bash
# Create the database
createdb -U postgres fedlearn
# Create user
psql -U postgres -c "CREATE USER meshery WITH PASSWORD 'meshery';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fedlearn TO meshery;"
```

### 2. Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create a .env file)
export DATABASE_URL="postgresql://meshery:meshery@localhost:5432/fedlearn"
export SECRET_KEY="dev-secret-key"

# Initialize database (creates tables + seeds admin/doctor users + FL clients)
cd .. && python scripts/init_db.py && cd backend

# Run with hot reload
uvicorn app.main:app --reload --port 8000
```

API available at http://localhost:8000. Swagger docs at http://localhost:8000/docs

### 3. Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Run dev server (proxies API calls to backend:8000)
npm run dev
```

Dashboard available at http://localhost:3000

### 4. FL Pipeline (Optional — for training)

```bash
cd fl_pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download ChestX-ray14 dataset (~45GB)
chmod +x ../scripts/download_dataset.sh
../scripts/download_dataset.sh

# Provision NVFlare workspace (generates mTLS certs)
chmod +x ../scripts/provision_nvflare.sh
../scripts/provision_nvflare.sh

# Start FL server + clients (see NVFlare docs for details)
```

---

## Project Structure

```
project/
├── docker-compose.yml          # All 7 services
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # SQLAlchemy engine
│   │   ├── models/             # 7 ORM models (user, client, training_round, etc.)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # API endpoints (auth, clients, training, metrics, inference, internal)
│   │   ├── services/           # Business logic
│   │   ├── ml/                 # DenseNet-121 model loading & inference
│   │   └── utils/security.py   # JWT + password hashing
│   ├── alembic/                # DB migrations
│   ├── tests/                  # pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Next.js 14 dashboard
│   ├── src/
│   │   ├── app/                # Pages (login, dashboard/*, inference)
│   │   ├── components/         # UI, charts, layout, training, clients, inference
│   │   ├── hooks/              # useAuth, useTrainingRounds, useClients
│   │   └── lib/                # API wrapper, types, auth helpers
│   ├── Dockerfile
│   └── package.json
├── fl_pipeline/                # NVFlare FL system
│   ├── app/
│   │   ├── custom/             # DenseNet, Selective HE, GeomMedian, DP, Trainer, Aggregator
│   │   ├── config/             # NVFlare server/client JSON configs
│   │   └── data/               # Non-IID data splitter
│   ├── provision/              # NVFlare mTLS provisioning
│   ├── tests/                  # Unit tests
│   ├── Dockerfile
│   └── requirements.txt
└── scripts/
    ├── init_db.py              # Create tables + seed data
    ├── download_dataset.sh     # Download ChestX-ray14
    └── provision_nvflare.sh    # Generate NVFlare startup kits
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user (admin only) |
| POST | `/api/auth/login` | Login → JWT token |
| GET | `/api/auth/me` | Current user profile |

### Clients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/clients` | List FL client nodes |
| GET | `/api/clients/{id}` | Client details + trust |
| GET | `/api/clients/{id}/trust` | Trust score timeline |
| PATCH | `/api/clients/{id}/status` | Update status (admin) |

### Training
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/training/rounds` | List training rounds |
| GET | `/api/training/rounds/current` | Active round |
| GET | `/api/training/rounds/{id}` | Round detail + client updates |

### Metrics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/overview` | Dashboard summary |
| GET | `/api/metrics/auc-history` | AUC across rounds |
| GET | `/api/metrics/loss-history` | Loss across rounds |
| GET | `/api/metrics/aggregation` | Aggregation stats |
| GET | `/api/metrics/privacy` | Privacy parameters |

### Inference
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/inference/predict` | Upload X-ray → predictions |
| GET | `/api/inference/history` | Past inference results |

Full Swagger docs: http://localhost:8000/docs

---

## Database Schema

7 tables: `users`, `clients`, `training_rounds`, `client_updates`, `trust_scores`, `round_metrics`, `inference_logs`

To initialize:
```bash
# With Docker Postgres running:
DATABASE_URL="postgresql://meshery:meshery@localhost:5432/fedlearn" python scripts/init_db.py
```

To create a migration after model changes:
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## FL Pipeline Components

| Component | File | Description |
|-----------|------|-------------|
| DenseNet-121 | `densenet_square.py` | Pretrained model with ReLU → Square activation (HE-friendly) |
| Selective HE | `selective_he.py` | TenSEAL CKKS encryption of classifier head only |
| GeomMedian | `geometric_median.py` | Weiszfeld algorithm — robust to Byzantine/poisoned clients |
| DP Noise | `dp_noise.py` | Gaussian noise on body gradients (configurable epsilon/delta) |
| Trainer | `trainer.py` | NVFlare Executor — local training + encryption + DP |
| Aggregator | `aggregator.py` | NVFlare Controller — aggregation + trust scoring + DB writes |
| Data Splitter | `data_splitter.py` | Dirichlet non-IID partitioning of ChestX-ray14 |

---

## Running Tests

```bash
# Backend tests
cd backend
pip install pytest httpx
pytest tests/ -v

# FL pipeline tests
cd fl_pipeline
pytest tests/ -v

# Frontend (if Jest is configured)
cd frontend
npm test
```

---

## Environment Variables

### Backend
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://meshery:meshery@postgres:5432/fedlearn` | Postgres connection |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `MODEL_PATH` | `./models/global_model.pth` | Trained model weights |
| `UPLOAD_DIR` | `./uploads` | X-ray upload directory |

### FL Pipeline
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Postgres connection |
| `FL_ROLE` | — | `server` or `client` |
| `CLIENT_NAME` | — | NVFlare site name |
| `DP_EPSILON` | `1.0` | Differential privacy budget |
| `DP_DELTA` | `1e-5` | DP delta parameter |

---

## Common Issues

**`tenseal` won't install**: Requires Python 3.11+ and a C++ compiler. The Docker image handles this with `gcc g++`.

**Frontend build fails**: Make sure `frontend/public/` directory exists (can be empty). Run `npm install` before `npm run build`.

**Database connection refused**: Make sure Postgres is running. With Docker: `docker compose up postgres -d`. Wait for the healthcheck to pass.

**Torch download is slow**: PyTorch wheels are ~800MB. First build takes time. Subsequent builds use Docker cache.

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run tests: `pytest` (backend) / `npm test` (frontend)
4. Push and open a PR

---

Built with FastAPI, Next.js, NVFlare, PyTorch, and TenSEAL.
