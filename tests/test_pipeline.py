"""Quick integration test for matching pipeline components."""
import sys
sys.path.insert(0, "f:/fyj")


def test_skill_matcher():
    from tools.skill_matcher import extract_skills_from_text, compute_skill_overlap

    resume_text = (
        "Senior Python Developer with 8 years of experience in Django, FastAPI, PostgreSQL. "
        "Expert in Docker, Kubernetes, AWS. Built microservices architecture using REST APIs. "
        "Proficient in React, TypeScript, and CI/CD with GitHub Actions."
    )

    jd_text = (
        "Looking for a Senior Backend Engineer with strong Python and Django experience. "
        "Must have PostgreSQL, Docker, and AWS skills. Microservices architecture required. "
        "Nice to have: Kubernetes, React, TypeScript."
    )

    resume_skills = extract_skills_from_text(resume_text)
    print("Resume skills found:", {k: v for k, v in resume_skills.items() if v})

    score, analysis = compute_skill_overlap(resume_skills, jd_text)
    print(f"Skill overlap score: {score:.2%}")
    print(f"Matched: {analysis['matched']}")
    print(f"Missing: {analysis['missing']}")
    assert score > 0.5, "Skill overlap should be significant"
    return score


def test_tfidf():
    from tools.tfidf_matcher import compute_tfidf_similarity

    resume = "Senior Python Django FastAPI PostgreSQL Docker Kubernetes AWS microservices"
    jd = "Python Django PostgreSQL Docker AWS microservices backend engineer"

    score = compute_tfidf_similarity(resume, jd)
    print(f"TF-IDF similarity: {score:.2%}")
    assert score > 0.3, "TF-IDF should find keyword overlap"
    return score


def test_embeddings():
    from tools.embedding_tools import embed_text, cosine_similarity

    resume = "Senior Python developer with Django and PostgreSQL experience"
    jd = "Backend engineer needed with Python and database skills"

    emb_a = embed_text(resume)
    emb_b = embed_text(jd)
    score = cosine_similarity(emb_a, emb_b)
    print(f"Semantic similarity: {score:.2%}")
    assert score > 0.3, "Semantic similarity should detect related texts"
    assert len(emb_a) == 384, "Embedding dimension should be 384"
    return score


def test_composite():
    skill_score = test_skill_matcher()
    tfidf_score = test_tfidf()
    semantic_score = test_embeddings()

    composite = 0.35 * semantic_score + 0.30 * tfidf_score + 0.35 * skill_score
    print(f"\n=== COMPOSITE SCORE: {composite:.2%} ===")
    print("Pipeline test PASSED!")
    return composite


if __name__ == "__main__":
    test_composite()
