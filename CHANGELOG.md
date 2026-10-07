# Changelog

All notable changes to the SpaceLoop platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-07

### Added
- Enterprise domain monorepo architecture aligning `.github/`, `frontend/`, `backend/`, `infrastructure/`, `security/`, `observability/`, and `operations/`.
- Dual fraud/risk architecture:
  - System A: Behavioral Trust & Safety Engine with bipartite graph relationship modeling, circular booking detection, and multi-LLM forensic narrative synthesis (Groq -> Gemini -> deterministic fallback).
  - System B: Autonomous ML Fraud Engine with Isolation Forest anomaly detection, sliding window velocity tracking, and risk tier decision thresholds.
- Comprehensive end-to-end QA and adversarial test suite (137 tests passing).
- Micro-escrow settlement with automated ₹100 security deposits, 5% platform fees, and duplicate payout guards.
- Geofenced and time-guarded physical access validation (50m radius, 15-minute temporal window, rotating QR/PIN fallback).
- Full seeker, host, and admin frontend applications built on Vite, React, Tailwind CSS, and Framer Motion.
- Persistent AI LoopBot assistant with multi-lingual search (Hindi, Marathi, Hinglish) and streaming responses.
- External adapters for Discom utility verification, UPI name-matching, Aadhaar SHA-256 tokenization, and multi-provider transactional email.
