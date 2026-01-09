interface TorusIconProps {
  className?: string
}

export function TorusIcon({ className }: TorusIconProps) {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer shell - top curves */}
      <path
        d="M 40 100 Q 50 40, 100 30 Q 150 40, 160 100"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M 45 100 Q 55 50, 100 40 Q 145 50, 155 100"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
      />
      <path
        d="M 50 100 Q 60 60, 100 50 Q 140 60, 150 100"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 55 100 Q 65 70, 100 60 Q 135 70, 145 100"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />

      {/* Outer shell - bottom curves */}
      <path
        d="M 40 100 Q 50 160, 100 170 Q 150 160, 160 100"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M 45 100 Q 55 150, 100 160 Q 145 150, 155 100"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
      />
      <path
        d="M 50 100 Q 60 140, 100 150 Q 140 140, 150 100"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 55 100 Q 65 130, 100 140 Q 135 130, 145 100"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />

      {/* Inner hole - top curves */}
      <path
        d="M 70 100 Q 75 85, 100 82 Q 125 85, 130 100"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 75 100 Q 80 90, 100 88 Q 120 90, 125 100"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />

      {/* Inner hole - bottom curves */}
      <path
        d="M 70 100 Q 75 115, 100 118 Q 125 115, 130 100"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M 75 100 Q 80 110, 100 112 Q 120 110, 125 100"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />

      {/* Side curves - left */}
      <path
        d="M 40 100 Q 35 100, 40 100"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
      />
      <ellipse
        cx="40"
        cy="100"
        rx="8"
        ry="50"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
      />
      <ellipse
        cx="45"
        cy="100"
        rx="6"
        ry="40"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <ellipse
        cx="50"
        cy="100"
        rx="5"
        ry="35"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />

      {/* Side curves - right */}
      <ellipse
        cx="160"
        cy="100"
        rx="8"
        ry="50"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
      />
      <ellipse
        cx="155"
        cy="100"
        rx="6"
        ry="40"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
      <ellipse
        cx="150"
        cy="100"
        rx="5"
        ry="35"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />

      {/* Vertical grid lines */}
      <path
        d="M 100 30 Q 98 50, 100 82 Q 102 110, 100 118 Q 98 150, 100 170"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
        opacity="0.6"
      />
      <path
        d="M 70 65 Q 68 80, 70 100 Q 72 120, 70 135"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.5"
      />
      <path
        d="M 130 65 Q 132 80, 130 100 Q 128 120, 130 135"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.5"
      />

      {/* Horizontal grid lines */}
      <path
        d="M 55 75 Q 100 72, 145 75"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.4"
      />
      <path
        d="M 55 125 Q 100 128, 145 125"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.4"
      />
    </svg>
  )
}