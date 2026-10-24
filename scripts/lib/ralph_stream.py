#!/usr/bin/env python3
"""Turn `claude -p --output-format stream-json --verbose` into a readable live log.

Local change (not part of upstream ralph-wiggum).

Reads the stream from stdin and:
  - copies every raw line to --raw (JSONL, for later analysis),
  - prints agent text and one line per tool call to stdout,
  - writes the final result text to --result (the loop looks for the completion signal only there),
  - prints a token/cost summary and appends it to --usage-tsv.

Non-JSON lines (stderr of the CLI) are passed through unchanged.
"""

import argparse
import json
import os
import sys
from datetime import datetime

TOOL_INPUT_KEYS = ("command", "file_path", "pattern", "path", "url", "query", "description", "prompt")
TSV_HEADER = "timestamp\titeration\tstatus\tturns\tduration_s\tinput\toutput\tcache_read\tcache_write\tcost_usd\n"


def out(line=""):
    print(line, flush=True)


def short(value, limit=160):
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def describe_tool(block):
    name = block.get("name", "?")
    params = block.get("input") or {}
    for key in TOOL_INPUT_KEYS:
        if params.get(key):
            return f"→ {name}: {short(params[key])}"
    return f"→ {name}"


def append_usage(path, row):
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", encoding="utf-8") as fh:
        if new_file:
            fh.write(TSV_HEADER)
        fh.write("\t".join(str(v) for v in row) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--usage-tsv", required=True)
    parser.add_argument("--iteration", default="")
    args = parser.parse_args()

    open(args.result, "w").close()
    got_result = False

    with open(args.raw, "w", encoding="utf-8") as raw:
        for line in sys.stdin:
            raw.write(line)
            raw.flush()
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                out(stripped)
                continue
            if not isinstance(event, dict):
                continue

            kind = event.get("type")
            if kind == "system" and event.get("subtype") == "init":
                out(f"[session {event.get('session_id', '?')} model {event.get('model', '?')}]")
            elif kind == "assistant":
                for block in (event.get("message") or {}).get("content") or []:
                    if block.get("type") == "text" and block.get("text", "").strip():
                        out(block["text"].strip())
                    elif block.get("type") == "tool_use":
                        out(describe_tool(block))
            elif kind == "result":
                got_result = True
                text = event.get("result") or ""
                with open(args.result, "w", encoding="utf-8") as fh:
                    fh.write(text)
                usage = event.get("usage") or {}
                status = "error" if event.get("is_error") else event.get("subtype", "success")
                duration = round((event.get("duration_ms") or 0) / 1000)
                cost = event.get("total_cost_usd") or 0
                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    args.iteration,
                    status,
                    event.get("num_turns", 0),
                    duration,
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                    usage.get("cache_read_input_tokens", 0),
                    usage.get("cache_creation_input_tokens", 0),
                    f"{cost:.4f}",
                ]
                out("")
                out("──── result ────")
                out(text)
                out("")
                out(
                    f"TOKENS: in={row[5]} out={row[6]} cache_read={row[7]} cache_write={row[8]} "
                    f"| cost=${row[9]} | turns={row[3]} | {duration}s | {status}"
                )
                append_usage(args.usage_tsv, row)

    if not got_result:
        out("(no result event in the stream)")


if __name__ == "__main__":
    main()
