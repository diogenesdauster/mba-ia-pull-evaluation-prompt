"""
Testes automatizados para validação de prompts.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import load_yaml

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
MIN_TECHNIQUES = 2
FEW_SHOT_PATTERN = re.compile(r"###\s*Exemplo\s*\d+", re.IGNORECASE)
ROLE_PATTERN = re.compile(r"Você\s+é\s+uma?\s+\w+", re.IGNORECASE)


@pytest.fixture(scope="module")
def prompt_body():
    """Carrega o corpo do prompt v2 uma vez por módulo."""
    data = load_yaml(str(PROMPT_PATH))
    assert data is not None, f"YAML vazio ou inválido: {PROMPT_PATH}"
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' ausente no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_body):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_body, "Campo 'system_prompt' ausente"
        system = prompt_body["system_prompt"]
        assert isinstance(system, str), "system_prompt deve ser string"
        assert system.strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self, prompt_body):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        system = prompt_body["system_prompt"]
        match = ROLE_PATTERN.search(system)
        assert match, (
            "Nenhuma definição de persona encontrada. "
            "Espera-se algo como 'Você é um Product Manager'."
        )

    def test_prompt_mentions_format(self, prompt_body):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system = prompt_body["system_prompt"]
        mentions = ("Markdown" in system) or ("User Story" in system) or ("user story" in system)
        assert mentions, "system_prompt não menciona formato Markdown nem User Story"

    def test_prompt_has_few_shot_examples(self, prompt_body):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system = prompt_body["system_prompt"]
        examples = FEW_SHOT_PATTERN.findall(system)
        assert len(examples) >= 2, (
            f"Esperados ≥2 exemplos few-shot (padrão '### Exemplo N'), "
            f"encontrados: {len(examples)}"
        )

    def test_prompt_no_todos(self, prompt_body):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        system = prompt_body["system_prompt"]
        assert "[TODO]" not in system, "system_prompt ainda contém marcador [TODO]"

    def test_minimum_techniques(self, prompt_body):
        """Verifica se pelo menos 2 técnicas foram listadas nos metadados."""
        techniques = prompt_body.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser lista"
        assert len(techniques) >= MIN_TECHNIQUES, (
            f"Mínimo de {MIN_TECHNIQUES} técnicas requeridas, encontradas: {len(techniques)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
