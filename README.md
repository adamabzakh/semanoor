# Semanoor — Knowledge in Motion

Complete website source, interactive Three.js scenes, assets, and Docling conversion demo.

## Run the website

Install Node.js 20.19+ or 22.12+, then run:

```sh
npm ci
npm run dev
```

Open the local URL printed by Vite. Serve the website over HTTP rather than opening index.html directly. The 3D scenes require WebGL; a static fallback appears when it is unavailable.

## Project structure

- `dist/`: deployable static website, local Three.js modules, images, and Document Studio frontend.
- `dist/hero3d.js`, `dist/journey3d.js`, `dist/spatial.js`: 3D scenes and model builders.
- `converter-service/`: Python FastAPI backend that runs Docling.
- `.openai/hosting.json`: existing Sites deployment configuration.

## Docling conversion

The website includes a preconverted sample. Live file uploads require the Python service to be running and connected. Follow `converter-service/README.md` for local setup or Docker deployment. No API keys or hosted converter are included.

## Upload to GitHub

Extract this archive. Create an empty private GitHub repository named `semanoor-motion`, then run from this folder:

```sh
git init
git add .
git commit -m "Initial Semanoor website"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/semanoor-motion.git
git push -u origin main
```

Alternatively upload the extracted files through GitHub's website. Include `.gitignore` when uploading.

The ZIP excludes installed dependencies, virtual environments, Git history, and credentials. Install dependencies using the lockfile. Third-party notices are in `dist/assets/`.
