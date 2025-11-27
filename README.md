# Comic Server

## 🌟 Core Features

### 1. High-Performance Library Management
* **Batch Scanner:** Processes massive libraries (25k+ files) in minutes using batched DB commits and SQLite WAL mode.
* **Smart Hierarchy:** Organizes files into Libraries -> Series -> Volumes -> Issues.
* **Metadata Extraction:** Automatically parses `ComicInfo.xml` from `.cbz` and `.cbr` archives.

### 2. Modern User Experience
* **Reactive UI:** Built with **FastAPI (Jinja2) + Alpine.js**, providing a SPA-like feel without the build complexity.
* **Component Architecture:** Reusable cards and list items ensure UI consistency across Search, Collections, and Detail views.
* **Web Reader:** A responsive reader with metadata inspection, page caching, and progress tracking.

### 3. Discovery & Curation
* **Advanced Search:** Rule-based search engine supporting complex logic (e.g., "Writer = Moore AND Character = Swamp Thing").
* **Auto-Suggestions:** "Find-as-you-type" autocomplete for all metadata fields.
* **Collections & Reading Lists:** Automatic and manual grouping of content.

### 4. Security & Multi-User
* **Role-Based Access:** Standard Users can browse/read; only Admins can Scan/Delete.
* **Secure Auth:** OAuth2 with JWT tokens and SHA-256/Bcrypt password hashing.
* **Personalized Progress:** Reading history is tracked per-user.

## 🏗 Architecture & Tech Stack
* **Backend:** Python 3.10+, FastAPI, SQLAlchemy, Pydantic v2.
* **Database:** SQLite (WAL Mode enabled).
* **Frontend:** TailwindCSS, Alpine.js v3, HTMX.
* **Deployment:** Docker & Docker Compose support.

## 📂 Key File Structure
* `app/api/`: REST endpoints (Secured with Dependency Injection).
* `app/services/`: Business logic (Scanner, Search Engine, Image Processing).
* `app/models/`: SQLAlchemy database definitions.
* `templates/`: Jinja2 HTML templates using partials for modularity.
* `storage/`: Persistent volume for Database and Thumbnails.

## ✅ Final Validation
1.  **Deployment:** `docker-compose up -d --build` successfully starts the container.
2.  **Security:** `/api/auth/register` creates the initial Superuser.
3.  **Ingestion:** Scanner successfully imports a sample library and generates thumbnails.
4.  **Usage:** Reading progress is saved and persists across reloads.