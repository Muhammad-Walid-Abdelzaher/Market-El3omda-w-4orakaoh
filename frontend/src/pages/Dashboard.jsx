import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import KPICards from '../components/dashboard/KPICards'
import './Dashboard.css'

const CATEGORY_COLORS = ['#4f8cff', '#29c79a', '#f5a623', '#ad7aff', '#27c2d1', '#f06c8b']

const currency = (value) =>
  `$${Number(value || 0).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

function EmptyState({ children }) {
  return <div className="dashboard-empty">{children}</div>
}

function Dashboard({ data, loading, error, onRetry }) {
  if (loading && !data) {
    return (
      <section className="dashboard-content" aria-live="polite">
        <div className="dashboard-loading">
          <span className="loading-spinner" />
          <span>Loading store data…</span>
        </div>
      </section>
    )
  }

  if (error && !data) {
    return (
      <section className="dashboard-content">
        <div className="dashboard-error" role="alert">
          <div>
            <strong>Unable to load dashboard data</strong>
            <p>{error}. Check that the StockVision API is running, then try again.</p>
          </div>
          <button className="button-secondary" onClick={onRetry}>Try again</button>
        </div>
      </section>
    )
  }

  const summary = data?.summary || {}
  const categories = data?.categories || []
  const sales = data?.salesChart || []
  const topProducts = data?.topProducts || []
  const inventory = data?.inventoryStatus || { status_counts: {}, low_stock_products: [] }
  const alerts = data?.alerts || []
  const tasks = data?.restockingTasks || []
  const movements = data?.stockMovements || []
  const stockCounts = inventory.status_counts || {}
  const totalStockStatuses =
    Number(stockCounts.healthy || 0) + Number(stockCounts.low || 0) + Number(stockCounts.out_of_stock || 0)

  return (
    <section className="dashboard-content">
      {error && (
        <div className="dashboard-inline-error" role="status">
          Refresh failed: {error}. Showing the last successfully loaded data.
        </div>
      )}

      <div className="dashboard-intro">
        <div>
          <p className="eyebrow">LIVE STORE OVERVIEW</p>
          <h2>Good to see you.</h2>
          <p className="dashboard-description">Here’s what’s happening across your inventory today.</p>
        </div>
        <div className="live-indicator"><span /> Connected to your store</div>
      </div>

      <KPICards summary={summary} />

      <div className="dashboard-grid dashboard-grid--primary">
        <article className="panel sales-panel">
          <div className="panel-heading">
            <div>
              <h3>Sales overview</h3>
              <p>Daily revenue · last 30 days</p>
            </div>
            <div className="panel-total">
              <span>Last 30 days</span>
              <strong>{Number(summary.sales_30d) > 0 ? currency(summary.sales_30d) : '—'}</strong>
            </div>
          </div>
          <div className="sales-chart">
            {sales.some((day) => Number(day.total) > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sales} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4f8cff" stopOpacity={0.32} />
                      <stop offset="95%" stopColor="#4f8cff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,.06)" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fill: '#747f97', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    interval="preserveStartEnd"
                    minTickGap={24}
                  />
                  <YAxis
                    tick={{ fill: '#747f97', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(value) => `$${value}`}
                    width={48}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#171d2b',
                      border: '1px solid rgba(255,255,255,.1)',
                      borderRadius: 10,
                      color: '#f0f2f5',
                    }}
                    formatter={(value) => [currency(value), 'Revenue']}
                  />
                  <Area
                    type="monotone"
                    dataKey="total"
                    stroke="#4f8cff"
                    strokeWidth={2.5}
                    fill="url(#salesFill)"
                    activeDot={{ r: 5, strokeWidth: 0, fill: '#78aaff' }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : <EmptyState>No sales data yet.</EmptyState>}
          </div>
        </article>

        <article className="panel category-panel">
          <div className="panel-heading">
            <div>
              <h3>Inventory by category</h3>
              <p>Current stock value</p>
            </div>
          </div>
          {categories.length ? (
            <>
              <div className="category-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categories}
                      dataKey="value"
                      nameKey="category"
                      innerRadius="62%"
                      outerRadius="86%"
                      paddingAngle={3}
                      stroke="none"
                    >
                      {categories.map((entry, index) => (
                        <Cell key={entry.category} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#171d2b',
                        border: '1px solid rgba(255,255,255,.1)',
                        borderRadius: 10,
                        color: '#f0f2f5',
                      }}
                      formatter={(value) => [currency(value), 'Stock value']}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="category-chart-center">
                  <strong>{categories.reduce((sum, item) => sum + Number(item.product_count || 0), 0)}</strong>
                  <span>products</span>
                </div>
              </div>
              <div className="category-legend">
                {categories.slice(0, 5).map((category, index) => (
                  <div className="legend-row" key={category.category}>
                    <span className="legend-name">
                      <i style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }} />
                      {category.category}
                    </span>
                    <span>{currency(category.value)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : <EmptyState>No category data available.</EmptyState>}
        </article>
      </div>

      <div className="dashboard-grid dashboard-grid--secondary">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h3>Inventory health</h3>
              <p>Stock levels across your products</p>
            </div>
            {totalStockStatuses > 0 && <span className="panel-count">{totalStockStatuses} items</span>}
          </div>
          {totalStockStatuses > 0 ? (
            <>
              <div className="inventory-summary">
                <div className="inventory-summary-item">
                  <span className="status-dot status-dot--healthy" />
                  <span>Healthy</span>
                  <strong>{stockCounts.healthy || 0}</strong>
                </div>
                <div className="inventory-summary-item">
                  <span className="status-dot status-dot--low" />
                  <span>Low stock</span>
                  <strong>{stockCounts.low || 0}</strong>
                </div>
                <div className="inventory-summary-item">
                  <span className="status-dot status-dot--out" />
                  <span>Out of stock</span>
                  <strong>{stockCounts.out_of_stock || 0}</strong>
                </div>
              </div>
              <div className="inventory-bar" aria-label="Inventory status distribution">
                <span className="inventory-bar-healthy" style={{ width: `${(stockCounts.healthy / totalStockStatuses) * 100}%` }} />
                <span className="inventory-bar-low" style={{ width: `${(stockCounts.low / totalStockStatuses) * 100}%` }} />
                <span className="inventory-bar-out" style={{ width: `${(stockCounts.out_of_stock / totalStockStatuses) * 100}%` }} />
              </div>
              <div className="subsection-heading">
                <h4>Needs attention</h4>
                <span>{inventory.low_stock_products?.length || 0} products</span>
              </div>
              {inventory.low_stock_products?.length ? (
                <div className="compact-list">
                  {inventory.low_stock_products.slice(0, 5).map((product, index) => (
                    <div className="compact-row" key={`${product.name}-${index}`}>
                      <div className="product-mark">{product.name?.charAt(0) || '?'}</div>
                      <div className="compact-row-main">
                        <strong>{product.name}</strong>
                        <span>{product.location || 'Location not set'}</span>
                      </div>
                      <span className={`stock-quantity${product.quantity === 0 ? ' is-out' : ''}`}>
                        {product.quantity} <small>left</small>
                      </span>
                    </div>
                  ))}
                </div>
              ) : <EmptyState>All listed products are above their minimum stock level.</EmptyState>}
            </>
          ) : <EmptyState>No inventory data yet.</EmptyState>}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h3>Top products</h3>
              <p>Best sellers · last 30 days</p>
            </div>
            <span className="panel-count">By revenue</span>
          </div>
          {topProducts.length ? (
            <div className="table-wrap">
              <table className="dashboard-table">
                <thead>
                  <tr><th>Product</th><th>Units sold</th><th>Revenue</th></tr>
                </thead>
                <tbody>
                  {topProducts.slice(0, 6).map((product, index) => (
                    <tr key={`${product.name}-${index}`}>
                      <td>
                        <div className="table-product">
                          <span className={`rank-badge${index === 0 ? ' rank-badge--first' : ''}`}>{index + 1}</span>
                          <span><strong>{product.name}</strong><small>{product.brand || '—'}</small></span>
                        </div>
                      </td>
                      <td>{Number(product.units_sold || 0).toLocaleString()}</td>
                      <td className="table-revenue">{currency(product.revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <EmptyState>No product sales recorded in the last 30 days.</EmptyState>}
        </article>
      </div>

      <div className="dashboard-grid dashboard-grid--tertiary">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h3>Recent alerts</h3>
              <p>Latest store notifications</p>
            </div>
            {summary.active_alerts > 0 && (
              <span className="panel-count">{summary.active_alerts} active</span>
            )}
          </div>
          {alerts.length ? (
            <div className="activity-list">
              {alerts.slice(0, 5).map((alert) => (
                <div className="activity-row" key={alert.id}>
                  <span className={`activity-icon activity-icon--${String(alert.severity || 'info').toLowerCase()}`}>
                    !
                  </span>
                  <div className="activity-copy">
                    <strong>{alert.product_name || alert.type || 'Store alert'}</strong>
                    <p>{alert.message}</p>
                    <span>{alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Recently'}</span>
                  </div>
                  <span className={`severity-pill severity-pill--${String(alert.severity || 'info').toLowerCase()}`}>
                    {alert.is_resolved ? 'Resolved' : alert.severity || 'Info'}
                  </span>
                </div>
              ))}
            </div>
          ) : <EmptyState>You’re all caught up. No recent alerts.</EmptyState>}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h3>Restocking tasks</h3>
              <p>Open tasks ordered by priority</p>
            </div>
            {summary.pending_tasks > 0 && (
              <span className="panel-count">{summary.pending_tasks} pending</span>
            )}
          </div>
          {tasks.length ? (
            <div className="task-list">
              {tasks.slice(0, 5).map((task) => (
                <div className="task-row" key={task.id}>
                  <span className={`priority-mark priority-mark--${String(task.priority || 'low').toLowerCase()}`} />
                  <div className="task-copy">
                    <strong>{task.product_name}</strong>
                    <span>{task.quantity_needed} units · {task.assigned_to || 'Unassigned'}</span>
                  </div>
                  <span className={`task-status task-status--${String(task.status || 'pending').toLowerCase().replaceAll('_', '-')}`}>
                    {String(task.status || 'Pending').replaceAll('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          ) : <EmptyState>No restocking tasks right now.</EmptyState>}
        </article>
      </div>

      <footer className="dashboard-footer">
        <span>StockVision AI</span>
        <span>
          {movements.length
            ? `Stock movements · last 7 days: ${movements.reduce((total, movement) => total + Number(movement.count || 0), 0)} recorded`
            : 'No stock movement data yet'}
        </span>
      </footer>
    </section>
  )
}

export default Dashboard
