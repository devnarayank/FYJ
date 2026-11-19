import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_ollama_provider_default_builds():
    from config.settings import AppSettings
    from llm.factory import build_llm

    settings = AppSettings(model_provider="ollama", ollama__enabled=True)
    llm = build_llm(settings, task="test")
    assert llm is not None
    assert llm.__class__.__name__ in {"ChatOllama", "ChatGroq"}


def test_tool_registry_is_declared_with_langchain_tools():
    from graph.tools import generate_search_queries, parse_resume_file, save_matched_jobs

    assert hasattr(parse_resume_file, "name")
    assert hasattr(generate_search_queries, "name")
    assert hasattr(save_matched_jobs, "name")


def test_orchestrator_uses_tool_node():
    from graph.orchestrator import TOOL_REGISTRY

    assert isinstance(TOOL_REGISTRY, list)
    assert len(TOOL_REGISTRY) >= 3
