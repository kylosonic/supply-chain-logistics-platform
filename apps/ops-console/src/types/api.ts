export type InventoryOverviewRow = {
  warehouse_code: string;
  warehouse_name: string;
  total_quantity_on_hand: number;
  total_safety_stock: number;
  utilization_percent: number;
};

export type ForecastPoint = {
  week_start: string;
  warehouse_code: string;
  sku: string;
  predicted_demand: number;
};

export type ForecastResponse = {
  horizon_weeks: number;
  model_name: string;
  points: ForecastPoint[];
};

export type RouteStop = {
  sequence: number;
  warehouse_code: string;
  demand_units: number;
  leg_distance_km: number;
  cumulative_distance_km: number;
  latitude?: number;
  longitude?: number;
  estimated_arrival?: string;
};

export type RouteScheduleSummary = {
  id: string;
  route_name: string;
  schedule_date: string;
  total_distance_km: number;
  total_cost: number;
  estimated_duration_min: number;
  status: string;
};

export type RouteOptimizeResponse = {
  route_name: string;
  schedule_date: string;
  objective: string;
  total_distance_km: number;
  total_cost: number;
  estimated_duration_min: number;
  capacity_used: number;
  unassigned_deliveries: { warehouse_code: string; demand_units: number }[];
  stops: RouteStop[];
  co2_saved_kg?: number | null;
  post_aha_toast?: boolean;
  data_origin?: string | null;
};

export type RouteOptimizePayload = {
  route_name: string;
  schedule_date: string;
  start_warehouse_code: string;
  deliveries: { warehouse_code: string; demand_units: number }[];
  vehicle_capacity_units: number;
  max_stops: number;
  speed_kmh: number;
  cost_per_km: number;
  persist_schedule: boolean;
  minimize_carbon_footprint: boolean;
};

export type RouteOptimizationRunSummary = {
  id: string;
  created_at: string;
  route_name: string;
  schedule_date: string;
  start_warehouse_code: string;
  objective: string;
  total_distance_km: number;
  total_cost: number;
  estimated_duration_min: number;
  capacity_used: number;
  deliveries_count: number;
  stops_count: number;
  unassigned_count: number;
  persist_requested: boolean;
  persisted_schedule_id: string | null;
};

export type RouteOptimizationRunDetail = RouteOptimizationRunSummary & {
  actor_user_id: string | null;
  organization_id: string | null;
  vehicle_capacity_units: number;
  max_stops: number;
  speed_kmh: number;
  cost_per_km: number;
  weights: {
    distance: number;
    time: number;
    cost: number;
  };
  deliveries: { warehouse_code: string; demand_units: number }[];
  stops: RouteStop[];
  unassigned_deliveries: { warehouse_code: string; demand_units: number }[];
};

export type ShipmentStatus = 'planned' | 'in_transit' | 'delivered' | 'delayed' | 'cancelled';

export type Shipment = {
  id: string;
  created_at: string;
  shipment_no: string;
  route_schedule_id: string | null;
  origin_warehouse_code: string;
  destination_warehouse_code: string;
  sku: string;
  quantity_units: number;
  planned_departure: string | null;
  expected_delivery: string | null;
  actual_delivery: string | null;
  status: ShipmentStatus;
  last_known_location: string | null;
  delay_reason: string | null;
  proof_of_delivery_ref: string | null;
};

export type AlertStatus = 'open' | 'acknowledged' | 'resolved';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertType = 'low_stock' | 'delayed_shipment' | 'planning_exception' | 'manual';

export type Alert = {
  id: string;
  created_at: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  acknowledged_by_user_id: string | null;
  acknowledged_at: string | null;
  resolved_by_user_id: string | null;
  resolved_at: string | null;
  resolution_note: string | null;
  payload?: { rerouting_plan?: any; [key: string]: any } | null;
};

export type ReplenishmentPlanStatus = 'pending_approval' | 'approved' | 'rejected';

