# CityVision — Render Deployment Guide

This guide details how to deploy the CityVision Road Anomaly Sensing Platform to [Render](https://render.com).

The project is structured with:
- **Backend**: FastAPI with SQLite / PostgreSQL support (`/backend`)
- **Frontend**: React + Vite SPA with MapLibre & Leaflet (`/frontend`)

---

## Method 1: Automatic Blueprint Deployment (Recommended)

Render Blueprints let you deploy both the backend web service and the frontend static site together with automated configuration.

1. Push this repository to GitHub.
2. Sign in to your **[Render Dashboard](https://dashboard.render.com/)**.
3. Click **New +** → **Blueprint**.
4. Connect your GitHub repository (`CityVision`).
5. Render will detect `render.yaml` and configure:
   - **`cityvision-backend`** (Python Web Service)
   - **`cityvision-frontend`** (Static Site with SPA rewrite rules)
6. Click **Apply**.
7. Render will automatically build and deploy both services!

---

## Method 2: Manual Deployment

If you prefer to deploy services individually:

### 1. Deploy the Backend Web Service

1. On the Render Dashboard, click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `cityvision-backend`
   - **Region**: Closest to you (e.g., Oregon or Frankfurt)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.9`
   - `CORS_ORIGINS`: `*`
   - `DATABASE_URL`: `sqlite:///./sih26124.db` (or attach a Render Postgres instance)
5. Click **Deploy Web Service**.
6. Note the deployed backend URL (e.g. `https://cityvision-backend.onrender.com`).

---

### 2. Deploy the Frontend Static Site

1. On the Render Dashboard, click **New +** → **Static Site**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `cityvision-frontend`
   - **Branch**: `main`
   - **Root Directory**: *(leave blank)*
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
4. Under **Redirects / Rewrites**, add:
   - **Type**: `Rewrite`
   - **Source**: `/*`
   - **Destination**: `/index.html`
5. Add **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://cityvision-backend.onrender.com` *(use your actual backend URL)*
6. Click **Create Static Site**.

---

## Database Options

- **Default (SQLite)**:
  By default, `DATABASE_URL` is set to `sqlite:///./sih26124.db`. SQLite starts pre-seeded or initializes tables automatically on startup. Note that on Render's free tier, local filesystem storage is ephemeral upon service restarts.
- **Render PostgreSQL (Persistent)**:
  1. In Render, click **New +** → **PostgreSQL**.
  2. Copy the **Internal Database URL** (or External URL).
  3. Set `DATABASE_URL` on `cityvision-backend` to the database URL.
  4. The backend automatically normalizes `postgres://` to `postgresql://` for SQLAlchemy 2.0.

---

## Health Check & Verification

Once deployed:
1. Verify backend health:
   ```
   GET https://<your-backend-url>/api/health
   Response: {"status": "ok", "service": "SIH26124 Road Anomaly Platform"}
   ```
2. Interactive API documentation:
   ```
   https://<your-backend-url>/docs
   ```
3. Open your frontend URL:
   ```
   https://<your-frontend-url>
   ```
   You should see the CityVision CommandCenter with live incident triage, density heatmaps, and field dispatch operations.
