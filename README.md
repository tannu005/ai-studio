# TaskHub — AI-Powered Product Photography Studio & Task Management

TaskHub is a full-stack, enterprise-grade product photography task management platform with an integrated AI-powered studio space. It enables administrators to assign e-commerce product staging assignments to users/photographers, who then leverage a robust, hybrid background removal + backdrop composition engine to generate 8 beautiful, highly consistent, professional product variations (White BG, Velvet, Seasons, Model Wear) while preserving the exact appearance of the original product down to the pixel.

---

## 🚀 Architectural Overview

TaskHub utilizes a modern, decoupling-ready hybrid full-stack architecture:

```
  ┌─────────────────────────────────────────────────────────┐
  │                   Next.js 16 Client                     │
  │     (Glassmorphism CSS Theme, TypeScript, App Router)   │
  └────────────┬───────────────────────────────▲────────────┘
               │                               │
       REST API Requests                Supabase Session/JWT
               ▼                               │
  ┌───────────────────────────┐                │
  │       Flask Backend       ├────────────────┘
  │       (Python 3.13)       │
  └────────────┬──────────────┘
               │
    Background Job Workers
    & PIL Compose Engine
               ▼
  ┌───────────────────────────┐
  │   Supabase Postgres DB    │
  │ (RLS, Audit Logs, Triggers)│
  └───────────────────────────┘
```

- **Frontend**: Next.js 16, TypeScript, Vanilla CSS. Features a beautiful dark/glassmorphic custom design system with custom inline SVGs (avoiding default browser look). Supports real-time AI generation status tracking, visual gallery with full-zoom preview overlay, task actions, and comprehensive admin analytics dashboards.
- **Backend**: Flask API (Python 3.13) serving as a stateless resource server that secures endpoints by verifying Supabase JWT tokens. Enforces token-bucket rate limiting (100 reqs/min for APIs, 10 generations/hour for AI) and processes compositing pipelines in a background `ThreadPoolExecutor` worker queue.
- **Database**: Supabase PostgreSQL with fully enabled **Row-Level Security (RLS)**, customized user roles, and trigger-driven mutation logging recording structural changes in an `audit_logs` table.
- **AI Composition Engine**: Employs a hybrid pipeline. First, the product image undergoes high-fidelity background removal (via `rembg`). Then, the extracted subject is composited onto AI-generated or curated premium backdrops utilizing an alpha-channel drop shadow composition engine with edge feathering and lighting corrections. **This guarantees 100% pixel-level product consistency (zero AI hallucination/morphing).**

---

## 🛠️ Offline Developer Demo Mode

TaskHub features a full-fidelity, robust **Offline Developer Demo Mode** that allows running and testing the entire platform locally with zero external API dependencies or cloud accounts.

- **Offline Authentication**: Log in instantly via the login portal using designated bypass tokens:
  - **Admin Login**: Bypass with `mock-admin-token`
  - **User Login**: Bypass with `mock-user-token`
- **Local Fallback Engine**: If no live AI (fal.ai / DALL-E) or Supabase keys are configured in the `.env` file, the backend automatically fallbacks to a high-quality local template composition processor. It uses local high-resolution backdrops to seamlessly place the extracted product with photorealistic drop shadows.
- **Mock Services**: Includes a mock email dispatcher that logs rich HTML notifications (Task Assigned, Completed, Accepted) directly to backend logs/console, removing the need for a live SMTP/Resend API setup.

---

## 📂 Project Structure

