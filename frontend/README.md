# PlaneBrane Frontend

Modern, intuitive frontend for the PlaneBrane geometric pattern to 3D transformation application.

## Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 7
- **UI Components**: shadcn (with Tailwind CSS v4)
- **State Management**: Zustand
- **API Client**: TanStack Query
- **3D Rendering**: Three.js with React Three Fiber
- **Icons**: Lucide React
- **Desktop**: Tauri (for standalone Windows app)

## Features

### 1. Image Upload Interface
- Drag-and-drop image upload
- Support for JPG, PNG, SVG formats
- Sample pattern library
- Image preview with editing capabilities

### 2. Pattern Analysis Visualization
- Real-time pattern analysis
- Geometric feature detection overlay
- Symmetry detection and visualization
- Confidence scoring

### 3. Interactive Point Adjustment
- Visual point overlay on pattern
- Draggable points for manual adjustment
- Slider controls for:
  - Point density
  - Detection threshold
  - Minimum spacing
  - Weighting factors
- Real-time visualization updates

### 4. 3D Visualization
- Interactive 3D model viewer
- Split-screen original pattern comparison
- Full-screen viewing mode
- Orbit controls (rotate, zoom, pan)
- Wireframe toggle
- Lighting adjustments

### 5. Export Options
- Multiple format support (STL, OBJ, GLTF)
- Quality/resolution options
- Progress indicators
- Model statistics display

## Getting Started

### Prerequisites
- Node.js 20.19+ or 22.12+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The application will start on `http://localhost:5173`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/             # shadcn UI components
│   │   ├── Layout.tsx      # Main layout wrapper
│   │   ├── StepIndicator.tsx
│   │   ├── UploadSection.tsx
│   │   ├── AnalysisSection.tsx
│   │   ├── AdjustSection.tsx
│   │   ├── View3DSection.tsx
│   │   └── ExportSection.tsx
│   ├── lib/                # Utilities
│   │   ├── api.ts          # API client
│   │   └── utils.ts        # Helper functions
│   ├── store/              # State management
│   │   └── useAppStore.ts  # Zustand store
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles & theme
├── public/                 # Static assets
└── package.json
```

## Design System

### Color Palette
- **Primary**: Tech Blue (#1560BD) - Actions and primary elements
- **Accent**: Strong Cyan (#00CCCC) - Highlights and interactive states
- **Background**: Clean white/dark slate depending on theme
- **Borders**: Subtle grays for depth and separation

### Typography
- **Headings**: Space Grotesk (geometric, modern)
- **Body**: Source Sans 3 (readable, professional)

### Theme
The application supports both light and dark modes with carefully selected colors for optimal contrast and accessibility.

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000/api/v1` with the following endpoints:

- `POST /images/analyze` - Upload and analyze pattern image
- `POST /points/adjust` - Adjust point detection parameters
- `POST /models3d/generate` - Generate 3D model from points
- `GET /export/{modelId}` - Export model in specified format

## Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Follow shadcn component patterns
4. Maintain consistent styling with Tailwind CSS
5. Test all features before committing

## License

MIT