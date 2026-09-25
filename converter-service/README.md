# Semanoor Document Studio

This service runs actual Docling conversion. The existing Sites host only serves the frontend; Python inference needs a separate persistent host. No public converter is preconfigured.

## Run the complete demo locally

From the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r converter-service/requirements.txt
CONVERTER_LOCAL=1 .venv/bin/uvicorn app:app --app-dir converter-service --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/convert/. The first PDF conversion downloads Docling model weights. Office/HTML conversion does not require PDF models. Arabic OCR quality and complex RTL layouts need evaluation on real source documents. PDF OCR is off by default. Scanned PDFs and image uploads use Tesseract with English and Arabic language data; install `tesseract-ocr`, `tesseract-ocr-eng`, and `tesseract-ocr-ara` when running without Docker. Images always use OCR.

## Deploy the service

Build from the repository root:

```sh
docker build -f converter-service/Dockerfile -t semanoor-docling .
```

For a local Docker demo, run:

```sh
docker run --rm -p 127.0.0.1:8000:8000 -e CONVERTER_LOCAL=1 semanoor-docling
```

Then open http://127.0.0.1:8000/convert/.

For a hosted service, run with a strong `CONVERTER_API_KEY` environment secret, HTTPS ingress, and `ALLOWED_ORIGINS=https://semanoor-knowledge-in-motion.adamabzakh.chatgpt.site`. Do not use `CONVERTER_LOCAL=1` on a public host. The service accepts one active conversion at a time; use a single Uvicorn worker. CPU inference requires a host with several GB of memory and outbound access to download the required model weights. This is an ephemeral demo, not a production job queue.

In Document Studio, choose **Connect converter**, enter the HTTPS service origin and its key. The key is held only in page memory. Alternatively set `dist/convert/config.json` to `{"serviceUrl":"https://YOUR-SERVICE"}` (never put the key in this file). The browser sends documents directly to that service, whose operator can access uploads. Configure only a service you control.

Temporary source files are deleted after processing. Completed output expires after 15 minutes (cleanup runs every minute), is deleted on reset, and disappears on service restart. Cancelling hides/discards the result but does not forcibly interrupt an in-progress native model operation.

Limits: 10 MB upload, 50 PDF pages, 80 MB expanded Office archive. No upload URLs or remote enrichment are accepted. Preview output is rendered as text/DOM, never trusted raw HTML. Encrypted or malformed documents produce an error. Password removal, automatic publishing, quizzes, and a tutor are outside this demo.
