#!/usr/bin/env python3
"""
One-touch publish for the Faeblheim Codex.

What it does:
1) Verifies git and MkDocs are available.
2) Builds the site before committing, so broken docs do not get pushed.
3) Stages all changes.
4) Commits if there are staged changes.
5) Pushes the current branch.
6) Deploys to GitHub Pages with MkDocs gh-deploy.

Requirements:
- Run from the folder containing mkdocs.example.yml.
- git must be installed and authenticated for the GitHub remote.
- MkDocs and the configured plugins must be installed in the active Python environment.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MKDOCS_YML = ROOT / "mkdocs.example.yml"
SITE_DIR = ROOT.parent / "_site_faeblheim"


def run(cmd, check=True):
    print(f"\n> {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, cwd=ROOT, check=check, text=True).returncode
    except subprocess.CalledProcessError as exc:
        print(f"\n[ERROR] Command failed with exit code {exc.returncode}: {' '.join(cmd)}")
        sys.exit(exc.returncode)


def output(cmd):
    return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()


def has_staged_changes():
    return subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 1


def current_branch():
    return output(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def mkdocs_command():
    if shutil.which("mkdocs"):
        return ["mkdocs"]

    candidates = [["python", "-m", "mkdocs"], ["py", "-m", "mkdocs"]]
    for candidate in candidates:
        result = subprocess.run(
            candidate + ["--version"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        if result.returncode == 0:
            return candidate

    print(
        "\n[ERROR] MkDocs is not available. Install the site toolchain first, for example:\n"
        "  python -m pip install mkdocs mkdocs-material mkdocs-awesome-pages-plugin mkdocs-roamlinks-plugin"
    )
    sys.exit(2)


def ensure_prereqs():
    if not MKDOCS_YML.exists():
        print("[ERROR] mkdocs.example.yml not found next to this script.")
        sys.exit(2)

    if not shutil.which("git"):
        print("[ERROR] git is not installed or not on PATH.")
        sys.exit(2)

    rc = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    ).returncode
    if rc != 0:
        print("[ERROR] This folder is not a git repository.")
        sys.exit(2)


def temporary_mkdocs_config():
    """Create a MkDocs config outside docs_dir for MkDocs 1.6+."""
    config = MKDOCS_YML.read_text(encoding="utf-8")
    lines = []
    for line in config.splitlines():
        if line.startswith("docs_dir:"):
            lines.append(f'docs_dir: "{ROOT.as_posix()}"')
        elif line.startswith("site_dir:"):
            lines.append(f'site_dir: "{SITE_DIR.as_posix()}"')
        else:
            lines.append(line)

    tmpdir = tempfile.TemporaryDirectory(prefix="faeblheim-mkdocs-")
    tmp_path = Path(tmpdir.name) / "mkdocs.yml"
    tmp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmpdir, tmp_path


def main():
    os.chdir(ROOT)
    print("== Faeblheim Codex: Deploy ==")

    ensure_prereqs()
    mkdocs = mkdocs_command()
    tmp_config_dir, mkdocs_yml = temporary_mkdocs_config()

    try:
        print("\n== Building MkDocs site ==")
        run(mkdocs + ["build", "-f", str(mkdocs_yml)], check=True)

        run(["git", "add", "-A"], check=True)

        if has_staged_changes():
            msg = f"Codex auto-deploy {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            if len(sys.argv) > 1:
                msg = " ".join(sys.argv[1:])
            run(["git", "commit", "-m", msg], check=True)
        else:
            print("No changes staged; skipping commit.")

        branch = current_branch()
        print(f"\n== Pushing branch: {branch} ==")
        run(["git", "push"], check=True)

        print("\n== Deploying to GitHub Pages (gh-pages) ==")
        run(mkdocs + ["gh-deploy", "-f", str(mkdocs_yml), "--force"], check=True)

        print("\nDone. Your site should update shortly on GitHub Pages.")
    finally:
        tmp_config_dir.cleanup()


if __name__ == "__main__":
    main()
