import { Upload, ScanLine, Sliders, Box, Download } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/lib/utils'

const steps = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'analyze', label: 'Analyze', icon: ScanLine },
  { id: 'adjust', label: 'Adjust', icon: Sliders },
  { id: 'view3d', label: '3D View', icon: Box },
  { id: 'export', label: 'Export', icon: Download },
] as const

export function StepIndicator() {
  const currentStep = useAppStore((state) => state.currentStep)

  const currentIndex = steps.findIndex((step) => step.id === currentStep)

  return (
    <div className="flex items-center justify-center gap-2 px-8 py-6">
      {steps.map((step, index) => {
        const Icon = step.icon
        const isActive = index === currentIndex
        const isCompleted = index < currentIndex
        
        return (
          <div key={step.id} className="flex items-center">
            <div className="flex flex-col items-center gap-2">
              <div
                className={cn(
                  'flex h-12 w-12 items-center justify-center rounded-lg border-2 transition-all',
                  isActive && 'border-primary bg-primary text-primary-foreground',
                  isCompleted && 'border-accent bg-accent text-accent-foreground',
                  !isActive && !isCompleted && 'border-border bg-muted text-muted-foreground'
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <span
                className={cn(
                  'label-text',
                  isActive && 'text-primary',
                  isCompleted && 'text-accent',
                  !isActive && !isCompleted && 'text-muted-foreground'
                )}
              >
                {step.label}
              </span>
            </div>
            
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'mx-4 h-0.5 w-16 transition-all',
                  isCompleted ? 'bg-accent' : 'bg-border'
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}