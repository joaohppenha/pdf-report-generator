import os
from playwright.async_api import async_playwright
from database import get_report_data


def generate_html(data: dict) -> str:
    """
    Builds the HTML document layout using data fetched from SQLite aggregations.
    Includes print CSS rules to handle clean page breaks across table rows.
    """
    # 1. Generate table rows for Top 5 Products by revenue
    top_products_rows = "".join(
        f"<tr><td>{p['product']}</td><td>R$ {p['revenue']:.2f}</td><td>{p['qty']}</td></tr>"
        for p in data["top_products"]
    )

    # 2. Generate table rows for Daily Stats (Last 7 Days)
    daily_rows = "".join(
        f"<tr><td>{d['order_date']}</td><td>{d['daily_orders']}</td><td>R$ {d['daily_revenue']:.2f}</td></tr>"
        for d in data["daily_stats"]
    )

    # 3. Generate table rows for full order details (Long table to test page breaks)
    all_orders_rows = "".join(
        f"<tr><td>#{o['id']}</td><td>{o['customer']}</td><td>{o['product']}</td><td>R$ {o['amount']:.2f}</td><td>{o['created_at']}</td></tr>"
        for o in data["all_orders"]
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            h1 {{ color: #111; margin-bottom: 5px; }}
            .date {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
            
            .cards {{ display: flex; gap: 20px; margin-bottom: 25px; }}
            .card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; flex: 1; }}
            .card-title {{ font-size: 12px; text-transform: uppercase; color: #6c757d; font-weight: bold; }}
            .card-value {{ font-size: 22px; font-weight: bold; margin-top: 5px; color: #0d6efd; }}

            h2 {{ font-size: 16px; margin-top: 25px; border-bottom: 2px solid #0d6efd; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
            th, td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; }}
            th {{ background-color: #f1f3f5; font-weight: bold; }}

            /* Print CSS: Prevents cutting table rows in half and repeats header on new pages */
            tr {{ break-inside: avoid; page-break-inside: avoid; }}
            thead {{ display: table-header-group; }}
        </style>
    </head>
    <body>
        <h1>Consolidated Sales Report</h1>
        <div class="date">Generated on: 2026-09-14</div>

        <div class="cards">
            <div class="card">
                <div class="card-title">Total Orders</div>
                <div class="card-value">{data['total_orders']}</div>
            </div>
            <div class="card">
                <div class="card-title">Total Revenue</div>
                <div class="card-value">R$ {data['total_revenue']:.2f}</div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>
        <table>
            <thead>
                <tr><th>Product</th><th>Total Revenue</th><th>Sales Qty</th></tr>
            </thead>
            <tbody>
                {top_products_rows}
            </tbody>
        </table>

        <h2>Performance (Last 7 Days)</h2>
        <table>
            <thead>
                <tr><th>Date</th><th>Total Orders</th><th>Revenue</th></tr>
            </thead>
            <tbody>
                {daily_rows}
            </tbody>
        </table>

        <h2>Detailed Orders List</h2>
        <table>
            <thead>
                <tr><th>ID</th><th>Customer</th><th>Product</th><th>Amount</th><th>Date</th></tr>
            </thead>
            <tbody>
                {all_orders_rows}
            </tbody>
        </table>
    </body>
    </html>
    """


async def render_pdf(output_path: str = "reports/test.pdf"):
    """
    Executes the Playwright headless browser to print the HTML template into a PDF file.
    Ensures output directory exists before writing artifacts.
    """
    # Ensure target output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Fetch aggregated metrics from SQLite database
    data = get_report_data()
    html_content = generate_html(data)

    # Render HTML into PDF using Playwright headless Chromium
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content)

        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
        )
        await browser.close()


if __name__ == "__main__":
    import asyncio

    # CLI test execution for Stage 3 checkpoint validation
    asyncio.run(render_pdf())