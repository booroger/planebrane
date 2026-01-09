# Line Width Control Fix for Cymatic Geometries

## Problem
The line width control wasn't working because THREE.js's `wireframeLinewidth` property doesn't work in WebGL - it's a known limitation.

## Solution
Implemented proper line rendering using `@react-three/drei`'s `Line` component which supports actual line thickness control.

## Changes Made

### 1. New Components
- **`CymaticGeometry.tsx`**: Renders 3D geometry with multiple modes
  - Solid: Standard mesh rendering
  - Wireframe: Proper wireframe with controllable line thickness
  - **Cymatic**: Creates geometric interconnections like crop circles (radial layers)
  - Points: Vertex-only visualization

### 2. Render Modes
The new system provides 4 render modes optimized for complex cymatic patterns:

- **Cymatic Mode**: Creates interconnected geometric patterns by:
  - Organizing vertices into radial layers from center
  - Connecting vertices within each layer
  - Creating radial connections between layers
  - Limiting connections based on distance for aesthetic patterns

### 3. Line Width Control
- Now properly controls thickness in Wireframe and Cymatic modes
- Uses `@react-three/drei`'s Line component instead of WebGL wireframe
- Range: 0.5 to 10 pixels
- Real-time updates

### 4. Enhanced 3D Viewer
- Better camera positioning and controls
- Improved lighting setup (ambient + directional + point lights)
- Gradient background
- Gizmo helper for orientation
- Smooth animation between 2D and 3D

## How It Works

The Cymatic render mode creates complex geometric patterns by:

1. Calculating distance of each vertex from center
2. Organizing vertices into 8 radial layers
3. Connecting nearby vertices within each layer
4. Creating radial connections to the next layer
5. Limiting total connections for performance (max 300 lines)

This creates patterns similar to the crop circle/cymatic imagery provided:
- Radial symmetry
- Layered interconnections
- Geometric complexity
- Sacred geometry aesthetics

## Usage

1. Navigate to the 3D View section
2. Select "Cymatic" render mode
3. Adjust "Line Thickness" slider (0.5-10)
4. Use animation controls to see 2D→3D transformation
5. Orbit with mouse, zoom with buttons or scroll

## Technical Notes

- Uses `@react-three/drei` Line component for proper WebGL line rendering
- Mock torus generator creates patterns from detected 2D points
- Each edge/connection is rendered as individual Line component
- Performance optimized with connection limits and layer-based algorithm