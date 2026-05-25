import sqlite3
from typing import List, Dict, Any, Optional
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'kb.sqlite')

def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sections TEXT,
        created_at TEXT,
        score REAL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        session_id INTEGER,
        section INTEGER,
        question TEXT,
        choices TEXT,
        correct_index INTEGER,
        explanation TEXT
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT,
        session_id INTEGER,
        selected_index INTEGER,
        correct INTEGER
    )
    ''')
    conn.commit()
    conn.close()

def persist_session(sections: List[int], questions: List[Dict], answers: Dict[str,int], score: float, created_at: str):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO sessions (sections, created_at, score) VALUES (?,?,?)', (json.dumps(sections), created_at, score))
    session_id = cur.lastrowid
    for q in questions:
        cur.execute('INSERT OR REPLACE INTO questions (id, session_id, section, question, choices, correct_index, explanation) VALUES (?,?,?,?,?,?,?)',
                    (q['id'], session_id, q['section'], q['question'], json.dumps(q['choices']), q['answer'], q['explanation']))
        sel = answers.get(q['id'], None)
        correct = 1 if sel==q['answer'] else 0
        cur.execute('INSERT INTO answers (question_id, session_id, selected_index, correct) VALUES (?,?,?,?)', (q['id'], session_id, sel, correct))
    conn.commit()
    conn.close()
    return session_id

def get_sessions_for_sections(sections: List[int]) -> List[Dict[str,Any]]:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    like = '%'  # simple approach: return recent sessions where any section matches stored sections
    cur.execute('SELECT id, sections, created_at, score FROM sessions ORDER BY id DESC LIMIT 50')
    rows = cur.fetchall()
    out = []
    for r in rows:
        s = json.loads(r[1])
        if any(sec in s for sec in sections):
            out.append({'id': r[0], 'sections': s, 'created_at': r[2], 'score': r[3]})
    conn.close()
    return out

def get_question_results_for_session(session_id: int) -> List[Dict[str,Any]]:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''SELECT q.id, q.section, q.question, q.choices, q.correct_index, a.selected_index, a.correct
                   FROM questions q JOIN answers a ON q.id=a.question_id WHERE q.session_id=?''', (session_id,))
    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append({'id': r[0], 'section': r[1], 'question': r[2], 'choices': json.loads(r[3]), 'correct_index': r[4], 'selected': r[5], 'correct': r[6]})
    conn.close()
    return out

def aggregate_wrong_counts() -> Dict[str,int]:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''SELECT q.question, SUM(CASE WHEN a.correct=0 THEN 1 ELSE 0 END) as wrongs
                   FROM questions q JOIN answers a ON q.id=a.question_id GROUP BY q.question''')
    rows = cur.fetchall()
    out = {r[0]: r[1] for r in rows}
    conn.close()
    return out

def snapshot_top_n(n=5):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, sections, created_at, score FROM sessions ORDER BY id DESC LIMIT ?', (n,))
    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append({'id': r[0], 'sections': json.loads(r[1]), 'created_at': r[2], 'score': r[3]})
    conn.close()
    return out

def get_mastered_questions(min_corrects: int = 2) -> Dict[str,int]:
    """Return questions considered mastered: mapping question -> correct_count.

    A question is considered mastered when it has been answered correctly at
    least `min_corrects` times and has zero wrongs.
    """
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''SELECT q.question,
                          SUM(CASE WHEN a.correct=1 THEN 1 ELSE 0 END) as corrects,
                          SUM(CASE WHEN a.correct=0 THEN 1 ELSE 0 END) as wrongs
                   FROM questions q JOIN answers a ON q.id=a.question_id
                   GROUP BY q.question''')
    rows = cur.fetchall()
    out = {}
    for r in rows:
        question = r[0]
        corrects = int(r[1] or 0)
        wrongs = int(r[2] or 0)
        if corrects >= min_corrects and wrongs == 0:
            out[question] = corrects
    conn.close()
    return out
