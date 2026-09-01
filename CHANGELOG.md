# Changelog

## Phase 9: Automated PDF Report Generation
**Commit Message:** `feat: implement dynamic PDF executive report generation`
* Integrated `reportlab` to construct dynamic, multi-page PDF documents.
* Built the `/api/v1/cases/{case_id}/report/pdf` endpoint which aggregates Case details, Risk Scores, Findings, and Timelines into a single executive summary.
* Updated React frontend to stream and download the PDF report seamlessly.

## Phase 8: Timeline Generation
**Commit Message:** `feat: implement chronological timeline reconstruction engine`
* Built a timeline engine to extract, normalize, and sort timestamps from Volatility outputs (`pslist`, `netscan`).
* Reconstructs the attacker's actions sequentially (e.g., `PROCESS_START`, `NETWORK_CONNECTION`, `PROCESS_EXIT`).
* Implemented a new `/api/v1/cases/{case_id}/timeline` endpoint and an interactive vertical timeline UI in React.

## Phase 7: Network Analysis
**Commit Message:** `feat: implement netscan C2 correlation engine`
* Engineered a cross-referencing module that maps active network sockets and listening ports against previously detected malicious PIDs.
* Automatically escalates risk (+40) to CRITICAL if a hidden or injected process maintains network communications, indicating Command and Control (C2) activity.

## Phase 6: Injection & DLL Analysis
**Commit Message:** `feat: implement detection rules for VAD injection and unlinked DLLs`
* Expanded the detection engine to analyze `malfind` and `ldrmodules` JSON outputs from Volatility.
* Added logic to automatically flag fileless malware (`PAGE_EXECUTE_READWRITE` injections) and reflective DLL injections (modules missing from `InLoad`/`InInit`/`InMem` PEB lists).
* Configured dynamic risk scoring (+25 for code injection, +20 for unlinked DLLs).

## Phase 4 & 5: Process Analysis & Hidden Process Detection
**Commit Message:** `feat: build Cross-View Analysis engine to detect hidden rootkit processes`
* Engineered a detection module that programmatically cross-references Volatility process lists (`pslist`, `psscan`, `psxview`).
* Implemented DKOM (Direct Kernel Object Manipulation) detection that flags processes present in memory pools but hidden from the OS process list, escalating the case risk score (+30).
* Created a new `/api/v1/cases/{case_id}/findings` endpoint and integrated a dynamic React UI to render structured `EvidenceMetadata` findings.
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
