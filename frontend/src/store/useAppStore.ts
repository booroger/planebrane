import { create } from 'zustand'

export interface Point2D {
  x: number
  y: number
  weight: number
  feature_type: string
}

export interface PatternAnalysis {
  pattern_type: string
  confidence: number
  symmetry_axes: number
  detected_points: Point2D[]
}

export interface StepState {
  step: 'upload' | 'analyze' | 'adjust' | 'view3d' | 'export'
  data: {
    uploadedImage?: string | null
    uploadedImageFile?: File | null
    imageId?: string | null
    patternAnalysis?: PatternAnalysis | null
    adjustedPoints?: Point2D[]
    pointDensity?: number
    detectionThreshold?: number
    minimumSpacing?: number
    weightingFactor?: number
    editMode?: 'automatic' | 'manual'
    selectedTool?: 'add' | 'delete' | 'move' | null
    geometricFeatures?: Array<{ x: number; y: number; type: 'corner' | 'edge' | 'curve' | 'intersection'; confidence: number }>
    frameCount?: number
    currentFrame?: number
    lineWidth?: number
  }
}

export interface ProjectData {
  version: string
  createdAt: string
  currentStep: string
  uploadedImage: string | null
  patternAnalysis: PatternAnalysis | null
  adjustedPoints: Point2D[]
  pointDensity: number
  detectionThreshold: number
  minimumSpacing: number
  weightingFactor: number
  frameCount: number
  lineWidth: number
  modelColor: string
  modelColor2: string
  useGradient: boolean
}

interface AppState {
  // Current workflow step
  currentStep: 'upload' | 'analyze' | 'adjust' | 'view3d' | 'export'
  setCurrentStep: (step: AppState['currentStep']) => void

  // Navigation history
  stepHistory: StepState[]
  currentHistoryIndex: number
  canGoBack: boolean
  canGoForward: boolean
  goBack: () => void
  goForward: () => void
  addToHistory: (state: StepState) => void

  // Uploaded image
  uploadedImage: string | null
  uploadedImageFile: File | null
  imageId: string | null
  setUploadedImage: (image: string | null, file: File | null) => void
  setImageId: (id: string | null) => void

  // Backend resource IDs
  pointsExtractionId: string | null
  modelId: string | null
  setPointsExtractionId: (id: string | null) => void
  setModelId: (id: string | null) => void

  // Pattern analysis results
  patternAnalysis: PatternAnalysis | null
  setPatternAnalysis: (analysis: PatternAnalysis | null) => void

  // Point adjustment parameters
  pointDensity: number
  detectionThreshold: number
  minimumSpacing: number
  weightingFactor: number
  setPointDensity: (value: number) => void
  setDetectionThreshold: (value: number) => void
  setMinimumSpacing: (value: number) => void
  setWeightingFactor: (value: number) => void

  // Adjusted points
  adjustedPoints: Point2D[]
  setAdjustedPoints: (points: Point2D[]) => void

  // Undo/Redo for points editing
  pointsHistory: Point2D[][]
  pointsHistoryIndex: number
  canUndo: boolean
  canRedo: boolean
  undo: () => void
  redo: () => void
  clearPointsHistory: () => void
  addPointsToHistory: (points: Point2D[]) => void

  // Point editing mode
  editMode: 'automatic' | 'manual'
  setEditMode: (mode: 'automatic' | 'manual') => void

  // Detected geometric features for snapping
  geometricFeatures: Array<{ x: number; y: number; type: 'corner' | 'edge' | 'curve' | 'intersection'; confidence: number }>
  setGeometricFeatures: (features: Array<{ x: number; y: number; type: 'corner' | 'edge' | 'curve' | 'intersection'; confidence: number }>) => void

  // Manual editing tool
  selectedTool: 'add' | 'delete' | 'move' | null
  setSelectedTool: (tool: 'add' | 'delete' | 'move' | null) => void

  // Animation controls
  frameCount: number
  currentFrame: number
  isAnimating: boolean
  setFrameCount: (count: number) => void
  setCurrentFrame: (frame: number) => void
  setIsAnimating: (animating: boolean) => void

  // 3D rendering controls
  lineWidth: number
  setLineWidth: (width: number) => void
  modelColor: string
  modelColor2: string
  useGradient: boolean
  setModelColor: (color: string) => void
  setModelColor2: (color: string) => void
  setUseGradient: (use: boolean) => void

