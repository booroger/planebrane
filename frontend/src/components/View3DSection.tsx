import { useRef, useEffect, useState, useCallback } from 'react'
import type * as THREE from 'three'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Grid, GizmoHelper, GizmoViewport } from '@react-three/drei'
import { ArrowRight, Maximize2, Play, Pause, ZoomIn, ZoomOut, Box, Grid3x3, Sparkles, Circle, Palette } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { useAppStore } from '@/store/useAppStore'
import { CymaticGeometry } from './CymaticGeometry'
import { Switch } from '@/components/ui/switch'

type RenderMode = 'solid' | 'wireframe' | 'lines' | 'points'

interface SceneProps {
  currentFrame: number
  frameCount: number
  lineWidth: number
  zoom: number
  renderMode: RenderMode
  modelColor: string
  modelColor2: string
  useGradient: boolean
  modelData: {
    vertices: [number, number, number][]
    faces: [number, number, number][]
    normals: [number, number, number][]
  } | null
}

function Scene({ currentFrame, frameCount, lineWidth, zoom, renderMode, modelColor, modelColor2, useGradient, modelData }: SceneProps) {
  const groupRef = useRef<THREE.Group>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera>(null)

  // Calculate animation progress (0 to 1)
  const animationProgress = currentFrame / Math.max(1, frameCount - 1)

  // Animate based on current frame
  useEffect(() => {
    if (groupRef.current) {
      // Animate transformation from 2D to 3D
      const scaleZ = 0.05 + animationProgress * 0.95
      groupRef.current.scale.setZ(scaleZ)
      
      // Add rotation animation
      groupRef.current.rotation.y = animationProgress * Math.PI * 0.25
    }
  }, [animationProgress])

  // Update camera zoom
  useEffect(() => {
    if (cameraRef.current) {
      const baseDistance = 6
      const distance = baseDistance / zoom
      const angle = Math.PI / 4
      cameraRef.current.position.set(
        distance * Math.cos(angle),
        distance * 0.5,
        distance * Math.sin(angle)
      )
    }
  }, [zoom])

  return (
    <>
      <PerspectiveCamera ref={cameraRef} makeDefault position={[4, 3, 4]} />
      <OrbitControls 
        enableDamping 
        dampingFactor={0.05}
        minDistance={2}
        maxDistance={20}
      />
      
      <ambientLight intensity={0.4} />
      <directionalLight position={[10, 10, 5]} intensity={1.2} castShadow />
      <directionalLight position={[-10, -5, -5]} intensity={0.4} />
      <pointLight position={[0, 5, 0]} intensity={0.5} color="#00CCCC" />

      {modelData && (
        <group ref={groupRef}>
          <CymaticGeometry
            vertices={modelData.vertices}
            faces={modelData.faces}
            normals={modelData.normals}
            renderMode={renderMode}
            lineWidth={lineWidth}
            color={modelColor}
            color2={modelColor2}
            useGradient={useGradient}
            opacity={0.9}
            animationProgress={animationProgress}
          />
        </group>
      )}

      <Grid 
        args={[20, 20]} 
        cellColor="#536878" 
        sectionColor="#00CCCC" 
        fadeDistance={15}
        fadeStrength={1}
      />
      
      <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
        <GizmoViewport axisColors={['#ff4444', '#44ff44', '#4444ff']} labelColor="white" />
      </GizmoHelper>
    </>
  )
}

