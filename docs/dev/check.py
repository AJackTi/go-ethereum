#!/usr/bin/env python3
"""Validate the developer handbook against the code it describes.

The handbook is only worth reading if its claims are still true. Four checks, all offline and
dependency-free:

  1. Tours       — every `.tours/*.tour` is valid JSON, every step's file exists, and every step's
                   `pattern` still matches that file. This is what catches a refactor silently
                   pointing a walkthrough at the wrong code.
  2. Paths       — every `path/to/file.go` mentioned in backticks actually exists.
  3. Links       — every relative Markdown link resolves in a plain git checkout (the GitHub view).
  4. Mirror      — the `vi/` tree mirrors `en/` file for file, and each pair has the same number of
                   `##` sections, so a translation cannot silently drift.

Run from the repository root:

    python3 docs/dev/check.py            # exits non-zero on the first failing check
    python3 docs/dev/check.py --quiet    # only print failures

The website build (`mkdocs build --strict`) covers a different surface: links between rendered
pages. This script covers the checkout, the tours, and the code references. Run both.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "dev"
TOURS = ROOT / ".tours"

# Paths that only exist after a build or a test download; referencing them is correct.
GENERATED = {"build/bin", "tests/spec-tests", "site"}

# Pages the site build generates, mapped to the file they are generated from. In a fresh checkout
# — which is what CI has when this script runs, before mkdocs — the target does not exist yet, so
# a reference to it is satisfied by its source instead.
GENERATED_PAGES = {
    (DOCS / "en" / "architecture.md").resolve(): ROOT / "ARCHITECTURE.md",
}


def resolves(path: Path) -> bool:
    """True if the path exists, or is a generated page whose source exists."""
    if path.exists():
        return True
    source = GENERATED_PAGES.get(path.resolve())
    return source is not None and source.exists()


PATH_RE = re.compile(r"`([a-zA-Z_][\w./\-]*\.go|[a-z][\w\-]*(?:/[\w\-.]+)+/?)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SECTION_RE = re.compile(r"^## +(.+)$", re.MULTILINE)


def markdown_files() -> list[Path]:
    files = [ROOT / "ARCHITECTURE.md", ROOT / "CONTRIBUTING.md"]
    files += sorted(DOCS.rglob("*.md"))
    return [f for f in files if f.is_file()]


def tour_files() -> list[Path]:
    return sorted(TOURS.glob("*.tour"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def check_tours() -> list[str]:
    """Tour steps must point at code that still exists and still matches."""
    errors: list[str] = []
    steps = 0
    for tour in tour_files():
        try:
            data = json.loads(tour.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            errors.append(f"{rel(tour)}: invalid JSON — {err}")
            continue
        if "title" not in data or "steps" not in data:
            errors.append(f"{rel(tour)}: missing required 'title' or 'steps'")
            continue
        for i, step in enumerate(data["steps"]):
            if "description" not in step:
                errors.append(f"{rel(tour)} step {i}: missing 'description'")
            target = step.get("file") or step.get("directory")
            if not target:
                continue  # content-only step
            steps += 1
            path = ROOT / target
            if not path.exists():
                errors.append(f"{rel(tour)} step {i}: no such file — {target}")
                continue
            if "line" in step and "pattern" not in step:
                errors.append(
                    f"{rel(tour)} step {i}: anchored by line number; use 'pattern' so the step "
                    f"survives refactors"
                )
                continue
            pattern = step.get("pattern")
            if not pattern:
                continue
            if not re.search(pattern, path.read_text(encoding="utf-8")):
                errors.append(f"{rel(tour)} step {i}: pattern no longer matches {target} — /{pattern}/")
    return errors + [] if errors else [f"__ok__{len(tour_files())} tours, {steps} anchored steps"]


def check_paths() -> list[str]:
    """Every `pkg/file.go` mentioned in the prose must exist."""
    errors: list[str] = []
    repo_filenames = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "site", "node_modules", ".venv")]
        repo_filenames.update(filenames)

    checked = 0
    sources: list[tuple[Path, str]] = [(f, f.read_text(encoding="utf-8")) for f in markdown_files()]
    for tour in tour_files():
        try:
            data = json.loads(tour.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # already reported by check_tours
        text = " ".join(f"{s.get('description', '')} {s.get('file', '')}" for s in data["steps"])
        sources.append((tour, text))

    for path, text in sources:
        for match in sorted(set(PATH_RE.findall(text))):
            if "://" in match:
                continue
            target = match.rstrip("/")
            checked += 1
            if target in GENERATED:
                continue
            if resolves(ROOT / target) or resolves(path.parent / target):
                continue
            if "*" in target and (list(ROOT.glob(target)) or list(path.parent.glob(target))):
                continue
            if "/" not in target and target in repo_filenames:
                continue  # bare filename used in the context of its package
            errors.append(f"{rel(path)}: references a path that does not exist — {target}")
    return errors or [f"__ok__{checked} code path references"]


def check_links() -> list[str]:
    """Relative Markdown links must work when browsing the repository itself."""
    errors: list[str] = []
    checked = 0
    for path in markdown_files():
        for text, link in LINK_RE.findall(path.read_text(encoding="utf-8")):
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            checked += 1
            if not resolves(path.parent / link.split("#")[0]):
                errors.append(f"{rel(path)}: broken link [{text}]({link})")
    return errors or [f"__ok__{checked} relative links"]


def check_mirror() -> list[str]:
    """`vi/` must mirror `en/`, file for file and section for section."""
    en, vi = DOCS / "en", DOCS / "vi"
    if not en.is_dir() or not vi.is_dir():
        return [f"missing language tree: {rel(en)} or {rel(vi)}"]

    generated = {"architecture.md"}  # built from the repo-root ARCHITECTURE.md
    en_files = {f.name for f in en.glob("*.md")} - generated
    vi_files = {f.name for f in vi.glob("*.md")} - generated

    errors: list[str] = []
    for name in sorted(en_files - vi_files):
        errors.append(f"docs/dev/vi/{name} is missing (docs/dev/en/{name} exists)")
    for name in sorted(vi_files - en_files):
        errors.append(f"docs/dev/en/{name} is missing (docs/dev/vi/{name} exists)")

    for name in sorted(en_files & vi_files):
        en_sections = SECTION_RE.findall((en / name).read_text(encoding="utf-8"))
        vi_sections = SECTION_RE.findall((vi / name).read_text(encoding="utf-8"))
        if len(en_sections) != len(vi_sections):
            errors.append(
                f"{name}: en has {len(en_sections)} '##' sections, vi has {len(vi_sections)} — "
                f"the translation has drifted"
            )
    return errors or [f"__ok__{len(en_files)} page pairs mirrored"]


CHECKS = [
    ("tours", check_tours),
    ("code paths", check_paths),
    ("links", check_links),
    ("en/vi mirror", check_mirror),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--quiet", action="store_true", help="only print failures")
    args = parser.parse_args()

    failed = False
    for name, check in CHECKS:
        results = check()
        ok = [r for r in results if r.startswith("__ok__")]
        problems = [r for r in results if not r.startswith("__ok__")]
        if problems:
            failed = True
            print(f"FAIL  {name}")
            for problem in problems:
                print(f"        {problem}")
        elif not args.quiet:
            print(f"ok    {name:<14} {ok[0].removeprefix('__ok__')}")

    if failed:
        print("\nhandbook check failed", file=sys.stderr)
        return 1
    if not args.quiet:
        print("\nhandbook check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
