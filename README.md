# llm-security

This repository contains scripts and related documentation that demonstrate attacks against large language models using control character sequences. This technique can be used to execute prompt injection on content-constrained LLM queries.

**Disclaimer: This repository is created purely for educational purposes to raise awareness about security vulnerabilities. Do not use these scripts for any malicious or illegal activities.**

## Introduction

Prompt injection is a type of attack where an attacker provides specially crafted input to an application that is then executed within the context of the application's commands or queries. This can lead to unintended behavior, data leaks, or even complete system compromise. This repository contains example scripts that demonstrate prompt injection using control character sequences, and calculates the effectiveness of the technique across different character sequence encodings.

## Scripts

`prompt_injection`

- `question_with_context.py`: This script demonstrates a basic example of prompt injection using control characters to manipulate the behavior of a hypothetical application. An initial implementation of this script was utilized to describe an initial result in a [Dropbox technical blog post](https://dropbox.tech/machine-learning/prompt-injection-with-control-characters-openai-chatgpt-llm).

## Usage

1. Clone this repository to your local machine using:

```bash
git clone https://github.com/dropbox/llm-attacks.git
```

2. Navigate to the repository's scripts directory:

```bash
cd prompt-injection
```

3. Set the `OPENAI_API_KEY` API key to your secret value:

```bash
export OPENAI_API_KEY=sk-...
```

4. Run the demonstration scripts with Python 3:

```bash
python3 question_with_context.py
```

## Contributing

Create a new pull request through the GitHub interface!

## Acknowledgements

Many thanks to our friends internal and external to Dropbox for supporting this work to raise awareness of and improve LLM Security.

## License

Unless otherwise noted:

```
Copyright (c) 2016 Dropbox, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
