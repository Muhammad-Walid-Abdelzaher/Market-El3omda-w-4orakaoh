import { useEffect, useRef, useState } from 'react'
import { BarcodeFormat, BrowserMultiFormatReader } from '@zxing/browser'
import { DecodeHintType } from '@zxing/library'
import { Camera, CircleAlert, Flashlight, ImageUp, RotateCcw, X } from 'lucide-react'

interface BarcodeScannerProps {
  onDetected: (barcode: string) => void
  onClose: () => void
}

function createReader() {
  const hints = new Map<DecodeHintType, unknown>()
  hints.set(DecodeHintType.TRY_HARDER, true)
  hints.set(DecodeHintType.POSSIBLE_FORMATS, [
    BarcodeFormat.EAN_13,
    BarcodeFormat.EAN_8,
    BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E,
  ])
  return new BrowserMultiFormatReader(hints, { delayBetweenScanAttempts: 150, delayBetweenScanSuccess: 150 })
}

function loadImage(source: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('The selected image could not be loaded.'))
    image.src = source
  })
}

async function decodeBarcodeImage(source: string): Promise<string> {
  const reader = createReader()
  try {
    return (await reader.decodeFromImageUrl(source)).getText()
  } catch {
    const image = await loadImage(source)
    for (const rotation of [0, 90, 270, 180]) {
      const sideways = rotation === 90 || rotation === 270
      const canvas = document.createElement('canvas')
      canvas.width = (sideways ? image.naturalHeight : image.naturalWidth) * 2
      canvas.height = (sideways ? image.naturalWidth : image.naturalHeight) * 2
      const context = canvas.getContext('2d', { willReadFrequently: true })
      if (!context) throw new Error('Image processing is unavailable in this browser.')
      context.imageSmoothingEnabled = false
      context.translate(canvas.width / 2, canvas.height / 2)
      context.rotate((rotation * Math.PI) / 180)
      context.filter = 'contrast(1.35) grayscale(1)'
      context.drawImage(image, -image.naturalWidth, -image.naturalHeight, image.naturalWidth * 2, image.naturalHeight * 2)
      try {
        return reader.decodeFromCanvas(canvas).getText()
      } catch {
        continue
      }
    }
    throw new Error('No supported barcode was found in that image.')
  }
}

