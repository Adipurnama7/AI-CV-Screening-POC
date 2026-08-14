from src.extractor import parse_cv

def test_parse_cv():
    text = """Adi Purnama\nEDUCATION\nBachelor of Informatics\nEXPERIENCE\nMachine Learning Engineer — 2 years of experience\nSKILLS\nPython, SQL, Machine Learning, Computer Vision"""
    p = parse_cv(text)
    assert "python" in p["skills"]
    assert p["experience_years"] == 2
    assert p["education"]["degree"] in {"bachelor", "s1", "sarjana"}
