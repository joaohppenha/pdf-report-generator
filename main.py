import sqlite3
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from database import get_report_data
from renderer import render_pdf

app = FastAPI(title="PDF Report Generator API")

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def get_db():
    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Ensure reports metadata table exists in SQLite database
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


# Initialize database schema on startup
init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports", status_code=201)
async def create_report(force: bool = False, response: Response = None):
    today = datetime.now().strftime("%Y-%m-%d")

    with get_db() as conn:
        cursor = conn.cursor()

        # Idempotency check: Return existing report generated today
        cursor.execute(
            "SELECT id, path FROM reports WHERE DATE(created_at) = ? ORDER BY id DESC LIMIT 1",
            (today,),
        )
        existing = cursor.fetchone()

        if existing and not force:
            response.status_code = 200
            return {
                "id": existing["id"],
                "file": f"/reports/{existing['id']}/file",
            }

        # Register report record in DB first to get unique report ID
        created_at = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO reports (path, created_at) VALUES ('', ?)",
            (created_at,),
        )
        report_id = cursor.lastrowid

        file_path = REPORTS_DIR / f"{report_id}.pdf"

        # Update disk file path in database record
        cursor.execute(
            "UPDATE reports SET path = ? WHERE id = ?",
            (str(file_path), report_id),
        )
        conn.commit()

    # Query metrics and render PDF via Playwright
    await render_pdf(output_path=str(file_path))

    return {"id": report_id, "file": f"/reports/{report_id}/file"}


@app.get("/reports/{report_id}")
def get_report_metadata(report_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, path, created_at FROM reports WHERE id = ?",
            (report_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404, detail="Report metadata not found"
            )

        return {
            "id": row["id"],
            "path": row["path"],
            "created_at": row["created_at"],
            "file": f"/reports/{row['id']}/file",
        }


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT path FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()

        # Verify record and ensure physical file exists on disk
        if not row or not Path(row["path"]).exists():
            raise HTTPException(
                status_code=404, detail="Report file not found"
            )

        # Serve binary file directly from disk
        return FileResponse(row["path"], media_type="application/pdf")