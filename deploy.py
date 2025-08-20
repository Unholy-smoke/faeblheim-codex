#!/usr/bin/env python3
"""
deploy.py — one-touch publish for the Faeblheim Codex (Option A layout).

What it does:
1) Stages any changes in subfolders.
2) Commits (if there are changes).
3) Pushes to your current git branch.
4) Builds the site to catch errors.
5) Deploys to GitHub Pages with: mkdocs gh-deploy -f ./mkdocs.example.yml --force

Requirements:
- Run this from the folder that contains mkdocs.example.yml (or just double-click if associated with Python).
- git and mkdocs must be installed and on PATH.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MKDOCS_YML = ROOT / "mkdocs.example.yml"

def run(cmd, check=True):
    print(f"\n> {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, cwd=ROOT, check=check, text=True)
        return res.returncode
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed with exit code {e.returncode}: {' '.join(cmd)}")
        sys.exit(e.returncode)

def has_staged_changes():
    # returns True if there are staged changes (after git add -A)
    rc = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode
    return rc == 1  # 1 means differences, 0 means none

def ensure_prereqs():
    if not MKDOCS_YML.exists():
        print("[ERROR] mkdocs.example.yml not found next to this script.")
        sys.exit(2)
    # quick git repo check
    rc = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    if rc != 0:
        print("[ERROR] This folder is not a git repository. Run `git init` and add a remote first.")
        sys.exit(2)

def current_branch():
    out = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip()
    return out

def main():
    os.chdir(ROOT)
    print("== Faeblheim Codex: Deploy ==")
    ensure_prereqs()

    # Stage everything
    run(["git", "add", "-A"], check=True)

    # Commit if there are staged changes
    if has_staged_changes():
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"Codex auto-deploy {ts}"
        # allow a custom message as args
        if len(sys.argv) > 1:
            msg = " ".join(sys.argv[1:])
        run(["git", "commit", "-m", msg], check=True)
    else:
        print("No changes staged; skipping commit.")

    # Push to current branch
    branch = current_branch()
    print(f"Pushing branch: {branch}")
    run(["git", "push"], check=True)

    # Build to catch errors early
    print("\n== Building MkDocs site ==")
    run(["mkdocs", "build", "-f", "./mkdocs.example.yml"], check=True)

    # Deploy to GitHub Pages
    print("\n== Deploying to GitHub Pages (gh-pages) ==")
    run(["mkdocs", "gh-deploy", "-f", "./mkdocs.example.yml", "--force"], check=True)

    print("\n✅ Done. Your site should update shortly on GitHub Pages.")

if __name__ == "__main__":
    main()
