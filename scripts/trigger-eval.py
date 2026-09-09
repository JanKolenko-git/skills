#!/usr/bin/env python3
"""Measure whether a skill's description fires on the prompts that should fire it.

For every query in an eval set, run `claude -p` once (or `--runs` times) against the skill
listing the user actually has — every installed plugin, plus this working tree loaded with
`--plugin-dir` so the description under test is the one on disk, not the cached one — and
watch the first tool call. The skill triggered when that call is `Skill` naming it. Nothing
else the model does is needed, so the process is killed as soon as the first tool call or
the first message completes; a query costs one model turn.

The eval set is a JSON list of {"query", "should_trigger", "instead"?}: `instead` names the
skill a near-miss query belongs to, so a failure can say which skill won. The format is the
one anthropic-skills:skill-creator's run_eval.py reads, so its sets work here unchanged.

Usage: scripts/trigger-eval.py --skill plan-change [--set evals/triggers/plan-change.json]
           [--runs 1] [--model claude-sonnet-5] [--workers 4] [--timeout 90] [--json out.json]
Exit 1 when any query fails its expectation (trigger rate on the wrong side of 0.5).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ID = "jankolenko-skills@jankolenko"
TRIGGER_THRESHOLD = 0.5
MAX_STREAM_LINES = 5000  # a stuck stream is killed, not read forever


def find_skill(name):
    skills_root = os.path.join(REPO, "skills")
    for bucket in sorted(os.listdir(skills_root)):
        candidate = os.path.join(skills_root, bucket, name, "SKILL.md")
        if os.path.isfile(candidate):
            return candidate
    sys.exit(f"error: no skill named '{name}' under {skills_root}")


def build_command(query, model):
    # The installed copy is disabled so the working tree's description is the only one
    # listed under this plugin's name; every other plugin stays, because they are the
    # competitors a near-miss has to lose to in real use.
    settings = json.dumps({"enabledPlugins": {PLUGIN_ID: False}})
    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json", "--verbose", "--include-partial-messages",
        "--plugin-dir", REPO,
        "--settings", settings,
        "--no-session-persistence",
    ]
    if model:
        cmd += ["--model", model]
    return cmd


def first_tool_call(process, timeout):
    """Return ("skill", <name>) / ("tool", <name>) / ("none", None) from the stream."""
    import select
    import time

    deadline = time.time() + timeout
    pending_json = ""
    pending_tool = None
    lines_read = 0
    buffer = ""
    while time.time() < deadline and lines_read < MAX_STREAM_LINES:
        if process.poll() is not None:
            buffer += process.stdout.read().decode("utf-8", errors="replace")
        else:
            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if not ready:
                continue
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            lines_read += 1
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "stream_event":
                inner = event.get("event", {})
                kind = inner.get("type")
                if kind == "content_block_start":
                    block = inner.get("content_block", {})
                    if block.get("type") == "tool_use":
                        pending_tool = block.get("name", "")
                        pending_json = ""
                elif kind == "content_block_delta" and pending_tool is not None:
                    delta = inner.get("delta", {})
                    if delta.get("type") == "input_json_delta":
                        pending_json += delta.get("partial_json", "")
                elif kind == "content_block_stop" and pending_tool is not None:
                    return classify(pending_tool, pending_json)
                elif kind == "message_stop":
                    return ("none", None)
            elif event.get("type") == "assistant":
                for item in event.get("message", {}).get("content", []):
                    if item.get("type") == "tool_use":
                        return classify(item.get("name", ""), json.dumps(item.get("input", {})))
                return ("none", None)
            elif event.get("type") == "result":
                return ("none", None)
        if process.poll() is not None and not buffer:
            break
    return ("timeout", None)


def classify(tool_name, input_json):
    if tool_name != "Skill":
        return ("tool", tool_name)
    try:
        skill = json.loads(input_json).get("skill", "")
    except json.JSONDecodeError:
        skill = input_json
    return ("skill", skill)


def run_query(query, model, timeout, workdir):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    process = subprocess.Popen(build_command(query, model), stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, cwd=workdir, env=env)
    try:
        return first_tool_call(process, timeout)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def matches(fired, skill_name):
    return fired == skill_name or fired.endswith(":" + skill_name)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--skill", required=True)
    parser.add_argument("--set", dest="eval_set")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--model", default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    find_skill(args.skill)
    set_path = args.eval_set or os.path.join(REPO, "evals", "triggers", f"{args.skill}.json")
    with open(set_path, encoding="utf-8") as fh:
        eval_set = json.load(fh)

    # A scratch project with nothing in it, so the only context the model has is the
    # listing and the query — the same position a fresh session is in.
    workdir = tempfile.mkdtemp(prefix="trigger-eval-")
    os.makedirs(os.path.join(workdir, ".claude"), exist_ok=True)
    outcomes = {item["query"]: [] for item in eval_set}
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {}
            for item in eval_set:
                for _ in range(args.runs):
                    future = pool.submit(run_query, item["query"], args.model, args.timeout, workdir)
                    futures[future] = item["query"]
            for future in as_completed(futures):
                query = futures[future]
                try:
                    outcomes[query].append(future.result())
                except Exception as exc:  # one broken run is a data point, not a crash
                    outcomes[query].append(("error", str(exc)))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    results = []
    for item in eval_set:
        runs = outcomes[item["query"]]
        hits = sum(1 for kind, name in runs if kind == "skill" and matches(name or "", args.skill))
        rate = hits / len(runs) if runs else 0.0
        expected = bool(item["should_trigger"])
        passed = rate >= TRIGGER_THRESHOLD if expected else rate < TRIGGER_THRESHOLD
        fired = sorted({f"{kind}:{name}" for kind, name in runs if not (kind == "skill" and matches(name or "", args.skill))})
        results.append({
            "query": item["query"], "should_trigger": expected, "instead": item.get("instead"),
            "trigger_rate": rate, "runs": len(runs), "pass": passed, "fired_instead": fired,
        })

    positives = [r for r in results if r["should_trigger"]]
    negatives = [r for r in results if not r["should_trigger"]]
    summary = {
        "skill": args.skill, "model": args.model, "runs_per_query": args.runs,
        "should_trigger": {"passed": sum(r["pass"] for r in positives), "total": len(positives)},
        "should_not_trigger": {"passed": sum(r["pass"] for r in negatives), "total": len(negatives)},
    }
    report = {"summary": summary, "results": results}
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)

    print(f"{args.skill}: should-trigger {summary['should_trigger']['passed']}/{summary['should_trigger']['total']}, "
          f"should-not-trigger {summary['should_not_trigger']['passed']}/{summary['should_not_trigger']['total']} "
          f"(runs per query: {args.runs}, model: {args.model or 'default'})")
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        extra = f"  fired: {', '.join(r['fired_instead'])}" if r["fired_instead"] and not r["pass"] else ""
        print(f"  [{mark}] {'+' if r['should_trigger'] else '-'} {r['trigger_rate']:.2f}  {r['query'][:90]}{extra}")
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
