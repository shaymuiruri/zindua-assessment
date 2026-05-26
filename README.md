# Zindua Assessment Submission

This repository contains the full Zindua Stage 2 assessment submission:

- a deployed Django + DRF demo app with JWT authentication and role-based access control
- a complete teaching package for the 60-minute lesson

---

## Live Demo

**Backend URL:** https://zindua-assessment-production.up.railway.app

---

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Instructor | instructor@demo.dev | Demo@1234 |
| Student | student@demo.dev | Demo@1234 |
| Observer | observer@demo.dev | Demo@1234 |

---

## How to Navigate This Submission

Start here and then drill into the two parts:

1. `demo-app/`
   - Django project, deployed backend, seed command, and app-specific README
   - includes the API behavior, security notes, and the teaching comment pointer
2. `teaching-package/`
   - `01-session-outline.md`
   - `02-learning-objectives.md`
   - `03-concept-explainers.md`
   - `04-anticipated-misconceptions.md`

If you are reviewing the backend live, use Postman with:

- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/refresh/`
- `GET /api/v1/assignments/`
- `POST /api/v1/assignments/`
- `POST /api/v1/submissions/`
- `GET /api/v1/submissions/{id}/feedback/`

---

## What Is in the Demo App

The Django app in `demo-app/` shows:

- JWT-based login and token refresh
- instructor, student, and observer roles
- strict role-based permissions
- observer row-level access through `ObserverLink`
- seeded demo data for live testing

---

## What Is in the Teaching Package

The teaching package is written to support the demo app as a 60-minute lesson.

- [01-session-outline.md](teaching-package/01-session-outline.md)
- [02-learning-objectives.md](teaching-package/02-learning-objectives.md)
- [03-concept-explainers.md](teaching-package/03-concept-explainers.md)
- [04-anticipated-misconceptions.md](teaching-package/04-anticipated-misconceptions.md)

---

## Submission Notes

- The app README with setup and security notes lives in `demo-app/README.md`.
- The teaching comment referenced in the submission is in `demo-app/classroom/permissions.py`.
- No `.env` file is committed; only `demo-app/.env.example` is included.