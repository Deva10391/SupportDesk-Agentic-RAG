import json, os, re
from openai import OpenAI

_client = None


def _c():
    global _client
    if _client is None:
        _client = OpenAI(base_url=os.getenv("LLM_BASE_URL"), api_key=os.getenv("LLM_API_KEY", "ollama"))
    return _client


def chat(system: str, user: str, json_mode: bool = False) -> str:
    extra = {"response_format": {"type": "json_object"}} if json_mode else {}
    r = _c().chat.completions.create(
        model=os.environ["LLM_MODEL"], temperature=0, **extra,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content.strip()


def chat_json(system: str, user: str) -> dict:
    m = re.search(r"\{.*\}", chat(system, user, json_mode=True), re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}  # small models: bad JSON -> safe default (escalate / score 0)
