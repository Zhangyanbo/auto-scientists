#!/usr/bin/env python3
"""Auto-Scientist: autonomous research loop powered by Claude Code CLI."""

import argparse
import json
import os
import re
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml


# ── Helpers ──────────────────────────────────────────────────────────────────

INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(INSTALL_DIR, "skills")

DIM = "\033[2m"
RESET = "\033[0m"


def load_skill(skill_name):
    """Load skill content from the skills/ directory next to this script."""
    skill_path = os.path.join(SKILLS_DIR, f"{skill_name}.md")
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Strip YAML frontmatter (metadata for Claude Code, not needed in prompt)
    stripped = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, count=1, flags=re.DOTALL)
    return stripped


def run_claude(skill_name, round_num, extra_context, project_dir, model="sonnet", debug=False):
    """Run claude CLI with skill instructions passed directly in the prompt."""
    skill_content = load_skill(skill_name)
    prompt = (
        f"{skill_content}\n\n"
        f"Current round number: {round_num}\n"
        f"Project directory: {project_dir}\n"
        f"{extra_context}"
    )

    cmd = ["claude", "-p", prompt, "--model", model, "--dangerously-skip-permissions"]

    if debug:
        print(f"{DIM}  ┌─ {skill_name} ({model}) ─────────────────────{RESET}")
        stream_cmd = cmd + ["--output-format", "stream-json", "--verbose"]
        proc = subprocess.Popen(
            stream_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=project_dir,
        )
        full_result = ""
        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            mtype = msg.get("type", "")
            if mtype == "assistant":
                # Extract text from content blocks
                content = msg.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                text = block.get("text", "")
                                if text:
                                    for tl in text.splitlines():
                                        print(f"  │ {tl}", flush=True)
                                    full_result += text
                            elif block.get("type") == "tool_use":
                                tool = block.get("name", "?")
                                inp = block.get("input", {})
                                # Show tool name + compact summary of input
                                summary = ""
                                if "command" in inp:
                                    summary = f" $ {inp['command'][:80]}"
                                elif "file_path" in inp:
                                    summary = f" {inp['file_path']}"
                                elif "pattern" in inp:
                                    summary = f" {inp['pattern']}"
                                elif "skill_name" in inp:
                                    summary = f" {inp['skill_name']}"
                                print(f"{DIM}  │ 🔧 {tool}{summary}{RESET}", flush=True)
                elif isinstance(content, str) and content:
                    for tl in content.splitlines():
                        print(f"  │ {tl}", flush=True)
                    full_result += content
            elif mtype == "result":
                content = msg.get("result", "")
                if content:
                    full_result = content
                cost = msg.get("cost_usd")
                duration = msg.get("duration_ms")
                info_parts = []
                if cost is not None:
                    info_parts.append(f"${cost:.4f}")
                if duration is not None:
                    info_parts.append(f"{duration / 1000:.1f}s")
                if info_parts:
                    print(f"{DIM}  │ ⏱  {' · '.join(info_parts)}{RESET}", flush=True)
            elif mtype in ("system", "user", "rate_limit_event"):
                pass  # known noise, skip
            else:
                # Truly unknown message type — print raw for debugging
                print(f"{DIM}  │ [{mtype}] {line[:300]}{RESET}", flush=True)
        stderr = proc.stderr.read()
        proc.wait()
        status = "✓" if proc.returncode == 0 else f"✗ exit {proc.returncode}"
        print(f"{DIM}  └─ {status} ─────────────────────────────────{RESET}")
        result = subprocess.CompletedProcess(
            args=stream_cmd, returncode=proc.returncode,
            stdout=full_result, stderr=stderr,
        )
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
    return result


def parse_review_scores(review_path):
    """Parse YAML frontmatter from a review file and return scores.

    Returns a dict with keys:
        user_criteria_average  (float or None)
        commitment_average     (float or None)
        verdict                (str  or None)
    """
    scores = {
        "user_criteria_average": None,
        "commitment_average": None,
        "verdict": None,
    }
    if not os.path.isfile(review_path):
        return scores

    with open(review_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?\n)---", content, re.DOTALL)
    if not match:
        return scores

    try:
        front = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return scores

    if not isinstance(front, dict):
        return scores

    for key in scores:
        if key in front:
            scores[key] = front[key]

    return scores


