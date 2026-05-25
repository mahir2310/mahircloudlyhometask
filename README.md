 # Adaptive Document Preparation System

 Overview
 - Small local backend implementing the prep flow from the assessment brief.

 Quick start
 1. Create a virtualenv and install dependencies:

 ```powershell
 python -m venv .venv
 .\.venv\Scripts\Activate.ps1
 pip install -r requirements.txt
 ```

 2. Run the CLI to execute Scenario B (generates outputs/):

 ```powershell
 python -m app.cli --generate-scenario-b
 ```

Docker (optional)

Build and run with Docker Compose:

```powershell
docker compose build --pull
docker compose up --detach
# API will be available at http://localhost:8000
```

Tests and CI

Run unit tests locally with:

```powershell
pip install -r requirements.txt
pytest -q
```

If `transformers` is installed and a supported model is available, the server
will attempt to use `google/flan-t5-small` for improved MCQ generation. The
code gracefully falls back to the local stub when HF is not available.

 Project layout
 - `app/` - source code
 - `outputs/` - generated scenario outputs

 Notes
 - The repository uses a local SQLite KB at `data/kb.sqlite` and a simple LLM stub
   that derives MCQs from the provided `SLATEFALL_DOSSIER.txt` (converted PDF).
 - The system is deterministic when `--seed` is provided to the CLI.

Schema & Access Patterns
- KB: SQLite at `data/kb.sqlite` with tables:
  - `sessions` (id, sections JSON, created_at, score)
  - `questions` (id, session_id, section, question, choices JSON, correct_index, explanation)
  - `answers` (id, question_id, session_id, selected_index, correct)
- Access helpers (in `app/kb.py`):
  - `get_sessions_for_sections([ids])` — retrieve prior sessions involving any of the given sections
  - `get_question_results_for_session(session_id)` — get question-level results for a session
  - `aggregate_wrong_counts()` — returns mapping question->wrong_count for adaptive weighting
  - `snapshot_top_n(n=5)` — human-readable snapshot of last-n sessions

API Endpoints
- `POST /prep` — body: `{"sections": [3,7], "n_per_section": 5}` → returns generated `questions` and `prior_sessions` metadata.
- `POST /submit` — body: `{"sections": [...], "questions": [...], "answers": {question_id: selected_index}}` → persists the session, returns `session_id`, `score`, and `kb_snapshot`.
- `GET /sessions?sections=5,8` — returns prior sessions involving those sections.
- `GET /session/{session_id}/questions` — returns question-level results for a session.

Scenario A (cold-start)
- Run a cold-start prep over any two sections (example: 1 and 2):

```powershell
python -m app.cli --seed 1
# or call the API:
# curl -X POST http://localhost:8000/prep -H "Content-Type: application/json" -d "{\"sections\": [1,2], \"n_per_section\": 5}"
```

Stack choices & reasoning
- Backend: `FastAPI` — lightweight, production-capable, and fast to scaffold REST endpoints for evaluation.
- Storage: `SQLite` — simple local persistence, easy to inspect, and sufficient for the assessment.
- PDF parsing: `PyPDF2` — reliable extraction for machine-readable PDFs; caches to `.txt` for convenience.
- LLM: optional `transformers` (`google/flan-t5-small`) — free and local; the code falls back to a deterministic stub when unavailable to ensure reproducible evaluation without paid APIs.

Known limitations & assumptions
- The HF model download may be large; the stub provides stable outputs for grading.
- Section splitting is heuristic on `Section {n}` headings; if the PDF uses other markers, mapping may be necessary.
- The MCQ generator produces structurally correct items (4 choices, one correct, explanation) but question quality depends on the available model.

Adaptive behavior details
- The system detects "mastered" questions in the KB (questions answered correctly at least twice with zero wrongs) and avoids repeating them when generating new question sets. This reduces excessive repetition while still focusing on historically weak topics via weighted selection.

