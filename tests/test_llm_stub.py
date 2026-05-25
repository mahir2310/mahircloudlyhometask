from app.llm import generate_mcqs_for_section


def test_llm_stub_returns_list():
    res = generate_mcqs_for_section(1, "This is a test section. It has facts. More facts.", n=2)
    assert isinstance(res, list)
    assert len(res) == 2