export type ReplenishmentPlan = {
  id: string;
  created_at: string;
  warehouse_code: string;
  sku: string;
  horizon_weeks: number;
  avg_weekly_demand: number;
  suggested_quantity: number;
  approved_quantity: number | null;
  status: ReplenishmentPlanStatus;
  rationale: string;
  created_by_user_id: string;
  approved_by_user_id: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
};

export type SubscriptionTier = 'starter' | 'scale' | 'enterprise';

export type SubscriptionPlan = {
  tier: SubscriptionTier;
  title: string;
  monthly_price_usd: number | null;
  seat_limit: number | null;
  vehicle_limit: number | null;
  included_tasks_per_month: number | null;
  overage_unit_price_usd: number | null;
  includes_sso: boolean;
  includes_priority_support: boolean;
};

export type CurrentSubscription = {
  organization_id: string;
  organization_name: string;
  tier: SubscriptionTier;
  status: 'trialing' | 'active' | 'past_due' | 'canceled';
  preferred_ai_provider: string | null;
  preferred_ai_key_id: string | null;
  updated_at: string | null;
};

export type UsageMetric = 'delivery_tasks';

export type UsageSummary = {
  metric: UsageMetric;
  period_start: string;
  period_end: string;
  included_units: number | null;
  used_units: number;
  overage_units: number;
  utilization_percent: number | null;
  estimated_overage_cost_usd: number | null;
};

export type UsageThresholdLevel = 'approaching_limit' | 'limit_reached' | 'overage';

export type UsageThresholdEvent = {
  metric: UsageMetric;
  tier: SubscriptionTier;
  level: UsageThresholdLevel;
  usage_units: number;
  included_units: number;
  utilization_percent: number;
  message: string;
};

export type UsageRecordResponse = {
  usage: UsageSummary;
  events: UsageThresholdEvent[];
};

export type ProviderKey = {
  id: string;
  provider_name: string;
  key_name: string;
  masked_key: string;
  status: string;
  created_at: string;
  revoked_at: string | null;
};

export type ProviderKeyTestResult = {
  key_id: string;
  provider_name: string;
  ok: boolean;
  message: string;
};

export type ProviderPreference = {
  organization_id: string;
  provider_name: string | null;
  key_id: string | null;
};

export type AuditEvent = {
  id: string;
  created_at: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  actor_user_id: string | null;
  organization_id: string | null;
  description: string;
  payload: Record<string, unknown> | unknown[] | null;
};

export type ExceptionFeedItem = {
  source_type: string;
  source_id: string;
  severity: string;
  status: string;
  title: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
  metadata: Record<string, unknown> | null;
};

export type ExceptionFeedSummary = {
  open_alerts: number;
  delayed_shipments: number;
  pending_replenishment_plans: number;
  route_runs_with_unassigned_deliveries: number;
};

export type ExceptionFeedResponse = {
  summary: ExceptionFeedSummary;
  items: ExceptionFeedItem[];
};

export type IngestionResult = {
  records_processed: number;
  records_created: number;
  records_updated: number;
  errors: string[];
};

export type WeatherRiskZone = {
  id: string;
  severity_score: number;
  polygon: [number, number][];
};

export type ReceiptStatus = 'pending' | 'verified' | 'rejected' | 'escalated';
export type Verdict = 'verify' | 'reject_wrong_bank' | 'reject_duplicate' | 'reject_illegible' | 'escalate';
export type TrustedPayerAction = 'added' | 'verified_once';
export type LargeSurplusDecision = 'credit_forward' | 'credit_backward' | 'partial_ignore';
export type ReversalStatus = 'undo' | 'reversed';

export type Receipt = {
  id: string;
  status: ReceiptStatus;
  verdict: Verdict | null;
  invoice_number: string | null;
  reference_number: string | null;
  amount_etb: string | null;
  sender_name: string | null;
  bank_code: string | null;
  rejection_reason: string | null;
  created_at: string;
  decided_at: string | null;
  reversal_status: ReversalStatus | null;
};

