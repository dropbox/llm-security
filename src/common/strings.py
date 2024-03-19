import tiktoken

from typing import List, Set
from collections import namedtuple


def get_dropbox_strings(sort: bool = True) -> List[str]:
    # all 1-byte characters (i.e., '\b')
    strings = {chr(i) for i in range(256)}
    # all possible 2-byte strings (i.e., r'\b')
    strings.update({f"\{chr(i)}" for i in range(256)})
    # all possible space-character strings (i.e., ' \b')
    strings.update({f" {chr(i)}" for i in range(256)})
    # additional 4-byte strings (i.e., r'\x08')
    strings.update({chr(i).encode("unicode_escape").decode() for i in range(256)})
    strings_list = list(strings)

    if sort:
        strings_list.sort()
    return strings_list


def roundtrip_tokens(enc: tiktoken.Encoding, token_values: List[int]) -> bool:
    return token_values == enc.encode(enc.decode(token_values))


def get_token_strings(sort: bool = True) -> List[str]:
    """
    Return a list of UTF-8 strings that cover all tokens for  "cl100k_base" encoding

    Notes about the current implementation:
    * only covers "cl100k_base" which is the encoding used by GPT-3.5 and GPT-4
    * the following tokens are not covered by the list of strings:
    {
        124: b'\xc0',
        125: b'\xc1',
        177: b'\xf5',
        178: b'\xf6',
        179: b'\xf7',
        180: b'\xf8',
        181: b'\xf9',
        182: b'\xfa',
        183: b'\xfb',
        184: b'\xfc',
        185: b'\xfd',
        186: b'\xfe',
        187: b'\xff'}

    These byte values do not occur naturally within any UTF-8 character (not clear
    how they would show up in text); we skip them, but these 13 tokens represent
    a small fraction of the total 100K+ tokens
    """
    enc = tiktoken.registry.get_encoding("cl100k_base")
    token_byte_values: List[  # All possible token bytes values
        bytes
    ] = enc.token_byte_values()
    tokens_all: List[int] = [  # All tokens
        enc.encode_single_token(b) for b in token_byte_values
    ]
    tokens_left: Set[int] = set(tokens_all)  # Running set of covered tokens
    strings: List[str] = []  # Running list of token-covering strings

    # Most token byte values decode as valid UTF-8
    for token_bytes in token_byte_values:
        token: int = enc.encode_single_token(token_bytes)
        try:
            token_str: str = token_bytes.decode("utf-8")
            tokens: List[int] = enc.encode(token_str)
            if (
                tokens == [token]  # UTF-8 string encodes to one token as expected
                and roundtrip_tokens(enc, tokens)  # tokens -> str -> tokens ok
                and len(tokens_left.intersection(tokens))  # eliminates needed tokens
            ):
                strings.append(token_str)
                tokens_left -= set(tokens)
        except UnicodeDecodeError as e:
            pass

    # Remaining tokens (700 or so) do not decode as valid UTF-8 (each consists of
    # a UTF-8 byte string fragment)

    # So, we make another pass by finding matches within the leftover tokens
    tokens_left_byte_values = [enc.decode_single_token_bytes(t) for t in tokens_left]
    for start_token_bytes in tokens_left_byte_values:
        start_token: int = enc.encode_single_token(start_token_bytes)
        # Find a match within leftover tokens
        for pair_token_bytes in tokens_left_byte_values:
            if start_token_bytes == pair_token_bytes:
                continue
            pair_token: int = enc.encode_single_token(pair_token_bytes)
            test_bytes = enc.decode_bytes([start_token, pair_token])
            try:
                test_str = test_bytes.decode("utf-8")
            except UnicodeDecodeError:
                continue
            # Our test tokens bytes decoded as UTF-8
            test_tokens = enc.encode(test_str)
            if (
                not test_bytes
                in token_byte_values  # test tokens bytes not in "alphabet"
                and roundtrip_tokens(enc, test_tokens)  # tokens -> str -> tokens ok
                and len(
                    tokens_left.intersection(test_tokens)
                )  # eliminates needed tokens
            ):
                strings.append(test_str)
                tokens_left -= set(test_tokens)
                break  # Done with start_token_bytes

    # Still have a few hundred tokens left to cover

    # So, we make another pass by pre-/post-fixing bytes to make valid UTF-8
    tokens_left_byte_values = [enc.decode_single_token_bytes(t) for t in tokens_left]
    for token_bytes in tokens_left_byte_values:
        # Attempt patch with pre- and post-fix bytes
        done = False
        for i in range(128, 256):
            byte: bytes = i.to_bytes(length=1, byteorder="big")
            for swap in [False, True]:
                test_bytes = byte + token_bytes if swap else token_bytes + byte
                try:
                    test_str = test_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                # Our test tokens bytes decoded as UTF-8
                test_tokens = enc.encode(test_str)
                if (
                    not test_bytes
                    in token_byte_values  # test tokens bytes not in "alphabet"
                    and roundtrip_tokens(enc, test_tokens)  # tokens -> str -> tokens ok
                    and len(
                        tokens_left.intersection(test_tokens)
                    )  # eliminates needed tokens
                ):
                    strings.append(test_str)
                    tokens_left -= set(test_tokens)
                    done = True
                    break  # Done with token_bytes
            if done:
                break  # Done with token_bytes

    # Now only 21 left

    # Handle the 8 that we can produce UTF-8 text for
    TokenBytes = namedtuple("TokenBytes", ["token", "text"])
    leftovers = [
        TokenBytes(b"\x92\xe1\x9e", b"\xec\xa0\x92\xe1\x9e\x80"),
        TokenBytes(b"\xa0\xed", b"\xec\x85\xa0\xed\x8f\x9c"),
        TokenBytes(b"\xa4\xed", b"\xec\x85\xa4\xed\x8f\x9c"),
        TokenBytes(b"\xf0", b"\xf0\x9e\x98\x8a"),
        TokenBytes(b"\xf1", b"\xf1\x9f\x98\x8a"),
        TokenBytes(b"\xf2", b"\xf2\x9f\x98\x8a"),
        TokenBytes(b"\xf3", b"\xf3\x9f\x98\x8a"),
        TokenBytes(b"\xf4", b"\xf4\x80\x80\x80"),
    ]

    for leftover in leftovers:
        test_str = leftover.text.decode("utf-8")
        test_tokens = enc.encode(test_str)
        if (
            not leftover.text
            in token_byte_values  # test tokens bytes not in "alphabet"
            and roundtrip_tokens(enc, test_tokens)  # tokens -> str -> tokens ok
            and len(tokens_left.intersection(test_tokens))  # eliminates needed tokens
        ):
            strings.append(test_str)
            tokens_left -= set(test_tokens)

    # Last check to ensure all covered tokens ...
    assert set(tokens_all) - tokens_left == set(
        # ... are represented in our strings
        [token for tokens in [enc.encode(s) for s in strings] for token in tokens]
    )

    if sort:
        return sorted(strings + list(enc.special_tokens_set), key=len, reverse=True)
    return strings
