# Semanoor — Knowledge in Motion

An interactive website concept for Semanoor, exploring how learning moves from the printed page to digital and immersive experiences. The project combines a Saudi-inspired visual identity, scroll-driven 3D scenes, and a document-conversion demo powered by Docling.

The website runs as a static HTML, CSS, and JavaScript application. Live document conversion is provided by an optional, separately hosted Python service.

## Features

- **Interactive 3D hero:** a curved-page book, textured globe, and floating content panels, with drag rotation, page-turn, reset, and pause controls.
- **Animated learning journey:** scroll-driven transitions between a book, tablet, interactive content, and a Saudi-inspired courtyard.
- **Saudi visual identity:** heritage imagery, Arabic accents, and a dismissible Saudi National Day banner for September 23.
- **Responsive presentation:** layouts for desktop and mobile, keyboard controls for the hero, reduced-motion handling, and static imagery when WebGL is unavailable.
- **Document Studio:** upload supported documents, inspect extracted content, and download Markdown or structured JSON when a converter is connected.
- **Included sample:** explore a preconverted English-and-Arabic lesson without running the backend.

## Project status

This repository contains a website concept and an experimental document-conversion service. The sample is available immediately; **live uploads require a running Docling backend**. No public conversion endpoint or API key is included.

The converter uses temporary, in-memory jobs and a shared access key. It is intended for a controlled demonstration, rather than a production service with user accounts, persistent storage, or a distributed queue.

## Technology

| Component | Technology |
| --- | --- |
| Website | HTML, CSS, JavaScript ES modules |
| 3D rendering | Three.js, bundled locally |
| Local development | Vite |
| Conversion API | Python, FastAPI, Uvicorn |
| Document processing | Docling |
| OCR | Tesseract with English and Arabic language data |
| Backend packaging | Docker |

## Quick start: website

Use Node.js **20.19+ or 22.12+** and npm. From the repository root:

```sh
npm ci
npm run dev
```

Open the local URL printed by Vite. Document Studio is available at `/convert/`.

The website files in `dist/` are authored static files and are ready to serve. This project does not require a production build command. Serve the files over HTTP or HTTPS; opening `index.html` directly through a `file://` URL will not reliably load JavaScript modules.

### Hero controls

| Action | Control |
| --- | --- |
| Rotate the scene | Drag, or focus the scene and use the arrow keys |
| Turn a page | **Turn a page** button, or Space while the scene is focused |
| Reset the view | **Reset view** button, or R while the scene is focused |
| Pause automatic hero motion | **Pause auto-motion** button |
| Progress through the scenes | Scroll the page |

3D rendering requires a browser and device that support WebGL. The website displays static fallback imagery if it cannot create a WebGL renderer.

## Run live document conversion

### Option 1: Docker

With Docker installed, run these commands from the repository root:

```sh
docker build -f converter-service/Dockerfile -t semanoor-docling .

docker run --rm \
  -p 127.0.0.1:8000:8000 \
  -e CONVERTER_LOCAL=1 \
  semanoor-docling
```

