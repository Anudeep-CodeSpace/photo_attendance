# Photo Attendance System

FastAPI + InsightFace + Qdrant + SQLite

A lightweight backend system that performs:

* Batch student registration (up to 100 photos)
* Group photo attendance extraction
* Face recognition using InsightFace
* Vector search using Qdrant
* Student metadata storage using SQLite
* Secure API-Key authentication
* Progress tracking for long operations
* Optimized async architecture

---

## Features

### 1. Batch Student Registration

* Upload 1–100 photos
* Filenames are treated as roll numbers (and should be roll numbers)
  (example: `21A91A0510.jpg`)
* Performs face detection → embedding → DB insert → Qdrant upsert
* Detects duplicates and invalid faces
* Tracks progress in real time

### 2. Group Photo Attendance

* Upload a single group image
* Detects all faces
* Filters weak detections
* Generates embeddings for each face
* Finds matching student roll numbers from Qdrant
* Returns list of recognized + unrecognized faces

### 3. Secure API Key Access

Only users who send the correct `X-API-Key` header can access any endpoint.

### 4. Clean Logging

* Initialization logs
* Detection / embedding issues
* Database events
* Qdrant search results
* Registration progress

### 5. Async + Thread Offloading

* Model calls run in background threads
* Face detection and embedding work in parallel
* Heavy work stays non-blocking

---

## Project Structure

```
app/
│
├── main.py
├── config.py
├── startup.py
├── dependencies.py
├── logs_config.py
├── locks.py
│
├── constants/
│   └── thresholds.py
│
├── db/
│   ├── init_db.py
│   └── schema.sql
│
├── logs/
│
├── models/
│   └── student.py
│
├── routers/
│   ├── register.py
│   └── attendance.py
│
├── services/
│   ├── embedding_service.py
│   ├── face_processing.py
│   ├── qdrant_service.py
│   └── sqlite_service.py
│
├── state/
│   └── progress.py
│
├── README.md
└── pyproject.toml 

```

---

## Installation

### 1. Clone the repository

```
git clone https://github.com/Anudeep-CodeSpace/photo_attendance_backend.git
cd photo_attendance_backend
```

### 2. Install dependencies (using UV)

```
uv sync
```

### 3. Create `.env`

```
ADMIN_API_KEY=your-secret-key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```

### 4. Initialize SQLite database

```
python app/db/init_db.py
```

### 5. Run the server

```
uvicorn app.main:app --reload
```

---

## API Summary

### `POST /register_students`

Registers student images (up to 100 photos).

Send as:

```
form-data:
files: <multiple image files>
```

### `POST /upload_photo`

Takes one group image and returns recognized roll numbers.

Send as:

```
form-data:
file: <image>
```

### `GET /register_status`

Returns registration progress.

---

## Authentication

All requests must include:

```
X-API-Key: <your-secret-key>
```

Example (Fetch API):

```js
fetch("/register_students", {
  method: "POST",
  headers: { "X-API-Key": "your-secret-key" },
  body: formData
});
```

---

## Future Improvements (Optional)

* JWT-based user login
* Role-based admin/student panels
* WebSocket progress updates
* GPU acceleration
* Export attendance to CSV/Excel

---

## Author

**Bandi Anudeep Reddy**
Tech enthusiast • Backend + AI developer • Loves bikes and anime

---
