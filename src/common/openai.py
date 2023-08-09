import json
import os
import requests
from typing import Any, Dict


# OpenAI API
# Documentation: https://platform.openai.com/docs/api-reference
SERVER_OPENAI_API = "api.openai.com"
ENDPOINT_OPENAI_API_CHAT_COMPLETIONS = "/v1/chat/completions"


def _init_session() -> requests.Session:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    session = requests.Session()
    session.headers.update(
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
    )
    return session


def post_chat_completion(
    session: requests.Session, data: Dict[str, Any]
) -> requests.Response:
    path = ENDPOINT_OPENAI_API_CHAT_COMPLETIONS
    url = f"https://{SERVER_OPENAI_API}{path}"
    return session.post(url, data=json.dumps(data))