Open [Document Studio locally](http://127.0.0.1:8000/convert/). The Python service also serves the website, so a separate Vite process is unnecessary for this setup.

`CONVERTER_LOCAL=1` allows access without an API key. Use this mode only with the localhost binding shown above.

### Option 2: Python

Use Python 3.12. Install Tesseract and its English and Arabic language data on your system before using OCR. The following commands use a macOS/Linux shell:

```sh
python3.12 -m venv .venv
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r converter-service/requirements.txt

CONVERTER_LOCAL=1 .venv/bin/uvicorn app:app \
  --app-dir converter-service \
  --host 127.0.0.1 \
  --port 8000
```

Open `http://127.0.0.1:8000/convert/`.

The first PDF conversion downloads model weights and can take longer. The service needs outbound access for those downloads and sufficient memory for inference. See the [converter setup guide](converter-service/README.md) for additional details.

### Supported files and limits

| Item | Current behavior |
| --- | --- |
| Input formats | PDF, DOCX, PPTX, HTML, PNG, JPG, JPEG |
| Output formats | Markdown and structured JSON |
| Upload size | Up to 10 MiB |
| PDF length | Up to 50 pages |
| Expanded Office archive | Up to 80 MiB |
| Concurrent conversion | One active conversion; additional requests receive a busy response |
| PDF OCR | Optional; enable **Read scanned pages** |
| Image OCR | Always enabled |
| OCR languages | English and Arabic |
| Completed-job retention | Approximately 15 minutes; results can also be evicted earlier or lost on restart |

Temporary source files are removed after processing. Cancelling a conversion discards its result but does not forcibly stop a native conversion already in progress. Extraction quality, especially for complex layouts and Arabic OCR, should be evaluated with representative documents.

## Deployment

### Static website: Hostinger shared hosting or another static host

1. Back up any existing website before replacing its files.
2. Upload **the contents of `dist/`** into the domain's document root. On Hostinger shared hosting, this is typically `public_html/`.
3. Ensure the main page is located at `public_html/index.html`, rather than inside an additional `dist/` folder.
4. Preserve the `assets/` and `convert/` folders and all JavaScript modules.
5. Open the domain and check the home page and `/convert/`.

No Node.js server, Python process, or database is required for the static website. Deploy it at a domain or subdomain root: some navigation links use root-relative paths such as `/convert/`.

The included sample works on static hosting. Live conversion needs a separate Python-capable host; uploading `converter-service/` to a shared-hosting document root does not start the API.

### Hosted converter

Deploy `converter-service/` together with `dist/` using the included Dockerfile or the Python setup above. Use a single Uvicorn worker because job state is kept in process memory.

Configure these values on the backend host:

| Variable | Purpose |
| --- | --- |
| `CONVERTER_API_KEY` | A strong secret required to access conversion endpoints |
| `ALLOWED_ORIGINS` | Comma-separated website origins allowed by CORS, for example `https://example.com,https://www.example.com` |
| `CONVERTER_LOCAL` | Leave unset for a publicly reachable service |

Serve the converter over HTTPS. In Document Studio, select **Connect converter**, then enter the service origin and access key. The browser sends uploaded documents directly to that service; the access key is held in page memory.

To preconfigure the service address, edit `dist/convert/config.json`:

```json
{
  "serviceUrl": "https://converter.example.com"
}
```

This is an example address, not an included service. **Never place the access key in this file, frontend code, or the repository.**

For a public application, add appropriate user authentication, per-user authorization, rate limiting, durable job storage, and operational monitoring before offering unrestricted uploads.

## Repository guide

| Path | Purpose |
| --- | --- |
| `dist/index.html` | Main website markup |
| `dist/style.css` | Website styles and responsive layouts |
| `dist/script.js` | General page interactions |
| `dist/hero3d.js` | Interactive hero scene |
| `dist/journey3d.js` | Scroll-driven learning journey |
| `dist/spatial.js` | Shared rendering setup and procedural model builders |
| `dist/three.module.js`, `dist/three.core.js` | Local Three.js runtime |
| `dist/rounded-box.js`, `dist/room-environment.js` | Three.js geometry and lighting helpers |
| `dist/assets/` | Earth texture, source information, and third-party license notice |
| `dist/convert/` | Document Studio frontend and preconverted sample |
| `converter-service/app.py` | Conversion API and temporary job handling |
| `converter-service/requirements.txt` | Python dependencies |
| `converter-service/Dockerfile` | Container configuration |
| `package.json`, `package-lock.json` | Local development dependencies and commands |
| `vite.config.js` | Development server configuration |
| `.openai/hosting.json` | Configuration for the original Sites deployment |

## Contributing

Issues and pull requests are welcome. Describe the problem or intended behavior, include reproduction steps where relevant, and keep changes focused.

For visual changes, check desktop and mobile layouts, reduced-motion behavior, and the WebGL fallback. For converter changes, use non-sensitive sample documents and verify the exported Markdown and JSON.

Do not commit API keys, environment files, private documents, installed dependencies, or model caches. The repository includes a `.gitignore` for common local files.

## Credits and licensing

- [Three.js](https://threejs.org/) provides the 3D rendering library and helper modules. Its MIT license notice is included in [dist/assets/THREE-LICENSE.txt](dist/assets/THREE-LICENSE.txt).
- [Docling](https://github.com/docling-project/docling) provides document conversion.
- [Tesseract](https://github.com/tesseract-ocr/tesseract) provides OCR.
- Asset source information is recorded in [dist/assets/SOURCES.txt](dist/assets/SOURCES.txt).

No project-wide license is currently included. Public repository access does not, by itself, grant permission to reuse or redistribute the original project code, Semanoor branding, or visual assets. Third-party components remain subject to their respective licenses.
