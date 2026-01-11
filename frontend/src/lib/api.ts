import axios from 'axios'
import type { Point2D } from '@/store/useAppStore'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response types matching backend
export interface UploadImageResponse {
  id: string
  filename: string
  message: string
}

export interface AnalyzeImageResponse {
  image_id: string
  edges: {
    edge_count: number
    edge_density: number
    dominant_angles: number[]
    contour_count: number
  }
  symmetry: {
    rotational_order: number
    rotation_correlation: number
    reflection_axes: number[]
    symmetry_score: number
  }
  geometry: {
    bounding_box: [number, number, number, number]
    centroid: [number, number]
    estimated_radius: number
    dominant_angles: number[]
    repetition_frequency: number
    complexity_score: number
  }
}

export interface PatternType {
  type: 'circular' | 'radial' | 'spiral' | 'polygonal' | 'hexagonal' | 'linear' | 'mixed'
  confidence: number
  description: string
}

export interface PatternClassificationResponse {
  image_id: string
  primary_type: PatternType
  secondary_types: PatternType[]
  symmetry_order: number | null
  complexity_score: number
  features: Record<string, any>
}

export interface ExtractPointsRequest {
  image_id: string
  density?: number
  threshold?: number
  min_distance?: number
  weight_edges?: number
  weight_intersections?: number
  weight_symmetry?: number
  max_points?: number
}

export interface ExtractPointsResponse {
  id: string
  image_id: string
  points: Point2D[]
  total_points: number
  parameters: {
    density: number
    threshold: number
    min_distance: number
    weight_edges: number
    weight_intersections: number
    weight_symmetry: number
    max_points: number
  }
  bounding_box: [number, number, number, number]
}

export type TargetShape = 
  | 'auto'
  | 'sphere'
  | 'torus'
  | 'ellipsoid'
  | 'cone'
  | 'cube'
  | 'cuboid'
  | 'hexagonal_prism'
  | 'pyramid'
  | 'helix'
  | 'twisted_torus'
  | 'wireframe_surface'

export interface GeometryParams {
  extrusion_depth?: number
  curvature?: number
  subdivision_level?: number
  smoothing_iterations?: number
  pattern_scale?: number
  hollow?: boolean
  wall_thickness?: number
}

export interface Generate3DRequest {
  points_extraction_id: string
  target_shape?: TargetShape
  geometry_params?: GeometryParams
}

export interface Generate3DResponse {
  id: string
  points_extraction_id: string
  image_id: string
  target_shape: string
  actual_shape: string
  vertex_count: number
  face_count: number
  geometry_params: GeometryParams
  created_at: string
  bounding_box: [number, number, number, number, number, number]
}

export interface ModelPreviewResponse {
  vertices: [number, number, number][]
  faces: [number, number, number][]
  normals: [number, number, number][]
}

export const apiClient = {
  // Step 1: Upload image
  uploadImage: async (file: File): Promise<UploadImageResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<UploadImageResponse>('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Step 2: Analyze uploaded image
  analyzeImage: async (imageId: string): Promise<AnalyzeImageResponse> => {
    const response = await api.post<AnalyzeImageResponse>(`/images/${imageId}/analyze`, {
      detect_symmetry: true,
      extract_geometry: true,
    })
    return response.data
  },

  // Combined upload and analyze for convenience
  uploadAndAnalyze: async (file: File): Promise<{
    imageId: string
    analysis: AnalyzeImageResponse
  }> => {
    const uploadResult = await apiClient.uploadImage(file)
    const analysis = await apiClient.analyzeImage(uploadResult.id)
    return {
      imageId: uploadResult.id,
      analysis,
    }
  },

  // Get pattern classification
  getPatternClassification: async (imageId: string): Promise<PatternClassificationResponse> => {
    const response = await api.get<PatternClassificationResponse>(`/patterns/${imageId}`)
    return response.data
  },

  // Extract points from image
  extractPoints: async (params: ExtractPointsRequest): Promise<ExtractPointsResponse> => {
    const response = await api.post<ExtractPointsResponse>('/points/extract', {
      image_id: params.image_id,
      density: params.density ?? 1.0,
      threshold: params.threshold ?? 0.5,
      min_distance: params.min_distance ?? 10,
      weight_edges: params.weight_edges ?? 1.0,
      weight_intersections: params.weight_intersections ?? 1.5,
      weight_symmetry: params.weight_symmetry ?? 1.2,
      max_points: params.max_points ?? 1000,
    })
    return response.data
  },

  // Adjust existing point extraction
  adjustPoints: async (extractionId: string, params: {
    density?: number
    threshold?: number
    min_distance?: number
    weight_edges?: number
    weight_intersections?: number
    weight_symmetry?: number
    max_points?: number
  }): Promise<ExtractPointsResponse> => {
    const response = await api.put<ExtractPointsResponse>(`/points/${extractionId}/adjust`, params)
    return response.data
  },

  // Generate 3D model
  generate3DModel: async (data: Generate3DRequest): Promise<Generate3DResponse> => {
    const response = await api.post<Generate3DResponse>('/models/generate', {
      points_extraction_id: data.points_extraction_id,
      target_shape: data.target_shape ?? 'auto',
      geometry_params: data.geometry_params ?? {},
    })
    return response.data
  },

  // Get 3D model preview (simplified mesh)
  get3DModelPreview: async (modelId: string): Promise<ModelPreviewResponse> => {
    const response = await api.get<ModelPreviewResponse>(`/models/${modelId}/preview`)
    return response.data
  },

  // Update model parameters
  updateModelParams: async (
    modelId: string, 
    params: { 
      target_shape?: TargetShape
      geometry_params?: GeometryParams 
    }
  ): Promise<Generate3DResponse> => {
    const response = await api.put<Generate3DResponse>(`/models/${modelId}/params`, params)
    return response.data
  },

  // Export model - format-specific endpoints
  exportModelSTL: async (modelId: string, binary: boolean = true): Promise<Blob> => {
    const response = await api.get(`/export/${modelId}/stl`, {
      params: { binary },
      responseType: 'blob',
    })
    return response.data
  },

  exportModelSTLText: async (modelId: string): Promise<Blob> => {
    const response = await api.get(`/export/${modelId}/stl`, {
      params: { binary: false },
      responseType: 'blob',
    })
    return response.data
  },

  exportModelOBJ: async (modelId: string): Promise<Blob> => {
    const response = await api.get(`/export/${modelId}/obj`, {
      responseType: 'blob',
    })
    return response.data
  },

  exportModelGLTF: async (modelId: string): Promise<Blob> => {
    const response = await api.get(`/export/${modelId}/gltf`, {
      responseType: 'blob',
    })
    return response.data
  },

  exportModelGLB: async (modelId: string): Promise<Blob> => {
    const response = await api.get(`/export/${modelId}/glb`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Generic export function
  exportModel: async (modelId: string, format: 'stl' | 'obj' | 'gltf' | 'glb'): Promise<Blob> => {
    const response = await api.get(`/export/${modelId}/${format}`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Save export to server
  saveExport: async (modelId: string, format: 'stl' | 'obj' | 'gltf' | 'glb', filename?: string): Promise<{ path: string; size: number }> => {
    const response = await api.post(`/export/${modelId}/save`, {
      format,
      filename,
    })
    return response.data
  },
}

export default api