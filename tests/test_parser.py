from app.parser import get_section_texts


def test_get_sections_exists():
    sections = get_section_texts('SLATEFALL_DOSSIER.txt')
    assert isinstance(sections, dict)
    # expect at least section 1 present based on dossier
    assert any(k == 1 for k in sections.keys())
