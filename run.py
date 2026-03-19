#!/usr/bin/env python3
"""Auto-Scientist: autonomous research loop powered by Claude Code CLI."""

import argparse
import os
import re
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml


# ── Helpers ──────────────────────────────────────────────────────────────────

def run_claude(skill_path, round_num, extra_context, allowed_tools, max_tokens, project_dir):
    """Run claude CLI with a skill prompt."""
    full_path = os.path.join(project_dir, skill_path)
    with open(full_path, "r", encoding="utf-8") as f:
        skill_content = f.read()

    prompt = (
        f"{skill_content}\n\n---\n\n"
        f"Current round number: {round_num}\n"
        f"Project directory: {project_dir}\n"
        f"{extra_context}"
    )

    cmd = [
        "claude", "-p", prompt,
        "--allowedTools", allowed_tools,
        "--max-tokens", str(max_tokens),
    ]

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
            skill_path=".claude/skills/theorist/SKILL.md",
            round_num=round_num,
            extra_context=f"Output file: proposals/proposal_{padded}.md",
            allowed_tools="Read,Write,Glob,Grep",
            max_tokens=16000,
            project_dir=project_dir,
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
            skill_path=".claude/skills/critic/SKILL.md",
            round_num=round_num,
            extra_context=(
                f"Proposal to review: proposals/proposal_{padded}.md\n"
                f"Output file: reviews/review_{padded}.md"
            ),
            allowed_tools="Read,Write,Glob,Grep",
            max_tokens=8000,
            project_dir=project_dir,
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
            skill_path=".claude/skills/synthesizer/SKILL.md",
            round_num=round_num,
            extra_context=(
                f"Latest proposal: proposals/proposal_{padded}.md\n"
                f"Latest review: reviews/review_{padded}.md"
            ),
            allowed_tools="Read,Write,Glob,Grep,Bash",
            max_tokens=8000,
            project_dir=project_dir,
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
