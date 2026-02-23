export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
  is_active: boolean;
}

export interface Client {
  id: number;
  name: string;
  client_id: string;
  description: string;
  data_profile: string;
  status: "online" | "offline" | "training" | "error";
  last_heartbeat: string;
  created_at: string;
  trust_score?: number;
  is_flagged?: boolean;
}

export interface TrainingRound {
  id: number;
  round_number: number;
  job_id: string;
  status:
    | "pending"
    | "in_progress"
    | "aggregating"
    | "completed"
    | "failed";
  num_clients: number;
  started_at: string;
  completed_at: string | null;
  global_loss: number | null;
  global_auc: number | null;
}

export interface ClientUpdate {
  id: number;
  round_id: number;
  client_id: string;
  local_loss: number;
  local_auc: number;
  num_samples: number;
  euclidean_distance: number;
  encryption_status: string;
  submitted_at: string;
}

export interface RoundMetric {
  id: number;
  round_id: number;
  aggregation_method: string;
  weiszfeld_iterations: number | null;
  convergence_epsilon: number | null;
  encryption_overhead_ms: number | null;
  aggregation_time_ms: number | null;
  poisoned_clients_detected: number;
}

export interface TrustScore {
  id: number;
  client_id: string;
  round_id: number;
  score: number;
  deviation_avg: number;
  is_flagged: boolean;
  computed_at: string;
}

export interface InferenceResult {
  id: number;
  image_filename: string;
  predictions: Record<string, number>;
  top_finding: string;
  confidence: number;
  inference_time_ms: number;
  model_version: string;
  created_at: string;
}

export interface OverviewMetrics {
  total_rounds: number;
  active_clients: number;
  latest_auc: number;
  flagged_clients: number;
  current_round_status: string;
}

export interface AUCHistoryItem {
  round_number: number;
  global_auc: number;
}

export interface LossHistoryItem {
  round_number: number;
  global_loss: number;
}

export interface RoundDetail extends TrainingRound {
  client_updates: ClientUpdate[];
  metrics: RoundMetric | null;
}

export interface AggregationStats {
  round_number: number;
  aggregation_method: string;
  aggregation_time_ms: number;
  encryption_overhead_ms: number;
  poisoned_clients_detected: number;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role?: string;
}
