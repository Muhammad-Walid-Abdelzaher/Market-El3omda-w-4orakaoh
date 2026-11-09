import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { AlertTriangle, Eye, ImageUp, RefreshCw, ScanSearch } from 'lucide-react'
import './ShelfVisionPage.css'

interface ObjectDetection {
  bbox: number[]
  label: string
  class_id: number
  confidence: number
}

interface ShelfAnalysis {
  analysis_id: number
  shelf_location: string | null
  captured_at: string
  annotated_image_url: string
  model: string
  detection_mode: string
  model_semantics: string
  inventory_effect: string
  total_detections: number
  detections: ObjectDetection[]
}

interface ShelfAnalysisHistory {
  id: number
  shelf_location: string | null
  status: string
  captured_at: string
  detection_mode?: string
  total_detections: number
  annotated_image_url: string | null
}

async function readError(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
    return body.detail
  }
  return `${fallback} (${response.status})`
}

export default function ShelfVisionPage() {
  const [analyses, setAnalyses] = useState<ShelfAnalysisHistory[]>([])
  const [analysis, setAnalysis] = useState<ShelfAnalysis | null>(null)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [historyError, setHistoryError] = useState('')
  const [success, setSuccess] = useState('')

  const fetchHistory = useCallback(async () => {
    const response = await fetch('/api/vision/analyses')
    if (!response.ok) throw new Error(await readError(response, 'Detection history could not be loaded'))
    return await response.json() as ShelfAnalysisHistory[]
  }, [])

  const loadHistory = useCallback(async () => {
    try {
      setAnalyses(await fetchHistory())
      setHistoryError('')
    } catch (cause) {
      setHistoryError(cause instanceof Error ? cause.message : 'Detection history could not be loaded.')
    } finally {
      setLoadingHistory(false)
    }
  }, [fetchHistory])

  useEffect(() => {
    let active = true
    fetchHistory().then((history) => {
      if (active) {
        setAnalyses(history)
        setHistoryError('')
      }
    }).catch((cause: unknown) => {
      if (active) setHistoryError(cause instanceof Error ? cause.message : 'Detection history could not be loaded.')
    }).finally(() => {
      if (active) setLoadingHistory(false)
    })
    return () => { active = false }
  }, [fetchHistory])

  async function submitAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSuccess('')
    setAnalysis(null)
    setAnalyzing(true)
    const form = event.currentTarget
    const formData = new FormData(form)

    try {
      const response = await fetch('/api/vision/analyze', { method: 'POST', body: formData })
      if (!response.ok) throw new Error(await readError(response, 'Object detection failed'))
      setAnalysis(await response.json() as ShelfAnalysis)
      setSuccess('Detection complete. Only model-detected objects are shown; inventory is unchanged.')
      setLoadingHistory(true)
      await loadHistory()
      form.reset()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Object detection failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="vision-page">
      <div className="vision-intro content-card">
        <div className="vision-intro-icon"><Eye size={21} /></div>
        <div>
          <strong>Object detection only</strong>
          <p>Upload an image to show only objects detected by the model. Empty shelves and gaps are not analyzed or highlighted.</p>
        </div>
      </div>

      {error && <div className="notice error" role="alert"><AlertTriangle size={16} />{error}</div>}
      {success && <div className="notice" role="status">{success}</div>}

      <div className="vision-grid">
        <section className="content-card">
          <div className="vision-card-heading">
            <div><span className="eyebrow">COMPUTER VISION</span><h2>Detect objects in an image</h2></div>
            <ImageUp size={19} />
          </div>
          <p className="muted">The configured YOLO checkpoint returns object boxes and confidence scores. The app does not infer empty space or stock status.</p>
          <form className="vision-form" onSubmit={(event) => void submitAnalysis(event)}>
            <label>Shelf or camera location
              <input name="shelf_location" maxLength={100} placeholder="e.g. Aisle 2, shelf B" />
            </label>
            <label>Image
              <input name="file" type="file" accept="image/*" required />
            </label>
            <label>Detection confidence threshold
              <input name="confidence" type="number" min={0.01} max={1} step={0.01} defaultValue={0.25} required />
            </label>
            <button className="button button-primary full-width" type="submit" disabled={analyzing}>
              <ScanSearch size={17} />{analyzing ? 'Detecting objects…' : 'Detect objects'}
            </button>
          </form>
        </section>

        <section className="content-card vision-results">
          <div className="vision-card-heading">
            <div><span className="eyebrow">DETECTIONS</span><h2>{analysis ? `Result #${analysis.analysis_id}` : 'What to expect'}</h2></div>
            {analysis && <span className="vision-summary">{analysis.total_detections} objects detected</span>}
          </div>
          {analysis ? (
            <>
              <img className="vision-annotated-image" src={analysis.annotated_image_url} alt="Image annotated with detected objects only" />
              <div className="vision-meta">
                <span>Model <strong>{analysis.model}</strong></span>
                <span>Objects only</span>
                {analysis.shelf_location && <span>{analysis.shelf_location}</span>}
              </div>
              <p className="vision-caveat">{analysis.model_semantics} This analysis does not change inventory.</p>
              <div className="vision-detection-list">
                {analysis.detections.map((detection, index) => (
                  <div key={`${index}-${detection.bbox.join('-')}`}>
                    <strong>Object {index + 1}</strong>
                    <span>{detection.label}</span>
                    <span>{Math.round(detection.confidence * 100)}% confidence</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="vision-guidance">
              <div><ScanSearch size={21} /></div>
              <strong>Only model detections are displayed</strong>
              <p>The annotated image shows bounding boxes returned by the object detector.</p>
              <ul>
                <li>No empty shelf or gap results are generated.</li>
                <li>The current checkpoint labels detected items as “object”; it does not identify product SKUs.</li>
                <li>Inventory is not changed by image analysis.</li>
              </ul>
            </div>
          )}
        </section>
      </div>

      <section className="content-card vision-history">
        <div className="vision-card-heading">
          <div><span className="eyebrow">SAVED RECORDS</span><h2>Recent object detections</h2></div>
          <button className="icon-button" aria-label="Refresh detection history" onClick={() => { setLoadingHistory(true); void loadHistory() }} disabled={loadingHistory}>
            <RefreshCw size={17} />
          </button>
        </div>
        {historyError && <div className="notice error" role="alert"><AlertTriangle size={16} />{historyError}</div>}
        {loadingHistory ? <p className="muted">Loading saved detections…</p> : analyses.length ? (
          <div className="vision-history-grid">
            {analyses.map((item) => (
              <article className="vision-history-item" key={item.id}>
                {item.detection_mode === 'objects_only' && item.annotated_image_url
                  ? <img src={item.annotated_image_url} alt={`Object-only detection ${item.id}`} />
                  : <div className="vision-history-placeholder"><Eye size={20} /></div>}
                <div><strong>{item.shelf_location || `Analysis #${item.id}`}</strong><span>{item.total_detections} objects · {new Date(item.captured_at).toLocaleString()}</span></div>
              </article>
            ))}
          </div>
        ) : <p className="vision-empty">No saved detections yet. Upload an image to get started.</p>}
      </section>
    </div>
  )
}
