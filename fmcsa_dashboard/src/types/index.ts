export interface Carrier {
  usdot_number: number;
  legal_name: string;
  dba_name?: string;
  physical_address?: string;
  physical_city?: string;
  physical_state?: string;
  physical_zip?: string;
  telephone?: string;
  email?: string;
  entity_type?: string;
  operating_status: string;
  power_units?: number;
  drivers?: number;
  hazmat_flag?: boolean;
  liability_insurance_date?: string;
  liability_insurance_amount?: number;
  insurance_company?: string;
  insurance_expiry_date?: string;
  insurance_data_source?: string;
  insurance_data_type?: string;
  last_inspection_date?: string;
  total_inspections?: number;
  total_violations?: number;
  out_of_service_violations?: number;
  violation_rate?: number;
  sample_vin?: string;
  total_vehicles?: number;
  safety_rating?: string;
  mcs_150_date?: string;
  cargo_carried?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any; // Allow for additional fields
}

export interface SearchFilters {
  usdot_number?: string;  // Changed to string to handle any format
  legal_name?: string;
  state?: string;
  city?: string;
  entity_type?: string;
  operating_status?: string;
  min_power_units?: number;
  max_power_units?: number;
  min_drivers?: number;
  max_drivers?: number;
  hazmat_only?: boolean;
  insurance_expiring_days?: number;
  insurance_companies?: string[];
  safety_rating?: string;
  text_search?: string;
}

export interface SearchResponse {
  carriers: Carrier[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  query_time_ms: number;
}

export interface ExportRequest {
  format: 'csv' | 'xlsx';
  filters?: SearchFilters;
  columns?: string[];
  include_raw_data?: boolean;
}

export interface ExportResponse {
  file_id: string;
  filename: string;
  format: string;
  size_bytes: number;
  row_count: number;
  download_url: string;
  expires_at?: string;
}

export interface Statistics {
  total_carriers: number;
  active_carriers: number;
  inactive_carriers: number;
  by_state: Record<string, number>;
  by_entity_type: Record<string, number>;
  by_operating_status: Record<string, number>;
  insurance_stats: {
    expired: number;
    expiring_30_days: number;
    expiring_60_days: number;
    expiring_90_days: number;
    valid: number;
    unknown: number;
  };
  hazmat_carriers: number;
  avg_power_units: number;
  avg_drivers: number;
  last_updated: string;
}

export interface Lead {
  usdot_number: number;
  legal_name: string;
  dba_name?: string;
  state: string;
  city?: string;
  telephone?: string;
  email?: string;
  liability_insurance_date?: string;
  liability_insurance_amount?: number;
  insurance_company?: string;
  days_until_expiration?: number;
  insurance_status: 'expired' | 'expiring_soon' | 'expiring_60_days' | 'expiring_90_days' | 'valid' | 'unknown';
  entity_type?: string;
  operating_status: string;
  power_units?: number;
  drivers?: number;
  safety_rating?: string;
  lead_score: 'hot' | 'warm' | 'cool' | 'cold';
  score_value: number;
  score_reasons: string[];
  priority: number;
  best_contact_method: string;
}