export interface Product {
  id: number
  name: string
  brand: string | null
  barcode: string
  category: string
  size: string
  purchase_price: number
  selling_price: number
  minimum_stock: number
  quantity: number
}

export interface DashboardSummary {
  registered_products: number
  inventory_units: number
  stock_receipts: number
  completed_sales: number
}

export interface ReceiptItem {
  product_id: number
  name: string
  barcode: string | null
  quantity: number
  unit_price: number
  subtotal: number
}

export interface Sale {
  id: number
  created_at: string
  total_amount: number
  employee: string | null
  items: ReceiptItem[]
}

export interface InventoryRow {
  product_id: number
  name: string
  barcode: string | null
  quantity: number
  minimum_stock: number
  updated_at: string | null
}
