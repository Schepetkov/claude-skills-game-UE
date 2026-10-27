#!/usr/bin/env python3
"""Checks the skills repo before a merge. Standard library only.

    python tools/check_skills.py                 # whole repo
    python tools/check_skills.py --base origin/main   # also list executable files changed since base

Fails (exit 1) on:
  - SKILL.md without frontmatter, or `name` not matching its directory, or empty `description`
  - a field note without the required frontmatter (see CONTRIBUTING.md, "Field notes")
  - personal paths, secrets or .env files anywhere in the tree
Warns on:
  - SKILL.md longer than 250 lines (move tables into references/)
  - changed files under hooks/, scripts/, templates/, tools/ or install.* - code that runs on
    every user's machine, reviewed line by line before merge
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

TEXT_EXT = {".md", ".py", ".sh", ".ps1", ".h", ".cpp", ".json", ".yml", ".yaml", ".txt", ".ini", ".cs", ".toml"}

# Placeholders like C:\Users\<you> or /home/<user> are fine; a real name is not.
PERSONAL = [
    (re.compile(r"[A-Za-z]:\\+Users\\+(?!<|\{|%|\$|Public\b|Default\b)[A-Za-z0-9._-]+"), "Windows user path"),
    (re.compile(r"(?<![\w.])/Users/(?!<|\{|\$|Shared\b)[A-Za-z0-9._-]+"), "macOS user path"),
    (re.compile(r"(?<![\w.])/home/(?!<|\{|\$|runner\b)[A-Za-z0-9._-]+"), "Linux home path"),
]
SECRETS = [
    (re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{24,}"), "API key (sk-...)"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS key"),
    (re.compile(r"\bmsy_[A-Za-z0-9]{20,}"), "Meshy key"),
    (re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{20,}"), "Slack token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
]

NOTE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
NOTE_KEYS = ("symptom", "engine", "status", "date")
NOTE_STATUS = ("observed", "verified")
EXECUTABLE_DIRS = ("hooks/", "scripts/", "templates/", "tools/", ".github/")

errors: list[str] = []
warnings: list[str] = []


def frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fields: dict[str, str] = {}
    key = None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def check_skills() -> None:
    for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{rel(skill_dir)}: no SKILL.md")
            continue
        fm = frontmatter(skill_md)
        if fm is None:
            errors.append(f"{rel(skill_md)}: no frontmatter")
            continue
        if fm.get("name") != skill_dir.name:
            errors.append(f"{rel(skill_md)}: name '{fm.get('name')}' does not match directory '{skill_dir.name}'")
        if len(fm.get("description", "").strip(">- ")) < 40:
            errors.append(f"{rel(skill_md)}: description missing or too short to trigger on")
        lines = skill_md.read_text(encoding="utf-8", errors="replace").count("\n")
        if lines > 250:
            warnings.append(f"{rel(skill_md)}: {lines} lines - move deep tables into references/")
        check_field_notes(skill_dir / "field-notes")


def check_field_notes(notes_dir: Path) -> None:
    if not notes_dir.is_dir():
        return
    for note in sorted(notes_dir.iterdir()):
        if note.name == "README.md":
            continue
        if not NOTE_NAME.match(note.name):
            errors.append(f"{rel(note)}: name it YYYY-MM-DD-short-slug.md")
            continue
        fm = frontmatter(note)
        if fm is None:
            errors.append(f"{rel(note)}: no frontmatter")
            continue
        for k in NOTE_KEYS:
            if not fm.get(k):
                errors.append(f"{rel(note)}: frontmatter needs '{k}'")
        status = fm.get("status", "")
        if status and status not in NOTE_STATUS:
            errors.append(f"{rel(note)}: status must be one of {', '.join(NOTE_STATUS)}")
        if status == "verified" and not fm.get("source"):
            errors.append(f"{rel(note)}: a verified note needs 'source' (engine path, doc URL or measurement)")


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        return [ROOT / p for p in out.splitlines() if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def check_privacy() -> None:
    for path in tracked_files():
        if not path.is_file():
            continue
        name = path.name
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            errors.append(f"{rel(path)}: .env file in the tree")
            continue
        if path.suffix.lower() not in TEXT_EXT or path == Path(__file__).resolve():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for rx, what in PERSONAL + SECRETS:
                if rx.search(line):
                    errors.append(f"{rel(path)}:{n}: {what}: {line.strip()[:120]}")


def report_executable(base: str) -> None:
    try:
        out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        warnings.append(f"could not diff against {base}: {e}")
        return
    for f in out.splitlines():
        if any(d in f for d in EXECUTABLE_DIRS) or f.startswith("install."):
            warnings.append(f"{f}: runs on users' machines - review every line before merging")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="git ref to diff against, e.g. origin/main")
    args = ap.parse_args()

    check_skills()
    check_privacy()
    if args.base:
        report_executable(args.base)

    gha = "GITHUB_ACTIONS" in __import__("os").environ
    for w in warnings:
        print(f"::warning::{w}" if gha else f"warning: {w}")
    for e in errors:
        print(f"::error::{e}" if gha else f"error: {e}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
