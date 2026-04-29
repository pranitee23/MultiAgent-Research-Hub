import pytest

class TestSettings:
    def test_default_provider(self):
        from src.config.settings import Settings
        assert Settings().llm_provider == "groq"

    def test_rejects_invalid_provider(self):
        from pydantic import ValidationError
        from src.config.settings import Settings
        with pytest.raises(ValidationError): Settings(llm_provider="bad")

    def test_rejects_bad_search_limit(self):
        from pydantic import ValidationError
        from src.config.settings import Settings
        with pytest.raises(ValidationError): Settings(arxiv_max_results=0)

class TestState:
    def test_all_keys(self):
        from src.core.state import ResearchState
        expected = {"query","sub_questions","retrieved_papers","synthesis","critique","critique_passed","revision_count","final_answer","messages"}
        assert set(ResearchState.__annotations__.keys()) == expected

class TestPrompts:
    def test_all_exist(self):
        from src.config.prompts import PLANNER_SYSTEM, RETRIEVER_SYSTEM, SYNTHESIZER_SYSTEM, CRITIC_SYSTEM
        for p in [PLANNER_SYSTEM, RETRIEVER_SYSTEM, SYNTHESIZER_SYSTEM, CRITIC_SYSTEM]:
            assert len(p) > 50
    def test_critic_format(self):
        from src.config.prompts import CRITIC_SYSTEM
        assert "VERDICT" in CRITIC_SYSTEM and "PASS" in CRITIC_SYSTEM

class TestLLMFactory:
    def test_provider_info(self):
        from src.core.llm import get_provider_info
        info = get_provider_info()
        assert "provider" in info and "model" in info