  // 3D Model state
  modelGenerated: boolean
  setModelGenerated: (generated: boolean) => void

  // Theme
  isDarkMode: boolean
  toggleDarkMode: () => void

  // Project management
  projectName: string
  setProjectName: (name: string) => void
  getProjectData: () => ProjectData
  loadProjectData: (data: ProjectData) => void

  // Reset
  reset: () => void
}

const initialState = {
  currentStep: 'upload' as const,
  uploadedImage: null,
  uploadedImageFile: null,
  imageId: null,
  pointsExtractionId: null,
  modelId: null,
  patternAnalysis: null,
  pointDensity: 50,
  detectionThreshold: 100,
  minimumSpacing: 5,
  weightingFactor: 1.0,
  adjustedPoints: [],
  editMode: 'automatic' as const,
  geometricFeatures: [],
  selectedTool: null,
  modelGenerated: false,
  frameCount: 30,
  currentFrame: 0,
  lineWidth: 2,
  modelColor: '#00CCCC',
  modelColor2: '#1560BD',
  useGradient: false,
  projectName: 'Untitled Project',
  stepHistory: [],
  currentHistoryIndex: -1,
  pointsHistory: [],
  pointsHistoryIndex: -1,
  isAnimating: false,
}

export const useAppStore = create<AppState>((set, get) => ({
  ...initialState,
  isDarkMode: false,

  setCurrentStep: (step) => {
    const currentState = get()
    const newStepState: StepState = {
      step,
      data: {
        uploadedImage: currentState.uploadedImage,
        uploadedImageFile: currentState.uploadedImageFile,
        imageId: currentState.imageId,
        patternAnalysis: currentState.patternAnalysis,
        adjustedPoints: currentState.adjustedPoints,
        pointDensity: currentState.pointDensity,
        detectionThreshold: currentState.detectionThreshold,
        minimumSpacing: currentState.minimumSpacing,
        weightingFactor: currentState.weightingFactor,
        editMode: currentState.editMode,
        selectedTool: currentState.selectedTool,
        geometricFeatures: currentState.geometricFeatures,
        frameCount: currentState.frameCount,
        currentFrame: currentState.currentFrame,
        lineWidth: currentState.lineWidth,
      }
    }

    set({ currentStep: step })
    get().addToHistory(newStepState)
  },

  // Navigation history
  canGoBack: false,
  canGoForward: false,

  addToHistory: (state) => {
    const { stepHistory, currentHistoryIndex } = get()
    const newHistory = stepHistory.slice(0, currentHistoryIndex + 1)
    newHistory.push(state)

    set({
      stepHistory: newHistory,
      currentHistoryIndex: newHistory.length - 1,
      canGoBack: newHistory.length > 1,
      canGoForward: false,
    })
  },

  goBack: () => {
    const { currentHistoryIndex, stepHistory } = get()
    if (currentHistoryIndex > 0) {
      const newIndex = currentHistoryIndex - 1
      const previousState = stepHistory[newIndex]

      set({
        currentHistoryIndex: newIndex,
        currentStep: previousState.step,
        ...previousState.data,
        canGoBack: newIndex > 0,
        canGoForward: true,
      })
    }
  },

  goForward: () => {
    const { currentHistoryIndex, stepHistory } = get()
    if (currentHistoryIndex < stepHistory.length - 1) {
      const newIndex = currentHistoryIndex + 1
      const nextState = stepHistory[newIndex]

      set({
        currentHistoryIndex: newIndex,
        currentStep: nextState.step,
        ...nextState.data,
        canGoBack: true,
        canGoForward: newIndex < stepHistory.length - 1,
      })
    }
  },

  setUploadedImage: (image, file) => set({ uploadedImage: image, uploadedImageFile: file }),
  setImageId: (id) => set({ imageId: id }),
  setPointsExtractionId: (id) => set({ pointsExtractionId: id }),
  setModelId: (id) => set({ modelId: id }),

  setPatternAnalysis: (analysis) => set({ patternAnalysis: analysis }),

  setPointDensity: (value) => set({ pointDensity: value }),
  setDetectionThreshold: (value) => set({ detectionThreshold: value }),
  setMinimumSpacing: (value) => set({ minimumSpacing: value }),
  setWeightingFactor: (value) => set({ weightingFactor: value }),

  setAdjustedPoints: (points) => {
    set({ adjustedPoints: points })
    get().addPointsToHistory(points)
  },

  // Undo/Redo for points
  canUndo: false,
  canRedo: false,

  addPointsToHistory: (points) => {
    const { pointsHistory, pointsHistoryIndex } = get()
    const newHistory = pointsHistory.slice(0, pointsHistoryIndex + 1)
    newHistory.push([...points])

    set({
      pointsHistory: newHistory,
      pointsHistoryIndex: newHistory.length - 1,
      canUndo: newHistory.length > 1,
      canRedo: false,
    })
  },

  undo: () => {
    const { pointsHistoryIndex, pointsHistory } = get()
    if (pointsHistoryIndex > 0) {
      const newIndex = pointsHistoryIndex - 1
      set({
        adjustedPoints: [...pointsHistory[newIndex]],
        pointsHistoryIndex: newIndex,
        canUndo: newIndex > 0,
        canRedo: true,
      })
    }
  },

  redo: () => {
    const { pointsHistoryIndex, pointsHistory } = get()
    if (pointsHistoryIndex < pointsHistory.length - 1) {
      const newIndex = pointsHistoryIndex + 1
      set({
        adjustedPoints: [...pointsHistory[newIndex]],
        pointsHistoryIndex: newIndex,
        canUndo: true,
        canRedo: newIndex < pointsHistory.length - 1,
      })
    }
  },

  clearPointsHistory: () => {
    set({
      adjustedPoints: [],
      pointsHistory: [[]],
      pointsHistoryIndex: 0,
      canUndo: false,
      canRedo: false,
    })
  },

  setEditMode: (mode) => set({ editMode: mode }),

  setGeometricFeatures: (features) => set({ geometricFeatures: features }),

  setSelectedTool: (tool) => set({ selectedTool: tool }),

  // Animation controls
  frameCount: 30,
  currentFrame: 0,
  isAnimating: false,
  setFrameCount: (count) => set({ frameCount: count, currentFrame: 0 }),
  setCurrentFrame: (frame) => set({ currentFrame: frame }),
  setIsAnimating: (animating) => set({ isAnimating: animating }),

  // 3D rendering controls
  lineWidth: 2,
  setLineWidth: (width) => set({ lineWidth: width }),
  modelColor: '#00CCCC',
  modelColor2: '#1560BD',
  useGradient: false,
  setModelColor: (color) => set({ modelColor: color }),
  setModelColor2: (color) => set({ modelColor2: color }),
  setUseGradient: (use) => set({ useGradient: use }),

  modelGenerated: false,
  setModelGenerated: (generated) => set({ modelGenerated: generated }),

  toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),

  // Project management
  projectName: 'Untitled Project',
  setProjectName: (name) => set({ projectName: name }),

  getProjectData: () => {
    const state = get()
    return {
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      currentStep: state.currentStep,
      uploadedImage: state.uploadedImage,
      patternAnalysis: state.patternAnalysis,
      adjustedPoints: state.adjustedPoints,
      pointDensity: state.pointDensity,
      detectionThreshold: state.detectionThreshold,
      minimumSpacing: state.minimumSpacing,
      weightingFactor: state.weightingFactor,
      frameCount: state.frameCount,
      lineWidth: state.lineWidth,
      modelColor: state.modelColor,
      modelColor2: state.modelColor2,
      useGradient: state.useGradient,
    }
  },

  loadProjectData: (data) => {
    set({
      currentStep: data.currentStep as AppState['currentStep'],
      uploadedImage: data.uploadedImage,
      patternAnalysis: data.patternAnalysis,
      adjustedPoints: data.adjustedPoints,
      pointDensity: data.pointDensity,
      detectionThreshold: data.detectionThreshold,
      minimumSpacing: data.minimumSpacing,
      weightingFactor: data.weightingFactor,
      frameCount: data.frameCount,
      lineWidth: data.lineWidth,
      modelColor: data.modelColor || '#00CCCC',
      modelColor2: data.modelColor2 || '#1560BD',
      useGradient: data.useGradient || false,
    })
  },

  reset: () => set({
    ...initialState,
    isDarkMode: get().isDarkMode,
  }),
}))