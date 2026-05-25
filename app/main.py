from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .parser import get_section_texts
from .llm import generate_mcqs_for_section
from .kb import get_sessions_for_sections, persist_session, snapshot_top_n, aggregate_wrong_counts, get_question_results_for_session, ensure_db
import datetime

app = FastAPI(title='Adaptive Prep')


class PrepRequest(BaseModel):
    sections: List[int]
    n_per_section: int = 5


class SubmitRequest(BaseModel):
    sections: List[int]
    questions: List[Dict[str, Any]]
    answers: Dict[str, int]
    created_at: Optional[str] = None


@app.post('/prep')
def prep(req: PrepRequest):
    """Generate MCQs for requested sections.

    The response includes generated questions and prior session metadata
    so the client can determine whether this is a cold-start or returning run.
    """
    corpus = 'SLATEFALL_DOSSIER.txt'
    sections_text = get_section_texts(corpus)
    prior = get_sessions_for_sections(req.sections)
    wrongs = aggregate_wrong_counts()
    from .kb import get_mastered_questions
    mastered_map = get_mastered_questions()
    mastered = set(mastered_map.keys())
    questions = []
    for s in req.sections:
        text = sections_text.get(s, '')
        qs = generate_mcqs_for_section(s, text, n=req.n_per_section, history=wrongs, mastered=mastered)
        questions.extend(qs)
    return {'questions': questions, 'prior_sessions': prior}


@app.post('/submit')
def submit(req: SubmitRequest):
    """Accept answered session data and persist to KB. Returns session id and score."""
    created_at = req.created_at or datetime.datetime.utcnow().isoformat()
    # compute score
    total = len(req.questions)
    corrects = 0
    # questions have 'id' and 'answer'
    for q in req.questions:
        qid = q.get('id')
        correct = q.get('answer')
        sel = req.answers.get(qid)
        if sel is not None and sel == correct:
            corrects += 1
    score = corrects / max(1, total)
    ensure_db()
    session_id = persist_session(req.sections, req.questions, req.answers, score, created_at)
    snapshot = snapshot_top_n()
    return {'session_id': session_id, 'score': score, 'kb_snapshot': snapshot}


@app.get('/sessions')
def sessions_for_sections(sections: str):
    """Query prior sessions involving the given comma-separated section IDs."""
    ids = []
    try:
        ids = [int(s) for s in sections.split(',') if s.strip()]
    except Exception:
        return {'error': 'invalid section ids'}
    res = get_sessions_for_sections(ids)
    return {'sessions': res}


@app.get('/session/{session_id}/questions')
def session_question_results(session_id: int):
    res = get_question_results_for_session(session_id)
    return {'results': res}
