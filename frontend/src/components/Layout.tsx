import type { ReactNode } from 'react'
import { Moon, Sun, ChevronLeft, ChevronRight, FilePlus, Save, FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/lib/utils'
import { FlowerOfLifeIcon } from '@/components/FlowerOfLifeIcon'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useCallback, useRef } from 'react'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const { 
    isDarkMode, 
    toggleDarkMode, 
    canGoBack, 
    canGoForward, 
    goBack, 
    goForward, 
    reset,
    getProjectData,
    loadProjectData,
    projectName,
  } = useAppStore()

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSaveProject = async () => {
    const projectData = getProjectData()
    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${projectName.replace(/\s+/g, '_')}.pbp`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleLoadProject = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const projectData = JSON.parse(event.target?.result as string)
        loadProjectData(projectData)
      } catch (error) {
        console.error('Failed to load project:', error)
        alert('Failed to load project file. Please ensure it is a valid .pbp file.')
      }
    }
    reader.readAsText(file)

    // Reset the input so the same file can be loaded again
    e.target.value = ''
  }, [loadProjectData])

  const handleNewProject = () => {
    if (confirm('Are you sure you want to start a new project? All unsaved changes will be lost.')) {
      reset()
    }
  }

  return (
    <div className={cn('min-h-screen', isDarkMode && 'dark')}>
      <div className="min-h-screen bg-background text-foreground">
        {/* Header */}
        <header className="border-b border-border bg-card">
          <div className="flex h-16 items-center justify-between px-6">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary p-0.5">
                <FlowerOfLifeIcon className="h-full w-full text-primary-foreground" />
              </div>
              <div>
                <h1 className="heading-md text-foreground">PlaneBrane</h1>
                <p className="body-sm text-muted-foreground">Geometric Pattern to 3D</p>
              </div>
            </div>

            <TooltipProvider>
              <div className="flex items-center gap-2">
                {/* Navigation buttons */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={goBack}
                      disabled={!canGoBack}
                      aria-label="Go back"
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Go back</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={goForward}
                      disabled={!canGoForward}
                      aria-label="Go forward"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Go forward</TooltipContent>
                </Tooltip>

                <div className="mx-2 h-6 w-px bg-border" />

                {/* New project button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleNewProject}
                      aria-label="New project"
                    >
                      <FilePlus className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>New project</TooltipContent>
                </Tooltip>

                {/* Save project button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleSaveProject}
                      aria-label="Save project"
                    >
                      <Save className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Save project (.pbp)</TooltipContent>
                </Tooltip>

                {/* Load project button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleLoadProject}
                      aria-label="Load project"
                    >
                      <FolderOpen className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Load project (.pbp)</TooltipContent>
                </Tooltip>

                {/* Hidden file input for loading projects */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pbp,application/json"
                  className="hidden"
                  onChange={handleFileChange}
                />

                <div className="mx-2 h-6 w-px bg-border" />

                {/* Theme toggle */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={toggleDarkMode}
                      aria-label="Toggle theme"
                    >
                      {isDarkMode ? (
                        <Sun className="h-5 w-5" />
                      ) : (
                        <Moon className="h-5 w-5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Toggle theme</TooltipContent>
                </Tooltip>
              </div>
            </TooltipProvider>
          </div>
        </header>

        {/* Main Content */}
        <main className="h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  )
}