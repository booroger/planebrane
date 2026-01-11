import { ArrowRight, Loader2, MousePointer2, Trash2, Move, Wand2, Undo2, Redo2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAppStore } from '@/store/useAppStore'
import { useAdjustPoints } from '@/hooks/useAdjustPoints'
import { useEffect, useRef, useState, useCallback } from 'react'
import type { Point2D } from '@/store/useAppStore'
import { findNearestFeature } from '@/utils/geometryDetection'

export function AdjustSection() {
  const {
    uploadedImage,
    patternAnalysis,
    imageId,
    pointDensity,
    detectionThreshold,
    minimumSpacing,
    weightEdges,
    weightIntersections,
    weightSymmetry,
    maxPoints,
    setPointDensity,
    setDetectionThreshold,
    setMinimumSpacing,
    setWeightEdges,
    setWeightIntersections,
    setWeightSymmetry,
    setMaxPoints,
    setCurrentStep,
    setAdjustedPoints,
    adjustedPoints,
    editMode,
    setEditMode,
    selectedTool,
    setSelectedTool,
    geometricFeatures,
    canUndo,
    canRedo,
    undo,
    redo,
    clearPointsHistory,
    frameCount,
    setFrameCount,
  } = useAppStore()

  const imgRef = useRef<HTMLImageElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [imgDimensions, setImgDimensions] = useState({ width: 0, height: 0 })
  const [hoveredPointIndex, setHoveredPointIndex] = useState<number | null>(null)
  const [draggedPointIndex, setDraggedPointIndex] = useState<number | null>(null)
  const [snapTarget, setSnapTarget] = useState<{ x: number; y: number } | null>(null)

  // Local state for sliders to prevent UI stalling
  const [localDensity, setLocalDensity] = useState(pointDensity)
  const [localThreshold, setLocalThreshold] = useState(detectionThreshold)
  const [localSpacing, setLocalSpacing] = useState(minimumSpacing)
  const [localWeightEdges, setLocalWeightEdges] = useState(weightEdges)
  const [localWeightIntersections, setLocalWeightIntersections] = useState(weightIntersections)
  const [localWeightSymmetry, setLocalWeightSymmetry] = useState(weightSymmetry)
  const [localMaxPoints, setLocalMaxPoints] = useState(maxPoints)

  // Sync local state when store changes (e.g. from analysis result or reset)
  useEffect(() => {
    setLocalDensity(pointDensity)
    setLocalThreshold(detectionThreshold)
    setLocalSpacing(minimumSpacing)
    setLocalWeightEdges(weightEdges)
    setLocalWeightIntersections(weightIntersections)
    setLocalWeightSymmetry(weightSymmetry)
    setLocalMaxPoints(maxPoints)
  }, [pointDensity, detectionThreshold, minimumSpacing, weightEdges, weightIntersections, weightSymmetry, maxPoints])

  const { points, isLoading } = useAdjustPoints({
    imageId,
    imageUrl: uploadedImage,
    density: pointDensity,
    threshold: detectionThreshold,
    minSpacing: minimumSpacing,
    weighting: 1.0,
    weightEdges,
    weightIntersections,
    weightSymmetry,
    maxPoints,
    enabled: !!uploadedImage && !!imageId && editMode === 'automatic',
    useGeometricDetection: true,
  })

  // Initialize with detected points from analysis or use fetched points
  const displayPoints: Point2D[] = editMode === 'manual'
    ? adjustedPoints
    : (points.length > 0 ? points : (patternAnalysis?.detected_points || adjustedPoints))

  // Update store with adjusted points
  useEffect(() => {
    if (points.length > 0 && editMode === 'automatic') {
      setAdjustedPoints(points)
    }
  }, [points, editMode, setAdjustedPoints])

  // Track image dimensions for point scaling
  useEffect(() => {
    if (imgRef.current) {
      const updateDimensions = () => {
        if (imgRef.current) {
          setImgDimensions({
            width: imgRef.current.clientWidth,
            height: imgRef.current.clientHeight,
          })
        }
      }

      updateDimensions()
      const observer = new ResizeObserver(updateDimensions)
      observer.observe(imgRef.current)

      return () => observer.disconnect()
    }
  }, [uploadedImage])

  // Handle clicking on canvas to add points
  const handleCanvasClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (editMode !== 'manual' || selectedTool !== 'add') return

    const svg = svgRef.current
    if (!svg) return

    const rect = svg.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height

    // Check for snap target
    const nearest = findNearestFeature(x, y, geometricFeatures, 0.03)
    const finalX = nearest ? nearest.x : x
    const finalY = nearest ? nearest.y : y

    const newPoint: Point2D = {
      x: finalX,
      y: finalY,
      weight: weightEdges,
      feature_type: 'edge',
    }

    setAdjustedPoints([...adjustedPoints, newPoint])
  }, [editMode, selectedTool, adjustedPoints, geometricFeatures, weightEdges, setAdjustedPoints])

  // Handle deleting a point
  const handleDeletePoint = useCallback((index: number) => {
    if (editMode !== 'manual' || selectedTool !== 'delete') return
    const newPoints = adjustedPoints.filter((_, i) => i !== index)
    setAdjustedPoints(newPoints)
  }, [editMode, selectedTool, adjustedPoints, setAdjustedPoints])

  // Handle dragging points
  const handlePointMouseDown = useCallback((index: number, e: React.MouseEvent) => {
    if (editMode !== 'manual' || selectedTool !== 'move') return
    e.stopPropagation()
    setDraggedPointIndex(index)
  }, [editMode, selectedTool])

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (draggedPointIndex === null) return

    const svg = svgRef.current
    if (!svg) return

    const rect = svg.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height

    // Check for snap
    const nearest = findNearestFeature(x, y, geometricFeatures, 0.03)

    if (nearest) {
      setSnapTarget({ x: nearest.x, y: nearest.y })
    } else {
      setSnapTarget(null)
    }

    const finalX = nearest ? nearest.x : x
    const finalY = nearest ? nearest.y : y

    const newPoints = [...adjustedPoints]
    newPoints[draggedPointIndex] = {
      ...newPoints[draggedPointIndex],
      x: finalX,
      y: finalY,
    }
    setAdjustedPoints(newPoints)
  }, [draggedPointIndex, adjustedPoints, geometricFeatures, setAdjustedPoints])

  const handleMouseUp = useCallback(() => {
    setDraggedPointIndex(null)
    setSnapTarget(null)
  }, [])

  // Calculate point statistics
  const edgePoints = displayPoints.filter(p => p.feature_type === 'edge').length
  const centerPoints = displayPoints.filter(p => p.feature_type === 'center').length
  const totalPoints = displayPoints.length

  return (
    <div className="grid h-full grid-cols-2 gap-6 p-8">
      {/* Left: Interactive Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="heading-md">Point Adjustment Preview</CardTitle>
              <CardDescription className="body-lg">
                {editMode === 'automatic'
                  ? (isLoading ? 'Detecting geometric features...' : 'Points aligned to geometric features')
                  : `${selectedTool === 'add' ? 'Click to add points' : selectedTool === 'delete' ? 'Click points to delete' : selectedTool === 'move' ? 'Drag points to move' : 'Select a tool to edit'}`
                }
              </CardDescription>
            </div>
            {editMode === 'manual' && (
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={undo}
                  disabled={!canUndo}
                  aria-label="Undo"
                >
                  <Undo2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={redo}
                  disabled={!canRedo}
                  aria-label="Redo"
                >
                  <Redo2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    if (confirm('Clear all points?')) {
                      clearPointsHistory()
                    }
                  }}
                  disabled={adjustedPoints.length === 0}
                  aria-label="Clear all"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative overflow-hidden rounded-lg border border-border bg-muted">
            {uploadedImage && (
              <>
                <img
                  ref={imgRef}
                  src={uploadedImage}
                  alt="Pattern with points"
                  className="h-full w-full object-contain opacity-60"
                  onLoad={() => {
                    if (imgRef.current) {
                      setImgDimensions({
                        width: imgRef.current.clientWidth,
                        height: imgRef.current.clientHeight,
                      })
                    }
                  }}
                />
                {/* Overlay for detected points */}
                <svg
                  ref={svgRef}
                  className="absolute inset-0 h-full w-full"
                  onClick={handleCanvasClick}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                  style={{ cursor: editMode === 'manual' ? (selectedTool === 'add' ? 'crosshair' : 'default') : 'default' }}
                >
                  {/* Snap target indicator */}
                  {snapTarget && editMode === 'manual' && (
                    <circle
                      cx={snapTarget.x * imgDimensions.width}
                      cy={snapTarget.y * imgDimensions.height}
                      r={8}
                      fill="none"
                      stroke="var(--color-primary)"
                      strokeWidth={2}
                      strokeDasharray="4 4"
                      className="animate-pulse"
                    />
                  )}

                  {/* Points */}
                  {displayPoints.map((point, index) => (
                    <g key={index}>
                      <circle
                        cx={point.x * imgDimensions.width}
                        cy={point.y * imgDimensions.height}
                        r={hoveredPointIndex === index ? 6 : (point.feature_type === 'edge' ? 3 : 4)}
                        fill={point.feature_type === 'edge' ? 'var(--color-accent)' : 'var(--color-primary)'}
                        opacity={0.8}
                        className="transition-all duration-200"
                        onMouseEnter={() => setHoveredPointIndex(index)}
                        onMouseLeave={() => setHoveredPointIndex(null)}
                        onMouseDown={(e) => handlePointMouseDown(index, e)}
                        onClick={(e) => {
                          e.stopPropagation()
                          if (selectedTool === 'delete') handleDeletePoint(index)
                        }}
                        style={{
                          cursor: editMode === 'manual'
                            ? (selectedTool === 'delete' ? 'pointer' : selectedTool === 'move' ? 'move' : 'default')
                            : 'default'
                        }}
                      />
                      {/* Point label on hover */}
                      {hoveredPointIndex === index && (
                        <text
                          x={point.x * imgDimensions.width + 10}
                          y={point.y * imgDimensions.height - 10}
                          className="body-sm fill-foreground"
                          style={{ pointerEvents: 'none' }}
                        >
                          {point.feature_type}
                        </text>
                      )}
                    </g>
                  ))}
                </svg>
                {/* Loading overlay */}
                {isLoading && editMode === 'automatic' && (
                  <div className="absolute inset-0 flex items-center justify-center bg-background/50">
                    <div className="flex items-center gap-2 rounded-lg bg-background px-4 py-2 shadow-lg">
                      <Loader2 className="h-4 w-4 animate-spin text-accent" />
                      <span className="body-sm text-muted-foreground">Detecting features...</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Right: Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="heading-md">Adjustment Controls</CardTitle>
          <CardDescription className="body-lg">
            Fine-tune point detection or edit manually
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Mode Tabs */}
          <Tabs value={editMode} onValueChange={(v) => setEditMode(v as 'automatic' | 'manual')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="automatic">
                <Wand2 className="mr-2 h-4 w-4" />
                Automatic
              </TabsTrigger>
              <TabsTrigger value="manual">
                <MousePointer2 className="mr-2 h-4 w-4" />
                Manual
              </TabsTrigger>
            </TabsList>

            <TabsContent value="automatic" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="density" className="label-text">
                      Point Density
                    </Label>
                    <Input
                      type="number"
                      value={localDensity}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalDensity(val)
                        setPointDensity(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="density"
                    value={[localDensity]}
                    onValueChange={(values) => setLocalDensity(values[0])}
                    onValueCommit={(values) => setPointDensity(values[0])}
                    min={10}
                    max={100}
                    step={5}
                  />
                  <p className="body-sm text-muted-foreground">
                    Controls maximum number of feature points
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="threshold" className="label-text">
                      Detection Threshold
                    </Label>
                    <Input
                      type="number"
                      value={localThreshold}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalThreshold(val)
                        setDetectionThreshold(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="threshold"
                    value={[localThreshold]}
                    onValueChange={(values) => setLocalThreshold(values[0])}
                    onValueCommit={(values) => setDetectionThreshold(values[0])}
                    min={0}
                    max={255}
                    step={5}
                  />
                  <p className="body-sm text-muted-foreground">
                    Edge detection sensitivity
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="spacing" className="label-text">
                      Minimum Spacing
                    </Label>
                    <Input
                      type="number"
                      value={localSpacing}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalSpacing(val)
                        setMinimumSpacing(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="spacing"
                    value={[localSpacing]}
                    onValueChange={(values) => setLocalSpacing(values[0])}
                    onValueCommit={(values) => setMinimumSpacing(values[0])}
                    min={1}
                    max={20}
                    step={1}
                  />
                  <p className="body-sm text-muted-foreground">
                    Minimum distance between points
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="weightEdges" className="label-text">
                      Edge Weight
                    </Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={localWeightEdges}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalWeightEdges(val)
                        setWeightEdges(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="weightEdges"
                    value={[localWeightEdges]}
                    onValueChange={(values) => setLocalWeightEdges(values[0])}
                    onValueCommit={(values) => setWeightEdges(values[0])}
                    min={0}
                    max={2}
                    step={0.1}
                  />
                  <p className="body-sm text-muted-foreground">
                    Weight for edge feature points
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="weightIntersections" className="label-text">
                      Intersection Weight
                    </Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={localWeightIntersections}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalWeightIntersections(val)
                        setWeightIntersections(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="weightIntersections"
                    value={[localWeightIntersections]}
                    onValueChange={(values) => setLocalWeightIntersections(values[0])}
                    onValueCommit={(values) => setWeightIntersections(values[0])}
                    min={0}
                    max={2}
                    step={0.1}
                  />
                  <p className="body-sm text-muted-foreground">
                    Weight for intersection points
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="weightSymmetry" className="label-text">
                      Symmetry Weight
                    </Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={localWeightSymmetry}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalWeightSymmetry(val)
                        setWeightSymmetry(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="weightSymmetry"
                    value={[localWeightSymmetry]}
                    onValueChange={(values) => setLocalWeightSymmetry(values[0])}
                    onValueCommit={(values) => setWeightSymmetry(values[0])}
                    min={0}
                    max={2}
                    step={0.1}
                  />
                  <p className="body-sm text-muted-foreground">
                    Weight for symmetry center points
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="maxPoints" className="label-text">
                      Max Points
                    </Label>
                    <Input
                      type="number"
                      value={localMaxPoints}
                      onChange={(e) => {
                        const val = Number(e.target.value)
                        setLocalMaxPoints(val)
                        setMaxPoints(val)
                      }}
                      className="w-20"
                    />
                  </div>
                  <Slider
                    id="maxPoints"
                    value={[localMaxPoints]}
                    onValueChange={(values) => setLocalMaxPoints(values[0])}
                    onValueCommit={(values) => setMaxPoints(values[0])}
                    min={10}
                    max={10000}
                    step={10}
                  />
                  <p className="body-sm text-muted-foreground">
                    Maximum number of points to extract
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="manual" className="space-y-4 mt-4">
              <div className="space-y-3">
                <Label className="label-text">Editing Tools</Label>
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    variant={selectedTool === 'add' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedTool(selectedTool === 'add' ? null : 'add')}
                    className="w-full"
                  >
                    <MousePointer2 className="mr-2 h-4 w-4" />
                    Add
                  </Button>
                  <Button
                    variant={selectedTool === 'delete' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedTool(selectedTool === 'delete' ? null : 'delete')}
                    className="w-full"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                  <Button
                    variant={selectedTool === 'move' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedTool(selectedTool === 'move' ? null : 'move')}
                    className="w-full"
                  >
                    <Move className="mr-2 h-4 w-4" />
                    Move
                  </Button>
                </div>
                <div className="rounded-lg bg-muted p-3">
                  <p className="body-sm text-muted-foreground">
                    {selectedTool === 'add' && '• Click anywhere to add a point\n• Points auto-snap to detected features'}
                    {selectedTool === 'delete' && '• Click on any point to remove it'}
                    {selectedTool === 'move' && '• Drag points to reposition them\n• Points auto-snap to detected features'}
                    {!selectedTool && 'Select a tool to begin editing'}
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <div className="border-t border-border pt-6">
            {/* Clear All Points Button */}
            <Button
              variant="destructive"
              className="w-full mb-4"
              onClick={() => {
                if (confirm('Clear all points? This action cannot be undone.')) {
                  clearPointsHistory()
                }
              }}
              disabled={adjustedPoints.length === 0}
            >
              <X className="mr-2 h-4 w-4" />
              Clear All Points
            </Button>

            <div className="mb-4 space-y-2">
              <div className="flex justify-between body-sm">
                <span className="text-muted-foreground">Total Points:</span>
                <span className="font-semibold">{totalPoints}</span>
              </div>
              <div className="flex justify-between body-sm">
                <span className="text-muted-foreground">Edge Points:</span>
                <span className="font-semibold">{edgePoints}</span>
              </div>
              <div className="flex justify-between body-sm">
                <span className="text-muted-foreground">Center Points:</span>
                <span className="font-semibold">{centerPoints}</span>
              </div>
            </div>

            {/* Frame count slider */}
            <div className="mb-4 space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="frameCount" className="label-text">
                  Animation Frames
                </Label>
                <Input
                  type="number"
                  value={frameCount}
                  onChange={(e) => setFrameCount(Number(e.target.value))}
                  className="w-20"
                />
              </div>
              <Slider
                id="frameCount"
                value={[frameCount]}
                onValueChange={(values) => setFrameCount(values[0])}
                min={10}
                max={120}
                step={5}
              />
              <p className="body-sm text-muted-foreground">
                Number of frames for 2D to 3D animation
              </p>
            </div>

            <Button
              onClick={() => setCurrentStep('view3d')}
              className="w-full"
              disabled={isLoading || totalPoints === 0}
            >
              Generate 3D Model
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}