export default function BarcodeScanner({ onDetected, onClose }: BarcodeScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const onDetectedRef = useRef(onDetected)
  const cameraUnavailable = !navigator.mediaDevices?.getUserMedia
  const [cameraError, setCameraError] = useState(
    cameraUnavailable ? 'Camera access is not available in this browser. Use manual barcode entry or upload an image.' : '',
  )
  const [cameraAttempt, setCameraAttempt] = useState(0)
  const [cameraId, setCameraId] = useState('')
  const [cameras, setCameras] = useState<MediaDeviceInfo[]>([])
  const [detectedBarcode, setDetectedBarcode] = useState('')
  const [cameraStatus, setCameraStatus] = useState('')
  const [cameraSettings, setCameraSettings] = useState('')
  const [torchAvailable, setTorchAvailable] = useState(false)
  const [torchEnabled, setTorchEnabled] = useState(false)
  const [zoomRange, setZoomRange] = useState<{ min: number; max: number; step: number } | null>(null)
  const [zoomValue, setZoomValue] = useState(1)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imageUrl, setImageUrl] = useState('')
  const [imageStatus, setImageStatus] = useState('')
  const [imageError, setImageError] = useState('')

  useEffect(() => {
    onDetectedRef.current = onDetected
  }, [onDetected])

  useEffect(() => {
    if (cameraUnavailable || imageFile) return
    const reader = createReader()
    const videoElement = videoRef.current
    const canvasElement = canvasRef.current
    let cancelled = false
    let scanTimer = 0
    let stream: MediaStream | null = null

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            ...(cameraId ? { deviceId: { exact: cameraId } } : { facingMode: { ideal: 'environment' } }),
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          },
        })
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        const track = stream.getVideoTracks()[0]
        if (!track) throw new Error('The selected camera did not provide a video track.')

        type CameraCapabilities = MediaTrackCapabilities & { focusMode?: string[]; zoom?: MediaSettingsRange }
        type CameraConstraints = MediaTrackConstraints & { advanced?: (MediaTrackConstraintSet & { focusMode?: string; zoom?: number })[] }
        const capabilities = track.getCapabilities() as CameraCapabilities
        if (capabilities.focusMode?.includes('continuous')) {
          try {
            await track.applyConstraints({ advanced: [{ focusMode: 'continuous' } as MediaTrackConstraintSet] } as CameraConstraints)
            setCameraSettings('Autofocus enabled')
          } catch {
            setCameraSettings('Keep the barcode steady while the camera focuses')
          }
        } else {
          setCameraSettings('Hold the barcode steady while the camera focuses')
        }
        if (capabilities.zoom) {
          const zoomMin = capabilities.zoom.min ?? 1
          const zoomMax = capabilities.zoom.max ?? zoomMin
          setZoomRange({ min: zoomMin, max: zoomMax, step: capabilities.zoom.step ?? 0.1 })
          setZoomValue(Math.max(zoomMin, Math.min(1, zoomMax)))
        }
        setTorchAvailable('torch' in capabilities)

        const devices = await navigator.mediaDevices.enumerateDevices()
        if (cancelled) return
        const videoDevices = devices.filter((device) => device.kind === 'videoinput')
        setCameras(videoDevices)

        const video = videoElement
        const canvas = canvasElement
        const context = canvas?.getContext('2d', { willReadFrequently: true })
        if (!video || !canvas || !context) throw new Error('Camera preview is unavailable in this browser.')
        video.srcObject = stream
        await video.play()
        if (cancelled) return
        setCameraStatus(capabilities.focusMode?.includes('continuous')
          ? 'Autofocus on · center barcode in the guide'
          : 'Center barcode · hold still while focusing')

        const scanFrame = () => {
          if (cancelled || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA || !video.videoWidth || !video.videoHeight) {
            scanTimer = window.setTimeout(scanFrame, 250)
            return
          }
          const cropWidth = Math.round(video.videoWidth * 0.88)
          const cropHeight = Math.round(video.videoHeight * 0.5)
          const cropX = Math.round((video.videoWidth - cropWidth) / 2)
          const cropY = Math.round((video.videoHeight - cropHeight) / 2)
          canvas.width = cropWidth
          canvas.height = cropHeight
          context.drawImage(video, cropX, cropY, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight)
          try {
            const result = reader.decodeFromCanvas(canvas)
            if (result && !cancelled) {
              cancelled = true
              setDetectedBarcode(result.getText())
              setCameraStatus('Barcode detected')
              stream?.getTracks().forEach((cameraTrack) => cameraTrack.stop())
              streamRef.current = null
              video.srcObject = null
              return
            }
          } catch {
            // Barcode not in focus or aligned yet; keep sampling the live preview.
          }
          scanTimer = window.setTimeout(scanFrame, 180)
        }
        scanTimer = window.setTimeout(scanFrame, 100)
      } catch (cause: unknown) {
        if (!cancelled) {
          stream?.getTracks().forEach((track) => track.stop())
          streamRef.current = null
          const detail = cause instanceof Error ? cause.message : 'Camera could not be started.'
          setCameraError(`${detail} Check browser camera permissions, or upload an image or enter the barcode manually.`)
        }
      }
    }

    void startCamera()

    return () => {
      cancelled = true
      window.clearTimeout(scanTimer)
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      if (videoElement) videoElement.srcObject = null
    }
  }, [cameraAttempt, cameraId, cameraUnavailable, imageFile])

  async function setZoom(value: number) {
    const track = streamRef.current?.getVideoTracks()[0]
    if (!track) return
    type CameraConstraints = MediaTrackConstraints & { advanced?: (MediaTrackConstraintSet & { zoom?: number })[] }
    try {
      await track.applyConstraints({ advanced: [{ zoom: value } as MediaTrackConstraintSet] } as CameraConstraints)
      setZoomValue(value)
    } catch (cause) {
      setCameraError(cause instanceof Error ? `Camera zoom could not be changed: ${cause.message}` : 'Camera zoom could not be changed.')
    }
  }

  async function toggleTorch() {
    const track = streamRef.current?.getVideoTracks()[0]
    if (!track) return
    type CameraConstraints = MediaTrackConstraints & { advanced?: (MediaTrackConstraintSet & { torch?: boolean })[] }
    try {
      await track.applyConstraints({ advanced: [{ torch: !torchEnabled } as MediaTrackConstraintSet] } as CameraConstraints)
      setTorchEnabled((enabled) => !enabled)
      setCameraError('')
    } catch (cause) {
      setCameraError(cause instanceof Error ? `Camera light could not be toggled: ${cause.message}` : 'Camera light could not be toggled.')
    }
  }

  useEffect(() => {
    if (!imageFile || !imageUrl) return

    let cancelled = false
    void decodeBarcodeImage(imageUrl).then((barcode) => {
      if (!cancelled) {
        setDetectedBarcode(barcode)
        setImageStatus('Barcode detected')
      }
    }).catch(() => {
      if (!cancelled) {
        setImageStatus('')
        setImageError('No supported barcode was found. Use a sharp, well-lit image with the entire barcode, its blank margins, and bars roughly horizontal.')
      }
    })

    return () => {
      cancelled = true
    }
  }, [imageFile, imageUrl])

  useEffect(() => () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl)
  }, [imageUrl])

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section className="scanner-modal" role="dialog" aria-modal="true" aria-labelledby="scanner-title" onClick={(event) => event.stopPropagation()}>
        <header className="modal-heading">
          <div><span className="eyebrow">BARCODE READER</span><h2 id="scanner-title">{imageFile ? 'Test with a barcode image' : 'Scan a barcode'}</h2></div>
          <button className="icon-button" aria-label="Close scanner" onClick={onClose}><X size={20} /></button>
        </header>
        <p className="muted">
          {imageFile
            ? 'The image is decoded locally in your browser and is not uploaded to the server.'
            : 'Allow camera access, then hold an EAN-13, EAN-8, UPC-A, or UPC-E barcode steady in view.'}
        </p>
        <div className={`camera-frame${imageFile ? ' image-frame' : ''}`}>
          {imageFile
            ? <img src={imageUrl} alt="Selected barcode for scanning" />
            : <><video ref={videoRef} autoPlay muted playsInline /><canvas ref={canvasRef} className="visually-hidden" /></>}
          {!imageFile && !cameraError && <span className="scan-guide" />}
          {!imageFile && !cameraError && <div className="camera-label"><Camera size={15} />{cameraStatus || cameraSettings || 'Live camera preview'}</div>}
          {imageFile && imageStatus && <div className="camera-label"><ImageUp size={15} />{imageStatus}</div>}
        </div>
        {detectedBarcode && <div className="detected-code"><span>Detected barcode</span><strong>{detectedBarcode}</strong></div>}
        {cameraError && !imageFile && <div className="inline-error"><CircleAlert size={18} />{cameraError}</div>}
        {imageError && <div className="inline-error"><CircleAlert size={18} />{imageError}</div>}
        <input
          ref={fileInputRef}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          aria-label="Upload barcode image"
          onChange={(event) => {
            const file = event.currentTarget.files?.[0]
            event.currentTarget.value = ''
            if (!file) return
            if (!file.type.startsWith('image/')) {
              setImageError('Choose an image file to scan.')
              return
            }
            setDetectedBarcode('')
            setImageUrl(URL.createObjectURL(file))
            setImageStatus('Reading barcode from image…')
            setImageError('')
            setImageFile(file)
          }}
        />
        <div className="scanner-actions">
          {!imageFile && cameras.length > 1 && <label className="camera-picker">Camera
            <select aria-label="Select camera" value={cameraId} onChange={(event) => { setDetectedBarcode(''); setCameraStatus(''); setCameraError(''); setCameraId(event.target.value) }}>
              {cameras.map((camera, index) => <option key={camera.deviceId} value={camera.deviceId}>{camera.label || `Camera ${index + 1}`}</option>)}
            </select>
          </label>}
          {!imageFile && torchAvailable && !detectedBarcode && <button className={`button button-secondary${torchEnabled ? ' selected' : ''}`} onClick={() => void toggleTorch()}><Flashlight size={15} /> Light</button>}
          <button className="button button-secondary" onClick={() => fileInputRef.current?.click()}><ImageUp size={16} /> Upload image</button>
          {!imageFile && zoomRange && !detectedBarcode && <label className="zoom-control">Zoom
            <input aria-label="Camera zoom" type="range" min={zoomRange.min} max={zoomRange.max} step={zoomRange.step} value={zoomValue} onChange={(event) => void setZoom(Number(event.target.value))} />
          </label>}
          {imageFile && <button className="button button-secondary" onClick={() => { setDetectedBarcode(''); setCameraStatus(''); setImageUrl(''); setCameraError(''); setImageFile(null); setImageStatus(''); setImageError('') }}><RotateCcw size={15} /> Use camera</button>}
          {cameraError && !cameraUnavailable && !imageFile && <button className="button button-secondary" onClick={() => { setDetectedBarcode(''); setCameraStatus(''); setCameraError(''); setCameraAttempt((attempt) => attempt + 1) }}><RotateCcw size={15} /> Try camera again</button>}
        </div>
        {detectedBarcode && <button className="button button-primary full-width scanner-confirm" onClick={() => onDetectedRef.current(detectedBarcode)}>Use barcode</button>}
        <button className="button button-secondary full-width" onClick={onClose}>Close scanner</button>
      </section>
    </div>
  )
}
