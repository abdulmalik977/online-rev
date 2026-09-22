"""One fresh Codex exec turn; never resumes. Parent runner owns the timeout."""
import json
import os
import subprocess
import sys


def main():
    try:
        maximum = int(os.environ["COMPANY_MAX_CREDITS"])
        if maximum < 1:
            raise ValueError("At least one turn must be reserved")
        # exec accepts one prompt: cap = min(reserved credits, 1), not internal model steps.
        command = json.loads(os.environ.get("CODEX_CLI_COMMAND", '["codex"]'))
        result = subprocess.run(command + ["exec", "--json", "--sandbox", "workspace-write", "-"],
                                input=sys.stdin.read(), text=True, encoding="utf-8", capture_output=True)
        turns, started, tokens, summary, failed = 0, 0, {}, "", False
        for line in result.stdout.splitlines():
            event = json.loads(line)
            kind = event.get("type")
            if kind == "turn.started":
                started += 1
            elif kind == "turn.completed":
                usage = event.get("usage")
                if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
                                                    for k in ("input_tokens", "output_tokens")):
                    raise ValueError("Codex did not report valid token usage")
                turns += 1
                for key, value in usage.items():
                    if type(value) is int and value >= 0:
                        tokens[key] = tokens.get(key, 0) + value
            elif kind == "item.completed" and event.get("item", {}).get("type") == "agent_message":
                summary = event["item"].get("text", "")
            elif kind in {"error", "turn.failed"}:
                failed = True
        if turns < 1 or started != turns:
            raise ValueError("Codex did not report complete turn usage")
        print(json.dumps({"usage": turns, "summary": summary, "tokens": tokens}))
        return 1 if result.returncode or failed or turns > min(maximum, 1) else 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"Codex adapter: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
