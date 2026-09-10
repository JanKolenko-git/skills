#!/usr/bin/env python3
"""Measure whether a skill's description fires on the prompts that should fire it.

For every query in an eval set, run `claude -p` once (or `--runs` times) against the skill
listing the user actually has — every installed plugin, plus this working tree loaded with
`--plugin-dir` so the description under test is the one on disk, not the cached one — and
watch the first few tool calls. The skill triggered when one of them is `Skill` naming it;
the model often looks first (git status, ls), and a tool `claude -p` cannot get permission
for is a cheap denied turn. The process is killed as soon as the skill fires, the tool-call
allowance is spent, or the message ends, so a query costs one to three short turns. The
scratch project is a git repository with one commit, because most prompts assume one.

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
DEFAULT_MAX_TOOL_CALLS = 3  # the model often looks (git status, ls) before it reaches for a skill


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


def watch_tool_calls(process, timeout, skill_name, max_tool_calls):
    """Return ("skill", <name>) as soon as the skill is invoked, else what happened instead.

    Reads the stream until the skill fires, `max_tool_calls` other tool calls have been seen
    (("tool", <first tool>) or ("skill", <other skill>) for the first of them), or the message
    ends without a tool call (("none", None)). A stuck stream returns ("timeout", None)."""
    import select
    import time

    deadline = time.time() + timeout
    pending_json = ""
    pending_tool = None
    seen = []
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
                    outcome = classify(pending_tool, pending_json)
                    pending_tool = None
                    if outcome[0] == "skill" and matches(outcome[1] or "", skill_name):
                        return outcome
                    seen.append(outcome)
                    if len(seen) >= max_tool_calls:
                        return seen[0]
            elif event.get("type") == "assistant":
                # One assistant event arrives per content block, and a thinking or text
                # block usually precedes the tool call, so a tool_use is the only thing
                # worth reading here; the stream events above already classified it.
                continue
            elif event.get("type") == "result":
                return seen[0] if seen else ("none", None)
        if process.poll() is not None and not buffer:
            break
    return seen[0] if seen else ("timeout", None)


def classify(tool_name, input_json):
    if tool_name != "Skill":
        return ("tool", tool_name)
    try:
        skill = json.loads(input_json).get("skill", "")
    except json.JSONDecodeError:
        skill = input_json
    return ("skill", skill)


def run_query(query, model, timeout, workdir, skill_name, max_tool_calls):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    process = subprocess.Popen(build_command(query, model), stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, cwd=workdir, env=env)
    try:
        return watch_tool_calls(process, timeout, skill_name, max_tool_calls)
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
    parser.add_argument("--max-tool-calls", type=int, default=DEFAULT_MAX_TOOL_CALLS,
                        help="stop watching after this many tool calls that are not the skill")
    args = parser.parse_args()

    find_skill(args.skill)
    set_path = args.eval_set or os.path.join(REPO, "evals", "triggers", f"{args.skill}.json")
    with open(set_path, encoding="utf-8") as fh:
        eval_set = json.load(fh)

    # A scratch project with nothing in it, so the only context the model has is the
    # listing and the query — the same position a fresh session is in.
    workdir = tempfile.mkdtemp(prefix="trigger-eval-")
    os.makedirs(os.path.join(workdir, ".claude"), exist_ok=True)
    with open(os.path.join(workdir, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# app\n")
    subprocess.run("git init -q . && git add -A && git -c user.email=e@x -c user.name=n commit -qm init",
                   shell=True, cwd=workdir, check=True, capture_output=True)
    outcomes = {item["query"]: [] for item in eval_set}
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {}
            for item in eval_set:
                for _ in range(args.runs):
                    future = pool.submit(run_query, item["query"], args.model, args.timeout, workdir,
                                         args.skill, args.max_tool_calls)
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
