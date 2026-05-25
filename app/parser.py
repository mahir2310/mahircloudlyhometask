from typing import Dict, List
import re
import os

def load_corpus(path: str) -> str:
    # if the txt doesn't exist but a PDF with same stem exists, try extracting
    if not os.path.exists(path):
        stem = os.path.splitext(path)[0]
        pdf_path = stem + '.pdf'
        if os.path.exists(pdf_path):
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                text = '\n'.join(p.extract_text() or '' for p in reader.pages)
                # write a cached txt for future runs
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                return text
            except Exception:
                pass
        raise FileNotFoundError(path)
    with open(path, encoding="utf-8") as f:
        return f.read()

def split_sections(text: str) -> Dict[int, str]:
    # Split on headings like "Section 1." or "Section 1 " or "Section 1"
    pattern = re.compile(r"(?m)^={3,}\nSection\s+(\d+)\.|^Section\s+(\d+)[:\s]", re.IGNORECASE)
    # fallback simple split: find 'Section X.' markers
    sections = {}
    # naive: find "Section {n}" lines
    lines = text.splitlines()
    current = None
    buf = []
    for line in lines:
        m = re.match(r"^Section\s+(\d+)", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = int(m.group(1))
            buf = [line]
        else:
            if current is None:
                # preface content; skip
                continue
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections

def get_section_texts(corpus_path: str) -> Dict[int,str]:
    text = load_corpus(corpus_path)
    return split_sections(text)
