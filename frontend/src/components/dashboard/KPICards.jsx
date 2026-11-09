import './KPICards.css'

const CARD_CONFIG = [
  {
    key: 'total_products',
    label: 'Total Products',
    icon: 'box',
    format: 'number',
    gradient: 'primary',
  },
  {
    key: 'inventory_value',
    label: 'Inventory Value',
    icon: 'dollar',
    format: 'currency',
    gradient: 'success',
  },
  {
    key: 'sales_today',
    label: 'Sales Today',
    icon: 'cart',
    format: 'currency',
    gradient: 'info',
  },
  {
    key: 'sales_7d',
    label: 'Sales (7 Days)',
    icon: 'trending',
    format: 'currency',
    gradient: 'primary',
  },
  {
    key: 'low_stock_count',
    label: 'Low Stock Items',
    icon: 'alert-triangle',
    format: 'number',
    gradient: 'warning',
  },
  {
    key: 'active_alerts',
    label: 'Active Alerts',
    icon: 'bell',
    format: 'number',
    gradient: 'danger',
  },
  {
    key: 'pending_tasks',
    label: 'Pending Tasks',
    icon: 'clipboard',
    format: 'number',
    gradient: 'warning',
  },
  {
    key: 'observations_today',
    label: 'Scans Today',
    icon: 'scan',
    format: 'number',
    gradient: 'info',
  },
]

const ICONS = {
  box: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
    </svg>
  ),
  dollar: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  ),
  cart: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="21" r="1" /><circle cx="20" cy="21" r="1" /><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
    </svg>
  ),
  trending: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" />
    </svg>
  ),
  'alert-triangle': (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  bell: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  ),
  clipboard: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    </svg>
  ),
  scan: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
    </svg>
  ),
}

function formatValue(value, format) {
  if (format === 'currency') {
    return `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }
  return Number(value).toLocaleString('en-US')
}

export default function KPICards({ summary }) {
  if (!summary) return null

  return (
    <div className="kpi-grid" id="kpi-cards">
      {CARD_CONFIG.map((card, i) => (
        <div
          key={card.key}
          className={`kpi-card kpi-card--${card.gradient}`}
          id={`kpi-${card.key}`}
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <div className="kpi-card-header">
            <span className="kpi-card-label">{card.label}</span>
            <div className={`kpi-card-icon kpi-card-icon--${card.gradient}`}>
              {ICONS[card.icon]}
            </div>
          </div>
          <div className="kpi-card-value">
            {Number(summary[card.key]) > 0 ? formatValue(summary[card.key], card.format) : '—'}
          </div>
          <div className="kpi-card-glow" />
        </div>
      ))}
    </div>
  )
}
