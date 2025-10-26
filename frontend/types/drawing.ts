export interface ParametricFunction {
  x_t: string
  y_t: string
  t_start: number
  t_end: number
}

export interface PenSpec {
  color: "none" | "#000000" | "#0000FF"
}

export interface RelativeCurveDef {
  name: string
  x_rel: string
  y_rel: string
  t_min: number
  t_max: number
  pen: PenSpec
}

export interface RelativeProgram {
  segments: RelativeCurveDef[]
}

export interface DrawingResponse {
  success: boolean
  prompt: string
  iterations: number
  evaluation_score: number
  evaluation_feedback?: string

  // Image data (full data URI with prefix)
  image_base64: string
  image_path?: string

  // Relative program for display (preferred)
  relative_program?: RelativeProgram

  // Legacy parametric functions (for backward compatibility)
  parametric_functions?: ParametricFunction[]

  // Metadata
  processing_time?: number
  session_id?: string
  notes?: string
  stats?: {
    run_id?: string
    export_path?: string
  }
  error?: string
}
