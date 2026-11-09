import { useCallback, useEffect, useState } from 'react'
import './ModulePage.css'

const API_BASE = '/api'

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const result = await response.json()
  if (!response.ok) {
    throw new Error(result.detail || `Request failed (${response.status})`)
  }
  return result
}

function ModulePage({ title, onDataChanged }) {
  const [products, setProducts] = useState([])
  const [inventory, setInventory] = useState([])
  const [sales, setSales] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadPageData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      if (title === 'Products') {
        setProducts(await request('/products'))
      } else if (title === 'Inventory') {
        const [productRows, inventoryRows] = await Promise.all([
          request('/products'),
          request('/inventory'),
        ])
        setProducts(productRows)
        setInventory(inventoryRows)
      } else if (title === 'Sales') {
        const [productRows, inventoryRows, saleRows] = await Promise.all([
          request('/products'),
          request('/inventory'),
          request('/sales'),
        ])
        setProducts(productRows)
        setInventory(inventoryRows)
        setSales(saleRows)
      } else if (title === 'Shelf Vision') {
        setAnalyses(await request('/vision/analyses'))
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not load data.')
    } finally {
      setLoading(false)
    }
  }, [title])

  useEffect(() => {
    loadPageData()
  }, [loadPageData])

  async function handleSubmit(event, path, makePayload, successMessage) {
    event.preventDefault()
    setError('')
    setSuccess('')
    const form = event.currentTarget
    const formData = new FormData(form)
    try {
      await request(path, {
        method: path === '/inventory' ? 'PUT' : 'POST',
        body: JSON.stringify(makePayload(formData)),
      })
      setSuccess(successMessage)
      form.reset()
      await loadPageData()
      await onDataChanged?.()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Could not save the entry.')
    }
  }

  async function handleVisionSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')
    setAnalysisResult(null)
    setAnalyzing(true)
    const formData = new FormData(event.currentTarget)
    try {
      const response = await fetch(`${API_BASE}/vision/analyze`, {
        method: 'POST',
        body: formData,
      })
      const result = await response.json()
      if (!response.ok) {
        throw new Error(result.detail || `Analysis request failed (${response.status})`)
      }
      setAnalysisResult(result)
      setSuccess('Object detection complete. Only model-detected objects are shown; inventory is unchanged.')
      await loadPageData()
      await onDataChanged?.()
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : 'Shelf analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const productsForm = (
    <form
      className="entry-form"
      onSubmit={(event) => handleSubmit(
        event,
        '/products',
        (form) => ({
          name: form.get('name'),
          brand: form.get('brand') || null,
          sku: form.get('sku') || null,
          barcode: form.get('barcode') || null,
          price: Number(form.get('price')),
          category: form.get('category') || null,
          min_stock_level: Number(form.get('min_stock_level')),
          shelf_location: form.get('shelf_location') || null,
          quantity: Number(form.get('quantity')),
        }),
        'Product added successfully.',
      )}
    >
      <label>Product name<input name="name" required maxLength="200" placeholder="e.g. Oat milk 1L" /></label>
      <div className="form-row">
        <label>Brand<input name="brand" maxLength="100" placeholder="Brand" /></label>
        <label>Category<input name="category" maxLength="100" placeholder="e.g. Dairy" /></label>
      </div>
      <div className="form-row">
        <label>Price<input name="price" type="number" min="0.01" step="0.01" required placeholder="0.00" /></label>
        <label>Initial quantity<input name="quantity" type="number" min="0" step="1" defaultValue="0" required /></label>
      </div>
      <div className="form-row">
        <label>SKU<input name="sku" maxLength="50" placeholder="Optional" /></label>
        <label>Barcode<input name="barcode" maxLength="50" placeholder="Optional" /></label>
      </div>
      <div className="form-row">
        <label>Minimum stock level<input name="min_stock_level" type="number" min="0" defaultValue="10" required /></label>
        <label>Shelf location<input name="shelf_location" maxLength="100" placeholder="Optional" /></label>
      </div>
      <button className="entry-submit" type="submit">Add product</button>
    </form>
  )

  const inventoryForm = (
    <form
      className="entry-form"
      onSubmit={(event) => handleSubmit(
        event,
        '/inventory',
        (form) => ({
          product_id: Number(form.get('product_id')),
          quantity: Number(form.get('quantity')),
        }),
        'Inventory quantity updated.',
      )}
    >
      <label>Product
        <select name="product_id" required defaultValue="">
          <option value="" disabled>Select a product</option>
          {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
        </select>
      </label>
      <label>Set quantity on hand<input name="quantity" type="number" min="0" step="1" required placeholder="Enter current stock count" /></label>
      <button className="entry-submit" type="submit" disabled={!products.length}>Save inventory</button>
    </form>
  )

  const salesForm = (
    <form
      className="entry-form"
      onSubmit={(event) => handleSubmit(
        event,
        '/sales',
        (form) => ({
          product_id: Number(form.get('product_id')),
          quantity: Number(form.get('quantity')),
        }),
        'Sale recorded and inventory updated.',
      )}
    >
      <label>Product
        <select name="product_id" required defaultValue="">
          <option value="" disabled>Select a product</option>
          {products.map((product) => {
            const stock = inventory.find((row) => row.product_id === product.id)?.quantity || 0
            return <option key={product.id} value={product.id} disabled={stock === 0}>{product.name} · {stock} in stock · ${Number(product.price).toFixed(2)}</option>
          })}
        </select>
      </label>
      <label>Quantity sold<input name="quantity" type="number" min="1" step="1" required placeholder="Enter units sold" /></label>
      <p className="form-help">A sale reduces the product’s available inventory automatically.</p>
      <button className="entry-submit" type="submit" disabled={!products.some((product) => (inventory.find((row) => row.product_id === product.id)?.quantity || 0) > 0)}>Record sale</button>
    </form>
  )

  return (
    <section className="module-page">
      <p className="eyebrow">STOCKVISION WORKSPACE</p>
      <h2>{title}</h2>
      <p className="module-description">{getDescription(title)}</p>

      {(error || success) && (
        <div className={`form-notice${error ? ' form-notice--error' : ' form-notice--success'}`} role={error ? 'alert' : 'status'}>
          {error || success}
        </div>
      )}

      {['Products', 'Inventory', 'Sales'].includes(title) && (
        <div className="entry-layout">
          <article className="entry-panel">
            <h3>{getFormTitle(title)}</h3>
            <p>{getFormDescription(title)}</p>
            {title === 'Products' ? productsForm : title === 'Inventory' ? inventoryForm : salesForm}
          </article>

          <article className="entry-panel entry-list-panel">
            <div className="entry-list-heading">
              <div>
                <h3>{getListTitle(title)}</h3>
                <p>{loading ? 'Loading records…' : `${getRows(title, { products, inventory, sales }).length} records`}</p>
              </div>
              <button className="entry-reload" type="button" onClick={loadPageData} disabled={loading} aria-label="Reload records" title="Reload records">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 7v5h-5M4 17v-5h5" /><path d="M5.6 9a7 7 0 0 1 11.8-2L20 12M4 12l2.6 5a7 7 0 0 0 11.8-2" /></svg>
              </button>
            </div>
            {loading ? <p className="records-empty">Loading…</p> : renderRecords(title, { products, inventory, sales })}
          </article>
        </div>
      )}

      {!['Products', 'Inventory', 'Sales'].includes(title) && (
        title === 'Shelf Vision' ? (
          <div className="vision-workspace">
            <div className="entry-layout">
              <article className="entry-panel">
                <h3>Detect objects in an image</h3>
                <p>Only YOLO object boxes are shown. The app does not infer empty shelves, gaps, occupancy, or stock status.</p>
                <form className="entry-form" onSubmit={handleVisionSubmit}>
                  <label>Shelf or camera location<input name="shelf_location" maxLength="100" placeholder="e.g. Aisle 2, shelf B" /></label>
                  <label>Image<input name="file" type="file" accept="image/*" required /></label>
                  <label>Detection confidence threshold<input name="confidence" type="number" min="0.01" max="1" step="0.01" defaultValue="0.25" required /></label>
                  <button className="entry-submit" type="submit" disabled={analyzing}>
                    {analyzing ? 'Detecting objects…' : 'Detect objects'}
                  </button>
                </form>
              </article>

              <article className="entry-panel">
                <div className="entry-list-heading">
                  <div><h3>{analysisResult ? 'Object detections' : 'How this works'}</h3><p>{analysisResult ? `Analysis #${analysisResult.analysis_id} · ${analysisResult.model}` : 'Object-only detection'}</p></div>
                  {analysisResult && <span className="vision-count">{analysisResult.total_detections} objects detected</span>}
                </div>
                {analysisResult ? (
                  <div className="analysis-result">
                    <img className="annotated-image" src={analysisResult.annotated_image_url} alt="Image annotated with detected object boxes only" />
                    <p className="analysis-note">{analysisResult.model_semantics} The app does not analyze empty shelves and does not change inventory.</p>
                    <div className="region-results">
                      {analysisResult.detections.map((detection, index) => (
                        <div className="region-result" key={`${index}-${detection.bbox.join('-')}`}>
                          <div className="region-result-heading">
                            <strong>Object {index + 1}</strong>
                            <span>{detection.label} · {(detection.confidence * 100).toFixed(0)}% confidence</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="vision-guidance">
                    <ul>
                      <li>The annotated image shows only bounding boxes returned by the YOLO object detector.</li>
                      <li>The current model uses the generic “object” class and does not identify product SKUs.</li>
                      <li>No empty shelf or gap findings are generated.</li>
                      <li>Image analysis does not change inventory.</li>
                    </ul>
                  </div>
                )}
              </article>
            </div>
            <article className="entry-panel analysis-history">
              <div className="entry-list-heading">
                <div><h3>Recent shelf analyses</h3><p>{loading ? 'Loading analyses…' : `${analyses.length} saved observations`}</p></div>
                <button className="entry-reload" type="button" onClick={loadPageData} disabled={loading} aria-label="Reload analyses" title="Reload analyses">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 7v5h-5M4 17v-5h5" /><path d="M5.6 9a7 7 0 0 1 11.8-2L20 12M4 12l2.6 5a7 7 0 0 0 11.8-2" /></svg>
                </button>
              </div>
              {analyses.length ? (
                <div className="analysis-history-grid">
                  {analyses.map((analysis) => (
                    <div className="history-card" key={analysis.id}>
                      {analysis.detection_mode === 'objects_only' && analysis.annotated_image_url
                        ? <img src={analysis.annotated_image_url} alt={`Object-only detection ${analysis.id}`} />
                        : <span className="vision-history-placeholder">Legacy analysis</span>}
                      <div><strong>{analysis.shelf_location || `Analysis #${analysis.id}`}</strong><span>{analysis.total_detections} detections · {new Date(analysis.captured_at).toLocaleString()}</span></div>
                    </div>
                  ))}
                </div>
              ) : <p className="records-empty">No shelf analyses yet. Upload an image to begin.</p>}
            </article>
          </div>
        ) : <div className="module-empty">
          <div className="module-empty-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H19a1 1 0 0 1 1 1v13a2 2 0 0 1-2 2H5.5A1.5 1.5 0 0 1 4 18.5z" />
              <path d="M4 17h14M8 8h8M8 12h5" />
            </svg>
          </div>
          <h3>Nothing here yet</h3>
          <p>{getEmptyDescription(title)}</p>
        </div>
      )}
    </section>
  )
}

function getDescription(title) {
  return {
    Products: 'Add products to build your catalog.',
    Inventory: 'Enter stock counts and keep quantities up to date.',
    Sales: 'Record sales to update revenue and inventory.',
    'Shelf Vision': 'Shelf images and product detections will appear here.',
    Alerts: 'Store notifications will appear here when generated.',
    'AI Assistant': 'Inventory questions and assistant responses will appear here.',
  }[title] || 'This page is not available.'
}

function getFormTitle(title) {
  return { Products: 'Add a product', Inventory: 'Update stock', Sales: 'Record a sale' }[title]
}

function getFormDescription(title) {
  return {
    Products: 'Fields marked required must be completed.',
    Inventory: 'Enter the current quantity available for a product.',
    Sales: 'Choose a stocked product and enter the quantity sold.',
  }[title]
}

function getListTitle(title) {
  return { Products: 'Your products', Inventory: 'Current stock', Sales: 'Recent sales' }[title]
}

function getRows(title, data) {
  return { Products: data.products, Inventory: data.inventory, Sales: data.sales }[title] || []
}

function renderRecords(title, data) {
  const rows = getRows(title, data)
  if (!rows.length) {
    const text = {
      Products: 'No products yet. Add the first product using the form.',
      Inventory: 'No inventory yet. Add products first.',
      Sales: 'No sales yet. Record a sale when you are ready.',
    }[title]
    return <p className="records-empty">{text}</p>
  }

  if (title === 'Products') {
    return (
      <div className="record-list">
        {rows.map((product) => (
          <div className="record-row" key={product.id}>
            <span className="record-avatar">{product.name.slice(0, 1).toUpperCase()}</span>
            <span className="record-main"><strong>{product.name}</strong><small>{[product.brand, product.category].filter(Boolean).join(' · ') || 'No brand or category'}</small></span>
            <span className="record-side"><strong>${Number(product.price).toFixed(2)}</strong><small>{product.quantity} in stock</small></span>
          </div>
        ))}
      </div>
    )
  }

  if (title === 'Inventory') {
    return (
      <div className="record-list">
        {rows.map((row) => (
          <div className="record-row" key={row.product_id}>
            <span className="record-avatar">{row.name.slice(0, 1).toUpperCase()}</span>
            <span className="record-main"><strong>{row.name}</strong><small>{row.shelf_location || 'No shelf location'}</small></span>
            <span className="record-side"><strong>{row.quantity} units</strong><small>Minimum {row.min_stock_level}</small></span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="record-list">
      {rows.map((sale) => (
        <div className="record-row" key={sale.id}>
          <span className="record-avatar record-avatar--sale">$</span>
          <span className="record-main"><strong>{sale.product_name}</strong><small>{new Date(sale.sale_date).toLocaleString()} · {sale.quantity} units</small></span>
          <span className="record-side"><strong>${Number(sale.total_amount).toFixed(2)}</strong></span>
        </div>
      ))}
    </div>
  )
}

function getEmptyDescription(title) {
  return {
    'Shelf Vision': 'Shelf scans will appear after you submit an observation.',
    Alerts: 'Alerts will appear when there is store data to evaluate.',
    'AI Assistant': 'Start a conversation to see assistant messages here.',
  }[title] || 'Use the sidebar to open an available section.'
}

export default ModulePage
