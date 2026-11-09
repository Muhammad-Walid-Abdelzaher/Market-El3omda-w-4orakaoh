import { useCallback, useEffect, useMemo, useState } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import {
  ArrowDownToLine, ArrowRight, Barcode, Box, Check, ChevronDown, CircleAlert, Eye,
  ClipboardList, CreditCard, LayoutDashboard, Plus, Printer, RefreshCw, Search,
  ShoppingBasket, Store, Trash2, X,
} from 'lucide-react'
import { api } from './api'
import BarcodeScanner from './components/BarcodeScanner'
import ShelfVisionPage from './pages/ShelfVisionPage'
import type { DashboardSummary, Product, Sale } from './types'
import './App.css'

const money = (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
const todayLabel = new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })

function useProducts() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setProducts(await api.products())
      setError('')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Products could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => {
    let active = true
    api.products().then((data) => {
      if (active) { setProducts(data); setError('') }
    }).catch((cause: unknown) => {
      if (active) setError(cause instanceof Error ? cause.message : 'Products could not be loaded.')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [])
  return { products, loading, error, refresh }
}

function Sidebar() {
  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/products', label: 'Products', icon: Box },
    { to: '/receiving', label: 'Stock receiving', icon: ArrowDownToLine },
    { to: '/pos', label: 'Point of sale', icon: CreditCard },
    { to: '/vision', label: 'Shelf Vision', icon: Eye },
  ]
  return (
    <aside className="sidebar">
      <div className="brand-lockup"><div className="brand-mark"><Store size={22} /></div><div><strong>StockVision</strong><span>RETAIL OPERATIONS</span></div></div>
      <div className="store-switch"><div className="store-avatar"><Store size={17} /></div><div><strong>StockVision Supermarket</strong><span>Main location</span></div><ChevronDown size={16} /></div>
      <div className="nav-caption">WORKSPACE</div>
      <nav className="side-nav">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            <Icon size={18} strokeWidth={1.8} /><span>{label}</span>{label === 'Point of sale' && <span className="nav-shortcut">POS</span>}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-bottom"><div className="staff-avatar">ST</div><div><strong>Store team</strong><span>Staff account</span></div><span className="online-dot" /></div>
    </aside>
  )
}

const titles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'A clear view of your store operations.' },
  '/products': { title: 'Products', subtitle: 'Manage your product catalog and pricing.' },
  '/receiving': { title: 'Stock receiving', subtitle: 'Register items and confirm incoming stock.' },
  '/pos': { title: 'Point of sale', subtitle: 'Scan products and complete a customer sale.' },
  '/vision': { title: 'Shelf Vision', subtitle: 'Review shelf images with computer vision.' },
}

function PageFrame({ children, onRefresh }: { children: React.ReactNode; onRefresh?: () => void }) {
  const location = useLocation()
  const page = titles[location.pathname] ?? titles['/']
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs"><span>Store</span><span className="crumb-slash">/</span><strong>{page.title}</strong></div>
          <div className="topbar-actions"><span className="open-status"><i /> Store open</span>{onRefresh && <button className="icon-button" title="Refresh dashboard" onClick={onRefresh}><RefreshCw size={17} /></button>}<div className="top-user"><span className="staff-avatar">ST</span><span>Staff</span><ChevronDown size={14} /></div></div>
        </header>
        <div className="page-content"><div className="page-heading"><div><h1>{page.title}</h1><p>{page.subtitle}</p></div></div>{children}</div>
      </main>
    </div>
  )
}

function StatCard({ label, value, icon: Icon, tone, helper }: { label: string; value: string | number; icon: typeof Box; tone: string; helper: string }) {
  return <article className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={19} /></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-helper">{helper}</div></article>
}

