import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import Dashboard from './pages/Dashboard'
import ModulePage from './pages/ModulePage'
import { useDashboardData } from './hooks/useDashboardData'
import './App.css'

const PAGE_DETAILS = {
  '/products': { title: 'Products', subtitle: 'Product catalog' },
  '/inventory': { title: 'Inventory', subtitle: 'Stock levels' },
  '/sales': { title: 'Sales', subtitle: 'Sales records' },
  '/vision': { title: 'Shelf Vision', subtitle: 'Shelf observations' },
  '/alerts': { title: 'Alerts', subtitle: 'Store notifications' },
  '/assistant': { title: 'AI Assistant', subtitle: 'Inventory assistant' },
}

function AppContent() {
  const location = useLocation()
  const { data, loading, error, refetch } = useDashboardData()
  const isDashboard = location.pathname === '/'
  const pageDetails = PAGE_DETAILS[location.pathname]
  const title = isDashboard ? 'Dashboard' : pageDetails?.title || 'Not found'

  return (
    <div className="app-shell">
      <Sidebar activeAlerts={data?.summary?.active_alerts || 0} />
      <main className="app-main">
        <Header
          title={title}
          subtitle={isDashboard ? 'Store overview' : pageDetails?.subtitle}
          onRefresh={isDashboard ? refetch : undefined}
          refreshing={isDashboard && loading}
        />
        <Routes>
          <Route
            path="/"
            element={<Dashboard data={data} loading={loading} error={error} onRetry={refetch} />}
          />
          {Object.entries(PAGE_DETAILS).map(([path, details]) => (
            <Route
              key={path}
              path={path}
              element={<ModulePage title={details.title} onDataChanged={refetch} />}
            />
          ))}
          <Route path="*" element={<ModulePage title="Page not found" />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
