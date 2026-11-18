/** Contrato de la API. Los montos llegan como texto decimal para no perder precisión. */

export type DecimalString = string

export type CostStatus =
  | 'UNDER_BUDGET'
  | 'ON_BUDGET'
  | 'OVER_BUDGET'
  | 'NOT_STARTED'
  | 'NOT_CALCULABLE'

export type ScheduleStatus = 'AHEAD' | 'ON_SCHEDULE' | 'BEHIND' | 'NOT_STARTED'

export type PerformanceBand = 'FAVORABLE' | 'WITHIN_TOLERANCE' | 'UNFAVORABLE' | 'NOT_AVAILABLE'

export interface Indicators {
  budget_at_completion: DecimalString
  planned_value: DecimalString
  earned_value: DecimalString
  actual_cost: DecimalString
  cost_variance: DecimalString
  schedule_variance: DecimalString
  cost_performance_index: DecimalString | null
  schedule_performance_index: DecimalString | null
  estimate_at_completion: DecimalString | null
  variance_at_completion: DecimalString | null
  estimate_is_reliable: boolean | null
  cost_status: CostStatus
  schedule_status: ScheduleStatus
  cost_band: PerformanceBand
  schedule_band: PerformanceBand
  cost_interpretation: string
  schedule_interpretation: string
}

export interface ActivityInput {
  name: string
  budget_at_completion: DecimalString
  planned_progress: DecimalString
  actual_progress: DecimalString
  actual_cost: DecimalString
}

export interface Activity extends ActivityInput {
  id: string
  project_id: string
  created_at: string
  updated_at: string
  indicators: Indicators
}

export interface ProjectInput {
  name: string
  description: string | null
  start_date: string | null
  end_date: string | null
  cutoff_date: string | null
}

export interface Project {
  id: string
  name: string
  description: string | null
  start_date: string | null
  end_date: string | null
  cutoff_date: string
  created_at: string
  updated_at: string
  activity_count: number
  indicators: Indicators
}

export type AlertSeverity = 'HIGH' | 'MEDIUM'

export interface Alert {
  type: string
  severity: AlertSeverity
  indicator: string
  observed_value: DecimalString
  message: string
  activity_id: string | null
  scope_name: string
}

export interface ProjectDetail extends Project {
  activities: Activity[]
  alerts: Alert[]
}

export interface ProjectPage {
  items: Project[]
  total: number
  limit: number
  offset: number
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details: { field: string; message: string }[] | null
  }
}
