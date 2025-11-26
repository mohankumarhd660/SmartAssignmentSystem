# Deploying a static export to Netlify

This project is a Flask app with dynamic features (login, upload, database). Netlify is a static-hosting platform — it cannot run Python server code. The included `freeze.py` creates a minimal static export (in `build/`) by fetching a few public pages and copying the `static/` folder so CSS/JS/images work.

Important: pages that require login, file uploads, or database interactions will not work after statically exporting.

How to create the static build (PowerShell):

```powershell
# create a virtualenv (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run the exporter
python freeze.py
```

After the script runs, a `build/` directory will be created. Verify it contains `index.html` and a `static/` directory.

Deploy to Netlify using the CLI (optional):

```powershell
# install netlify cli (requires node/npm installed)
npm install -g netlify-cli

# login once interactively (opens browser)
netlify login

# deploy the build folder interactively (first time) or to production
netlify deploy --dir=build --prod
```

Or, if you use Git/GitHub, you can push this repo to GitHub and create a Netlify site that points to the repo and uses the `build/` directory as the published folder. Netlify's automatic builds expect a build command; since this is a pre-built folder, choose the repo and set the build command to blank and publish directory to `build`.

If you want a full backend deployment (to keep login and submission features), consider Render, Railway, or another Python host. I can prepare a `Procfile` and `runtime.txt` and guide deployment to Render — ask me to do that if you prefer a full server deployment.