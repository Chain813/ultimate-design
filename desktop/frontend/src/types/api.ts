export type StudioRoute = "home" | "wb1" | "wb2" | "wb3" | "datav-popout";

export type StudioSubTab =
  | "diagnosis"
  | "assets"
  | "datav"
  | "strategy"
  | "master-plan"
  | "detail"
  | "aigc"
  | "delivery"
  | "guideline"
  | "systems"
  | "timing"
  | "skills";

export interface StageMetadata {
  code: string;
  name: string;
  phase: string;
  route: StudioRoute;
  subTab: StudioSubTab;
  description: string;
}

export interface ProjectInfo {
  id: string;
  project_id?: string;
  name: string;
  city?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  is_default?: boolean;
  [key: string]: any;
}

export interface EngineStatusHud {
  status?: string;
  active_project_id?: string;
  active_project_name?: string;
  duckdb_version?: string;
  spatial_extension?: boolean;
  rustworkx_available?: boolean;
  llm_provider?: string;
  llm_model?: string;
  llm_configured?: boolean;
  sd_configured?: boolean;
  sd_url?: string;
  rag_rules_count?: number;
  total_buildings?: number;
  total_plots?: number;
  total_roads?: number;
  engines?: Record<string, any>;
  [key: string]: any;
}

export interface FusedPlot {
  plot_id: string;
  name: string;
  area_m2: number;
  bldg_count: number;
  footprint_sum_m2?: number;
  gfa_sum_m2?: number;
  bcr: number;
  far: number;
  avg_floor: number;
  hist_bldg_count?: number;
  dominant_landuse?: string;
  poi_count?: number;
  poi_density: number;
  gvi_mean: number;
  svf_mean: number;
  nlp_sentiment_mean?: number;
  syntax_int_mean: number;
  traffic_load_mean?: number;
  mpi_score?: number;
  priority_tier?: string;
  rank?: number;
  lon?: number;
  lat?: number;
  centroid?: [number, number];
  updated_at?: string;
  [key: string]: any;
}

export interface GeoJsonFeature<P = Record<string, any>> {
  type: "Feature";
  id?: string | number;
  geometry: {
    type: string;
    coordinates: any;
  };
  properties: P;
}

export interface GeoJsonFeatureCollection<P = Record<string, any>> {
  type: "FeatureCollection";
  features: Array<GeoJsonFeature<P>>;
}

export interface MpiResult {
  ranking: FusedPlot[];
  weights?: Record<string, number>;
  summary?: Record<string, any>;
  top_plot?: FusedPlot | null;
  [key: string]: any;
}

export interface SpatialSyntaxSummary {
  total_segments: number;
  max_int_r400?: number;
  mean_int_r400?: number;
  max_int_r800?: number;
  mean_int_r800?: number;
  max_int_rn?: number;
  mean_int_rn?: number;
  max_choice_norm?: number;
  mean_choice_norm?: number;
  top_roads?: Array<Record<string, any>>;
  [key: string]: any;
}

export interface BackgroundJob {
  id: string;
  job_id?: string;
  type?: string;
  job_type?: string;
  title?: string;
  name?: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled" | string;
  progress: number;
  message?: string;
  output_path?: string;
  artifact_path?: string;
  result?: Record<string, any>;
  logs?: string[];
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface BinaryLayerHeader {
  layer: string;
  count: number;
  stride: number;
  fields: string[];
  bounds?: [number, number, number, number];
  [key: string]: any;
}

export interface BinaryLayerPayload {
  header: BinaryLayerHeader;
  data: Float32Array;
}

export interface CopilotCitation {
  id?: string;
  source: string;
  clause?: string;
  category?: string;
  snippet?: string;
  score?: number;
  [key: string]: any;
}

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  stage_label?: string;
  citations?: CopilotCitation[];
  streaming?: boolean;
}

export interface SystemSettingsPayload {
  llm_provider?: string;
  llm_model?: string;
  llm_base_url?: string;
  llm_api_key?: string;
  llm_api_key_masked?: string;
  sd_api_url?: string;
  baidu_ak?: string;
  baidu_ak_masked?: string;
  has_baidu_ak?: boolean;
  streetview_dir?: string;
  amap_api_key?: string;
  amap_key_masked?: string;
  [key: string]: any;
}

export type SyntaxMetricKey = "int_r400" | "int_r800" | "int_rn" | "choice_norm";

export type SolarSeasonKey = "winter" | "equinox" | "summer";
