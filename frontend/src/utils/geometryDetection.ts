import type { Point2D } from '@/store/useAppStore'

export interface GeometricFeature {
  type: 'corner' | 'edge' | 'curve' | 'intersection'
  x: number
  y: number
  confidence: number
}

/**
 * Detect geometric features from an image using edge detection and feature analysis
 */
export async function detectGeometricFeatures(
  imageUrl: string,
  options: {
    threshold: number
    minSpacing: number
    density: number
  }
): Promise<Point2D[]> {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        resolve([])
        return
      }

      // Set canvas size
      canvas.width = img.width
      canvas.height = img.height
      
      // Draw image
      ctx.drawImage(img, 0, 0)
      
      // Get image data
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      
      // Detect features
      const features = detectFeaturesFromImageData(imageData, options)
      
      // Convert features to points
      const points = features.map(f => ({
        x: f.x / canvas.width,
        y: f.y / canvas.height,
        weight: f.confidence,
        feature_type: f.type === 'corner' || f.type === 'intersection' ? 'center' : 'edge',
      }))
      
      resolve(points)
    }
    
    img.onerror = () => resolve([])
    img.src = imageUrl
  })
}

/**
 * Detect features from image data using edge detection
 */
function detectFeaturesFromImageData(
  imageData: ImageData,
  options: { threshold: number; minSpacing: number; density: number }
): GeometricFeature[] {
  const { width, height, data } = imageData
  const { threshold, minSpacing, density } = options
  
  // Convert to grayscale
  const gray = new Uint8Array(width * height)
  for (let i = 0; i < data.length; i += 4) {
    const idx = i / 4
    gray[idx] = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
  }
  
  // Apply Sobel edge detection
  const edges = applySobelFilter(gray, width, height, threshold)
  
  // Find corners using Harris corner detection
  const corners = detectCorners(gray, width, height, threshold)
  
  // Find curve points
  const curvePoints = detectCurvePoints(edges, width, height)
  
  // Combine all features
  const allFeatures: GeometricFeature[] = [
    ...corners.map(p => ({ ...p, type: 'corner' as const })),
    ...curvePoints.map(p => ({ ...p, type: 'curve' as const })),
  ]
  
  // Filter by minimum spacing
  const filteredFeatures = filterBySpacing(allFeatures, minSpacing)
  
  // Limit by density (convert density 10-100 to point count)
  const maxPoints = Math.floor((density / 100) * 200 + 20)
  
  // Sort by confidence and take top N
  const sortedFeatures = filteredFeatures
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, maxPoints)
  
  return sortedFeatures
}

/**
 * Apply Sobel filter for edge detection
 */
function applySobelFilter(
  gray: Uint8Array,
  width: number,
  height: number,
  threshold: number
): Uint8Array {
  const edges = new Uint8Array(width * height)
  
  const sobelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1]
  const sobelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1]
  
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      let gx = 0, gy = 0
      
      for (let ky = -1; ky <= 1; ky++) {
        for (let kx = -1; kx <= 1; kx++) {
          const idx = (y + ky) * width + (x + kx)
          const kernelIdx = (ky + 1) * 3 + (kx + 1)
          gx += gray[idx] * sobelX[kernelIdx]
          gy += gray[idx] * sobelY[kernelIdx]
        }
      }
      
      const magnitude = Math.sqrt(gx * gx + gy * gy)
      edges[y * width + x] = magnitude > threshold ? 255 : 0
    }
  }
  
  return edges
}

/**
 * Detect corners using Harris corner detection
 */
function detectCorners(
  gray: Uint8Array,
  width: number,
  height: number,
  threshold: number
): Array<{ x: number; y: number; confidence: number }> {
  const corners: Array<{ x: number; y: number; confidence: number }> = []
  const k = 0.04
  const windowSize = 3
  
  for (let y = windowSize; y < height - windowSize; y += 2) {
    for (let x = windowSize; x < width - windowSize; x += 2) {
      let Ixx = 0, Iyy = 0, Ixy = 0
      
      for (let wy = -windowSize; wy <= windowSize; wy++) {
        for (let wx = -windowSize; wx <= windowSize; wx++) {
          const idx = (y + wy) * width + (x + wx)
          const idxX = (y + wy) * width + (x + wx + 1)
          const idxY = (y + wy + 1) * width + (x + wx)
          
          if (idxX < gray.length && idxY < gray.length) {
            const Ix = gray[idxX] - gray[idx]
            const Iy = gray[idxY] - gray[idx]
            
            Ixx += Ix * Ix
            Iyy += Iy * Iy
            Ixy += Ix * Iy
          }
        }
      }
      
      const det = Ixx * Iyy - Ixy * Ixy
      const trace = Ixx + Iyy
      const response = det - k * trace * trace
      
      if (response > threshold * 100) {
        corners.push({ x, y, confidence: response / 1000000 })
      }
    }
  }
  
  return corners
}

/**
 * Detect curve points along edges
 */
function detectCurvePoints(
  edges: Uint8Array,
  width: number,
  height: number
): Array<{ x: number; y: number; confidence: number }> {
  const curvePoints: Array<{ x: number; y: number; confidence: number }> = []
  
  // Sample along edges
  for (let y = 0; y < height; y += 5) {
    for (let x = 0; x < width; x += 5) {
      if (edges[y * width + x] > 0) {
        // Check if this is a significant curve point
        const curvature = calculateCurvature(edges, x, y, width, height)
        if (curvature > 0.3) {
          curvePoints.push({ x, y, confidence: curvature })
        }
      }
    }
  }
  
  return curvePoints
}

/**
 * Calculate curvature at a point
 */
function calculateCurvature(
  edges: Uint8Array,
  x: number,
  y: number,
  width: number,
  height: number
): number {
  const radius = 5
  let edgeCount = 0
  
  for (let dy = -radius; dy <= radius; dy++) {
    for (let dx = -radius; dx <= radius; dx++) {
      const nx = x + dx
      const ny = y + dy
      if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
        if (edges[ny * width + nx] > 0) {
          edgeCount++
        }
      }
    }
  }
  
  return edgeCount / ((radius * 2 + 1) ** 2)
}

/**
 * Filter features by minimum spacing
 */
function filterBySpacing(
  features: GeometricFeature[],
  minSpacing: number
): GeometricFeature[] {
  const filtered: GeometricFeature[] = []
  const minDistSq = minSpacing * minSpacing
  
  for (const feature of features) {
    let tooClose = false
    for (const existing of filtered) {
      const dx = feature.x - existing.x
      const dy = feature.y - existing.y
      const distSq = dx * dx + dy * dy
      if (distSq < minDistSq) {
        tooClose = true
        break
      }
    }
    if (!tooClose) {
      filtered.push(feature)
    }
  }
  
  return filtered
}

/**
 * Find the nearest geometric feature to a point (for snapping)
 */
export function findNearestFeature(
  x: number,
  y: number,
  features: GeometricFeature[],
  maxDistance: number = 0.02
): GeometricFeature | null {
  let nearest: GeometricFeature | null = null
  let minDist = maxDistance
  
  for (const feature of features) {
    const dx = x - feature.x
    const dy = y - feature.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    
    if (dist < minDist) {
      minDist = dist
      nearest = feature
    }
  }
  
  return nearest
}