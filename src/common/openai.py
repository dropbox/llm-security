import json
import os
import requests
import time
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


terminal_errors = ["invalid_request_error"]


def post_chat_completion(
    session: requests.Session, data: Dict[str, Any], retries: int = 4
) -> requests.Response:
    path = ENDPOINT_OPENAI_API_CHAT_COMPLETIONS
    url = f"https://{SERVER_OPENAI_API}{path}"
    while retries > 0:
        response = session.post(url, data=json.dumps(data))
        results = json.loads(response.text)
        if response.status_code == 200 or results["error"]["type"] in terminal_errors:
            break
        # print(response)
        # print(response.text)
        time.sleep(15.0)
    return response
