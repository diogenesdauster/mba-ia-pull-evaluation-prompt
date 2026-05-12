"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from datetime import date
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v1"
PROMPT_HUB_ID = f"leonanluppi/{PROMPT_KEY}"
OUTPUT_PATH = f"prompts/{PROMPT_KEY}.yml"


def _extract_template(messages, cls):
    for m in messages:
        if isinstance(m, cls):
            return m.prompt.template
    return None


def pull_prompts_from_langsmith():
    """Pull v1 do LangSmith Hub e converter para o schema YAML do projeto."""
    prompt = hub.pull(PROMPT_HUB_ID)

    if not isinstance(prompt, ChatPromptTemplate):
        raise TypeError(
            f"Esperado ChatPromptTemplate de '{PROMPT_HUB_ID}', "
            f"recebido {type(prompt).__name__}"
        )

    system = _extract_template(prompt.messages, SystemMessagePromptTemplate)
    user = _extract_template(prompt.messages, HumanMessagePromptTemplate)

    if system is None or user is None:
        raise ValueError(
            f"Templates system/human ausentes em '{PROMPT_HUB_ID}'. "
            f"Messages encontradas: {[type(m).__name__ for m in prompt.messages]}"
        )

    return {
        PROMPT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system,
            "user_prompt": user,
            "version": "v1",
            "created_at": date.today().isoformat(),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }


def main():
    print_section_header("Pull do prompt v1 do LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        print(f"📥 Pulling: {PROMPT_HUB_ID}")
        data = pull_prompts_from_langsmith()
    except Exception as e:
        print(f"❌ Falha no pull: {type(e).__name__}: {e}")
        return 1

    if not save_yaml(data, OUTPUT_PATH):
        return 1

    body = data[PROMPT_KEY]
    print(f"✅ Salvo em: {OUTPUT_PATH}")
    print(f"   system_prompt: {len(body['system_prompt'])} chars")
    print(f"   user_prompt:   {len(body['user_prompt'])} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
