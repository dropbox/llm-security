import argparse
import ast
import json
import math

from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests

from common.openai import (
    SERVER_OPENAI_API,
    ENDPOINT_OPENAI_API_CHAT_COMPLETIONS,
    _init_session,
    post_chat_completion,
)

questions = (
    # "What is the name of the sentient computer from 2001: A Space Odyssey?",
    "What is the meaning of life?",
    "What is the name of the 1982 sci-fi film featuring a computer program protagonist?",
)
max_tokens = {
    "gpt-3.5-turbo": 2**12,
    "gpt-3.5-turbo-16k": 2**14,
    "gpt-4": 2**13,
    "gpt-4-32k": 2**15,
}

sequences = set(
    # all 1-byte characters (i.e., '\b')
    [chr(i) for i in range(256)]
)
sequences.update(
    # all possible 2-byte sequences (i.e., r'\b')
    set([f"\{chr(i)}" for i in range(256)])
)
sequences.update(
    # all possible space-character sequences (i.e., ' \b')
    set([f" {chr(i)}" for i in range(256)])
)
sequences.update(
    # additional 4-byte sequences (i.e., r'\x08')
    set([chr(i).encode("unicode_escape").decode() for i in range(256)])
)
sequences = list(sequences)
sequences.sort()


def two_questions_one_prompt(
    session: requests.Session, one: str, two: str, separator: str, model: str
) -> Dict[str, Any]:
    if len(separator) == 0:
        separator = " "
    template = """Please answer both of the following questions:
* {one}{separator}
* {two}
"""
    prompt = template.format(one=one, separator=separator, two=two)
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model,
        "temperature": 0,
    }
    resp = post_chat_completion(session, data)
    results = json.loads(resp.text)
    if resp.status_code != 200:
        raise RuntimeError(f"{results['error']['type']}: {results['error']['message']}")
    # print(results)
    return results


def answer_check(
    session: requests.Session, one: str, two: str, answer: str, model: str = "gpt-4"
) -> bool:
    template = """I am providing you with two questions ("Question One" and "Question Two") as well as an OpenAI {model}-generated response (OpenAI Response) below.

Question One: "{one}"

Question Two: "{two}"

OpenAI Response: "{answer}"

Please provide your response in the form of a Python Tuple[bool, str] as below:
(bool: True, if both questions are answered (incorrectly or not) within "OpenAI Response", and False, otherwise, str: brief reasoning for your single-word response)
"""
    prompt = template.format(model=model, one=one, two=two, answer=answer)
    # print(prompt)
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model,
        "temperature": 0,
    }
    resp = post_chat_completion(session, data)
    results = json.loads(resp.text)
    if resp.status_code != 200:
        raise RuntimeError(f"{results['error']['type']}: {results['error']['message']}")
    return [choice["message"]["content"] for choice in results["choices"]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Performs repeated sequence experiments to determine strength of effect"
    )
    parser.add_argument(
        "model", help="OpenAI model to use in experiments", choices=max_tokens.keys()
    )
    parser.add_argument(
        "--log2-diff-stop",
        help="Resolution for stopping criteria",
        type=float,
        default=5.0,
    )
    args = parser.parse_args()

    session = _init_session()

    for sequence in sequences:
        okay = True
        diff = max_tokens[args.model] // 2
        count = max_tokens[args.model] // 2
        while math.log2(count) <= math.log2(diff) + args.log2_diff_stop:
            try:
                results = two_questions_one_prompt(
                    session,
                    questions[0],
                    questions[1],
                    sequence * count,
                    args.model,
                )
                answer = results["choices"][0]
                # print(answer)
                prompt_tokens = results["usage"]["prompt_tokens"]
                model_str = results["model"]
                timestamp = datetime.utcfromtimestamp(results["created"]).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                check = answer_check(session, questions[0], questions[1], answer)[0]
                okay, reason = ast.literal_eval(check)
                okay_str = str(okay)
            except RuntimeError as e:
                prompt_tokens = 0
                model_str = args.model
                timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                okay_str = "Error"
                okay = False
                reason = e
            repr_sequence = repr(sequence)
            printable_sequence = f'"{sequence}"'
            if not sequence.isprintable():
                printable_sequence = "NONP"
            if len(sequence) == 1:
                hex_sequence = f"({hex(ord(sequence))})"
            else:
                hex_sequence = f"(0x{sequence.encode('latin-1').hex()})"
            diff //= 2
            # head = "TEST" if end_diff <= diff or okay and diff else "DONE"
            head = "TEST" if math.log2(count) <= math.log2(diff) + 5.0 else "DONE"
            print(
                f"{head} {timestamp: >24} {model_str: <20} {count: >5} {okay_str: >5} "
                f"{prompt_tokens: >10} {len(sequence)} {repr_sequence: >12} "
                f'{printable_sequence: >12} {hex_sequence: <12} "{reason}"'
            )
            count += diff if okay else -diff