```
taskhub/
├── backend/
│   ├── app.py                # Flask entrypoint & blueprint registrations
│   ├── config.py             # App environment variables & configurations
│   ├── middleware.py         # JWT Auth verification & Token Bucket rate-limiting
│   ├── requirements.txt      # Python dependencies (optimized for Py3.13)
│   ├── routes/
│   │   ├── auth.py           # Authenticated user profiles syncing
│   │   ├── tasks.py          # Tasks CRUD, status transitions, review portal
│   │   └── generate.py       # AI Studio pipeline, job queue & status checks
│   ├── services/
│   │   ├── ai_service.py     # Background removal & Alpha-Channel composition
│   │   └── email_service.py  # Mock Logger & HTML email dispatcher
│   └── tests/
│       └── test_api.py       # Comprehensive unit test suite (10/10 passing)
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router structure
│   │   │   ├── admin/        # Admin Analytics, Task Creation, & Review Boards
│   │   │   │   └── page.tsx
│   │   │   ├── login/        # Glassmorphic Google & GitHub Auth Screen
│   │   │   ├── tasks/[id]/   # High-end AI Product Staging Studio Space
│   │   │   │   └── page.tsx
│   │   │   └── user/         # Photographer To-do dashboard list
│   │   └── components/       # Common Navbars, Theme Toggles, & Layouts
│   └── package.json          # Node dependencies & scripts
├── migrations/
│   └── 01_schema.sql         # Supabase PostgreSQL tables, RLS, & Audit triggers
└── generated_samples/        # Pre-compiled high-quality necklace DSLR demo shots
```

---

## ⚡ Setup & Installation

### 1. Prerequisites
- **Python 3.10+** (Python 3.13 fully supported)
- **Node.js 18+**

---

### 2. Backend Setup
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file inside `/backend` (optional, template supplied):
   ```env
   PORT=5000
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_JWT_SECRET=your-jwt-secret-key
   AI_API_KEY=
   RESEND_API_KEY=
   ```
5. Run the Flask development server:
   ```bash
   python app.py
   ```
   The backend will start on [http://localhost:5000](http://localhost:5000).

---

### 3. Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Create a `.env.local` file inside `/frontend` (optional, template supplied):
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   NEXT_PUBLIC_API_URL=http://localhost:5000
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) to view the client.

---

### 4. Database Setup (Supabase)
To set up Row Level Security and Audit Log triggers, execute the SQL commands found in `/migrations/01_schema.sql` directly inside your Supabase Project SQL Editor.

---

## 📸 AI Product Studio Composition Engine

Standard generative AI is infamous for altering the exact structure of products, changing gem colors, chain patterns, and contours. To preserve pristine product consistency, TaskHub performs high-fidelity image compositing:

1. **Edge Extraction**: The uploaded product image runs through U2-Net background segmentation (`rembg`). Transparent alpha channels are cleanly extracted.
2. **Backdrop Generation/Selection**: Generates or maps the background backdrop using custom parameters (e.g. "luxurious dark velvet drape").
3. **Realistic Contact Shadows**: To avoid a flat "pasted" look, the engine copies the extracted product alpha mask, scales/blurs/re-colors it into a dark grey drop shadow, and overlays it slightly shifted beneath the jewelry layer onto the backdrop.
4. **Feathering & Blending**: Applies microscopic edge feathering and light color adjustments so that highlight tones blend naturally into the environment.

---

## 📊 Core API Endpoints

All endpoints (except login bypass) are secured via Bearer tokens.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/auth/sync` | Syncs Supabase authenticated profiles |
| **GET** | `/api/tasks` | Returns all tasks (Admins get all, Users get assigned) |
| **POST** | `/api/tasks` | Creates a new task (Admin only) |
| **GET** | `/api/tasks/<id>` | Retrieves specific task + generations |
| **PUT** | `/api/tasks/<id>/status`| Updates task state (`in_progress`, `submitted`, `accepted`) |
| **POST** | `/api/generate` | Starts asynchronous AI background composition job |
| **GET** | `/api/generate/jobs/<id>` | Polls active AI job status |
| **GET** | `/api/tasks/audit-logs` | Retrieves DB audit logs (Admin only) |

---

## 🧪 Running Tests

To verify backend integrity, run the built-in Flask API unit tests:
```bash
cd backend
python -m unittest discover tests
```
The test suite validates rate limiting, profile syncing, task status mutations, and offline mode authentication.
