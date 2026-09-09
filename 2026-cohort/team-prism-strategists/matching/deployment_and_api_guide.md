# 📘 Mentoring-Me — Complete Pre- & Post-Deployment & API Integration Guide

This guide provides end-to-end instructions for configuring all third-party APIs (Google OAuth, Facebook Login, SMTP Email, AI LLMs, GitHub, ORCID) and deploying the **Mentoring-Me** platform to production hosting (e.g., Render, Railway, Google Cloud Run, AWS).

---

## 🏛️ Platform Architecture Overview

The Mentoring-Me application consists of two decoupled components:
1. **Backend (FastAPI REST API)**:
   - Handles JWT authentication, bcrypt password hashing, 2FA OTP generation, password reset tokens, SQL database management, weighted matching algorithms, in-app messaging, and external directory integrations.
   - Default local port: `http://127.0.0.1:8000`
   - Interactive API Documentation: `http://127.0.0.1:8000/docs`
2. **Frontend (Streamlit Web Interface)**:
   - Provides consumer-grade UI, role-aware onboarding, interactive match exploration, chat messaging, calendar booking tools, and admin controls.
   - Default local port: `http://localhost:8501`

---

## 🔑 Part 1: Third-Party API Configuration (Pre-Deployment)

### 1.1 Google OAuth 2.0 (Single Sign-On & Social Login)
Google OAuth allows users to sign up and sign in with their Google accounts with zero manual form typing.

#### Steps to configure Google OAuth:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `mentoring-me-production`).
3. Navigate to **APIs & Services** → **OAuth consent screen**:
   - Select **External** user type and click **Create**.
   - Fill in **App Name** (`Mentoring-Me`), **User support email**, and **Developer contact email**.
   - Add scopes: `openid`, `.../auth/userinfo.email`, `.../auth/userinfo.profile`.
   - In Test Users, add your personal email to test before publishing.
4. Navigate to **APIs & Services** → **Credentials**:
   - Click **+ CREATE CREDENTIALS** → **OAuth client ID**.
   - Select **Application type**: `Web application`.
   - Name: `Mentoring-Me Web Client`.
   - **Authorized JavaScript origins**:
     - Local development: `http://localhost:8501`
     - Production: `https://your-frontend-app.onrender.com` (or your custom domain)
   - **Authorized redirect URIs**:
     - Local development: `http://localhost:8501`
     - Production: `https://your-frontend-app.onrender.com`
5. Copy your **Client ID** and **Client Secret** into your `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

---

### 1.2 Facebook (Meta) Login
Facebook Login allows users to sign up and sign in using their Facebook profile.

#### Steps to configure Facebook Login:
1. Go to [Meta for Developers](https://developers.facebook.com/).
2. Click **My Apps** → **Create App**.
3. Select **Authenticate and request data from users with Facebook Login** (or **Consumer** app type).
4. Enter an App Name (e.g., `Mentoring-Me`) and Contact Email.
5. In the App Dashboard, under **Add products to your app**, locate **Facebook Login** and click **Set Up**.
6. Select **Web** as the platform.
7. Go to **Facebook Login** → **Settings** (in left sidebar):
   - Under **Valid OAuth Redirect URIs**, enter:
     - Local: `http://localhost:8501`
     - Production: `https://your-frontend-app.onrender.com`
8. Go to **App Settings** → **Basic**:
   - Copy **App ID** and **App Secret**.
   - In production, set **App Mode** from *Development* to *Live*.
9. Add to `.env`:
   ```env
   FACEBOOK_APP_ID=your_facebook_app_id
   FACEBOOK_APP_SECRET=your_facebook_app_secret
   ```

---

### 1.3 SMTP Email Configuration (2FA & Password Reset OTPs)
Enables automated dispatch of 6-digit security codes for Double Authentication (2FA) and Password Reset requests.

#### Option A: Gmail SMTP (Free & Easy)
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is turned ON.
3. Search for **App Passwords** or visit: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
4. Create an App Password with name `Mentoring-Me SMTP`.
5. Google will generate a 16-character password (e.g., `abcd efgh ijkl mnop`).
6. Add to `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_character_app_password
   SMTP_FROM_EMAIL=your_email@gmail.com
   ```

#### Option B: SendGrid / Mailgun / AWS SES (Enterprise)
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

---

### 1.4 AI Career Advisor (Google Gemini / OpenAI)
Powers the interactive AI career roadmap advisor and CV analysis.

