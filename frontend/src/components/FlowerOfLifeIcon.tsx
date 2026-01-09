interface FlowerOfLifeIconProps {
  className?: string
}

export function FlowerOfLifeIcon({ className }: FlowerOfLifeIconProps) {
  const r = 33.33 // radius of each circle
  const cx = 100 // center x
  const cy = 100 // center y
  
  // Calculate positions for the 6 surrounding circles in hexagonal pattern
  const positions = [
    { x: cx, y: cy }, // center
    { x: cx + r, y: cy }, // right
    { x: cx + r/2, y: cy + r * Math.sqrt(3)/2 }, // bottom-right
    { x: cx - r/2, y: cy + r * Math.sqrt(3)/2 }, // bottom-left
    { x: cx - r, y: cy }, // left
    { x: cx - r/2, y: cy - r * Math.sqrt(3)/2 }, // top-left
    { x: cx + r/2, y: cy - r * Math.sqrt(3)/2 }, // top-right
  ]

  // Outer ring of circles
  const outerPositions = [
    { x: cx + 2*r, y: cy },
    { x: cx + 3*r/2, y: cy + r * Math.sqrt(3)/2 },
    { x: cx + r, y: cy + r * Math.sqrt(3) },
    { x: cx, y: cy + r * Math.sqrt(3) },
    { x: cx - r, y: cy + r * Math.sqrt(3) },
    { x: cx - 3*r/2, y: cy + r * Math.sqrt(3)/2 },
    { x: cx - 2*r, y: cy },
    { x: cx - 3*r/2, y: cy - r * Math.sqrt(3)/2 },
    { x: cx - r, y: cy - r * Math.sqrt(3) },
    { x: cx, y: cy - r * Math.sqrt(3) },
    { x: cx + r, y: cy - r * Math.sqrt(3) },
    { x: cx + 3*r/2, y: cy - r * Math.sqrt(3)/2 },
  ]

  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer boundary circle */}
      <circle
        cx={cx}
        cy={cy}
        r={r * 3}
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
      />

      {/* Outer ring of 12 circles */}
      {outerPositions.map((pos, i) => (
        <circle
          key={`outer-${i}`}
          cx={pos.x}
          cy={pos.y}
          r={r}
          stroke="currentColor"
          strokeWidth="2.5"
          fill="none"
        />
      ))}

      {/* Inner 7 circles (including center) */}
      {positions.map((pos, i) => (
        <circle
          key={`inner-${i}`}
          cx={pos.x}
          cy={pos.y}
          r={r}
          stroke="currentColor"
          strokeWidth="2.5"
          fill="none"
        />
      ))}
    </svg>
  )
}