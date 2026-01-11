import { useState } from 'react'
import { Download, CheckCircle2, FileDown, FolderOpen, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { useAppStore } from '@/store/useAppStore'
import { apiClient } from '@/lib/api'

type ExportFormat = 'stl-binary' | 'stl-text' | 'obj' | 'gltf' | 'glb'

export function ExportSection() {
  const { projectName, modelId, exportFormat, setExportFormat } = useAppStore()
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('high')
  const [exporting, setExporting] = useState<string | null>(null)
  const [exportProgress, setExportProgress] = useState(0)
  const [exportedFormats, setExportedFormats] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)

  const handleExport = async (format: ExportFormat) => {
    setExporting(format)
    setExportProgress(0)
    setError(null)

    try {
      // Simulate progress while waiting for API
      const progressInterval = setInterval(() => {
        setExportProgress((prev) => Math.min(prev + 10, 90))
      }, 100)

      let blob: Blob
      let fileExtension: string

      if (modelId) {
        // Use real API
        switch (format) {
          case 'stl-binary':
            blob = await apiClient.exportModelSTL(modelId, true)
            fileExtension = 'stl'
            break
          case 'stl-text':
            blob = await apiClient.exportModelSTLText(modelId)
            fileExtension = 'stl'
            break
          case 'obj':
            blob = await apiClient.exportModelOBJ(modelId)
            fileExtension = 'obj'
            break
          case 'gltf':
            blob = await apiClient.exportModelGLTF(modelId)
            fileExtension = 'gltf'
            break
          case 'glb':
            blob = await apiClient.exportModelGLB(modelId)
            fileExtension = 'glb'
            break
          default:
            throw new Error(`Unknown format: ${format}`)
        }
      } else {
        // Fallback to mock data for development
        fileExtension = format.includes('stl') ? 'stl' : format
        const mockContent = `Mock ${format.toUpperCase()} file content for ${projectName}`
        blob = new Blob([mockContent], { type: 'application/octet-stream' })
      }

      clearInterval(progressInterval)
      setExportProgress(100)

      // Trigger download
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${projectName.replace(/\s+/g, '_')}.${fileExtension}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      setExportedFormats((prev) => new Set(prev).add(format))
      setExportFormat(format)
    } catch (err) {
      console.error('Export failed:', err)
      setError(`Failed to export ${format.toUpperCase()}. Please try again.`)
    } finally {
      setExporting(null)
    }
  }

  const handleSaveToServer = async (format: ExportFormat) => {
    if (!modelId) {
      setError('No model available to save')
      return
    }

    try {
      // Map format to API format
      const apiFormat = format.includes('stl') ? 'stl' : format as 'obj' | 'gltf' | 'glb'
      const result = await apiClient.saveExport(modelId, apiFormat, projectName)
      console.log('Saved to:', result.path, 'Size:', result.size)
      // Could show a toast notification here
    } catch (err) {
      console.error('Save to server failed:', err)
      setError(`Failed to save ${format.toUpperCase()} to server.`)
    }
  }

  const formatDescriptions = {
    'stl-binary': { name: 'STL (Binary)', description: 'Compact binary format for 3D printing', extension: '.stl' },
    'stl-text': { name: 'STL (ASCII)', description: 'Human-readable text format', extension: '.stl' },
    obj: { name: 'OBJ', description: 'Widely compatible format', extension: '.obj' },
    gltf: { name: 'glTF', description: 'Web-optimized JSON format', extension: '.gltf' },
    glb: { name: 'GLB', description: 'Binary glTF (compact)', extension: '.glb' },
  }

  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="heading-lg">Export 3D Model</CardTitle>
          <CardDescription className="body-lg">
            Choose format and quality settings for your 3D model
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-4 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span className="body-sm">{error}</span>
            </div>
          )}

          {/* Export All Formats */}
          <div className="space-y-3">
            <Label className="label-text">Export Formats</Label>
            <p className="body-sm text-muted-foreground">
              Export your model in multiple formats
            </p>

            <div className="space-y-2">
              {Object.entries(formatDescriptions).map(([format, info]) => (
                <Card
                  key={format}
                  className={exportedFormats.has(format) ? 'border-accent' : ''}
                >
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <FileDown className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="body-sm font-medium">{info.name}</p>
                        <p className="body-sm text-muted-foreground">{info.description}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleExport(format as ExportFormat)}
                        disabled={exporting === format}
                        variant={exportedFormats.has(format) ? 'outline' : 'default'}
                      >
                        {exporting === format ? (
                          <>
                            <Download className="mr-2 h-4 w-4 animate-pulse" />
                            {exportProgress}%
                          </>
                        ) : exportedFormats.has(format) ? (
                          <>
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            Exported
                          </>
                        ) : (
                          <>
                            <Download className="mr-2 h-4 w-4" />
                            Download
                          </>
                        )}
                      </Button>
                      {modelId && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleSaveToServer(format as ExportFormat)}
                          disabled={exporting === format}
                          title="Save to server"
                        >
                          <FolderOpen className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Quality Selection */}
          <div className="space-y-2">
            <Label htmlFor="quality" className="label-text">
              Quality / Resolution
            </Label>
            <Select value={quality} onValueChange={(value: typeof quality) => setQuality(value)}>
              <SelectTrigger id="quality">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">
                  <div>
                    <p className="body-sm font-medium">Low (Fast export)</p>
                    <p className="body-sm text-muted-foreground">~500 KB, 10k vertices</p>
                  </div>
                </SelectItem>
                <SelectItem value="medium">
                  <div>
                    <p className="body-sm font-medium">Medium (Balanced)</p>
                    <p className="body-sm text-muted-foreground">~1.5 MB, 25k vertices</p>
                  </div>
                </SelectItem>
                <SelectItem value="high">
                  <div>
                    <p className="body-sm font-medium">High (Best quality)</p>
                    <p className="body-sm text-muted-foreground">~4 MB, 50k vertices</p>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Preview Info */}
          <Card className="bg-muted">
            <CardContent className="p-4">
              <div className="space-y-2">
                <div className="flex justify-between body-sm">
                  <span className="text-muted-foreground">Quality:</span>
                  <Badge variant="secondary">{quality}</Badge>
                </div>
                <div className="flex justify-between body-sm">
                  <span className="text-muted-foreground">Estimated Size:</span>
                  <span className="font-semibold">
                    {quality === 'low' ? '~500 KB' : quality === 'medium' ? '~1.5 MB' : '~4 MB'}
                  </span>
                </div>
                <div className="flex justify-between body-sm">
                  <span className="text-muted-foreground">Exports Completed:</span>
                  <Badge variant="secondary">{exportedFormats.size} / 5</Badge>
                </div>
                <div className="flex justify-between body-sm">
                  <span className="text-muted-foreground">Selected Format:</span>
                  <Badge variant="secondary">{exportFormat}</Badge>
                </div>
                <div className="flex justify-between body-sm">
                  <span className="text-muted-foreground">Model ID:</span>
                  <span className="font-mono text-xs">{modelId || 'Not generated'}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Export Progress */}
          {exporting && (
            <div className="space-y-2">
              <Progress value={exportProgress} />
              <p className="body-sm text-muted-foreground text-center">
                Exporting {exporting.toUpperCase()}: {exportProgress}%
              </p>
            </div>
          )}

          {/* Success Message */}
          {exportedFormats.size === 5 && !exporting && (
            <div className="flex items-center gap-2 rounded-lg bg-accent/10 p-4">
              <CheckCircle2 className="h-5 w-5 text-accent" />
              <span className="body-sm text-accent">All formats exported successfully!</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}