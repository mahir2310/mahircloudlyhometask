import random
from typing import List, Dict, Any, Optional

try:
    from transformers import pipeline
    _HF_AVAILABLE = True
except Exception:
    _HF_AVAILABLE = False


def _stub_generate(section_id: int, section_text: str, n: int = 5, history: Optional[Dict] = None, mastered: Optional[set] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    rnd = random.Random(seed or 0)
    sents = [s.strip() for s in section_text.split('.') if s.strip()]
    if not sents:
        return []
    weights = [1.0 for _ in sents]
    if history:
        for i, s in enumerate(sents):
            wrong = history.get(s, 0)
            weights[i] += wrong * 2.0

    items = []
    for i in range(n*3):
        if sum(weights) <= 0:
            idx = rnd.randrange(len(sents))
        else:
            total = sum(weights)
            pick = rnd.random() * total
            acc = 0
            idx = 0
            for j, w in enumerate(weights):
                acc += w
                if pick <= acc:
                    idx = j
                    break
        correct = sents[idx]
        # If this sentence exactly matches a mastered question, avoid repeating it
        if mastered and correct in mastered:
            # reduce its weight heavily and continue searching
            weights[idx] *= 0.05
            continue
        distractors = []
        pool = [s for j, s in enumerate(sents) if j != idx]
        rnd.shuffle(pool)
        for d in pool[:3]:
            distractors.append(d if len(d) > 10 else (d + ' (detail)'))

        choices = [correct] + distractors
        rnd.shuffle(choices)
        ans = choices.index(correct)

        q = {
            'id': f's{section_id}-{i}',
            'section': section_id,
            'question': f'Which statement best matches the section content? "{correct[:120]}"',
            'choices': choices,
            'answer': ans,
            'explanation': correct
        }
        items.append(q)
        if len(items) >= n:
            break
    return items


def generate_mcqs_for_section(section_id: int, section_text: str, n: int = 5, history: Optional[Dict] = None, mastered: Optional[set] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Generate MCQs using HF model if available, otherwise use stub.

    The HF generation is optional and best-effort: if `transformers` and a model
    are available, a simple prompt will be used. Otherwise the local stub runs.
    """
    if _HF_AVAILABLE:
        try:
            gen = pipeline('text2text-generation', model='google/flan-t5-small')
            prompt = f"Create {n} multiple choice questions (4 choices each) from the following text. Include correct index and short explanation for each. Text:\n{section_text[:2000]}"
            out = gen(prompt, max_length=512)
            # best-effort parse: return stub when parsing fails
            text = out[0]['generated_text']
            # naive parse: split by lines
            items = []
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for i, line in enumerate(lines[:n]):
                items.append({'id': f's{section_id}-hf{i}', 'section': section_id, 'question': line, 'choices': ['A','B','C','D'], 'answer': 0, 'explanation': line})
            return items
        except Exception:
            return _stub_generate(section_id, section_text, n=n, history=history, seed=seed, mastered=mastered)
    else:
        return _stub_generate(section_id, section_text, n=n, history=history, mastered=mastered, seed=seed)