def get_last_commit_message(project_dir):
    """Return the subject line of the most recent git commit."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%s", "-1"],
            capture_output=True, text=True, cwd=project_dir,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return ""


def update_progress_chart(history, project_dir):
    """Generate / update syntheses/progress.png with score history.

    Parameters
    ----------
    history : list[dict]
        Each dict has keys: round, user_criteria_average, commitment_average,
        commit_msg.
    """
    if not history:
        return

    syntheses_dir = os.path.join(project_dir, "syntheses")
    os.makedirs(syntheses_dir, exist_ok=True)
    chart_path = os.path.join(syntheses_dir, "progress.png")

    rounds = [h["round"] for h in history]
    user_scores = [h["user_criteria_average"] for h in history]
    commit_scores = [h["commitment_average"] for h in history]

    # Replace None with 0 for plotting; track which are valid
    def safe(val):
        return val if val is not None else 0

    user_plot = [safe(v) for v in user_scores]
    commit_plot = [safe(v) for v in commit_scores]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(rounds, user_plot, "o-", color="royalblue", label="User Criteria Average")
    ax.plot(rounds, commit_plot, "s-", color="darkorange", label="Commitment Average")

    # Annotate significant changes (>10 points from previous round)
    for idx in range(1, len(history)):
        for series, values in [("user", user_plot), ("commit", commit_plot)]:
            prev = values[idx - 1]
            curr = values[idx]
            if abs(curr - prev) > 10:
                msg = history[idx].get("commit_msg", "")
                if msg:
                    # Truncate long messages
                    label = msg if len(msg) <= 40 else msg[:37] + "..."
                    ax.annotate(
                        label,
                        xy=(rounds[idx], curr),
                        xytext=(0, 12),
                        textcoords="offset points",
                        fontsize=7,
                        ha="center",
                        arrowprops=dict(arrowstyle="->", color="gray", lw=0.5),
                    )
                    break  # one annotation per round is enough

    ax.set_xlabel("Round")
    ax.set_ylabel("Score (0-100)")
    ax.set_ylim(0, 100)
    ax.set_title("Research Progress")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    # Integer ticks for rounds
    ax.set_xticks(rounds)

    fig.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)


# ── Banner helpers ───────────────────────────────────────────────────────────

def print_banner(round_num, total_rounds):
    print()
    print("\u2550" * 38)
    print(f"  Round {round_num:03d} / {total_rounds:03d}")
    print("\u2550" * 38)


def print_phase(phase, total, message):
    print(f"[Phase {phase}/{total}] {message}")


def print_ok(message):
    print(f"  \u2713 {message}")


def print_err(message):
    print(f"  \u2717 {message}", file=sys.stderr)


def print_separator():
    print("\u2500" * 38)


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Auto-Scientist research loop")
    parser.add_argument("--rounds", type=int, default=10, help="Number of research rounds (default: 10)")
    parser.add_argument("--start", type=int, default=1, help="Starting round number, for resuming (default: 1)")
    parser.add_argument("--project-dir", type=str, default=os.getcwd(), help="Project root directory (default: cwd)")
    parser.add_argument("--model", type=str, default="sonnet", help="Claude model to use (default: sonnet)")
    parser.add_argument("--debug", action="store_true", help="Stream Claude output in real-time for debugging")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    total_rounds = args.rounds
    start = args.start

    # Ensure required directories exist
    for d in ("proposals", "reviews", "syntheses", "memory", "config"):
        os.makedirs(os.path.join(project_dir, d), exist_ok=True)

    # Accumulate score history (load any existing data from prior runs would
    # go here; for now we start fresh each invocation).
    history = []

    for round_num in range(start, start + total_rounds):
        padded = f"{round_num:03d}"
        print_banner(round_num, start + total_rounds - 1)

        # ── Phase 1: Theorist ────────────────────────────────────────────
        print_phase(1, 3, "Theorist generating proposal...")
        result = run_claude(
            skill_name="theorist",
            round_num=round_num,
            extra_context=f"Output file: proposals/proposal_{padded}.md",
            project_dir=project_dir,
            model=args.model,
            debug=args.debug,
        )
        proposal_path = os.path.join(project_dir, f"proposals/proposal_{padded}.md")
        if result.returncode != 0:
            print_err(f"Theorist failed (exit {result.returncode})")
            if result.stderr:
                print_err(result.stderr[:500])
            print_separator()
            continue
        if os.path.isfile(proposal_path):
            print_ok(f"Proposal saved: proposals/proposal_{padded}.md")
        else:
            print_err(f"Theorist exited 0 but proposals/proposal_{padded}.md not found")

        # ── Phase 2: Critic ──────────────────────────────────────────────
        print_phase(2, 3, "Critic reviewing proposal...")
        result = run_claude(
            skill_name="critic",
            round_num=round_num,
            extra_context=(
                f"Proposal to review: proposals/proposal_{padded}.md\n"
                f"Output file: reviews/review_{padded}.md"
            ),
            project_dir=project_dir,
            model=args.model,
            debug=args.debug,
        )
        review_path = os.path.join(project_dir, f"reviews/review_{padded}.md")
        if result.returncode != 0:
            print_err(f"Critic failed (exit {result.returncode})")
            if result.stderr:
                print_err(result.stderr[:500])
            print_separator()
            continue
        if os.path.isfile(review_path):
            print_ok(f"Review saved: reviews/review_{padded}.md")
        else:
            print_err(f"Critic exited 0 but reviews/review_{padded}.md not found")

        # Parse scores
        scores = parse_review_scores(review_path)
        uc = scores["user_criteria_average"]
        cm = scores["commitment_average"]
        vd = scores["verdict"]
        uc_str = f"{uc:.1f}" if uc is not None else "N/A"
        cm_str = f"{cm:.1f}" if cm is not None else "N/A"
        vd_str = vd if vd is not None else "N/A"
        print(f"  Scores \u2014 User Criteria: {uc_str} | Commitments: {cm_str} | Verdict: {vd_str}")

        # ── Phase 3: Synthesizer ─────────────────────────────────────────
        print_phase(3, 3, "Synthesizer updating memory...")
        result = run_claude(
            skill_name="synthesizer",
            round_num=round_num,
            extra_context=(
                f"Latest proposal: proposals/proposal_{padded}.md\n"
                f"Latest review: reviews/review_{padded}.md"
            ),
            project_dir=project_dir,
            model=args.model,
            debug=args.debug,
        )
        if result.returncode != 0:
            print_err(f"Synthesizer failed (exit {result.returncode})")
            if result.stderr:
                print_err(result.stderr[:500])
            print_separator()
            continue
        print_ok("Lessons updated, directive set")

        # Grab the commit message the synthesizer just created
        commit_msg = get_last_commit_message(project_dir)
        if commit_msg:
            print_ok(f"Git commit: {commit_msg}")

        # ── Update chart ─────────────────────────────────────────────────
        history.append({
            "round": round_num,
            "user_criteria_average": uc,
            "commitment_average": cm,
            "commit_msg": commit_msg,
        })
        try:
            update_progress_chart(history, project_dir)
        except Exception as exc:
            print_err(f"Chart update failed: {exc}")

        print_separator()

    # Final summary
    print()
    print(f"Completed {total_rounds} rounds ({start} .. {start + total_rounds - 1}).")
    valid = [h for h in history if h["user_criteria_average"] is not None]
    if valid:
        best = max(valid, key=lambda h: h["user_criteria_average"])
        print(f"Best user-criteria score: {best['user_criteria_average']:.1f} (round {best['round']})")
    print()


if __name__ == "__main__":
    main()
