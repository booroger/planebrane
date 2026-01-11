# Cymatic Vibration Animation

## Overview
The Cymatic vibration animation creates a living, breathing energy field effect on the 3D crop circle models using custom GLSL shaders. This simulates standing waves and interference patterns similar to physical Cymatic phenomena.

## Features

### 1. Standing Wave Effect
- **Purpose**: Makes the shape pulse or breathe in and out
- **Formula**: `FinalZ = InputZ × sin(Time × Speed)`
- **Controls**:
  - Wave Speed (0.1 - 5.0): Controls how fast the shape breathes
  - Wave Intensity (0 - 3.0): Controls the amplitude of the pulsing

### 2. Ripple Propagation
- **Purpose**: Creates interference patterns radiating from center
- **Implementation**: Radial sine waves with time-based phase shift
- **Controls**:
  - Ripple Speed (0.1 - 3.0): Controls propagation speed
  - Ripple Intensity (0 - 0.5): Controls displacement amplitude

### 3. Visual Appearance
- Semi-transparent metallic/liquid material
- Fresnel edge lighting for energy grid effect
- Gradient color blending from center to edge
- Shimmer effect based on position and time

## Usage

### In the Main App
1. Navigate to the **3D VIEW** step
2. Select **Solid** render mode from the rendering controls
3. Scroll down to find the **Cymatic Vibration** card
4. Toggle on "Standing Wave" and/or "Ripple Propagation"
5. Adjust the speed and intensity sliders to taste

### Standalone Test
Open `frontend/shader-test.html` in a browser to test the shader independently:
```bash
# From the frontend directory
cd frontend
# Open in browser
open shader-test.html  # macOS
start shader-test.html # Windows
xdg-open shader-test.html # Linux
```

Or access via dev server:
```
http://localhost:5173/shader-test.html
```

## Technical Implementation

### Files
- `src/components/CymaticShaderMaterial.tsx` - Main shader component
- `src/components/CymaticGeometry.tsx` - Geometry wrapper using the shader
- `src/components/View3DSection.tsx` - UI controls integration
- `src/store/useAppStore.ts` - State management for animation parameters

### Shader Details

**Vertex Shader**:
- Transforms vertices along surface normals for ripple effect
- Scales entire mesh uniformly for breathing effect
- Calculates distance from center for radial patterns

**Fragment Shader**:
- Gradient color mixing based on distance from center
- Fresnel effect for metallic/liquid appearance
- Time-based shimmer overlay

## Fixes Applied

### Issue 1: Fullscreen Button Not Working
- **Problem**: Button had no onClick handler
- **Fix**: Added `handleFullscreen` callback with proper fullscreen API calls
- **Location**: `View3DSection.tsx:231-247`

### Issue 2: Shader Effects Not Visible
- **Problem**: 
  - Shader only applies to "Solid" render mode
  - Default render mode was "Lines"
  - Controls were hidden unless in solid mode
- **Fix**: 
  - Improved shader vertex transformations for more pronounced effects
  - Added better visual feedback in controls
  - Created standalone test page to verify shader works

## Default Values
```typescript
waveSpeed: 1.0        // Moderate breathing rate
waveAmplitude: 1.0    // Noticeable but not extreme
rippleSpeed: 0.5      // Slower wave propagation  
rippleAmplitude: 0.15 // Subtle displacement
enableStandingWave: true
enableRipple: true
```

## Performance Notes
- Shader runs entirely on GPU
- Minimal CPU overhead
- Real-time animation at 60 FPS
- Works well with meshes up to 50K vertices

## Troubleshooting

**Shader not visible?**
1. Make sure you're in **Solid** render mode
2. Check that at least one effect is enabled (Standing Wave or Ripple)
3. Try increasing the intensity sliders
4. Test with the standalone `shader-test.html` page

**Performance issues?**
1. Reduce mesh complexity (lower subdivision level)
2. Disable one of the effects
3. Lower the wave/ripple intensity

**Fullscreen not working?**
1. Browser must support Fullscreen API
2. User gesture (click) required to enter fullscreen
3. Some browsers block fullscreen in iframes