function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    setLoading(true)
    try { setSummary(await api.summary()); setError('') }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Dashboard could not be loaded.') }
    finally { setLoading(false) }
  }, [])
  useEffect(() => {
    let active = true
    api.summary().then((data) => {
      if (active) { setSummary(data); setError('') }
    }).catch((cause: unknown) => {
      if (active) setError(cause instanceof Error ? cause.message : 'Dashboard could not be loaded.')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [])
  return (
    <PageFrame onRefresh={() => void load()}>
      <div className="welcome-strip"><div className="welcome-icon"><Store size={21} /></div><div><strong>Your store, at a glance</strong><p>Products and inventory are updated as your team receives stock and completes sales.</p></div><span className="today-label">{todayLabel}</span></div>
      {error && <Notice message={error} tone="error" />}
      <div className="section-title-row"><div><h2>Store overview</h2><p>Current totals from your database</p></div>{loading && <span className="loading-label">Updating…</span>}</div>
      <div className="stats-grid">
        <StatCard label="Registered products" value={summary?.registered_products ?? '—'} icon={Box} tone="blue" helper="Active items in your catalog" />
        <StatCard label="Available inventory" value={summary?.inventory_units ?? '—'} icon={ShoppingBasket} tone="green" helper="Total units currently in stock" />
        <StatCard label="Stock receipts" value={summary?.stock_receipts ?? '—'} icon={ArrowDownToLine} tone="amber" helper="Confirmed receiving transactions" />
        <StatCard label="Completed sales" value={summary?.completed_sales ?? '—'} icon={CreditCard} tone="violet" helper="Sales completed at checkout" />
      </div>
      <div className="quick-grid">
        <NavLink to="/receiving" className="quick-card"><span className="quick-icon green"><ArrowDownToLine size={20} /></span><span><strong>Receive stock</strong><small>Find or register a product, then confirm incoming quantity.</small></span><ArrowRight size={18} /></NavLink>
        <NavLink to="/pos" className="quick-card"><span className="quick-icon blue"><CreditCard size={20} /></span><span><strong>Open point of sale</strong><small>Scan products, check stock, and complete a sale.</small></span><ArrowRight size={18} /></NavLink>
      </div>
      <div className="info-panel"><div className="panel-icon"><ClipboardList size={19} /></div><div><strong>Inventory changes only on confirmation</strong><p>Scanning a barcode never changes stock. Quantities are recorded only after a stock receipt or sale is confirmed.</p></div><Check size={18} className="panel-check" /></div>
    </PageFrame>
  )
}

function Notice({ message, tone = 'success' }: { message: string; tone?: 'success' | 'error' }) {
  return <div className={`notice ${tone}`}><span>{tone === 'success' ? <Check size={17} /> : <CircleAlert size={17} />}</span>{message}</div>
}

interface ProductFieldsProps {
  barcode?: string
  onCreated: (product: Product) => void
  onCancel?: () => void
}

function ProductFields({ barcode = '', onCreated, onCancel }: ProductFieldsProps) {
  const [values, setValues] = useState({ name: '', brand: '', barcode, category: '', size: '', purchase_price: '', selling_price: '', minimum_stock: '10' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const update = (key: keyof typeof values, value: string) => setValues((current) => ({ ...current, [key]: value }))
  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true); setError('')
    try {
      const product = await api.createProduct({
        name: values.name.trim(), brand: values.brand.trim() || null, barcode: values.barcode.trim(),
        category: values.category.trim(), size: values.size.trim(), purchase_price: Number(values.purchase_price),
        selling_price: Number(values.selling_price), minimum_stock: Number(values.minimum_stock),
      })
      onCreated(product)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Product could not be registered.') }
    finally { setSaving(false) }
  }
  return (
    <form className="form-card" onSubmit={(event) => void submit(event)}>
      <div className="form-heading"><div><span className="eyebrow">PRODUCT DETAILS</span><h2>Register a product</h2><p>New products start at zero stock. Receive units separately to update inventory.</p></div>{onCancel && <button type="button" className="icon-button" onClick={onCancel} aria-label="Close form"><X size={18} /></button>}</div>
      {error && <Notice tone="error" message={error} />}
      <div className="form-grid">
        <label>Product name *<input required maxLength={200} value={values.name} onChange={(e) => update('name', e.target.value)} placeholder="e.g. Whole milk" /></label>
        <label>Brand<input maxLength={100} value={values.brand} onChange={(e) => update('brand', e.target.value)} placeholder="Brand name" /></label>
        <label>Barcode *<input required maxLength={50} value={values.barcode} onChange={(e) => update('barcode', e.target.value)} placeholder="Scan or enter barcode" /></label>
        <label>Category *<input required maxLength={100} value={values.category} onChange={(e) => update('category', e.target.value)} placeholder="e.g. Dairy" /></label>
        <label>Size or weight *<input required maxLength={100} value={values.size} onChange={(e) => update('size', e.target.value)} placeholder="e.g. 1 L" /></label>
        <label>Purchase price *<input type="number" min="0" step="0.01" required value={values.purchase_price} onChange={(e) => update('purchase_price', e.target.value)} placeholder="0.00" /></label>
        <label>Selling price *<input type="number" min="0.01" step="0.01" required value={values.selling_price} onChange={(e) => update('selling_price', e.target.value)} placeholder="0.00" /></label>
        <label>Minimum stock threshold *<input type="number" min="0" step="1" required value={values.minimum_stock} onChange={(e) => update('minimum_stock', e.target.value)} /></label>
      </div>
      <div className="form-actions">{onCancel && <button type="button" className="button button-secondary" onClick={onCancel}>Cancel</button>}<button className="button button-primary" disabled={saving}>{saving ? 'Saving…' : <><Plus size={17} /> Register product</>}</button></div>
    </form>
  )
}

function ProductsPage() {
  const { products, loading, error, refresh } = useProducts()
  const [showForm, setShowForm] = useState(false)
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState('')
  const visible = products.filter((p) => `${p.name} ${p.brand ?? ''} ${p.barcode} ${p.category}`.toLowerCase().includes(query.toLowerCase()))
  return (
    <PageFrame>
      {message && <Notice message={message} />}
      <div className="content-card">
        <div className="toolbar"><div className="searchbox"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search products or barcode" /></div><button className="button button-primary" onClick={() => setShowForm((value) => !value)}><Plus size={17} /> Register product</button></div>
        {showForm && <div className="embedded-form"><ProductFields onCancel={() => setShowForm(false)} onCreated={async () => { setShowForm(false); setMessage('Product registered with zero stock.'); await refresh() }} /></div>}
        {error && <Notice tone="error" message={error} />}
        <div className="table-scroll"><table><thead><tr><th>PRODUCT</th><th>BARCODE</th><th>CATEGORY</th><th>SELLING PRICE</th><th>IN STOCK</th></tr></thead><tbody>
          {loading ? <tr><td colSpan={5} className="empty-row">Loading products…</td></tr> : visible.length === 0 ? <tr><td colSpan={5} className="empty-row">{products.length ? 'No matching products.' : 'No products registered yet.'}</td></tr> : visible.map((product) => <tr key={product.id}><td><div className="product-cell"><span className="product-thumb"><Box size={17} /></span><span><strong>{product.name}</strong><small>{product.brand || product.size || '—'}</small></span></div></td><td className="mono">{product.barcode}</td><td>{product.category || '—'}</td><td>{money(product.selling_price)}</td><td><span className={`stock-pill${product.quantity <= product.minimum_stock ? ' low' : ''}`}>{product.quantity} units</span></td></tr>)}
        </tbody></table></div>
        <div className="table-foot">{visible.length} product{visible.length === 1 ? '' : 's'} <button className="text-button" onClick={() => void refresh()}><RefreshCw size={14} /> Refresh</button></div>
      </div>
    </PageFrame>
  )
}

function ReceivingPage() {
  const [barcode, setBarcode] = useState('')
  const [product, setProduct] = useState<Product | null>(null)
  const [unknownBarcode, setUnknownBarcode] = useState('')
  const [scanOpen, setScanOpen] = useState(false)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [quantity, setQuantity] = useState('')
  const [unitCost, setUnitCost] = useState('')
  const [batch, setBatch] = useState('')
  const [employee, setEmployee] = useState('Store staff')
  const [saving, setSaving] = useState(false)
  const lookup = useCallback(async (value: string) => {
    const code = value.trim()
    if (!code) { setError('Enter or scan a barcode first.'); return }
    setBarcode(code); setProduct(null); setUnknownBarcode(''); setError(''); setMessage(''); setSearching(true)
    try {
      const found = await api.productByBarcode(code)
      setProduct(found); setUnitCost(String(found.purchase_price))
    } catch (cause) {
      if (cause instanceof Error && cause.message.toLowerCase().includes('no product')) setUnknownBarcode(code)
      else setError(cause instanceof Error ? cause.message : 'Product lookup failed.')
    } finally { setSearching(false) }
  }, [])
  async function confirmReceive(event: React.FormEvent) {
    event.preventDefault()
    if (!product) return
    setSaving(true); setError(''); setMessage('')
    try {
      const result = await api.receive({ product_id: product.id, quantity: Number(quantity), unit_cost: Number(unitCost), batch_number: batch.trim() || undefined, employee: employee.trim() || 'Store staff' })
      setProduct({ ...product, quantity: result.quantity })
      setMessage(result.message); setQuantity(''); setBatch('')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Stock could not be received.') }
    finally { setSaving(false) }
  }
  const onDetected = useCallback((code: string) => { setScanOpen(false); void lookup(code) }, [lookup])
  return (
    <PageFrame>
      <div className="receiving-layout">
        <section className="content-card receive-search">
          <span className="eyebrow">STEP 1 · IDENTIFY ITEM</span><h2>Find a product</h2><p className="muted">Scan a retail barcode or enter it manually. Scanning never changes stock.</p>
          <div className="scan-actions"><button className="button button-primary" onClick={() => { setError(''); setScanOpen(true) }}><Barcode size={18} /> Scan Barcode</button><span>or enter manually</span></div>
          <form className="barcode-entry" onSubmit={(event) => { event.preventDefault(); void lookup(barcode) }}><input aria-label="Barcode" value={barcode} onChange={(event) => setBarcode(event.target.value)} placeholder="Enter barcode number" /><button className="button button-secondary" disabled={searching}>{searching ? 'Searching…' : 'Find product'}</button></form>
          {error && <Notice tone="error" message={error} />}
          {product && <div className="identified-product"><div className="product-thumb large"><Box size={21} /></div><div className="identified-copy"><span className="eyebrow">PRODUCT FOUND</span><h3>{product.name}</h3><p>{product.brand || product.category} · {product.size} · {product.barcode}</p></div><span className="stock-pill">{product.quantity} on hand</span></div>}
        </section>
        {product && <form className="content-card receive-form" onSubmit={(event) => void confirmReceive(event)}>
          <span className="eyebrow">STEP 2 · CONFIRM DELIVERY</span><h2>Add stock</h2><p className="muted">Inventory changes only after you confirm the quantity received.</p>
          {message && <Notice message={message} />}
          <div className="form-grid compact">
            <label>Quantity received *<input autoFocus type="number" min="1" step="1" required value={quantity} onChange={(event) => setQuantity(event.target.value)} placeholder="Enter units" /></label>
            <label>Purchase cost per unit *<input type="number" min="0" step="0.01" required value={unitCost} onChange={(event) => setUnitCost(event.target.value)} /></label>
            <label>Batch number <input value={batch} onChange={(event) => setBatch(event.target.value)} placeholder="Optional" /></label>
            <label>Received by *<input required value={employee} onChange={(event) => setEmployee(event.target.value)} /></label>
          </div>
          {error && <Notice tone="error" message={error} />}
          <button className="button button-primary full-width" disabled={saving}>{saving ? 'Saving receipt…' : <><ArrowDownToLine size={17} /> Add Stock</>}</button>
        </form>}
        {unknownBarcode && <ProductFields key={unknownBarcode} barcode={unknownBarcode} onCreated={(created) => { setProduct(created); setBarcode(created.barcode); setUnitCost(String(created.purchase_price)); setUnknownBarcode(''); setMessage('Product registered. Enter the received quantity below to update inventory.') }} />}
      </div>
      {scanOpen && <BarcodeScanner onDetected={onDetected} onClose={() => setScanOpen(false)} />}
    </PageFrame>
  )
}

interface CartLine { product: Product; quantity: number }

function POSPage() {
  const { products, loading, error: loadError, refresh } = useProducts()
  const [barcode, setBarcode] = useState('')
  const [cart, setCart] = useState<CartLine[]>([])
  const [scanOpen, setScanOpen] = useState(false)
  const [notice, setNotice] = useState('')
  const [noticeTone, setNoticeTone] = useState<'success' | 'error'>('error')
  const [employee, setEmployee] = useState('Cashier')
  const [confirming, setConfirming] = useState(false)
  const [saving, setSaving] = useState(false)
  const [receipt, setReceipt] = useState<Sale | null>(null)
  const total = useMemo(() => cart.reduce((sum, line) => sum + line.product.selling_price * line.quantity, 0), [cart])

  const addByBarcode = useCallback((code: string) => {
    const product = products.find((candidate) => candidate.barcode === code.trim())
    if (!product) { setNotice(`No product is registered for barcode ${code}.`); setNoticeTone('error'); return }
    const inCart = cart.find((line) => line.product.id === product.id)?.quantity ?? 0
    if (inCart + 1 > product.quantity) { setNotice(`Insufficient stock for ${product.name}. Available: ${product.quantity}.`); setNoticeTone('error'); return }
    setCart((current) => {
      const line = current.find((item) => item.product.id === product.id)
      return line ? current.map((item) => item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item) : [...current, { product, quantity: 1 }]
    })
    setNotice(`${product.name} added to cart.`); setNoticeTone('success'); setBarcode('')
  }, [products, cart])
  const onDetected = useCallback((code: string) => { setScanOpen(false); addByBarcode(code) }, [addByBarcode])
  function changeQuantity(productId: number, amount: number) {
    setCart((current) => current.flatMap((line) => {
      if (line.product.id !== productId) return [line]
      const next = line.quantity + amount
      if (next < 1) return []
      if (next > line.product.quantity) {
        setNotice(`Only ${line.product.quantity} units of ${line.product.name} are available.`); setNoticeTone('error')
        return [line]
      }
      return [{ ...line, quantity: next }]
    }))
  }
  async function completeSale() {
    setSaving(true); setNotice('')
    try {
      const result = await api.completeSale({ items: cart.map(({ product, quantity }) => ({ product_id: product.id, quantity })), employee: employee.trim() || 'Cashier' })
      setReceipt(result); setCart([]); setConfirming(false); await refresh()
    } catch (cause) {
      setNotice(cause instanceof Error ? cause.message : 'Sale failed. No stock was changed.')
      setNoticeTone('error'); setConfirming(false); await refresh()
    } finally { setSaving(false) }
  }

  return (
    <PageFrame>
      {receipt ? <ReceiptView sale={receipt} onNewSale={() => { setReceipt(null); setNotice('') }} /> : <div className="pos-layout">
        <section className="content-card pos-left">
          <div className="pos-title"><div><span className="eyebrow">CASHIER TERMINAL</span><h2>Build your cart</h2><p className="muted">Scan each item or enter its barcode below.</p></div><span className="terminal-badge"><i /> Ready</span></div>
          <div className="pos-scan-row"><button className="button button-primary scan-product-button" onClick={() => { setNotice(''); setScanOpen(true) }}><Barcode size={19} /> Scan Product</button><span className="or-label">OR</span><form className="pos-manual" onSubmit={(event) => { event.preventDefault(); addByBarcode(barcode) }}><input autoFocus value={barcode} onChange={(event) => setBarcode(event.target.value)} placeholder="Type barcode and press Enter" /><button className="button button-secondary" type="submit"><Plus size={17} /> Add</button></form></div>
          {notice && <Notice tone={noticeTone} message={notice} />}
          {loadError && <Notice tone="error" message={loadError} />}
          <div className="cart-heading"><h3>Shopping cart <span>{cart.reduce((n, item) => n + item.quantity, 0)}</span></h3><button className="text-button" onClick={() => setCart([])} disabled={cart.length === 0}><Trash2 size={14} /> Clear cart</button></div>
          {cart.length === 0 ? <div className="cart-empty"><div className="empty-illustration"><ShoppingBasket size={25} /></div><strong>Your cart is empty</strong><span>Scan a product barcode to get started.</span></div> :
            <div className="cart-list">{cart.map(({ product, quantity }) => <article className="cart-line" key={product.id}><div className="product-thumb"><Box size={17} /></div><div className="cart-product"><strong>{product.name}</strong><small>{product.barcode} · {money(product.selling_price)} each</small></div><div className="quantity-control"><button aria-label={`Decrease ${product.name}`} onClick={() => changeQuantity(product.id, -1)}>−</button><span>{quantity}</span><button aria-label={`Increase ${product.name}`} onClick={() => changeQuantity(product.id, 1)}>+</button></div><strong className="line-total">{money(product.selling_price * quantity)}</strong><button className="icon-button remove-button" aria-label={`Remove ${product.name}`} onClick={() => setCart((items) => items.filter((item) => item.product.id !== product.id))}><Trash2 size={16} /></button></article>)}</div>}
          {loading && <div className="loading-label">Loading product inventory…</div>}
          <div className="cashier-note"><CircleAlert size={16} /><span>Stock is checked before each item is added and revalidated when the sale is saved.</span></div>
        </section>
        <aside className="content-card order-card">
          <div className="order-top"><div className="order-icon"><ShoppingBasket size={20} /></div><div><span className="eyebrow">CURRENT ORDER</span><h2>Order summary</h2></div></div>
          <label className="cashier-field">Cashier name<input value={employee} onChange={(event) => setEmployee(event.target.value)} /></label>
          <div className="order-count"><span>Items in cart</span><strong>{cart.reduce((n, item) => n + item.quantity, 0)}</strong></div>
          <div className="order-total"><span>Total due</span><strong>{money(total)}</strong></div>
          <button className="button button-primary checkout-button" disabled={!cart.length || saving} onClick={() => setConfirming(true)}><CreditCard size={18} /> Complete Sale</button>
          <div className="secure-note"><Check size={15} /> Inventory updates after sale confirmation</div>
        </aside>
      </div>}
      {scanOpen && <BarcodeScanner onDetected={onDetected} onClose={() => setScanOpen(false)} />}
      {confirming && <div className="modal-backdrop"><section className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><button className="icon-button modal-close" aria-label="Close" onClick={() => setConfirming(false)}><X size={19} /></button><div className="confirm-icon"><CreditCard size={23} /></div><span className="eyebrow">CHECKOUT</span><h2 id="confirm-title">Confirm this sale?</h2><p>This will charge {money(total)} and deduct {cart.reduce((n, item) => n + item.quantity, 0)} unit(s) from inventory.</p><div className="confirm-summary">{cart.map(({ product, quantity }) => <div key={product.id}><span>{quantity} × {product.name}</span><strong>{money(product.selling_price * quantity)}</strong></div>)}<div className="confirm-grand"><span>Total</span><strong>{money(total)}</strong></div></div><div className="form-actions"><button className="button button-secondary" onClick={() => setConfirming(false)} disabled={saving}>Back to cart</button><button className="button button-primary" onClick={() => void completeSale()} disabled={saving}>{saving ? 'Processing…' : 'Confirm sale'}</button></div></section></div>}
    </PageFrame>
  )
}

function ReceiptView({ sale, onNewSale }: { sale: Sale; onNewSale: () => void }) {
  return <div className="receipt-layout">
    <div className="receipt-actions no-print"><div><span className="success-check"><Check size={20} /></span><span><strong>Sale completed</strong><small>Inventory has been updated.</small></span></div><button className="button button-secondary" onClick={() => window.print()}><Printer size={17} /> Print Receipt</button><button className="button button-primary" onClick={onNewSale}>New sale</button></div>
    <article className="receipt-paper">
      <div className="receipt-brand"><span className="receipt-logo"><Store size={20} /></span><h2>StockVision AI Supermarket</h2><span>SALES RECEIPT</span></div>
      <div className="receipt-meta"><span>Transaction ID<strong>SV-{String(sale.id).padStart(6, '0')}</strong></span><span>Date &amp; time<strong>{new Date(sale.created_at).toLocaleString()}</strong></span></div>
      <div className="receipt-items"><div className="receipt-table-head"><span>ITEM</span><span>QTY</span><span>PRICE</span><span>AMOUNT</span></div>{sale.items.map((item) => <div className="receipt-row" key={item.product_id}><span>{item.name}<small>{item.barcode}</small></span><span>{item.quantity}</span><span>{money(item.unit_price)}</span><strong>{money(item.subtotal)}</strong></div>)}</div>
      <div className="receipt-total"><span>Amount paid</span><strong>{money(sale.total_amount)}</strong></div><div className="receipt-thanks">Thank you for shopping with us.</div>
    </article>
  </div>
}

function App() {
  return <Routes><Route path="/" element={<DashboardPage />} /><Route path="/products" element={<ProductsPage />} /><Route path="/receiving" element={<ReceivingPage />} /><Route path="/pos" element={<POSPage />} /><Route path="/vision" element={<PageFrame><ShelfVisionPage /></PageFrame>} /><Route path="*" element={<DashboardPage />} /></Routes>
}

export default App