export type ReversalRead = {
  receipt_id: string;
  invoice_number: string | null;
  reference_number: string | null;
  amount_etb: string | null;
  reversal_status: ReversalStatus;
  reversal_note: string | null;
  reversed_at: string | null;
  restored_balance_etb: string | null;
  wallet_voided_etb: string | null;
  message: string | null;
};

export type VerifiedReceiptAudit = {
  id: string;
  organization_id: string;
  organization_name: string;
  invoice_number: string | null;
  reference_number: string | null;
  amount_etb: string | null;
  sender_name: string | null;
  decided_at: string | null;
  reversal_status: ReversalStatus | null;
  undo_available: boolean;
  undo_available_until: string | null;
  reverse_available: boolean;
};

export type ReceiptAuditEvent = {
  id: string;
  event_type: string;
  description: string;
  created_at: string;
  payload: Record<string, unknown> | unknown[] | null;
  available_actions: string[];
};

export type ExtractedField = {
  [key: string]: string | null;
};

export type ReceiptQueueItem = {
  id: string;
  organization_id: string;
  organization_name: string;
  invoice_number: string | null;
  designated_bank_code: string | null;
  status: ReceiptStatus;
  verdict: Verdict | null;
  extracted_fields: ExtractedField;
  confidence: Record<string, number>;
  low_confidence_fields: string[];
  is_new_sender: boolean;
  is_cash_sender: boolean;
  is_wrong_bank_within_portfolio: boolean;
  is_large_surplus: boolean;
  is_duplicate: boolean;
  has_zero_confidence: boolean;
  zero_confidence_warning: string | null;
  recommended_verdict: Verdict | null;
  surplus_etb: string | null;
  large_surplus_decision: LargeSurplusDecision | null;
  partial_credit_amount_etb: string | null;
  trusted_payer_action: TrustedPayerAction | null;
  admin_note: string | null;
  sender_has_reversed_credit: boolean;
  fraud_risk_since: string | null;
  dispute_text: string | null;
  dispute_status: string | null;
  file_name: string;
  content_type: string;
  file_size_bytes: number;
  created_at: string;
};

export type WalletCredit = {
  amount_etb: string;
  status: string;
  applied_to_invoice_number: string | null;
  created_at: string;
};

export type WalletSummary = {
  available_etb: string;
  credits: WalletCredit[];
};

// ---------------------------------------------------------------------------
// Phase 4 activation surfaces (blueprint §2.4 / §9)
// ---------------------------------------------------------------------------

export type ActivationCategoryStatus = 'real' | 'sample' | 'empty';

export type CategoryMilestone = {
  category: string;
  label: string;
  status: ActivationCategoryStatus;
  real_rows: number;
  sample_rows: number;
  completed: boolean;
};

export type ActivationBanner = {
  visible: boolean;
  n_of_5: number;
  pct_complete: number;
  cta: '/upload' | '/routes' | null;
  demo_mode: boolean;
};

export type FreeCapState = {
  locked: boolean;
  utilization_pct: number | null;
  message: string | null;
};

export type PitchState = {
  banner: 'p100' | 'p80' | 'p60' | null;
  dismissible: boolean;
  fired: string[];
};

export type ActivationState = {
  organization_id: string;
  n_of_5: number;
  pct_complete: number;
  milestones: CategoryMilestone[];
  m6_completed: boolean;
  m6_completed_at: string | null;
  next_step: { category: string; label: string; cta: string } | null;
  banner: ActivationBanner;
  free_cap: FreeCapState;
  pitch: PitchState;
  toast_fired: boolean;
};

export type ResetWorkspaceResult = {
  rows_reseeded: Record<string, number>;
  activation_reset: boolean;
};

export type PitchDismissResult = {
  dismissed: boolean;
};
