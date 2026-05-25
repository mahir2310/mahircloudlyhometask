"""CLI runner for scenarios and simple end-to-end runs."""
import argparse
import json
import random
import os
from datetime import datetime
from .parser import get_section_texts
from .llm import generate_mcqs_for_section
from .kb import persist_session, snapshot_top_n, aggregate_wrong_counts, ensure_db


def run_prep_iteration(sections, n_per_section=5, simulate='random', seed=None):
    seed = seed or 0
    rnd = random.Random(seed)
    corpus = os.path.join(os.getcwd(), 'SLATEFALL_DOSSIER.txt')
    sections_text = get_section_texts(corpus)
    history = aggregate_wrong_counts()
    from .kb import get_mastered_questions
    mastered_map = get_mastered_questions()
    mastered = set(mastered_map.keys())
    questions = []
    for s in sections:
        text = sections_text.get(s, '')
        qs = generate_mcqs_for_section(s, text, n=n_per_section, history=history, mastered=mastered, seed=seed+s)
        questions.extend(qs)

    # simulate answers
    answers = {}
    for q in questions:
        if simulate == 'random':
            sel = rnd.randrange(len(q['choices']))
        elif simulate == 'mostly_wrong':
            sel = (q['answer'] + 1) % len(q['choices'])
        else:
            sel = q['answer']
        answers[q['id']] = sel

    # score
    corrects = sum(1 for q in questions if answers.get(q['id']) == q['answer'])
    score = corrects / max(1, len(questions))
    created_at = datetime.utcnow().isoformat()
    ensure_db()
    session_id = persist_session(sections, questions, answers, score, created_at)
    return {
        'session_id': session_id,
        'questions': questions,
        'answers': answers,
        'score': score,
        'created_at': created_at
    }


def generate_scenario_b(outroot='outputs', seed=42):
    os.makedirs(outroot, exist_ok=True)
    # Iter 1: sections 5,8
    iter1 = run_prep_iteration([5,8], seed=seed, simulate='random')
    p1 = os.path.join(outroot, 'scenario_b_iter1')
    os.makedirs(p1, exist_ok=True)
    with open(os.path.join(p1, 'questions_iter1.json'), 'w', encoding='utf-8') as f:
        json.dump(iter1['questions'], f, indent=2)
    with open(os.path.join(p1, 'kb_snapshot_iter1.json'), 'w', encoding='utf-8') as f:
        json.dump(snapshot_top_n(), f, indent=2)

    # Iter 2: sections 6,8,9
    iter2 = run_prep_iteration([6,8,9], seed=seed+1, simulate='random')
    p2 = os.path.join(outroot, 'scenario_b_iter2')
    os.makedirs(p2, exist_ok=True)
    with open(os.path.join(p2, 'questions_iter2.json'), 'w', encoding='utf-8') as f:
        json.dump(iter2['questions'], f, indent=2)
    with open(os.path.join(p2, 'kb_snapshot_iter2.json'), 'w', encoding='utf-8') as f:
        json.dump(snapshot_top_n(), f, indent=2)

    # Iter 3: section 8
    iter3 = run_prep_iteration([8], seed=seed+2, simulate='random')
    p3 = os.path.join(outroot, 'scenario_b_iter3')
    os.makedirs(p3, exist_ok=True)
    with open(os.path.join(p3, 'questions_iter3.json'), 'w', encoding='utf-8') as f:
        json.dump(iter3['questions'], f, indent=2)
    with open(os.path.join(p3, 'kb_snapshot_iter3.json'), 'w', encoding='utf-8') as f:
        json.dump(snapshot_top_n(), f, indent=2)

    return {'iter1': iter1, 'iter2': iter2, 'iter3': iter3}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate-scenario-b', action='store_true')
    parser.add_argument('--out', default='outputs')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.generate_scenario_b:
        res = generate_scenario_b(outroot=args.out, seed=args.seed)
        print('Scenario B generated in', args.out)


if __name__ == '__main__':
    main()
