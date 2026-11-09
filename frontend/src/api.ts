import type { DashboardSummary, InventoryRow, Product, Sale } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message = typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status})`
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export const api = {
  summary: () => request<DashboardSummary>('/dashboard/summary'),
  products: () => request<Product[]>('/products'),
  productByBarcode: (barcode: string) =>
    request<Product>(`/products/barcode/${encodeURIComponent(barcode)}`),
  createProduct: (payload: Omit<Product, 'id' | 'quantity'>) =>
    request<Product>('/products', { method: 'POST', body: JSON.stringify(payload) }),
  inventory: () => request<InventoryRow[]>('/inventory'),
  receive: (payload: { product_id: number; quantity: number; unit_cost: number; batch_number?: string; employee: string }) =>
    request<{ message: string; quantity: number }>('/inventory/receive', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  completeSale: (payload: { items: { product_id: number; quantity: number }[]; employee: string }) =>
    request<Sale>('/sales', { method: 'POST', body: JSON.stringify(payload) }),
  sales: () => request<Sale[]>('/sales'),
}
