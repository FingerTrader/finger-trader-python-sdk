"""Keep Markdown links and documented Python snippets valid."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = [
    ROOT / "README.md",
    *sorted((ROOT / "docs").glob("*.md")),
    ROOT / "examples/README.md",
]


def test_relative_markdown_links_resolve() -> None:
    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    missing = []
    for markdown_file in MARKDOWN_FILES:
        for target in link_pattern.findall(markdown_file.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            file_part = target.split("#", 1)[0]
            if file_part and not (markdown_file.parent / file_part).resolve().exists():
                missing.append(f"{markdown_file.relative_to(ROOT)} -> {target}")
    assert not missing, "Broken Markdown links:\n" + "\n".join(missing)


def test_python_fenced_blocks_compile() -> None:
    failures = []
    pattern = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
    for markdown_file in MARKDOWN_FILES:
        snippets = pattern.findall(markdown_file.read_text(encoding="utf-8"))
        for index, source in enumerate(snippets, 1):
            try:
                compile(source, f"{markdown_file.relative_to(ROOT)}:python-block-{index}", "exec")
            except SyntaxError as exc:
                failures.append(f"{markdown_file.relative_to(ROOT)} block {index}: {exc}")
    assert not failures, "Invalid documented Python:\n" + "\n".join(failures)


def test_example_scripts_compile() -> None:
    for example in sorted((ROOT / "examples").glob("*.py")):
        compile(example.read_text(encoding="utf-8"), str(example.relative_to(ROOT)), "exec")
