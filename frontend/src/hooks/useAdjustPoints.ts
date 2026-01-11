import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'
import type { Point2D } from '@/store/useAppStore'
import { detectGeometricFeatures } from '@/utils/geometryDetection'

interface UseAdjustPointsParams {
  imageId: string | null
  imageUrl: string | null
  density: number
  threshold: number
  minSpacing: number
  weighting: number
  weightEdges: number
  weightIntersections: number
  weightSymmetry: number
  maxPoints: number
  enabled?: boolean
  useGeometricDetection?: boolean
}

// Generate mock points based on parameters for development
function generateMockPoints(params: {
  density: number
  threshold: number
  minSpacing: number
  weighting: number
}): Point2D[] {
  const { density, threshold, minSpacing, weighting } = params

  // Calculate number of points based on density (10-100 maps to ~20-200 points)
  const totalPoints = Math.floor((density / 100) * 180 + 20)

  // Threshold affects the spread of points (higher threshold = more edge points)
  const edgeRatio = threshold / 255

  // Minimum spacing affects clustering (higher = more spread out)
  const minDist = minSpacing / 100

  const points: Point2D[] = []

  // Generate points with controlled distribution
  for (let i = 0; i < totalPoints; i++) {
    let x: number, y: number
    let attempts = 0
    const maxAttempts = 50

    // Try to place point with minimum spacing constraint
    do {
      // Use weighting to influence distribution pattern
      if (Math.random() < edgeRatio) {
        // Edge point - place near boundary
        const angle = Math.random() * Math.PI * 2
        const radius = 0.3 + Math.random() * 0.2
        x = 0.5 + Math.cos(angle) * radius
        y = 0.5 + Math.sin(angle) * radius
      } else {
        // Center point - more random
        x = 0.2 + Math.random() * 0.6
        y = 0.2 + Math.random() * 0.6
      }

      // Check minimum spacing
      const tooClose = points.some(p => {
        const dx = p.x - x
        const dy = p.y - y
        return Math.sqrt(dx * dx + dy * dy) < minDist
      })

      if (!tooClose) break
      attempts++
    } while (attempts < maxAttempts)

    if (attempts < maxAttempts) {
      points.push({
        x: Math.max(0, Math.min(1, x)),
        y: Math.max(0, Math.min(1, y)),
        weight: weighting,
        feature_type: Math.random() < edgeRatio ? 'edge' : 'center',
      })
    }
  }

  return points
}

export function useAdjustPoints({
  imageId,
  imageUrl,
  density,
  threshold,
  minSpacing,
  weighting,
  weightEdges,
  weightIntersections,
  weightSymmetry,
  maxPoints,
  enabled = true,
  useGeometricDetection = true,
}: UseAdjustPointsParams) {
  // Debounce parameters
  const [debouncedParams, setDebouncedParams] = useState({
    density,
    threshold,
    minSpacing,
    weighting,
    weightEdges,
    weightIntersections,
    weightSymmetry,
    maxPoints,
  })

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedParams({
        density,
        threshold,
        minSpacing,
        weighting,
        weightEdges,
        weightIntersections,
        weightSymmetry,
        maxPoints,
      })
    }, 300) // 300ms debounce delay

    return () => clearTimeout(timer)
  }, [density, threshold, minSpacing, weighting, weightEdges, weightIntersections, weightSymmetry, maxPoints])

  const { data, isLoading, error, refetch } = useQuery<{
    id: string
    points: Point2D[]
  }>({
    queryKey: [
      'extractPoints',
      imageId,
      debouncedParams.density,
      debouncedParams.threshold,
      debouncedParams.minSpacing,
      debouncedParams.weightEdges,
      debouncedParams.weightIntersections,
      debouncedParams.weightSymmetry,
      debouncedParams.maxPoints,
    ],
    queryFn: async () => {
      if (!imageId) {
        throw new Error('No image ID provided')
      }

      try {
        // Call the real API with correct endpoint
        const result = await apiClient.extractPoints({
          image_id: imageId,
          density: debouncedParams.density / 100, // Normalize to 0-1 range
          threshold: debouncedParams.threshold / 255, // Normalize to 0-1 range
          min_distance: Math.max(1, debouncedParams.minSpacing),
          weight_edges: debouncedParams.weightEdges,
          weight_intersections: debouncedParams.weightIntersections,
          weight_symmetry: debouncedParams.weightSymmetry,
          max_points: debouncedParams.maxPoints,
        })

        return {
          id: result.id,
          points: result.points,
        }
      } catch (error) {
        console.warn('API call failed, using geometric detection or mock data:', error)

        // Use geometric detection if image URL is available
        if (useGeometricDetection && imageUrl) {
          try {
            const detectedPoints = await detectGeometricFeatures(imageUrl, {
              threshold: debouncedParams.threshold,
              minSpacing: debouncedParams.minSpacing,
              density: debouncedParams.density,
            })

            if (detectedPoints.length > 0) {
              return {
                id: `local-${Date.now()}`,
                points: detectedPoints,
              }
            }
          } catch (detectionError) {
            console.warn('Geometric detection failed, using mock data:', detectionError)
          }
        }

        // Final fallback to mock data
        return {
          id: `mock-${Date.now()}`,
          points: generateMockPoints(debouncedParams),
        }
      }
    },
    enabled: enabled && !!imageId,
    staleTime: 0, // Always refetch when params change
    refetchOnWindowFocus: false,
  })

  return {
    extractionId: data?.id || null,
    points: data?.points || [],
    isLoading,
    error,
    refetch,
  }
}