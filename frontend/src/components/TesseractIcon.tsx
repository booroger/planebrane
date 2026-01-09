interface TesseractIconProps {
  className?: string
}

export function TesseractIcon({ className }: TesseractIconProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer cube */}
      <path
        d="M 30 25 L 70 25 L 70 65 L 30 65 Z"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 30 25 L 20 15 L 60 15 L 70 25"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 70 25 L 60 15 L 60 55 L 70 65"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 30 65 L 20 55 L 60 55 L 70 65"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 30 25 L 20 15 L 20 55 L 30 65"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 20 15 L 60 15 L 60 55 L 20 55 Z"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />

      {/* Inner cube */}
      <path
        d="M 40 35 L 60 35 L 60 55 L 40 55 Z"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 40 35 L 35 30 L 55 30 L 60 35"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 60 35 L 55 30 L 55 50 L 60 55"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 40 55 L 35 50 L 55 50 L 60 55"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 40 35 L 35 30 L 35 50 L 40 55"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 35 30 L 55 30 L 55 50 L 35 50 Z"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />

      {/* Connecting lines between cubes */}
      <path d="M 30 25 L 40 35" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 70 25 L 60 35" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 30 65 L 40 55" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 70 65 L 60 55" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 20 15 L 35 30" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 60 15 L 55 30" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 20 55 L 35 50" stroke="currentColor" strokeWidth="1.5" />
      <path d="M 60 55 L 55 50" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}