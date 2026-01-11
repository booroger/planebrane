import { useRef, useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface CymaticShaderMaterialProps {
  color?: string
  color2?: string
  useGradient?: boolean
  opacity?: number
  children?: React.ReactNode
  waveSpeed?: number
  waveAmplitude?: number
  rippleSpeed?: number
  rippleAmplitude?: number
  enableStandingWave?: boolean
  enableRipple?: boolean
}

export function CymaticShaderMaterial({
  color = '#00CCCC',
  color2 = '#1560BD',
  useGradient = false,
  opacity = 0.9,
  children,
  waveSpeed = 1.0,
  waveAmplitude = 1.0,
  rippleSpeed = 0.5,
  rippleAmplitude = 0.15,
  enableStandingWave = true,
  enableRipple = true,
}: CymaticShaderMaterialProps) {
  const materialRef = useRef<THREE.ShaderMaterial>(null)

  // Convert hex colors to RGB
  const color1RGB = useMemo(() => new THREE.Color(color), [color])
  const color2RGB = useMemo(() => new THREE.Color(color2), [color2])

  // Custom shader material with Cymatic vibration
  const shaderUniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor1: { value: color1RGB },
    uColor2: { value: color2RGB },
    uUseGradient: { value: useGradient ? 1.0 : 0.0 },
    uOpacity: { value: opacity },
    uWaveSpeed: { value: waveSpeed },
    uWaveAmplitude: { value: waveAmplitude },
    uRippleSpeed: { value: rippleSpeed },
    uRippleAmplitude: { value: rippleAmplitude },
    uEnableStandingWave: { value: enableStandingWave ? 1.0 : 0.0 },
    uEnableRipple: { value: enableRipple ? 1.0 : 0.0 },
  }), [color1RGB, color2RGB, useGradient, opacity, waveSpeed, waveAmplitude, rippleSpeed, rippleAmplitude, enableStandingWave, enableRipple])

  // Update uniforms when props change
  useEffect(() => {
    if (materialRef.current) {
      materialRef.current.uniforms.uColor1.value = color1RGB
      materialRef.current.uniforms.uColor2.value = color2RGB
      materialRef.current.uniforms.uUseGradient.value = useGradient ? 1.0 : 0.0
      materialRef.current.uniforms.uOpacity.value = opacity
      materialRef.current.uniforms.uWaveSpeed.value = waveSpeed
      materialRef.current.uniforms.uWaveAmplitude.value = waveAmplitude
      materialRef.current.uniforms.uRippleSpeed.value = rippleSpeed
      materialRef.current.uniforms.uRippleAmplitude.value = rippleAmplitude
      materialRef.current.uniforms.uEnableStandingWave.value = enableStandingWave ? 1.0 : 0.0
      materialRef.current.uniforms.uEnableRipple.value = enableRipple ? 1.0 : 0.0
    }
  }, [color1RGB, color2RGB, useGradient, opacity, waveSpeed, waveAmplitude, rippleSpeed, rippleAmplitude, enableStandingWave, enableRipple])

  // Animate time uniform
  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime
    }
  })

  // Vertex Shader: Apply standing wave and ripple effects
  const vertexShader = `
    uniform float uTime;
    uniform float uWaveSpeed;
    uniform float uWaveAmplitude;
    uniform float uRippleSpeed;
    uniform float uRippleAmplitude;
    uniform float uEnableStandingWave;
    uniform float uEnableRipple;
    
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying float vDistanceFromCenter;
    
    void main() {
      vNormal = normalize(normalMatrix * normal);
      
      // Calculate distance from center (XZ plane for horizontal distance)
      vec2 centerXZ = vec2(0.0, 0.0);
      vec2 posXZ = vec2(position.x, position.z);
      vDistanceFromCenter = length(posXZ - centerXZ);
      
      vec3 newPosition = position;
      
      // Standing Wave Effect: Pulsing/breathing effect
      // Multiplies the entire position by a sine wave to create breathing
      float waveEffect = 0.0;
      if (uEnableStandingWave > 0.5) {
        float standingWave = sin(uTime * uWaveSpeed * 2.0);
        waveEffect = standingWave * uWaveAmplitude * 0.3;
        
        // Apply to all axes for a breathing effect, stronger on Y
        newPosition = position * (1.0 + waveEffect);
      }
      
      // Ripple Propagation: Radial wave from center
      // Creates interference pattern radiating outward
      if (uEnableRipple > 0.5) {
        float rippleFreq = 8.0;
        float ripple = sin(vDistanceFromCenter * rippleFreq - uTime * uRippleSpeed * 5.0);
        
        // Apply ripple along the normal direction for natural wave propagation
        newPosition += normal * ripple * uRippleAmplitude;
      }
      
      vPosition = newPosition;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    }
  `

  // Fragment Shader: Semi-transparent metallic/liquid appearance
  const fragmentShader = `
    uniform vec3 uColor1;
    uniform vec3 uColor2;
    uniform float uUseGradient;
    uniform float uOpacity;
    uniform float uTime;
    
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying float vDistanceFromCenter;
    
    void main() {
      vec3 baseColor = uColor1;
      
      // Gradient based on distance from center
      if (uUseGradient > 0.5) {
        float t = vDistanceFromCenter / 2.0; // Normalize distance
        t = clamp(t, 0.0, 1.0);
        baseColor = mix(uColor1, uColor2, t);
      }
      
      // Add subtle shimmer effect based on time and position
      float shimmer = sin(vDistanceFromCenter * 3.0 + uTime * 2.0) * 0.1 + 0.9;
      baseColor *= shimmer;
      
      // Fresnel effect for metallic/liquid appearance
      vec3 viewDirection = normalize(cameraPosition - vPosition);
      float fresnel = pow(1.0 - abs(dot(viewDirection, vNormal)), 2.0);
      
      // Enhance edges with fresnel
      vec3 finalColor = baseColor + vec3(fresnel * 0.3);
      
      gl_FragColor = vec4(finalColor, uOpacity);
    }
  `

  return (
    <shaderMaterial
      ref={materialRef}
      vertexShader={vertexShader}
      fragmentShader={fragmentShader}
      uniforms={shaderUniforms}
      transparent
      opacity={opacity}
      side={THREE.DoubleSide}
      blending={THREE.AdditiveBlending}
      depthWrite={false}
      lights={false}
    >
      {children}
    </shaderMaterial>
  )
}