export function View3DSection() {
  const { 
    setCurrentStep, 
    uploadedImage,
    adjustedPoints,
    frameCount,
    currentFrame,
    setCurrentFrame,
    isAnimating,
    setIsAnimating,
    lineWidth,
    setLineWidth,
    modelColor,
    modelColor2,
    useGradient,
    setModelColor,
    setModelColor2,
    setUseGradient,
  } = useAppStore()

  const [zoom, setZoom] = useState(1)
  const [renderMode, setRenderMode] = useState<RenderMode>('lines')
  const [modelData, setModelData] = useState<{
    vertices: [number, number, number][]
    faces: [number, number, number][]
    normals: [number, number, number][]
  } | null>(null)
  const canvasContainerRef = useRef<HTMLDivElement>(null)

  // Generate 3D model from adjusted points
  useEffect(() => {
    if (adjustedPoints.length > 0) {
      // Generate mock torus for cymatic patterns
      const mockData = generateMockTorusFromPoints(adjustedPoints)
      setModelData(mockData)
    }
  }, [adjustedPoints])

  // Animation loop
  useEffect(() => {
    if (!isAnimating) return

    const interval = setInterval(() => {
      const nextFrame = currentFrame >= frameCount - 1 ? 0 : currentFrame + 1
      setCurrentFrame(nextFrame)
    }, 50)

    return () => clearInterval(interval)
  }, [isAnimating, frameCount, currentFrame, setCurrentFrame])

  // Zoom handlers
  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + 0.2, 3))
  }, [])

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - 0.2, 0.5))
  }, [])

  // Mouse wheel zoom
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault()
    if (e.deltaY < 0) {
      handleZoomIn()
    } else {
      handleZoomOut()
    }
  }, [handleZoomIn, handleZoomOut])

  useEffect(() => {
    const container = canvasContainerRef.current
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false })
      return () => container.removeEventListener('wheel', handleWheel)
    }
  }, [handleWheel])

  return (
    <div className="grid h-full grid-cols-[2fr_1fr] gap-6 p-8">
      {/* 3D Viewer */}
      <Card className="overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="heading-md">3D Model Preview</CardTitle>
              <CardDescription className="body-lg">
                Interact with the model using your mouse
              </CardDescription>
            </div>
            <Button variant="outline" size="icon">
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div ref={canvasContainerRef} className="relative h-[600px] w-full bg-gradient-to-br from-background to-muted">
            <Canvas shadows dpr={[1, 2]}>
              <Scene 
                currentFrame={currentFrame} 
                frameCount={frameCount} 
                lineWidth={lineWidth}
                zoom={zoom}
                renderMode={renderMode}
                modelColor={modelColor}
                modelColor2={modelColor2}
                useGradient={useGradient}
                modelData={modelData}
              />
            </Canvas>
            
            {/* Zoom controls overlay */}
            <div className="absolute bottom-4 right-4 flex flex-col gap-1">
              <Button
                variant="secondary"
                size="icon"
                onClick={handleZoomIn}
                className="h-8 w-8 bg-background/80 backdrop-blur-sm hover:bg-background"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="icon"
                onClick={handleZoomOut}
                className="h-8 w-8 bg-background/80 backdrop-blur-sm hover:bg-background"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Animation Controls */}
          <div className="border-t border-border p-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="label-text">Animation Frame</Label>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setIsAnimating(!isAnimating)}
                  >
                    {isAnimating ? (
                      <Pause className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </Button>
                  <span className="body-sm text-muted-foreground">
                    {currentFrame} / {frameCount - 1}
                  </span>
                </div>
              </div>
              <Slider
                value={[currentFrame]}
                onValueChange={(values) => {
                  setCurrentFrame(values[0])
                  setIsAnimating(false)
                }}
                min={0}
                max={frameCount - 1}
                step={1}
                className="w-full"
              />
              <p className="body-sm text-muted-foreground">
                Scrub to watch dots connect frame-by-frame forming the 3D shape
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Side Panel */}
      <div className="space-y-6">
        {/* Original Image */}
        <Card>
          <CardHeader>
            <CardTitle className="heading-sm">Original Pattern</CardTitle>
          </CardHeader>
          <CardContent>
            {uploadedImage && (
              <div className="overflow-hidden rounded-lg border border-border">
                <img
                  src={uploadedImage}
                  alt="Original pattern"
                  className="h-full w-full object-cover"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Rendering Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="heading-sm">Rendering Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Render Mode */}
            <div className="space-y-2">
              <Label className="label-text">Render Mode</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={renderMode === 'solid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRenderMode('solid')}
                  className="w-full"
                >
                  <Box className="mr-2 h-4 w-4" />
                  Solid
                </Button>
                <Button
                  variant={renderMode === 'wireframe' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRenderMode('wireframe')}
                  className="w-full"
                >
                  <Grid3x3 className="mr-2 h-4 w-4" />
                  Wire
                </Button>
                <Button
                  variant={renderMode === 'lines' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRenderMode('lines')}
                  className="w-full"
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Cymatic
                </Button>
                <Button
                  variant={renderMode === 'points' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRenderMode('points')}
                  className="w-full"
                >
                  <Circle className="mr-2 h-4 w-4" />
                  Points
                </Button>
              </div>
              <p className="body-sm text-muted-foreground">
                {renderMode === 'lines' ? 'Cymatic geometric interconnections' : 
                 renderMode === 'wireframe' ? 'Show mesh structure' :
                 renderMode === 'points' ? 'Show vertices only' :
                 'Solid surface rendering'}
              </p>
            </div>

            {/* Line Width */}
            {(renderMode === 'wireframe' || renderMode === 'lines') && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="lineWidth" className="label-text">
                    Line Thickness
                  </Label>
                  <Input
                    type="number"
                    value={lineWidth}
                    onChange={(e) => setLineWidth(Number(e.target.value))}
                    className="w-20"
                    step="0.5"
                    min="0.5"
                    max="10"
                  />
                </div>
                <Slider
                  id="lineWidth"
                  value={[lineWidth]}
                  onValueChange={(values) => setLineWidth(values[0])}
                  min={0.5}
                  max={10}
                  step={0.5}
                />
                <p className="body-sm text-muted-foreground">
                  Control thickness of geometric lines
                </p>
              </div>
            )}

            {/* Color Controls */}
            <div className="space-y-4 border-t border-border pt-4">
              <div className="flex items-center justify-between">
                <Label className="label-text flex items-center gap-2">
                  <Palette className="h-4 w-4" />
                  Color Options
                </Label>
              </div>

              {/* Gradient Toggle */}
              <div className="flex items-center justify-between">
                <Label htmlFor="gradient" className="body-sm">
                  Use Gradient
                </Label>
                <Switch
                  id="gradient"
                  checked={useGradient}
                  onCheckedChange={setUseGradient}
                />
              </div>

              {/* Primary Color */}
              <div className="space-y-2">
                <Label htmlFor="color1" className="body-sm">
                  {useGradient ? 'Start Color' : 'Model Color'}
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="color1"
                    type="color"
                    value={modelColor}
                    onChange={(e) => setModelColor(e.target.value)}
                    className="h-10 w-20 cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={modelColor}
                    onChange={(e) => setModelColor(e.target.value)}
                    className="flex-1 font-mono text-xs"
                    placeholder="#00CCCC"
                  />
                </div>
              </div>

              {/* Secondary Color (only for gradient) */}
              {useGradient && (
                <div className="space-y-2">
                  <Label htmlFor="color2" className="body-sm">
                    End Color
                  </Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="color2"
                      type="color"
                      value={modelColor2}
                      onChange={(e) => setModelColor2(e.target.value)}
                      className="h-10 w-20 cursor-pointer"
                    />
                    <Input
                      type="text"
                      value={modelColor2}
                      onChange={(e) => setModelColor2(e.target.value)}
                      className="flex-1 font-mono text-xs"
                      placeholder="#1560BD"
                    />
                  </div>
                </div>
              )}

              <p className="body-sm text-muted-foreground">
                {useGradient 
                  ? 'Gradient blends from start to end color across the mesh'
                  : 'Single color applied to entire mesh'
                }
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Model Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="heading-sm">Model Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between body-sm">
              <span className="text-muted-foreground">Vertices:</span>
              <Badge variant="secondary">24,567</Badge>
            </div>
            <div className="flex justify-between body-sm">
              <span className="text-muted-foreground">Faces:</span>
              <Badge variant="secondary">48,932</Badge>
            </div>
            <div className="flex justify-between body-sm">
              <span className="text-muted-foreground">File Size:</span>
              <Badge variant="secondary">2.4 MB</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="space-y-3">
          <Button
            onClick={() => setCurrentStep('export')}
            className="w-full"
          >
            Proceed to Export
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

// Helper function to generate mock torus geometry from 2D points
function generateMockTorusFromPoints(points: Array<{ x: number; y: number }>) {
  const vertices: [number, number, number][] = []
  const faces: [number, number, number][] = []
  const normals: [number, number, number][] = []
  
  const majorRadius = 1.2
  const minorRadius = 0.4
  const majorSegments = 48
  const minorSegments = 24
  
  // Generate torus vertices
  for (let i = 0; i <= majorSegments; i++) {
    const theta = (i / majorSegments) * Math.PI * 2
    const cosTheta = Math.cos(theta)
    const sinTheta = Math.sin(theta)
    
    for (let j = 0; j <= minorSegments; j++) {
      const phi = (j / minorSegments) * Math.PI * 2
      const cosPhi = Math.cos(phi)
      const sinPhi = Math.sin(phi)
      
      // Add displacement based on nearby 2D points
      let displacement = 0
      points.forEach(p => {
        const px = (p.x - 0.5) * 2
        const py = (p.y - 0.5) * 2
        const angle = Math.atan2(py, px)
        const angleDiff = Math.abs(((angle - theta + Math.PI) % (Math.PI * 2)) - Math.PI)
        if (angleDiff < 0.5) {
          displacement += 0.1 * (1 - angleDiff / 0.5)
        }
      })
      
      const r = minorRadius + displacement
      const x = (majorRadius + r * cosPhi) * cosTheta
      const y = r * sinPhi
      const z = (majorRadius + r * cosPhi) * sinTheta
      
      vertices.push([x, y, z])
      
      // Normal
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
  
  return { vertices, faces, normals }
}