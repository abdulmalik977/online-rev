"""Bounded Claude print-mode adapter; the parent runner owns the process timeout."""
import json
import os
import subprocess
import sys


def main():
    try:
        maximum = int(os.environ["COMPANY_MAX_CREDITS"])
        if maximum < 1:
            raise ValueError("At least one turn must be reserved")
        command = json.loads(os.environ.get("CLAUDE_CLI_COMMAND", '["claude"]'))
        result = subprocess.run(command + ["-p", "--output-format", "json", "--max-turns", str(maximum)],
                                input=sys.stdin.read(), text=True, encoding="utf-8", capture_output=True)
        data = json.loads(result.stdout)
        turns, tokens = data.get("num_turns"), data.get("usage")
        if type(turns) is not int or turns < 1 or not isinstance(tokens, dict):
            raise ValueError("Claude did not report turn and token usage")
        if any(type(tokens.get(k)) is not int or tokens[k] < 0 for k in ("input_tokens", "output_tokens")):
            raise ValueError("Claude token usage is missing or invalid")
        print(json.dumps({"usage": turns, "summary": str(data.get("result", data.get("subtype", ""))),
                          "tokens": tokens}))
        return 1 if result.returncode or data.get("is_error") else 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"Claude adapter: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
