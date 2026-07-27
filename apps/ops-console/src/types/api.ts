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

export type IngestionResult = {
  records_processed: number;
  records_created: number;
  records_updated: number;
  errors: string[];
};
