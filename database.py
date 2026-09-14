import sqlite3

def get_report_data() -> dict:
    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Total KPI Metrics
    cursor.execute("SELECT COUNT(*) as total_orders, COALESCE(SUM(amount), 0) as total_revenue FROM orders")
    totals = cursor.fetchone()

    # 2. Top 5 Products by Revenue
    cursor.execute("""
        SELECT product, SUM(amount) as revenue, COUNT(*) as qty
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """)
    top_products = [dict(row) for row in cursor.fetchall()]

    # 3. Daily Sales Performance (Last 7 Days)
    cursor.execute("""
        SELECT DATE(created_at) as order_date, COUNT(*) as daily_orders, SUM(amount) as daily_revenue
        FROM orders
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY order_date DESC
    """)
    daily_stats = [dict(row) for row in cursor.fetchall()]

    # 4. Detailed Orders List
    cursor.execute("SELECT id, customer, product, amount, created_at FROM orders ORDER BY id ASC")
    all_orders = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_orders": totals["total_orders"],
        "total_revenue": totals["total_revenue"],
        "top_products": top_products,
        "daily_stats": daily_stats,
        "all_orders": all_orders
    }

if __name__ == "__main__":
    import json
    data = get_report_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))