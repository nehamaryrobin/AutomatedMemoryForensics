# Changelog

## Phase 3: Volatility 3 Integration
**Commit Message:** `feat: integrate Volatility 3 forensic engine wrapper`
* Implemented a secure Python wrapper for Volatility 3 using isolated subprocesses to prevent crashes on corrupted memory dumps.
* Configured the Celery worker to automatically execute 12 standard Windows forensic plugins and securely log the JSON results to PostgreSQL.

## Phase 2: Job Queue + Worker
**Commit Message:** `feat: implement Celery job queue and Redis worker`
* Transitioned the architecture to an asynchronous model using Redis and Celery to handle long-running memory analysis tasks.
* Updated the frontend React dashboard to dynamically poll the FastAPI backend and display real-time job status updates (QUEUED, RUNNING, COMPLETED).

## Phase 1: Frontend + FastAPI + Upload System
**Commit Message:** `feat: initialize React frontend and FastAPI backend for memory dump upload`
* Scaffolded the project structure including a React/Vite dashboard, a FastAPI backend with PostgreSQL, and standard `.gitignore` rules.
* Implemented a secure file upload pipeline that streams large memory dumps to disk in chunks, calculates SHA-256 hashes on-the-fly, and safely extracts ZIP archives.
