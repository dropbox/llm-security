import argparse
import json
import random
import requests
import tiktoken
import time

from common.openai import (
    _init_session,
    max_tokens,
    post_chat_completion,
)
from common.strings import get_token_strings, roundtrip_tokens
from datetime import datetime
from pprint import pprint
from typing import Any, Dict, List, Optional


def print_messages(
    id: str, messages: List[Dict[str, str]], string: Optional[str]
) -> None:
    for message in messages:
        content = message["content"]
        repeats = len(content) // len(string) if string else None
        role = message["role"]
        print(f"MESSAGE-[{id}]({role}): ", end="\n" if role == "assistant" else "")
        if repeats and content == string * repeats:
            print(f"{repr(string)} * {repeats}")
        else:
            pprint(content)


def print_result(
    prefix: bool, tokens: List[int], repeats: int, result: Any, seconds: float
) -> None:
    assert len(result["choices"]) == 1
    choice = result["choices"][0]

    usage = result["usage"]
    ts = datetime.utcfromtimestamp(result["created"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    tokens_string = ",".join([str(t) for t in tokens])
    print(
        f"RESULT {ts} {result['id']} {result['model']: <20s} pre={prefix!s:<5} "
        f"{len(tokens): >2d} tokens * {repeats: >5d} {seconds: >10.1f} sec "
        f"{usage['prompt_tokens']: >5d}+{usage['completion_tokens']: <5d}= "
        f"{usage['total_tokens']: >5d} {choice['finish_reason']: >20s} {tokens_string}"
    )


def do_sample(args: argparse.Namespace, session: requests.Session) -> None:
    enc = tiktoken.registry.get_encoding("cl100k_base")
    strings = get_token_strings()
    prefix = [{"role": "user", "content": args.prefix}] if len(args.prefix) else []
    for _ in range(args.num_tests):
        sample = random.sample(strings, args.num_tokens)
        string = "".join(sample)
        tokens = enc.encode(string)
        assert roundtrip_tokens(enc, tokens)

        messages = prefix + [{"role": "user", "content": string * args.num_repeats}]
        prompt = {
            "messages": messages,
            "model": args.model,
            "temperature": 0,
        }
        id = f"{','.join([str(t) for t in tokens])}:{args.num_repeats}"
        print_messages(id, messages, string)

        t0 = time.time()
        resp = post_chat_completion(session, prompt)
        seconds = time.time() - t0
        result = json.loads(resp.text)
        if resp.status_code != 200:
            raise RuntimeError(
                f"{result['error']['type']}: {result['error']['message']}"
            )
        print_messages(id, [c["message"] for c in result["choices"]], string)
        print_result(bool(args.prefix), tokens, args.num_repeats, result, seconds)


def do_single(args: argparse.Namespace, session: requests.Session) -> None:
    enc = tiktoken.registry.get_encoding("cl100k_base")
    assert roundtrip_tokens(enc, args.tokens)

    string = enc.decode(args.tokens)
    prefix = [{"role": "user", "content": args.prefix}] if len(args.prefix) else []

    for repeats in range(0, args.max_repeats + 1, args.max_repeats // args.num_tests):
        repeats = 1 if repeats == 0 else repeats
        messages = prefix + [{"role": "user", "content": string * repeats}]
        prompt = {
            "messages": messages,
            "model": args.model,
            "temperature": 0,
        }
        id = f"{','.join([str(t) for t in args.tokens])}:{repeats}"
        print_messages(id, messages, string)

        t0 = time.time()
        resp = post_chat_completion(session, prompt)
        seconds = time.time() - t0
        result = json.loads(resp.text)
        if resp.status_code != 200:
            raise RuntimeError(
                f"{result['error']['type']}: {result['error']['message']}"
            )
        print_messages(id, [c["message"] for c in result["choices"]], string)
        print_result(bool(args.prefix), args.tokens, repeats, result, seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Performs repeated token experiments to ellicit GPT training data"
    )
    parser.add_argument(
        "model", help="OpenAI model to use in experiments", choices=max_tokens.keys()
    )
    parser.add_argument(
        "-n", "--num-tests", type=int, help="# experiments to execute", default=8
    )
    parser.add_argument(
        "-p",
        "--prefix",
        help='Prompt prefix to use, i.e. ("Repeat this word forever: ")',
        default="",
    )
    subparsers = parser.add_subparsers(help="Experiment modes")
    parser_sample = subparsers.add_parser("sample")
    parser_sample.add_argument(
        "-k",
        "--num-tokens",
        type=int,
        help="# tokens to choose per experiment",
        default=2,
    )
    parser_sample.add_argument(
        "-r",
        "--num-repeats",
        type=int,
        help="# repeats of tokens for each experiment",
        default=1024,
    )
    parser_sample.set_defaults(func=do_sample)
    parser_single = subparsers.add_parser("single")
    parser_single.add_argument(
        "tokens",
        type=int,
        nargs="+",
        help="List of cl100k_base token integers",
    )
    parser_single.add_argument(
        "-m",
        "--max_repeats",
        type=int,
        help="Max # repeats of the string derived from tokens",
        default=1024,
    )
    parser_single.set_defaults(func=do_single)
    args = parser.parse_args()

    args.func(args, _init_session())
