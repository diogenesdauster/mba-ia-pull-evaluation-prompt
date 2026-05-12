"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
YAML_PATH = f"prompts/{PROMPT_KEY}.yml"
REQUIRED_FIELDS = ("system_prompt", "user_prompt", "version", "techniques_applied")
MIN_TECHNIQUES = 2


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """Valida estrutura básica do prompt antes do push."""
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório ausente: {field}")

    system = prompt_data.get("system_prompt", "")
    if not system.strip():
        errors.append("system_prompt está vazio")
    if "[TODO]" in system:
        errors.append("system_prompt ainda contém [TODO]")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < MIN_TECHNIQUES:
        errors.append(
            f"Mínimo de {MIN_TECHNIQUES} técnicas requeridas, encontradas: {len(techniques)}"
        )

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> None:
    """Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO). Raises em falha."""
    template = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])

    url = Client().push_prompt(
        prompt_name,
        object=template,
        is_public=True,
        description=prompt_data.get("description"),
        tags=prompt_data.get("tags"),
    )

    print(f"   ✓ Push concluído: {url}")


def main():
    print_section_header("Push do prompt v2 ao LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/{PROMPT_KEY}"

    data = load_yaml(YAML_PATH)
    if data is None or PROMPT_KEY not in data:
        print(f"❌ Falha ao carregar {YAML_PATH} ou chave '{PROMPT_KEY}' ausente")
        return 1

    body = data[PROMPT_KEY]

    print(f"📋 Validando {YAML_PATH}...")
    valid, errors = validate_prompt(body)
    if not valid:
        print("❌ Validação falhou:")
        for e in errors:
            print(f"   - {e}")
        return 1
    print(f"   ✓ Validação OK ({len(body.get('techniques_applied', []))} técnicas, "
          f"system_prompt {len(body['system_prompt'])} chars)")

    print(f"📤 Pushing público para: {prompt_name}")
    try:
        push_prompt_to_langsmith(prompt_name, body)
    except Exception as e:
        print(f"❌ Falha no push: {type(e).__name__}: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
