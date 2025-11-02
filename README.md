# HTML To PDF Generator

A lightweight FastAPI microservice that generates PDFs from HTML or URLs using **Playwright (Chromium)**.  
It supports configurable formatting, automatic cleanup of old files, and cross-origin access for frontend apps.

---

## Features

1. Generate PDFs from raw HTML or a public URL
2. Serve generated PDFs via static routes
3. Automatic cleanup of old files (default: 1 hour retention)
4. Fully customizable PDF output (size, margins, scale, backgrounds)
5. Deployable on any domain or Docker host without code changes

---

## Usage

### 1. Run locally (standalone mode)

**Install dependencies:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
playwright install --with-deps chromium
```

**Run the service:**

```bash
python pdf_service.py
```

Default port: **http://localhost:8080**

---

### 2. Build & Run with Docker

**Build:**

```bash
docker build -t pdf-generator-service .
```

**Run:**

```bash
docker run --rm -d \
  -p 8080:8080 \
  -e PDF_BASE_URL="https://yourdomain.com" \
  -e PDF_RETENTION_SECONDS=3600 \
  -e PDF_FORMAT=A4 \
  -e PDF_PRINT_BACKGROUND=false \
  -e PDF_SCALE=0.6 \
  -e PDF_MARGIN_TOP=1cm \
  -e PDF_MARGIN_BOTTOM=1cm \
  -e PDF_MARGIN_LEFT=1cm \
  -e PDF_MARGIN_RIGHT=1cm \
  -v $(pwd)/generated_pdfs:/app/generated_pdfs \
  --name pdf-generator-service \
  pdf-generator-service
```

---

## API Endpoints

### `POST /generate-pdf`

Generate a PDF from HTML or URL.

**Example (HTML):**

```bash
curl -X POST http://localhost:8080/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Hello World</h1>"}'
```

**Example (URL):**

```bash
curl -X POST http://localhost:8080/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Response:**

```json
{
  "pdf_url": "http://localhost:8080/pdfs/abc1234.pdf"
}
```

---

### `GET /`

Simple health check endpoint:

```json
{ "message": "PDF Generator Service is running." }
```

---

## Environment Variables

| Variable                | Default                 | Description                             |
| ----------------------- | ----------------------- | --------------------------------------- |
| `PORT`                  | `8080`                  | Port to run the service                 |
| `PDF_BASE_URL`          | auto-detected           | Base URL for returning full PDF links   |
| `PDF_RETENTION_SECONDS` | `3600`                  | How long to keep PDFs before deleting   |
| `PDF_CLEANUP_INTERVAL`  | `300`                   | How often to check for expired PDFs     |
| `PDF_FORMAT`            | `A4`                    | Paper format (`A4`, `Letter`, etc.)     |
| `PDF_PRINT_BACKGROUND`  | `false`                 | Print background colors/images          |
| `PDF_SCALE`             | `0.6`                   | Scaling factor for page content         |
| `PDF_MARGIN_TOP`        | `1cm`                   | Top margin                              |
| `PDF_MARGIN_BOTTOM`     | `1cm`                   | Bottom margin                           |
| `PDF_MARGIN_LEFT`       | `1cm`                   | Left margin                             |
| `PDF_MARGIN_RIGHT`      | `1cm`                   | Right margin                            |
| `PDF_COOKIE_DOMAIN`     | auto-detected           | Domain for injected cookies             |
| `CORS_ORIGINS`          | `http://localhost:5173` | Comma-separated list of allowed origins |

---

## Recommended Retention Settings

| Use Case                      | Retention                  |
| ----------------------------- | -------------------------- |
| Sensitive data (user reports) | `900` seconds (15 min)     |
| Normal app usage              | `3600` seconds (1 hour)    |
| Archival or testing           | `86400` seconds (24 hours) |

---

## Frontend Example

```js
const response = await fetch("http://localhost:8080/generate-pdf", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ html: "<h1>Hello PDF</h1>" }),
});

const data = await response.json();
window.open(data.pdf_url, "_blank");
```

---

## License

Licensed under the **Apache License 2.0**.

---

## Author

**Balázs Sárközi**
