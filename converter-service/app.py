"""Semanoor's ephemeral, authenticated Docling conversion demo."""
import asyncio
import hmac
import logging
import os
import secrets
import tempfile
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 50
TTL = 900
EXTENSIONS = {'.pdf', '.docx', '.pptx', '.html', '.png', '.jpg', '.jpeg'}
JOBS = {}
UPLOAD_LOCK = asyncio.Lock()
API_KEY = os.environ.get('CONVERTER_API_KEY', '')
LOCAL = os.environ.get('CONVERTER_LOCAL', '') == '1'
if not API_KEY and not LOCAL:
    raise RuntimeError('Set CONVERTER_API_KEY, or use CONVERTER_LOCAL=1 on localhost only.')

async def auth(authorization: str = Header(default='')):
    if LOCAL and not API_KEY:
        return
    supplied = authorization.removeprefix('Bearer ')
    if not supplied or not hmac.compare_digest(supplied, API_KEY):
        raise HTTPException(401, 'The converter access key is missing or incorrect.')

async def reap():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for key in list(JOBS):
            job = JOBS[key]
            if job['status'] not in ('queued', 'converting') and now - job['created'] > TTL:
                JOBS.pop(key, None)

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(reap())
    yield
    task.cancel()

app = FastAPI(title='Semanoor Document Studio', lifespan=lifespan)
origins = [x.strip() for x in os.environ.get('ALLOWED_ORIGINS', 'https://semanoor-knowledge-in-motion.adamabzakh.chatgpt.site').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Authorization', 'Content-Type'], max_age=600)

@app.get('/api/health')
async def health():
    return {'ready': True, 'engine': 'Docling', 'max_bytes': MAX_BYTES, 'max_pages': MAX_PAGES}

@app.get('/api/session', dependencies=[Depends(auth)])
async def session():
    return {'authorized': True}

def convert_document(data, suffix, filename, ocr):
    from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
    options = PdfPipelineOptions()
    options.do_ocr = ocr
    options.document_timeout = 300
    if ocr:
        options.ocr_options = TesseractCliOcrOptions(lang=["eng", "ara"])
    options.do_table_structure = True
    options.enable_remote_services = False
    image_options = options.model_copy(deep=True)
    image_options.do_ocr = True
    image_options.ocr_options = TesseractCliOcrOptions(lang=["eng", "ara"])
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options), InputFormat.IMAGE: ImageFormatOption(pipeline_options=image_options)})
    with tempfile.TemporaryDirectory(prefix='semanoor-') as temp:
        source = Path(temp) / ('document' + suffix)
        source.write_bytes(data)
        result = converter.convert(source, max_num_pages=MAX_PAGES, max_file_size=MAX_BYTES)
        if result.status.value not in ('success', 'partial_success'):
            raise ValueError('Docling could not convert this document.')
        doc = result.document
        markdown = doc.export_to_markdown()
        if not markdown.strip():
            raise ValueError('No readable content was found. For scanned PDFs, enable OCR and try again.')
        document = doc.export_to_dict()
        # Avoid leaking the server's temporary path in exported metadata.
        document['name'] = Path(filename).stem
        outline = []
        for item, level in doc.iterate_items():
            label = str(getattr(item, 'label', ''))
            if label in ('title', 'section_header'):
                pages = [p.page_no for p in getattr(item, 'prov', [])]
                outline.append({'text': getattr(item, 'text', ''), 'page': pages[0] if pages else None})
        return {'filename': filename, 'markdown': markdown, 'document': document,
                'outline': outline, 'stats': {'pages': len(doc.pages) or None, 'tables': len(doc.tables),
                'sections': len(outline), 'words': len(markdown.split())},
                'partial': result.status.value == 'partial_success', 'engine': 'Docling'}

async def run_job(job_id, data, suffix, filename, ocr):
    job = JOBS[job_id]
    job['status'] = 'converting'
    try:
        result = await asyncio.to_thread(convert_document, data, suffix, filename, ocr)
        if job_id in JOBS and not job.get('cancelled'):
            job.update(status='complete', result=result)
        else:
            job.update(status='cancelled')
    except Exception as exc:
        logging.exception('Docling conversion failed')
        if job_id in JOBS:
            message = str(exc) if isinstance(exc, ValueError) else 'Conversion failed. Check the document and the converter service logs.'
            job.update(status='failed', error=message)
    finally:
        job['created'] = time.time()

def validate_upload(data, suffix):
    if suffix == '.pdf' and not data.startswith(b'%PDF-'):
        raise HTTPException(400, 'This file is not a valid PDF.')
    if suffix in ('.docx', '.pptx'):
        import io
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(x.file_size for x in archive.infolist()) > 80 * 1024 * 1024:
                    raise HTTPException(400, 'The expanded document is too large for this demo.')
                required = 'word/document.xml' if suffix == '.docx' else 'ppt/presentation.xml'
                if required not in archive.namelist():
                    raise HTTPException(400, 'The file contents do not match its extension.')
        except zipfile.BadZipFile:
            raise HTTPException(400, 'The Office document is damaged or invalid.')

@app.post('/api/jobs', dependencies=[Depends(auth)], status_code=202)
async def create_job(file: UploadFile = File(...), ocr: bool = Form(False)):
    async with UPLOAD_LOCK:
        if any(j['status'] in ('queued', 'converting') for j in JOBS.values()):
            raise HTTPException(429, 'The demo is converting another document. Please try again shortly.')
        if len(JOBS) >= 12:
            oldest = next((k for k, j in JOBS.items() if j['status'] not in ('queued', 'converting')), None)
            if oldest:
                JOBS.pop(oldest)
        filename = Path(file.filename or 'document').name[:160]
        suffix = Path(filename).suffix.lower()
        if suffix not in EXTENSIONS:
            raise HTTPException(415, 'Choose a PDF, DOCX, PPTX, HTML, PNG or JPEG file.')
        data = await file.read(MAX_BYTES + 1)
        await file.close()
        if not data or len(data) > MAX_BYTES:
            raise HTTPException(413, 'Choose a nonempty document smaller than 10 MB.')
        validate_upload(data, suffix)
        job_id = secrets.token_urlsafe(24)
        JOBS[job_id] = {'status': 'queued', 'created': time.time()}
        asyncio.create_task(run_job(job_id, data, suffix, filename, ocr))
        return {'id': job_id, 'status': 'queued'}

@app.get('/api/jobs/{job_id}', dependencies=[Depends(auth)])
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, 'This conversion has expired. Upload the document again.')
    return {key: value for key, value in job.items() if key != 'created'}

@app.delete('/api/jobs/{job_id}', dependencies=[Depends(auth)])
async def cancel_job(job_id: str):
    job = JOBS.get(job_id)
    if job:
        if job['status'] in ('queued', 'converting'):
            job['cancelled'] = True
        else:
            JOBS.pop(job_id, None)
    return {'cancelled': True}

static = Path(__file__).resolve().parent.parent / 'dist'
if static.exists():
    app.mount('/', StaticFiles(directory=static, html=True), name='site')
