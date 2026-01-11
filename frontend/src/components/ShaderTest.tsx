import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { CymaticShaderMaterial } from './CymaticShaderMaterial'
import * as THREE from 'three'
import { useMemo } from 'react'

function TestTorus() {
  const geometry = useMemo(() => {
    return new THREE.TorusGeometry(1.2, 0.4, 24, 48)
  }, [])

  return (
    <mesh geometry={geometry}>
      <CymaticShaderMaterial
        color="#00CCCC"
        color2="#1560BD"
        useGradient={true}
        opacity={0.9}
        waveSpeed={1.0}
        waveAmplitude={1.0}
        rippleSpeed={0.5}
        rippleAmplitude={0.15}
        enableStandingWave={true}
        enableRipple={true}
      />
    </mesh>
  )
}

export function ShaderTest() {
  return (
    <div className="h-screen w-screen bg-black">
      <Canvas camera={{ position: [4, 2, 4], fov: 50 }}>
        <OrbitControls />
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <TestTorus />
        <gridHelper args={[20, 20]} />
      </Canvas>
    </div>
  )
}