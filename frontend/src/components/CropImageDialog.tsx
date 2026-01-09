import { useState, useCallback } from 'react'
import Cropper from 'react-easy-crop'
import type { Area, Point } from 'react-easy-crop'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { RotateCcw, Check, X, Square, RectangleHorizontal, RectangleVertical, Maximize, Move } from 'lucide-react'

interface CropImageDialogProps {
  open: boolean
  imageSrc: string
  onCropComplete: (croppedImage: string) => void
  onCancel: () => void
}

// Aspect ratio options
type AspectRatioOption = 'none' | '1:1' | '4:3' | '3:4' | '16:9' | '9:16' | 'custom'

interface AspectRatioConfig {
  label: string
  value: number | undefined
  icon: React.ReactNode
}

const aspectRatioOptions: Record<AspectRatioOption, AspectRatioConfig> = {
  'none': { label: 'No Crop', value: undefined, icon: <Maximize className="h-4 w-4" /> },
  '1:1': { label: '1:1', value: 1, icon: <Square className="h-4 w-4" /> },
  '4:3': { label: '4:3', value: 4 / 3, icon: <RectangleHorizontal className="h-4 w-4" /> },
  '3:4': { label: '3:4', value: 3 / 4, icon: <RectangleVertical className="h-4 w-4" /> },
  '16:9': { label: '16:9', value: 16 / 9, icon: <RectangleHorizontal className="h-4 w-4" /> },
  '9:16': { label: '9:16', value: 9 / 16, icon: <RectangleVertical className="h-4 w-4" /> },
  'custom': { label: 'Custom', value: undefined, icon: <Move className="h-4 w-4" /> },
}

export function CropImageDialog({ open, imageSrc, onCropComplete, onCancel }: CropImageDialogProps) {
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 })
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null)
  const [selectedAspect, setSelectedAspect] = useState<AspectRatioOption>('1:1')

  const onCropChange = useCallback((location: Point) => {
    setCrop(location)
  }, [])

  const onZoomChange = useCallback((zoom: number) => {
    setZoom(zoom)
  }, [])

  const onCropCompleteHandler = useCallback((_croppedArea: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels)
  }, [])

  const handleReset = useCallback(() => {
    setCrop({ x: 0, y: 0 })
    setZoom(1)
    setRotation(0)
    setSelectedAspect('1:1')
  }, [])

  const handleAspectChange = useCallback((aspect: AspectRatioOption) => {
    setSelectedAspect(aspect)
    // Reset crop position when changing aspect ratio
    setCrop({ x: 0, y: 0 })
  }, [])

  const createCroppedImage = useCallback(async () => {
    if (!croppedAreaPixels) return

    try {
      const croppedImage = await getCroppedImg(imageSrc, croppedAreaPixels, rotation)
      onCropComplete(croppedImage)
    } catch (error) {
      console.error('Error cropping image:', error)
    }
  }, [imageSrc, croppedAreaPixels, rotation, onCropComplete])

  // Get the current aspect ratio value
  const currentAspect = aspectRatioOptions[selectedAspect].value

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-4xl h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="heading-md">Crop Pattern Image</DialogTitle>
          <DialogDescription className="body-lg">
            Adjust the crop area to focus on the geometric pattern
          </DialogDescription>
        </DialogHeader>

        {/* Aspect Ratio Selector */}
        <div className="space-y-2">
          <Label className="label-text">Aspect Ratio</Label>
          <div className="flex flex-wrap gap-2">
            {(Object.keys(aspectRatioOptions) as AspectRatioOption[]).map((key) => {
              const option = aspectRatioOptions[key]
              const isSelected = selectedAspect === key
              return (
                <Button
                  key={key}
                  variant={isSelected ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleAspectChange(key)}
                  className={`
                    flex items-center gap-2 transition-all duration-200
                    ${isSelected
                      ? 'ring-2 ring-primary ring-offset-2 ring-offset-background'
                      : 'hover:bg-accent hover:text-accent-foreground'
                    }
                  `}
                >
                  {option.icon}
                  <span className="text-xs font-medium">{option.label}</span>
                </Button>
              )
            })}
          </div>
        </div>

        <div className="flex-1 relative bg-muted rounded-lg overflow-hidden min-h-[300px]">
          <Cropper
            image={imageSrc}
            crop={crop}
            zoom={zoom}
            rotation={rotation}
            aspect={currentAspect}
            onCropChange={onCropChange}
            onZoomChange={onZoomChange}
            onCropComplete={onCropCompleteHandler}
            objectFit="contain"
          />
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="label-text">Zoom</Label>
            <Slider
              value={[zoom]}
              onValueChange={(values) => setZoom(values[0])}
              min={1}
              max={3}
              step={0.1}
            />
          </div>

          <div className="space-y-2">
            <Label className="label-text">Rotation</Label>
            <Slider
              value={[rotation]}
              onValueChange={(values) => setRotation(values[0])}
              min={0}
              max={360}
              step={1}
            />
          </div>
        </div>

        <DialogFooter className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button variant="outline" onClick={onCancel}>
            <X className="mr-2 h-4 w-4" />
            Cancel
          </Button>
          <Button onClick={createCroppedImage}>
            <Check className="mr-2 h-4 w-4" />
            Apply Crop
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Create a cropped image from the source image and crop area
 */
async function getCroppedImg(
  imageSrc: string,
  pixelCrop: Area,
  rotation = 0
): Promise<string> {
  const image = await createImage(imageSrc)
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  if (!ctx) {
    throw new Error('No 2d context')
  }

  const maxSize = Math.max(image.width, image.height)
  const safeArea = 2 * ((maxSize / 2) * Math.sqrt(2))

  // Set canvas size to safe area
  canvas.width = safeArea
  canvas.height = safeArea

  // Translate canvas context to center
  ctx.translate(safeArea / 2, safeArea / 2)
  ctx.rotate((rotation * Math.PI) / 180)
  ctx.translate(-safeArea / 2, -safeArea / 2)

  // Draw rotated image
  ctx.drawImage(
    image,
    safeArea / 2 - image.width * 0.5,
    safeArea / 2 - image.height * 0.5
  )

  const data = ctx.getImageData(0, 0, safeArea, safeArea)

  // Set canvas size to crop size
  canvas.width = pixelCrop.width
  canvas.height = pixelCrop.height

  // Paste generated rotate image with correct offset
  ctx.putImageData(
    data,
    Math.round(0 - safeArea / 2 + image.width * 0.5 - pixelCrop.x),
    Math.round(0 - safeArea / 2 + image.height * 0.5 - pixelCrop.y)
  )

  // Convert to blob and create data URL
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        throw new Error('Canvas is empty')
      }
      const reader = new FileReader()
      reader.readAsDataURL(blob)
      reader.onloadend = () => {
        resolve(reader.result as string)
      }
    }, 'image/jpeg')
  })
}

/**
 * Create an image element from source
 */
function createImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.addEventListener('load', () => resolve(image))
    image.addEventListener('error', (error) => reject(error))
    image.src = url
  })
}