1. **Google Gemini (Free tier available)**:
   - Get API key at: [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Add to `.env`: `GEMINI_API_KEY=AIzaSy...`
2. **OpenAI (Optional alternative)**:
   - Get API key at: [OpenAI Platform](https://platform.openai.com/api-keys).
   - Add to `.env`: `OPENAI_API_KEY=sk-...`

---

### 1.5 External Directory APIs (GitHub & ORCID)
Enables live searching of open-source developers and academic researchers.

1. **GitHub Personal Access Token**:
   - Go to [GitHub Developer Settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens).
   - Generate token with `read:user` and `user:email` scopes.
   - Add to `.env`: `GITHUB_TOKEN=ghp_...`
2. **ORCID Public API**:
   - Register at [ORCID Developer Tools](https://orcid.org/developer-tools).
   - Add to `.env`:
     ```env
     ORCID_CLIENT_ID=APP-XXXXXXXXXXXXXXXX
     ORCID_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
     ```

---

## 🚀 Part 2: Production Deployment Walkthrough

### Option A: Deploying on Render.com (Recommended)

Render provides a unified cloud hosting platform with free/low-cost tiers for both FastAPI backend services and Streamlit frontend web apps.

#### Step 1: Push Code to GitHub
Ensure your latest codebase is pushed to your GitHub repository:
```bash
git add .
git commit -m "Mentoring-Me platform release with full messaging, 2FA, and deployment guides"
git push origin main
```

#### Step 2: Create FastAPI Backend Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository.
4. Configure Backend Settings:
   - **Name**: `mentoring-me-backend`
   - **Region**: `Frankfurt` (EU) or `Oregon` (US)
   - **Branch**: `main`
   - **Root Directory**: `matching`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `SECRET_KEY` = (A secure 64-character random string)
   - `APP_BASE_URL` = `https://mentoring-me-frontend.onrender.com` (Your live frontend public URL)
   - `GOOGLE_CLIENT_ID` = `...`
   - `GOOGLE_CLIENT_SECRET` = `...`
   - `FACEBOOK_APP_ID` = `...`
   - `FACEBOOK_APP_SECRET` = `...`
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `...`
   - `SMTP_PASSWORD` = `...`
   - `GEMINI_API_KEY` = `...`
   - `GITHUB_TOKEN` = `...`
6. Click **Create Web Service**. Note your backend URL (e.g. `https://mentoring-me-backend.onrender.com`).

#### Step 3: Create Streamlit Frontend Web Service
1. Click **New +** → **Web Service**.
2. Connect the same repository.
3. Configure Frontend Settings:
   - **Name**: `mentoring-me-frontend`
   - **Root Directory**: `matching`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. Under **Environment Variables**, add:
   - `APP_BASE_URL` = `https://mentoring-me-frontend.onrender.com` (Your live frontend public URL)
   - `API_URL` = `https://mentoring-me-backend.onrender.com/api/v1`
   - `GOOGLE_CLIENT_ID` = `...`
   - `FACEBOOK_APP_ID` = `...`
5. Click **Create Web Service**. Note your frontend URL (e.g. `https://mentoring-me-frontend.onrender.com`).

---

### Option B: Deploying with Docker / Docker Compose

If deploying on a VPS (AWS EC2, DigitalOcean, Linode) or Cloud Run, you can containerize both services:

#### `Dockerfile.backend`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `Dockerfile.frontend`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

---

## 🔒 Part 3: Post-Deployment Steps & Verification

Once your platform is live at your public domain or hosting URL (e.g., `https://mentoring-me-frontend.onrender.com`):

### Step 1: Update OAuth Redirect URIs
1. **Google Cloud Console**:
   - Edit your Web Client credentials.
   - Add to **Authorized JavaScript origins**: `https://mentoring-me-frontend.onrender.com`
   - Add to **Authorized redirect URIs**: `https://mentoring-me-frontend.onrender.com`
2. **Meta for Developers**:
   - Edit Facebook Login Settings.
   - Add to **Valid OAuth Redirect URIs**: `https://mentoring-me-frontend.onrender.com`

### Step 2: Production Database Initialization
1. Visit your backend interactive documentation: `https://mentoring-me-backend.onrender.com/docs`.
2. The initial database tables and admin user (`admin@mentoring-me.demo` / `adminpassword`) will be auto-generated.
3. Log in as Admin on the frontend and navigate to **Administration** to verify live operations.

### Step 3: End-to-End Smoke Test Checklist
- [ ] **Sign-Up Flow**: Register a new Mentee account and a new Mentor account.
- [ ] **2FA Verification**: Verify 6-digit OTP delivery upon login.
- [ ] **Forgot Password**: Request a password reset code and update credentials.
- [ ] **Matching Algorithm**: Run "Search Active Mentor Pool" and verify score breakdown bar chart.
- [ ] **In-App Messaging**: Send and receive messages between connected pairs.
- [ ] **Calendar Scheduling**: Click "Add to Google Calendar" and download the `.ics` calendar file.
- [ ] **Colleague Nomination**: Generate an external colleague invitation code and outreach email.

---

## ❓ Frequently Asked Questions (FAQ)

**Q1: How does the system handle missing third-party API keys?**  
The platform is built with graceful fallbacks. If live OAuth credentials or external directory keys are not provided in `.env`, the system automatically activates simulated flows and curated directories without crashing or blocking users.

**Q2: How can I change the default admin password?**  
Log in with the default credentials (`admin@mentoring-me.demo` / `adminpassword`), then use the **🔑 Forgot Password?** drawer to set a custom secure password.

**Q3: Can I connect a PostgreSQL database instead of SQLite?**  
Yes! Provide `DATABASE_URL=postgresql://user:password@host:5432/dbname` in your backend `.env` variables. SQLAlchemy will automatically connect and create tables in PostgreSQL.
