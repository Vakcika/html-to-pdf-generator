#!/usr/bin/env python3

#--------------------------------------------------------
# PDF Generator Service
#--------------------------------------------------------
# FastAPI-based microservice to render HTML or URLs
# into PDF files using Playwright (Chromium).
# Automatically cleans up old PDFs after a retention time
# and allows full PDF rendering customization.
#
# created by: Balázs Sárközi
# last updated: 2025.11.02
#--------------------------------------------------------

import os
import uuid
import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright

#--------------------------------------------------------
# Initialization
#--------------------------------------------------------

app = FastAPI(title="PDF Generator Service")

# CORS setup (customizable for production)
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for generated PDFs
PDF_DIR = "generated_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=PDF_DIR), name="pdfs")

# Retention configuration
PDF_RETENTION_SECONDS = int(os.environ.get("PDF_RETENTION_SECONDS", 3600))  # 1 hour
PDF_CLEANUP_INTERVAL = int(os.environ.get("PDF_CLEANUP_INTERVAL", 300))     # 5 min

# PDF generation settings (defaults)
PDF_FORMAT = os.environ.get("PDF_FORMAT", "A4")
PDF_PRINT_BACKGROUND = os.environ.get("PDF_PRINT_BACKGROUND", "false").lower() == "true"
PDF_SCALE = float(os.environ.get("PDF_SCALE", 0.6))
PDF_MARGIN_TOP = os.environ.get("PDF_MARGIN_TOP", "1cm")
PDF_MARGIN_BOTTOM = os.environ.get("PDF_MARGIN_BOTTOM", "1cm")
PDF_MARGIN_LEFT = os.environ.get("PDF_MARGIN_LEFT", "1cm")
PDF_MARGIN_RIGHT = os.environ.get("PDF_MARGIN_RIGHT", "1cm")

# Optional cookie domain override
PDF_COOKIE_DOMAIN = os.environ.get("PDF_COOKIE_DOMAIN")

#--------------------------------------------------------
# Background cleanup task
#--------------------------------------------------------
async def cleanup_old_pdfs():
    """Delete PDFs older than the retention limit."""
    while True:
        now = time.time()
        removed = 0
        for filename in os.listdir(PDF_DIR):
            file_path = os.path.join(PDF_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    age = now - os.path.getmtime(file_path)
                    if age > PDF_RETENTION_SECONDS:
                        os.remove(file_path)
                        removed += 1
            except Exception:
                pass
        if removed > 0:
            print(f"[CLEANUP] Removed {removed} expired PDF(s)")
        await asyncio.sleep(PDF_CLEANUP_INTERVAL)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_pdfs())

#--------------------------------------------------------
# PDF rendering helper
#--------------------------------------------------------
async def render_pdf(page, output_path: str):
    """Render a PDF using environment-based settings."""
    await page.emulate_media(media="print")
    await page.pdf(
        path=output_path,
        format=PDF_FORMAT,
        print_background=PDF_PRINT_BACKGROUND,
        scale=PDF_SCALE,
        margin={
            "top": PDF_MARGIN_TOP,
            "bottom": PDF_MARGIN_BOTTOM,
            "left": PDF_MARGIN_LEFT,
            "right": PDF_MARGIN_RIGHT,
        },
    )

#--------------------------------------------------------
# Endpoint: Generate PDF
#--------------------------------------------------------
@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    """
    Generate a PDF from HTML or a URL.

    Example JSON:
    {
        "html": "<html>...</html>"
    }
    or
    {
        "url": "https://example.com"
    }
    """
    data = await request.json()
    pdf_id = str(uuid.uuid4())
    output_path = os.path.join(PDF_DIR, f"{pdf_id}.pdf")

    laravel_token = request.cookies.get("token")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        # Inject Laravel cookie if provided
        if laravel_token:
            domain = PDF_COOKIE_DOMAIN or request.url.hostname or "localhost"
            await context.add_cookies([{
                "name": "token",
                "value": laravel_token,
                "domain": domain,
                "path": "/",
            }])

        page = await context.new_page()

        if "html" in data:
            await page.set_content(data["html"], wait_until="networkidle")
        elif "url" in data:
            await page.goto(data["url"], wait_until="networkidle")
        else:
            await browser.close()
            return JSONResponse(
                status_code=400,
                content={"error": "Provide either 'html' or 'url' in the JSON body."},
            )

        await render_pdf(page, output_path)
        await browser.close()

    # Determine base URL for PDF link
    base_url = os.environ.get("PDF_BASE_URL")
    if not base_url:
        scheme = request.url.scheme
        host = request.headers.get("host", f"localhost:{os.environ.get('PORT', 8080)}")
        base_url = f"{scheme}://{host}"

    pdf_url = f"{base_url}/pdfs/{pdf_id}.pdf"
    return {"pdf_url": pdf_url}

#--------------------------------------------------------
# Health check
#--------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "PDF Generator Service is running."}

#--------------------------------------------------------
# Main entry
#--------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("pdf_service:app", host="0.0.0.0", port=port, reload=True)
