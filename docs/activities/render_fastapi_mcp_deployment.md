# Render Deployment Activity for FastAPI + FastMCP

This activity documents how to deploy the FastAPI + FastMCP server in this repository to Render as a reusable web service deployment pattern.

## Goal

Deploy the existing ASGI app to Render so the following endpoints are publicly reachable:

- `/`
- `/health`
- `/docs`
- `/mcp/`

## Current App Entrypoint

This repository does **not** use `main:app`.

The correct ASGI app import path for Render is:

```bash
converter_streamable_http_server:app
```

Source file:

- `converter_streamable_http_server.py`

## Repo Preconditions

Confirm these files exist before deployment:

- `converter_streamable_http_server.py`
- `requirements.txt`

Current Python dependencies already include:

- `fastapi`
- `fastmcp`
- `uvicorn`

## Local Verification

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the server locally:

```bash
uvicorn converter_streamable_http_server:app --host 127.0.0.1 --port 8003
```

Verify these URLs locally:

```text
http://localhost:8003/
http://localhost:8003/health
http://localhost:8003/docs
http://localhost:8003/mcp/
```

Expected results:

- `/` returns a small JSON service document
- `/health` returns JSON with `"status": "ok"`
- `/docs` loads Swagger UI
- `/mcp/` responds as the MCP streamable HTTP endpoint

Notes:

- The MCP endpoint should be tested with `/mcp/` including the trailing slash for consistency with existing tests.

## GitHub Preparation

Push the current repository state to GitHub:

```bash
git add .
git commit -m "Prepare FastAPI MCP app for Render deployment"
git push
```

Do not commit `.env`. It is already ignored by `.gitignore`.

## Render Service Setup

In Render:

1. Create a new `Web Service`
2. Connect the GitHub repository
3. Choose `Python 3`
4. Configure the service with the following values

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn converter_streamable_http_server:app --host 0.0.0.0 --port $PORT
```

Recommended Health Check Path:

```text
/health
```

Why this start command matters:

- Render requires the app to bind to `0.0.0.0`
- Render injects the runtime port through `$PORT`
- This repository’s ASGI app is exported from `converter_streamable_http_server.py`

## Environment Variables

Add only the environment variables your deployed service actually needs.

For the FastAPI/MCP server itself, no required secret has been identified in the current server startup path.

Optional variables used elsewhere in the repo include:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
MCP_SERVER_URL=https://your-service-name.onrender.com/mcp
```

Important:

- `GEMINI_API_KEY` is used by `gemini_client/simulated_gemini_client.py`, not by the FastAPI server startup path itself
- Store secrets in Render environment variables, not in the repository

## Deploy

Create the web service in Render and wait for the first build to complete.

After deployment, Render will assign a URL similar to:

```text
https://your-service-name.onrender.com
```

## Post-Deploy Verification

Test these URLs:

```text
https://your-service-name.onrender.com/
https://your-service-name.onrender.com/health
https://your-service-name.onrender.com/docs
https://your-service-name.onrender.com/mcp/
```

Expected results:

- `/` returns a small JSON service document
- `/health` returns a successful JSON response
- `/docs` loads successfully
- `/mcp/` is reachable for MCP clients

## Successful Deployment Record

This deployment flow was completed successfully for this repository.

### Git commands used

```bash
git status --short
git add converter_streamable_http_server.py utils/resource_utils.py render.yaml docs/activities/render_fastapi_mcp_deployment.md
git commit -m "Prepare FastAPI MCP server for Render deployment"
git push
```

Notes:

- this staged only the intended deployment files
- unrelated `.DS_Store` changes were intentionally excluded

### Render settings that worked

- Service type: `Web Service`
- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn converter_streamable_http_server:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

### Deployed endpoint checks

The following URLs were used as the post-deploy checks:

```text
https://<your-service>.onrender.com/
https://<your-service>.onrender.com/health
https://<your-service>.onrender.com/docs
https://<your-service>.onrender.com/mcp/
```

Outcome:

- deployment succeeded with the repository’s current FastAPI + FastMCP setup
- the documented Render configuration in this activity is now confirmed working for this repo

## Troubleshooting

If the deploy fails to start:

- confirm the start command uses `converter_streamable_http_server:app`
- confirm `requirements.txt` contains all required packages
- confirm the service binds with `--host 0.0.0.0 --port $PORT`

If `/docs` works but `/mcp/` does not:

- check Render logs for startup errors
- confirm the MCP app is mounted at `/mcp`
- test with a trailing slash: `/mcp/`

If logs are noisy on startup:

- confirm the latest deployment includes the resource logging cleanup described below
- check Render logs for application exceptions instead of import-time debug output

## Free Tier Notes

Render’s current free web service limitations include:

- services spin down after 15 minutes of inactivity
- cold starts can take about a minute
- free usage is limited to 750 instance hours per calendar month
- local filesystem changes are ephemeral

This is acceptable for demos, labs, and teaching activities, but not ideal for always-on production use.

## Deployment Changes Applied

The following deployment-prep changes were applied to this repository.

### 1. Added a root `/` route

File changed:

- `converter_streamable_http_server.py`

What changed:

- added a `GET /` endpoint that returns a small JSON response
- included links to `/docs`, `/health`, and `/mcp/`

Why:

- Render deployments are easier to sanity-check when the root URL responds successfully
- this provides a simple human-readable homepage for demos and quick smoke tests

### 2. Removed import-time debug output from resource registration

File changed:

- `utils/resource_utils.py`

What changed:

- removed the `print(...)` statement that dumped resource definitions during startup/import

Why:

- import-time debug output adds noise to Render logs
- reducing startup noise makes real deployment issues easier to identify

### 3. Added a `render.yaml` blueprint

File changed:

- `render.yaml`

What changed:

- added a Render blueprint with:
  - service type `web`
  - runtime `python`
  - build command `pip install -r requirements.txt`
  - start command `uvicorn converter_streamable_http_server:app --host 0.0.0.0 --port $PORT`
  - health check path `/health`

Why:

- the deployment settings now live in the repository
- this makes the Render configuration reusable and less error-prone

## Suggested Follow-Up Improvements

These are optional future improvements beyond the deployment-prep changes already applied:

- add more structured startup logging if operational visibility is needed
- add a deployment-specific smoke test that checks `/`, `/health`, and `/mcp/`
- document Render redeploy and rollback steps for classroom use

## Official References

- Render FastAPI deployment docs: `https://render.com/docs/deploy-fastapi`
- Render web services docs: `https://render.com/docs/web-services/`
- Render environment variables docs: `https://render.com/docs/configure-environment-variables`
- Render free tier docs: `https://render.com/docs/free`
