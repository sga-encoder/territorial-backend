# Territorial Assessment Backend

Flask REST API with layered architecture:

- Presentation layer: `app/controllers`
- Business layer: `app/services`
- Data access layer: `app/repositories`
- Database: SQLite with SQLAlchemy
- Uploads: images are stored in `app/uploads`, and the database stores the relative path.

## Requirements

- Python 3.10+

## Setup on Windows, Linux or macOS

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Initialize database with seed data:

```bash
python scripts/seed.py
```

Or fill every table with rich demo data for exhibitions (drops and recreates the database; generated images go to Cloudinary when `CLOUDINARY_URL` is set, otherwise to `UPLOAD_FOLDER`):

```bash
python scripts/seed_demo.py
```

Then create a Firebase e-mail/password login (password `Admin123*`) for every seeded official and citizen. The key is the frontend's `environment.firebase.apiKey`:

```bash
FIREBASE_API_KEY=<web api key> python scripts/seed_firebase_users.py
```

Demo accounts: `admin@example.com` (admin), `funcionario@example.com` (official), `ciudadano@example.com` (citizen).

Run the API:

```bash
python run.py
```

The API will be available at:

```text
http://127.0.0.1:5000
```

## Image endpoint

Images can be read from the frontend with:

```text
GET /api/images/<relative_path>
```

Example:

```text
GET /api/images/logos/alcaldia.png
```

When `CLOUDINARY_URL` (`cloudinary://<api_key>:<api_secret>@<cloud_name>`) is set, uploads for logos, categories and evidences go to Cloudinary under `territorial/<folder>` and the stored URL is the absolute `https://res.cloudinary.com/...` link. This is required on Render, whose disk is ephemeral. Without it, files are saved to `UPLOAD_FOLDER` and served by the endpoint above.

## Pagination behavior

List endpoints return all records when `page` and `pageSize` are not sent.

When sent, response shape is:

```json
{
  "page": 1,
  "pageSize": 10,
  "totalItems": 25,
  "totalPages": 3,
  "items": []
}
```

## File upload endpoints

These endpoints accept `multipart/form-data` with a `file` field:

- `POST /api/entities`
- `PUT /api/entities/{id}`
- `POST /api/categories`
- `PUT /api/categories/{id}`
- `POST /api/evidences`
- `PUT /api/evidences/{id}`

All other endpoints accept JSON.

## Postman

Import:

```text
postman/Territorial_Assessment_API.postman_collection.json
```
