import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, type Generate3DResponse, type ModelPreviewResponse } from '@/lib/api'

interface GeometryParams {
  extrusion_depth?: number
  curvature?: number
  subdivision_level?: number
  smoothing_iterations?: number
  pattern_scale?: number
  hollow?: boolean
  wall_thickness?: number
}

interface UseGenerateModelParams {
  pointsExtractionId: string | null
  targetShape?: string
  geometryParams?: GeometryParams
}

export function useGenerateModel({
  pointsExtractionId,
  targetShape = 'auto',
  geometryParams = {},
}: UseGenerateModelParams) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async (): Promise<Generate3DResponse> => {
      if (!pointsExtractionId) {
        throw new Error('No points extraction ID provided')
      }

      try {
        // Call the actual API
        const result = await apiClient.generate3DModel({
          points_extraction_id: pointsExtractionId,
          target_shape: targetShape,
          geometry_params: geometryParams,
        })
        return result
      } catch (error) {
        console.warn('3D model generation failed, using mock data:', error)
        // Return mock model data for development
        return generateMockModel(targetShape)
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['3dModel', pointsExtractionId], data)
    },
  })

  return mutation
}

interface UseModelPreviewParams {
  modelId: string | null
  enabled?: boolean
}

export function useModelPreview({ modelId, enabled = true }: UseModelPreviewParams) {
  return useQuery<ModelPreviewResponse>({
    queryKey: ['3dModelPreview', modelId],
    queryFn: async () => {
      if (!modelId) {
        throw new Error('No model ID provided')
      }

      try {
        return await apiClient.get3DModelPreview(modelId)
      } catch (error) {
        console.warn('Failed to fetch 3D model preview, using mock:', error)
        return generateMockModel('sphere')
      }
    },
    enabled: enabled && !!modelId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })
}

interface UseUpdateModelParams {
  modelId: string | null
}

export function useUpdateModelParams({ modelId }: UseUpdateModelParams) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (params: GeometryParams): Promise<Generate3DResponse> => {
      if (!modelId) {
        throw new Error('No model ID provided')
      }

      try {
        return await apiClient.updateModelParams(modelId, params)
      } catch (error) {
        console.warn('Failed to update model params:', error)
        throw error
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['3dModel', modelId], data)
      queryClient.invalidateQueries({ queryKey: ['3dModelPreview', modelId] })
    },
  })
}

// Generate mock 3D model for development
function generateMockModel(shape: string): Generate3DResponse {
  const modelData = shape === 'torus' ? generateTorusModel() : generateSphereModel()

  return {
    id: `mock-${Date.now()}`,
    shape: shape === 'torus' ? 'torus' : 'sphere',
    ...modelData,
  }
}

interface MockModelData {
  vertices: [number, number, number][]
  faces: [number, number, number][]
  normals: [number, number, number][]
  vertex_count: number
  face_count: number
  bounding_box: [number, number, number, number, number, number]
}

function generateSphereModel(): MockModelData {
  const vertices: [number, number, number][] = []
  const faces: [number, number, number][] = []
  const normals: [number, number, number][] = []

  const radius = 1
  const segments = 16
  const rings = 16

  // Generate vertices
  for (let ring = 0; ring <= rings; ring++) {
    const theta = (ring / rings) * Math.PI
    const sinTheta = Math.sin(theta)
    const cosTheta = Math.cos(theta)

    for (let segment = 0; segment <= segments; segment++) {
      const phi = (segment / segments) * Math.PI * 2
      const sinPhi = Math.sin(phi)
      const cosPhi = Math.cos(phi)

      const x = radius * sinTheta * cosPhi
      const y = radius * cosTheta
      const z = radius * sinTheta * sinPhi

      vertices.push([x, y, z])
      normals.push([x, y, z])
    }
  }

  // Generate faces
  for (let ring = 0; ring < rings; ring++) {
    for (let segment = 0; segment < segments; segment++) {
      const v0 = ring * (segments + 1) + segment
      const v1 = v0 + segments + 1
      const v2 = v0 + 1
      const v3 = v1 + 1

      faces.push([v0, v1, v2])
      faces.push([v2, v1, v3])
    }
  }

  return {
    vertices,
    faces,
    normals,
    vertex_count: vertices.length,
    face_count: faces.length,
    bounding_box: [-radius, -radius, -radius, radius, radius, radius],
  }
}

function generateTorusModel(): MockModelData {
  const vertices: [number, number, number][] = []
  const faces: [number, number, number][] = []
  const normals: [number, number, number][] = []

  const majorRadius = 1
  const minorRadius = 0.3
  const majorSegments = 32
  const minorSegments = 16

  // Generate vertices
  for (let i = 0; i <= majorSegments; i++) {
    const theta = (i / majorSegments) * Math.PI * 2
    const cosTheta = Math.cos(theta)
    const sinTheta = Math.sin(theta)

    for (let j = 0; j <= minorSegments; j++) {
      const phi = (j / minorSegments) * Math.PI * 2
      const cosPhi = Math.cos(phi)
      const sinPhi = Math.sin(phi)

      const x = (majorRadius + minorRadius * cosPhi) * cosTheta
      const y = minorRadius * sinPhi
      const z = (majorRadius + minorRadius * cosPhi) * sinTheta

      vertices.push([x, y, z])

      // Normal calculation
      const nx = cosPhi * cosTheta
      const ny = sinPhi
      const nz = cosPhi * sinTheta
      normals.push([nx, ny, nz])
    }
  }

  // Generate faces
  for (let i = 0; i < majorSegments; i++) {
    for (let j = 0; j < minorSegments; j++) {
      const v0 = i * (minorSegments + 1) + j
      const v1 = v0 + minorSegments + 1
      const v2 = v0 + 1
      const v3 = v1 + 1

      faces.push([v0, v1, v2])
      faces.push([v2, v1, v3])
    }
  }

  return {
    vertices,
    faces,
    normals,
    vertex_count: vertices.length,
    face_count: faces.length,
    bounding_box: [-majorRadius - minorRadius, -minorRadius, -majorRadius - minorRadius,
    majorRadius + minorRadius, minorRadius, majorRadius + minorRadius],
  }
}