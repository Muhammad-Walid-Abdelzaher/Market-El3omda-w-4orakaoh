"""
StockVision AI - Database Seeder

Populates the database with realistic sample data for development and demonstration.
"""

import random
from datetime import datetime, timedelta, timezone

import sqlite3

DB_PATH = "stockvision.db"

# ──────────────────────────────────────────────
# Categories
# ──────────────────────────────────────────────
CATEGORIES = [
    ("Beverages", "Soft drinks, juices, water, energy drinks"),
    ("Snacks", "Chips, crackers, cookies, candy, nuts"),
    ("Dairy", "Milk, cheese, yogurt, butter, cream"),
    ("Bakery", "Bread, pastries, cakes, rolls"),
    ("Canned Goods", "Canned vegetables, soups, beans, tuna"),
    ("Frozen Foods", "Frozen meals, ice cream, vegetables, pizza"),
    ("Personal Care", "Shampoo, soap, toothpaste, deodorant"),
    ("Cleaning Supplies", "Detergent, disinfectant, wipes, sponges"),
]

# ──────────────────────────────────────────────
# Products  (name, brand, price, category_index, min_stock)
# ──────────────────────────────────────────────
PRODUCTS = [
    # Beverages (0)
    ("Coca-Cola 330ml", "Coca-Cola", 1.50, 0, 20),
    ("Pepsi 500ml", "PepsiCo", 1.75, 0, 15),
    ("Sprite 330ml", "Coca-Cola", 1.50, 0, 15),
    ("Red Bull 250ml", "Red Bull", 3.25, 0, 10),
    ("Evian Water 1L", "Evian", 2.00, 0, 25),
    ("Orange Juice 1L", "Tropicana", 3.50, 0, 12),
    ("Apple Juice 500ml", "Minute Maid", 2.75, 0, 10),
    ("Green Tea 500ml", "Lipton", 2.25, 0, 12),
    # Snacks (1)
    ("Lay's Classic Chips 150g", "Lay's", 2.99, 1, 18),
    ("Doritos Nacho 170g", "Frito-Lay", 3.49, 1, 15),
    ("Oreo Cookies 154g", "Nabisco", 2.79, 1, 12),
    ("Pringles Original 150g", "Pringles", 3.25, 1, 10),
    ("Snickers Bar 52g", "Mars", 1.25, 1, 20),
    ("KitKat 4-Finger", "Nestlé", 1.35, 1, 20),
    # Dairy (2)
    ("Whole Milk 1L", "Dairy Pure", 1.99, 2, 30),
    ("Greek Yogurt 200g", "Chobani", 2.49, 2, 15),
    ("Cheddar Cheese 200g", "Tillamook", 4.99, 2, 10),
    ("Butter 250g", "Kerrygold", 5.49, 2, 8),
    ("Cream Cheese 200g", "Philadelphia", 3.29, 2, 10),
    # Bakery (3)
    ("White Bread Loaf", "Wonder", 2.49, 3, 20),
    ("Croissant 4-Pack", "La Boulangerie", 3.99, 3, 10),
    ("Chocolate Muffin 2-Pack", "Otis Spunkmeyer", 3.49, 3, 8),
    ("Bagels 6-Pack", "Thomas'", 4.29, 3, 10),
    # Canned Goods (4)
    ("Tomato Soup 300ml", "Campbell's", 1.99, 4, 15),
    ("Baked Beans 400g", "Heinz", 1.75, 4, 18),
    ("Tuna Chunks 160g", "StarKist", 2.25, 4, 12),
    ("Sweet Corn 340g", "Green Giant", 1.50, 4, 15),
    ("Chickpeas 400g", "Goya", 1.25, 4, 12),
    # Frozen Foods (5)
    ("Frozen Pizza Margherita", "DiGiorno", 5.99, 5, 8),
    ("Ice Cream Vanilla 1L", "Häagen-Dazs", 6.99, 5, 6),
    ("Frozen Vegetables Mix 500g", "Birds Eye", 2.99, 5, 12),
    ("Fish Fingers 10-Pack", "Gorton's", 4.49, 5, 10),
    # Personal Care (6)
    ("Shampoo 400ml", "Head & Shoulders", 6.99, 6, 8),
    ("Toothpaste 100ml", "Colgate", 3.49, 6, 12),
    ("Body Wash 500ml", "Dove", 5.99, 6, 8),
    ("Deodorant Spray 150ml", "Old Spice", 4.99, 6, 10),
    # Cleaning Supplies (7)
    ("Dish Soap 750ml", "Dawn", 3.99, 7, 10),
    ("Laundry Detergent 1.5L", "Tide", 9.99, 7, 6),
    ("Disinfectant Wipes 80ct", "Clorox", 4.99, 7, 8),
    ("All-Purpose Cleaner 750ml", "Mr. Clean", 3.49, 7, 8),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Always clear existing data before seeding
    print("Clearing existing data...")
    for table in [
        "restocking_tasks", "alerts", "detections", "sale_items",
        "stock_movements", "inventory", "shelf_observations", "sales",
        "ai_conversations", "products", "categories",
    ]:
        c.execute(f"DELETE FROM [{table}]")
    conn.commit()

    now = datetime.now(timezone.utc)

    # ── Insert Categories ──
    for name, desc in CATEGORIES:
        c.execute(
            "INSERT INTO categories (name, description, created_at) VALUES (?, ?, ?)",
            (name, desc, now.isoformat()),
        )
    conn.commit()
    print(f"✅ Inserted {len(CATEGORIES)} categories")

    # ── Insert Products ──
    shelf_locations = ["Aisle 1", "Aisle 2", "Aisle 3", "Aisle 4", "Aisle 5", "End Cap", "Checkout"]
    for i, (name, brand, price, cat_idx, min_stock) in enumerate(PRODUCTS):
        sku = f"SV-{cat_idx+1:02d}-{i+1:04d}"
        barcode = f"8901234{i+1:06d}"
        created = now - timedelta(days=random.randint(30, 180))
        c.execute(
            """INSERT INTO products
               (name, brand, sku, barcode, price, category_id, description,
                image_path, min_stock_level, shelf_location, is_active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name, brand, sku, barcode, price,
                cat_idx + 1,  # category_id (1-indexed)
                f"{name} by {brand}",
                None,
                min_stock,
                random.choice(shelf_locations),
                True,
                created.isoformat(),
                now.isoformat(),
            ),
        )
    conn.commit()
    print(f"✅ Inserted {len(PRODUCTS)} products")

    # ── Insert Inventory ──
    for pid in range(1, len(PRODUCTS) + 1):
        min_stock = PRODUCTS[pid - 1][4]
        # Most products have healthy stock, some are low, a few are critical
        roll = random.random()
        if roll < 0.15:  # 15% chance of low/zero stock
            qty = random.randint(0, min_stock // 2)
        elif roll < 0.3:  # 15% chance of near-min stock
            qty = random.randint(min_stock // 2, min_stock)
        else:  # 70% healthy stock
            qty = random.randint(min_stock, min_stock * 4)

        shelf_qty = max(0, qty - random.randint(0, qty // 3)) if qty > 0 else 0

        c.execute(
            """INSERT INTO inventory
               (product_id, quantity_in_stock, quantity_on_shelf, last_counted_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (pid, qty, shelf_qty, (now - timedelta(hours=random.randint(1, 72))).isoformat(), now.isoformat()),
        )
    conn.commit()
    print(f"✅ Inserted {len(PRODUCTS)} inventory records")

    # ── Insert Sales (last 30 days) ──
    sale_id = 0
    total_sale_items = 0
    for day_offset in range(30, -1, -1):
        sale_date = now - timedelta(days=day_offset)
        # 8-25 sales per day
        num_sales = random.randint(8, 25)
        for _ in range(num_sales):
            sale_time = sale_date.replace(
                hour=random.randint(8, 21),
                minute=random.randint(0, 59),
            )
            # 1-5 items per sale
            num_items = random.randint(1, 5)
            items = random.sample(range(1, len(PRODUCTS) + 1), min(num_items, len(PRODUCTS)))
            sale_total = 0.0
            item_rows = []
            for prod_id in items:
                qty = random.randint(1, 4)
                unit_price = PRODUCTS[prod_id - 1][2]
                subtotal = round(qty * unit_price, 2)
                sale_total += subtotal
                item_rows.append((prod_id, qty, unit_price, subtotal))

            sale_id += 1
            c.execute(
                """INSERT INTO sales (sale_date, total_amount, source, notes, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (sale_time.isoformat(), round(sale_total, 2), "POS", None, sale_time.isoformat()),
            )
            actual_sale_id = c.lastrowid
            for prod_id, qty, unit_price, subtotal in item_rows:
                c.execute(
                    """INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
                       VALUES (?, ?, ?, ?, ?)""",
                    (actual_sale_id, prod_id, qty, unit_price, subtotal),
                )
                total_sale_items += 1

    conn.commit()
    print(f"✅ Inserted {sale_id} sales with {total_sale_items} line items")

    # ── Insert Stock Movements (last 30 days) ──
    movement_types = ["DELIVERY", "SALE", "WASTE", "ADJUSTMENT", "RETURN"]
    movement_count = 0
    for day_offset in range(30, -1, -1):
        move_date = now - timedelta(days=day_offset)
        num_movements = random.randint(5, 15)
        for _ in range(num_movements):
            prod_id = random.randint(1, len(PRODUCTS))
            m_type = random.choices(movement_types, weights=[20, 50, 5, 10, 5], k=1)[0]
            if m_type in ("DELIVERY", "RETURN"):
                qty = random.randint(5, 50)
            elif m_type == "SALE":
                qty = -random.randint(1, 8)
            elif m_type == "WASTE":
                qty = -random.randint(1, 5)
            else:
                qty = random.randint(-10, 10)

            mt = move_date.replace(hour=random.randint(6, 22), minute=random.randint(0, 59))
            c.execute(
                """INSERT INTO stock_movements (product_id, movement_type, quantity, reason, reference, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (prod_id, m_type, qty, f"{m_type.lower()} event", f"REF-{movement_count+1:05d}", mt.isoformat()),
            )
            movement_count += 1
    conn.commit()
    print(f"✅ Inserted {movement_count} stock movements")

    # ── Insert Alerts ──
    alert_types = [
        ("LOW_STOCK", "MEDIUM", "Stock level below minimum threshold for {product}"),
        ("LOW_STOCK", "HIGH", "Critical low stock for {product}"),
        ("OUT_OF_STOCK", "CRITICAL", "{product} is completely out of stock"),
        ("DISCREPANCY", "MEDIUM", "Shelf count mismatch detected for {product}"),
        ("EMPTY_SHELF", "HIGH", "Empty shelf section detected at {location}"),
        ("EXPIRY_WARNING", "LOW", "{product} approaching expiry date"),
    ]
    alert_count = 0
    for _ in range(random.randint(15, 30)):
        at = random.choice(alert_types)
        prod_id = random.randint(1, len(PRODUCTS))
        product_name = PRODUCTS[prod_id - 1][0]
        location = random.choice(shelf_locations)
        message = at[2].format(product=product_name, location=location)
        is_resolved = random.random() < 0.6
        created = now - timedelta(hours=random.randint(1, 168))
        resolved = (created + timedelta(hours=random.randint(1, 24))).isoformat() if is_resolved else None
        c.execute(
            """INSERT INTO alerts (product_id, alert_type, severity, message, is_resolved, created_at, resolved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (prod_id, at[0], at[1], message, is_resolved, created.isoformat(), resolved),
        )
        alert_count += 1
    conn.commit()
    print(f"✅ Inserted {alert_count} alerts")

    # ── Insert Restocking Tasks ──
    sources = ["LOW_STOCK_ALERT", "CV_OBSERVATION", "AI_RECOMMENDATION", "MANUAL"]
    statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
    priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
    task_count = 0
    for _ in range(random.randint(12, 25)):
        prod_id = random.randint(1, len(PRODUCTS))
        status = random.choices(statuses, weights=[30, 25, 35, 10], k=1)[0]
        created = now - timedelta(hours=random.randint(1, 120))
        completed = (created + timedelta(hours=random.randint(1, 48))).isoformat() if status == "COMPLETED" else None
        c.execute(
            """INSERT INTO restocking_tasks
               (product_id, quantity_needed, priority, status, source, assigned_to, created_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prod_id,
                random.randint(5, 50),
                random.choices(priorities, weights=[10, 40, 35, 15], k=1)[0],
                status,
                random.choice(sources),
                random.choice(["Ahmed", "Sara", "Omar", "Fatima", None]),
                created.isoformat(),
                completed,
            ),
        )
        task_count += 1
    conn.commit()
    print(f"✅ Inserted {task_count} restocking tasks")

    # ── Insert Shelf Observations ──
    obs_count = 0
    det_count = 0
    for day_offset in range(7, -1, -1):
        obs_date = now - timedelta(days=day_offset)
        num_obs = random.randint(2, 5)
        for _ in range(num_obs):
            obs_time = obs_date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
            loc = random.choice(shelf_locations)
            status = random.choices(["COMPLETED", "PENDING", "PROCESSING"], weights=[70, 20, 10], k=1)[0]
            processed = (obs_time + timedelta(seconds=random.randint(5, 30))).isoformat() if status == "COMPLETED" else None
            c.execute(
                """INSERT INTO shelf_observations
                   (image_path, shelf_location, status, notes, captured_at, processed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f"uploads/shelf_{obs_count+1}.jpg", loc, status, None, obs_time.isoformat(), processed),
            )
            obs_id = c.lastrowid
            obs_count += 1

            if status == "COMPLETED":
                num_dets = random.randint(3, 12)
                det_products = random.sample(range(1, len(PRODUCTS) + 1), min(num_dets, len(PRODUCTS)))
                for dp in det_products:
                    confidence = round(random.uniform(0.45, 0.99), 3)
                    det_status = random.choices(["CONFIRMED", "PENDING", "CORRECTED", "REJECTED"], weights=[50, 30, 10, 10], k=1)[0]
                    c.execute(
                        """INSERT INTO detections
                           (observation_id, product_id, label, confidence, bbox_x, bbox_y,
                            bbox_width, bbox_height, status, verified_quantity, employee_notes, reviewed_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            obs_id,
                            dp if random.random() > 0.1 else None,
                            PRODUCTS[dp - 1][0],
                            confidence,
                            round(random.uniform(0.0, 0.8), 3),
                            round(random.uniform(0.0, 0.8), 3),
                            round(random.uniform(0.05, 0.3), 3),
                            round(random.uniform(0.05, 0.3), 3),
                            det_status,
                            random.randint(1, 10) if det_status in ("CONFIRMED", "CORRECTED") else None,
                            None,
                            (obs_time + timedelta(minutes=random.randint(5, 60))).isoformat() if det_status != "PENDING" else None,
                        ),
                    )
                    det_count += 1

    conn.commit()
    print(f"✅ Inserted {obs_count} shelf observations with {det_count} detections")

    conn.close()
    print("\n🎉 Database seeded successfully!")


if __name__ == "__main__":
    seed()
