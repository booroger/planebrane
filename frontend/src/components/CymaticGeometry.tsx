import { useMemo } from 'react'
import * as THREE from 'three'
import { Line } from '@react-three/drei'

interface CymaticGeometryProps {
  vertices: [number, number, number][]
  faces: [number, number, number][]
  normals: [number, number, number][]
  renderMode: 'solid' | 'wireframe' | 'lines' | 'points'
  lineWidth: number
  color?: string
  color2?: string
  useGradient?: boolean
  opacity?: number
  animationProgress?: number
}

export function CymaticGeometry({
  vertices,
  faces,
  normals,
  renderMode,
  lineWidth,
  color = '#00CCCC',
  color2 = '#1560BD',
  useGradient = false,
  opacity = 1.0,
  animationProgress = 1.0,
}: CymaticGeometryProps) {
  // Convert arrays to Three.js format
  const geometry = useMemo(() => {
    const geom = new THREE.BufferGeometry()
    
    // Set vertices
    const vertArray = new Float32Array(vertices.flat())
    geom.setAttribute('position', new THREE.BufferAttribute(vertArray, 3))
    
    // Set normals
    const normalArray = new Float32Array(normals.flat())
    geom.setAttribute('normal', new THREE.BufferAttribute(normalArray, 3))
    
    // Set faces
    const indices = new Uint32Array(faces.flat())
    geom.setIndex(new THREE.BufferAttribute(indices, 1))
    
    geom.computeBoundingSphere()
    
    return geom
  }, [vertices, faces, normals])

  // Extract edges for wireframe rendering
  const edges = useMemo(() => {
    const edgeSet = new Set<string>()
    const edgeList: [number, number][] = []
    
    faces.forEach(([a, b, c]) => {
      // Add each edge, ensuring smaller index first for uniqueness
      const edges: [number, number][] = [
        [Math.min(a, b), Math.max(a, b)],
        [Math.min(b, c), Math.max(b, c)],
        [Math.min(c, a), Math.max(c, a)],
      ]
      
      edges.forEach(([v1, v2]) => {
        const key = `${v1}-${v2}`
        if (!edgeSet.has(key)) {
          edgeSet.add(key)
          edgeList.push([v1, v2])
        }
      })
    })
    
    return edgeList
  }, [faces])

  // Create animated cymatic interconnection lines (for complex patterns)
  const cymaticLines = useMemo(() => {
    if (renderMode !== 'lines' || vertices.length === 0) return []
    
    // Create geometric patterns by connecting vertices based on distance and symmetry
    const allLines: [THREE.Vector3, THREE.Vector3, number][] = [] // Added connection order
    const maxConnections = Math.min(300, Math.floor(vertices.length * 0.5))
    
    // Calculate center
    const center = vertices.reduce(
      (acc, v) => [acc[0] + v[0], acc[1] + v[1], acc[2] + v[2]] as [number, number, number],
      [0, 0, 0] as [number, number, number]
    ).map(c => c / vertices.length) as [number, number, number]
    
    // Calculate distances from center
    const vertexData = vertices.map((v, i) => ({
      index: i,
      pos: new THREE.Vector3(...v),
      distFromCenter: Math.sqrt(
        (v[0] - center[0]) ** 2 + 
        (v[1] - center[1]) ** 2 + 
        (v[2] - center[2]) ** 2
      ),
    }))
    
    // Sort by distance from center
    vertexData.sort((a, b) => a.distFromCenter - b.distFromCenter)
    
    // Create radial connections (like crop circles) with connection order
    const layers = 8
    let connectionOrder = 0
    
    for (let layer = 0; layer < layers; layer++) {
      const startIdx = Math.floor((layer / layers) * vertexData.length)
      const endIdx = Math.floor(((layer + 1) / layers) * vertexData.length)
      const layerVertices = vertexData.slice(startIdx, endIdx)
      
      // Connect vertices within the same layer
      for (let i = 0; i < layerVertices.length && allLines.length < maxConnections; i++) {
        const v1 = layerVertices[i]
        // Connect to nearby vertices in the layer
        for (let j = i + 1; j < Math.min(i + 4, layerVertices.length) && allLines.length < maxConnections; j++) {
          const v2 = layerVertices[j]
          const dist = v1.pos.distanceTo(v2.pos)
          
          // Only connect if distance is reasonable
          if (dist < 0.5) {
            allLines.push([v1.pos.clone(), v2.pos.clone(), connectionOrder++])
          }
        }
        
        // Connect to next layer
        if (layer < layers - 1 && allLines.length < maxConnections) {
          const nextLayerStart = Math.floor(((layer + 1) / layers) * vertexData.length)
          const nextLayerEnd = Math.floor(((layer + 2) / layers) * vertexData.length)
          
          if (nextLayerStart < vertexData.length) {
            const nearestInNextLayer = vertexData
              .slice(nextLayerStart, Math.min(nextLayerEnd, vertexData.length))
              .sort((a, b) => v1.pos.distanceTo(a.pos) - v1.pos.distanceTo(b.pos))
              .slice(0, 2)
            
            nearestInNextLayer.forEach(v2 => {
              if (allLines.length < maxConnections) {
                allLines.push([v1.pos.clone(), v2.pos.clone(), connectionOrder++])
              }
            })
          }
        }
      }
    }
    
    return allLines
  }, [vertices, renderMode])

  // Calculate how many lines to show based on animation progress
  const visibleLineCount = Math.floor(cymaticLines.length * animationProgress)
  const visibleLines = cymaticLines.slice(0, visibleLineCount)

  // Create gradient material if needed
  const materialColor = useMemo(() => {
    if (useGradient) {
      // For gradient, we'll interpolate between color and color2 based on vertex position
      return color // We'll handle gradient per-line
    }
    return color
  }, [color, useGradient])

  if (renderMode === 'solid') {
    return (
      <mesh geometry={geometry}>
        <meshStandardMaterial
          color={materialColor}
          roughness={0.3}
          metalness={0.7}
          transparent={opacity < 1}
          opacity={opacity}
        />
      </mesh>
    )
  }

  if (renderMode === 'wireframe') {
    return (
      <>
        {/* Render edges as individual lines for proper thickness */}
        {edges.map(([v1Idx, v2Idx], i) => {
          const v1 = vertices[v1Idx]
          const v2 = vertices[v2Idx]
          
          // Calculate color for gradient
          let lineColor = color
          if (useGradient) {
            const centerY = vertices.reduce((sum, v) => sum + v[1], 0) / vertices.length
            const avgY = (v1[1] + v2[1]) / 2
            const t = (avgY - centerY + 2) / 4 // Normalize to 0-1
            lineColor = interpolateColor(color, color2, Math.max(0, Math.min(1, t)))
          }
          
          return (
            <Line
              key={i}
              points={[v1, v2]}
              color={lineColor}
              lineWidth={lineWidth}
              transparent={opacity < 1}
              opacity={opacity}
            />
          )
        })}
      </>
    )
  }

  if (renderMode === 'lines') {
    return (
      <>
        {/* Render animated cymatic interconnection lines */}
        {visibleLines.map(([start, end, order], i) => {
          // Calculate color for gradient
          let lineColor = color
          if (useGradient) {
            const t = order / Math.max(1, cymaticLines.length)
            lineColor = interpolateColor(color, color2, t)
          }
          
          return (
            <Line
              key={i}
              points={[start.toArray(), end.toArray()]}
              color={lineColor}
              lineWidth={lineWidth}
              transparent
              opacity={opacity * 0.6}
            />
          )
        })}
      </>
    )
  }

  if (renderMode === 'points') {
    return (
      <points geometry={geometry}>
        <pointsMaterial
          color={materialColor}
          size={lineWidth * 0.5}
          transparent={opacity < 1}
          opacity={opacity}
        />
      </points>
    )
  }

  return null
}

// Helper function to interpolate between two hex colors
function interpolateColor(color1: string, color2: string, t: number): string {
  const c1 = new THREE.Color(color1)
  const c2 = new THREE.Color(color2)
  const result = new THREE.Color()
  result.r = c1.r + (c2.r - c1.r) * t
  result.g = c1.g + (c2.g - c1.g) * t
  result.b = c1.b + (c2.b - c1.b) * t
  return '#' + result.getHexString()
}