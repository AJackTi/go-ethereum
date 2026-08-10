"""MkDocs hooks for the developer handbook.

Three jobs:

1. `ARCHITECTURE.md` lives at the repository root, which is the convention every reader (and most
   tooling) expects. MkDocs only sees files under `docs_dir`, so before the build we copy it to
   `docs/dev/en/architecture.md`. That copy is generated, git-ignored, and rewritten on every
   build — never edit it, edit the root file.

   (It is copied rather than injected as a virtual file because the i18n plugin needs every file
   to have a real path on disk.)

2. The Markdown is written to be correct when browsed on GitHub, where links are relative to the
   repo root. On the published site those same links must resolve differently. Rather than
   breaking one view to serve the other, we rewrite the handful of known link targets at build
   time.

3. That generated copy has no git history of its own, so the revision-date plugin would stamp it
   with the build date and have it claim to change on every rebuild. The last hook puts the source
   file's real commit date back.

Nothing here modifies hand-written files.
"""

import pathlib
import re
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
GITHUB_BLOB = "https://github.com/AJackTi/go-ethereum/blob/master"
GITHUB_TREE = "https://github.com/AJackTi/go-ethereum/tree/master"

GENERATED_BANNER = (
    "<!-- Generated at build time from ARCHITECTURE.md at the repository root. "
    "Do not edit; edit that file instead. -->\n\n"
)

# Links in the root ARCHITECTURE.md are relative to the repository root.
ARCHITECTURE_REWRITES = [
    ("docs/dev/vi/architecture.md", "../vi/architecture.md"),
    ("docs/dev/en/getting-started.md", "getting-started.md"),
    ("docs/dev/en/start-here.md", "start-here.md"),
    ("docs/dev/en/learning-path.md", "learning-path.md"),
    ("docs/dev/en/run-a-node.md", "run-a-node.md"),
    ("docs/dev/en/debugging.md", "debugging.md"),
    ("docs/dev/en/glossary.md", "glossary.md"),
    ("docs/dev/en/subsystems.md", "subsystems.md"),
    ("CONTRIBUTING.md", GITHUB_BLOB + "/CONTRIBUTING.md"),
    ("docs/dev/adr/", "../adr/index.md"),
    ("docs/dev/adr", "../adr/index.md"),
    ("docs/dev/README.md", "index.md"),
    (".tours/", GITHUB_TREE + "/.tours"),
    (".tours", GITHUB_TREE + "/.tours"),
]

# Links that only resolve inside a git checkout, on any page of the handbook.
PAGE_REWRITES = [
    ("../../../ARCHITECTURE.md", "../en/architecture.md"),
    ("../../../.tours/", GITHUB_TREE + "/.tours"),
    ("../../../.tours", GITHUB_TREE + "/.tours"),
    ("../../../AGENTS.md", GITHUB_BLOB + "/AGENTS.md"),
    ("../../../README.md", GITHUB_BLOB + "/README.md"),
    ("../README.md", "index.md"),
    ("../../../CONTRIBUTING.md", GITHUB_BLOB + "/CONTRIBUTING.md"),
    ("../adr", "../adr/index.md"),
]


def _rewrite(markdown: str, rules) -> str:
    def replace(match: re.Match) -> str:
        text, target = match.group(1), match.group(2)
        for old, new in rules:
            if target == old:
                return f"[{text}]({new})"
        return match.group(0)

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace, markdown)


def _rewrite_cross_language(markdown: str, src_path: str, directory_urls: bool) -> str:
    """Fix links that point at the other language.

    In the checkout the two trees sit side by side (`../vi/start-here.md`). On the site the
    default language is served from the root and `vi` from `/vi/`, so the number of hops differs
    per direction — and differs again in the offline build, where directory URLs are turned off.

    The result is emitted as a raw anchor: MkDocs only validates Markdown links, and these
    targets live in the *other* language build, which the current one cannot see.
    """
    if directory_urls:
        to_en, to_vi = r'<a href="../../\2/">\1</a>', r'<a href="../vi/\2/">\1</a>'
    else:
        to_en, to_vi = r'<a href="../\2.html">\1</a>', r'<a href="vi/\2.html">\1</a>'

    if "/vi/" in src_path:
        return re.sub(r"\[([^\]]+)\]\((?:\.\./)+en/([\w.-]+)\.md\)", to_en, markdown)
    if "/en/" in src_path:
        return re.sub(r"\[([^\]]+)\]\((?:\.\./)+vi/([\w.-]+)\.md\)", to_vi, markdown)
    return markdown


def on_config(config):
    """Refresh the generated English architecture page from the repo-root file."""
    source = REPO_ROOT / "ARCHITECTURE.md"
    if not source.is_file():
        return config

    target = pathlib.Path(config.docs_dir) / "en" / "architecture.md"
    content = GENERATED_BANNER + _rewrite(source.read_text(encoding="utf-8"), ARCHITECTURE_REWRITES)
    if not target.is_file() or target.read_text(encoding="utf-8") != content:
        target.write_text(content, encoding="utf-8")
    return config


def on_page_markdown(markdown, page, config, files):
    markdown = _rewrite(markdown, PAGE_REWRITES)
    return _rewrite_cross_language(
        markdown, page.file.abs_src_path or "", config.use_directory_urls
    )


def _last_commit_timestamp(path: str):
    """Unix timestamp of the last commit touching `path`, or None outside a usable checkout."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    stamp = result.stdout.strip()
    return int(stamp) if result.returncode == 0 and stamp.isdigit() else None


def on_page_context(context, page, config, nav):
    """Stamp the generated architecture page with its *source* file's date.

    The page is written at build time and git-ignored, so it has no history of its own — the
    revision-date plugin falls back to the build date and the page claims to have been updated
    every time anything triggers a rebuild. The honest date is the one on `ARCHITECTURE.md`.

    Degrades to the plugin's own behaviour if the plugin is absent or git is unavailable.
    """
    if (page.file.src_path or "").replace("\\", "/").rsplit("/", 1)[-1] != "architecture.md":
        return context
    if not page.meta.get("git_revision_date_localized"):
        return context  # the plugin is disabled; nothing to correct
    if page.file.abs_src_path and pathlib.Path(page.file.abs_src_path).is_relative_to(
        pathlib.Path(config.docs_dir) / "vi"
    ):
        return context  # the Vietnamese page is hand-written and tracked; its date is real

    timestamp = _last_commit_timestamp("ARCHITECTURE.md")
    if timestamp is None:
        return context
    try:
        from mkdocs_git_revision_date_localized_plugin.dates import get_date_formats
    except ImportError:
        return context

    plugin = config.plugins.get("git-revision-date-localized")
    locale = getattr(page.file, "locale", None) or "en"
    time_zone = plugin.config.get("timezone", "UTC") if plugin else "UTC"
    page.meta["git_revision_date_localized"] = get_date_formats(
        timestamp, locale=locale, time_zone=time_zone
    )["date"]
    return context
