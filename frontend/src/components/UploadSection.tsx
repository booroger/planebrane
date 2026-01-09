import { useCallback, useState } from 'react'
import { Upload, Image as ImageIcon, FileImage } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/lib/utils'
import { CropImageDialog } from '@/components/CropImageDialog'

// Generate sample SVG patterns
function generateSampleSVG(pattern: string): string {
  const width = 500
  const height = 500
  const cx = width / 2
  const cy = height / 2

  let shapes = ''

  if (pattern === 'Circular') {
    // Concentric circles
    for (let i = 1; i <= 5; i++) {
      const r = i * 40
      shapes += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="black" stroke-width="2"/>`
    }
  } else if (pattern === 'Hexagonal') {
    // Hexagonal pattern
    const size = 60
    for (let row = -2; row <= 2; row++) {
      for (let col = -2; col <= 2; col++) {
        const x = cx + col * size * 1.5
        const y = cy + row * size * Math.sqrt(3) + (col % 2 === 0 ? 0 : size * Math.sqrt(3) / 2)
        const points = Array.from({ length: 6 }, (_, i) => {
          const angle = (Math.PI / 3) * i
          const px = x + size * Math.cos(angle)
          const py = y + size * Math.sin(angle)
          return `${px},${py}`
        }).join(' ')
        shapes += `<polygon points="${points}" fill="none" stroke="black" stroke-width="2"/>`
      }
    }
  } else if (pattern === 'Spiral') {
    // Spiral pattern
    const points = []
    for (let i = 0; i < 360; i += 5) {
      const angle = (i * Math.PI) / 180
      const r = i / 2
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      points.push(`${x},${y}`)
    }
    shapes = `<polyline points="${points.join(' ')}" fill="none" stroke="black" stroke-width="2"/>`
  }

  return `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">${shapes}</svg>`
}

export function UploadSection() {
  const [isDragging, setIsDragging] = useState(false)
  const [showCropDialog, setShowCropDialog] = useState(false)
  const [tempImage, setTempImage] = useState<{ src: string; file: File } | null>(null)
  const { setUploadedImage, setCurrentStep } = useAppStore()

  const handleFile = useCallback((file: File) => {
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const imageSrc = e.target?.result as string
        setTempImage({ src: imageSrc, file })
        setShowCropDialog(true)
      }
      reader.readAsDataURL(file)
    }
  }, [])

  const handleCropComplete = useCallback((croppedImage: string) => {
    if (tempImage) {
      // Create a new file from the cropped image
      fetch(croppedImage)
        .then(res => res.blob())
        .then(blob => {
          const croppedFile = new File([blob], tempImage.file.name, { type: 'image/jpeg' })
          setUploadedImage(croppedImage, croppedFile)
          setShowCropDialog(false)
          setTempImage(null)
          setCurrentStep('analyze')
        })
    }
  }, [tempImage, setUploadedImage, setCurrentStep])

  const handleCropCancel = useCallback(() => {
    setShowCropDialog(false)
    setTempImage(null)
  }, [])

  const handleSamplePattern = useCallback((pattern: string) => {
    // Generate sample SVG pattern
    const svgContent = generateSampleSVG(pattern)
    const blob = new Blob([svgContent], { type: 'image/svg+xml' })
    const file = new File([blob], `${pattern.toLowerCase()}.svg`, { type: 'image/svg+xml' })
    
    const reader = new FileReader()
    reader.onload = (e) => {
      const imageSrc = e.target?.result as string
      setTempImage({ src: imageSrc, file })
      setShowCropDialog(true)
    }
    reader.readAsDataURL(blob)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }, [handleFile])

  return (
    <>
      <CropImageDialog
        open={showCropDialog}
        imageSrc={tempImage?.src || ''}
        onCropComplete={handleCropComplete}
        onCancel={handleCropCancel}
      />
      
      <div className="flex h-full items-center justify-center p-8">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="heading-lg">Upload Pattern Image</CardTitle>
          <CardDescription className="body-lg">
            Upload a geometric pattern image to begin the 3D transformation process
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={cn(
              'relative flex min-h-[300px] flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-all',
              isDragging ? 'border-primary bg-primary/5' : 'border-border',
              'hover:border-primary hover:bg-primary/5'
            )}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept="image/*"
              onChange={handleFileInput}
            />
            
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="rounded-full bg-primary/10 p-4">
                <Upload className="h-10 w-10 text-primary" />
              </div>
              
              <div>
                <p className="heading-sm mb-2">Drag and drop your image here</p>
                <p className="body-sm text-muted-foreground">
                  or click to browse from your computer
                </p>
              </div>
              
              <label htmlFor="file-upload">
                <Button className="mt-2" asChild>
                  <span>
                    <FileImage className="mr-2 h-4 w-4" />
                    Choose File
                  </span>
                </Button>
              </label>
              
              <p className="label-text text-muted-foreground">
                Supported formats: JPG, PNG, SVG
              </p>
            </div>
          </div>

          {/* Sample Patterns */}
          <div className="mt-8">
            <h3 className="heading-sm mb-4">Or try a sample pattern</h3>
            <div className="grid grid-cols-3 gap-4">
              {['Circular', 'Hexagonal', 'Spiral'].map((pattern) => (
                <Card
                  key={pattern}
                  className="cursor-pointer transition-all hover:border-primary hover:shadow-md"
                  onClick={() => handleSamplePattern(pattern)}
                >
                  <CardContent className="flex aspect-square items-center justify-center p-4">
                    <div className="text-center">
                      <ImageIcon className="mx-auto mb-2 h-12 w-12 text-muted-foreground" />
                      <p className="body-sm font-medium">{pattern}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
    </>
  )
}