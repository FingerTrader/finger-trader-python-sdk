"""Conservative Dart dependency gate, without resolving unreviewed packages.

Only reviewed SDK libraries are allowed. There are no approved third-party
packages in P0. Every reachable internal dependency is checked, including all
conditional branches. Platform/presentation adapters cannot be imported by core.
"""

import json
import re
from pathlib import Path

POLICY = Path("contracts/quant/v1/core-dependencies.json")


def tokens(source):
    """Lex literals/comments separately so commented imports cannot hide edges."""
    i = 0
    while i < len(source):
        if source[i].isspace():
            i += 1
        elif source.startswith("//", i):
            end = source.find("\n", i)
            i = len(source) if end < 0 else end + 1
        elif source.startswith("/*", i):
            depth = 1
            i += 2
            while i < len(source) and depth:
                if source.startswith("/*", i):
                    depth += 1
                    i += 2
                elif source.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated Dart comment")
        elif source[i] in "\"'" or (
            source[i] == "r" and i + 1 < len(source) and source[i + 1] in "\"'"
        ):
            raw = source[i] == "r"
            if raw:
                i += 1
            quote = source[i] * (3 if source.startswith(source[i] * 3, i) else 1)
            i += len(quote)
            start = i
            while i < len(source) and not source.startswith(quote, i):
                i += 2 if not raw and source[i] == "\\" else 1
            if i >= len(source):
                raise ValueError("unterminated Dart string")
            yield "string", source[start:i]
            i += len(quote)
        elif source[i].isalpha() or source[i] in "_$":
            start = i
            i += 1
            while i < len(source) and (source[i].isalnum() or source[i] in "_$"):
                i += 1
            yield "word", source[start:i]
        else:
            yield "symbol", source[i]
            i += 1


def dependency_uris(source):
    stream = iter(tokens(source))
    for kind, value in stream:
        if kind == "symbol" and value == "@":
            raise ValueError("annotated directive/header requires explicit dependency review")
        if kind != "word" or value not in {"library", "import", "export", "part"}:
            # Dart directives precede declarations; 'part' can also be an
            # ordinary identifier inside a class and must not be read as URI.
            return
        strings = []
        for next_kind, next_value in stream:
            if next_kind == "symbol" and next_value == ";":
                break
            if next_kind == "string":
                if "\\" in next_value or "$" in next_value:
                    raise ValueError("dependency URI must be a canonical literal")
                strings.append(next_value)
        else:
            raise ValueError("unterminated Dart dependency directive")
        if value != "library":
            yield from strings


def boundaries(root):
    root = root.resolve()
    policy = json.loads((root / POLICY).read_text())
    if policy["schema_version"] != 1 or policy["external_packages"] != []:
        raise ValueError("external package approval requires extending the reviewed gate")
    core = root / policy["core_root"]
    adapters = [root / path for path in policy["adapter_roots"]]
    allowed_sdk = set(policy["allowed_dart_libraries"])
    visited = set()

    def in_adapter(path):
        return any(path == adapter or adapter in path.parents for adapter in adapters)

    def visit(path):
        path = path.resolve()
        if not path.is_relative_to(root) or in_adapter(path):
            raise ValueError("prohibited dependency: outside repository or adapter: " + str(path))
        if path in visited:
            return
        if not path.is_file():
            raise ValueError("missing internal dependency: " + str(path))
        visited.add(path)
        for uri in dependency_uris(path.read_text(encoding="utf-8")):
            if uri.startswith("dart:"):
                if uri not in allowed_sdk:
                    raise ValueError("prohibited dependency: unreviewed SDK library " + uri)
            elif uri.startswith("package:") and not uri.startswith("package:finger_desk/"):
                raise ValueError("prohibited dependency: unreviewed external package " + uri)
            else:
                package = uri.startswith("package:finger_desk/")
                relative = uri.removeprefix("package:finger_desk/") if package else uri
                if not re.fullmatch(r"[A-Za-z0-9_./-]+\.dart", relative):
                    raise ValueError("noncanonical internal dependency: " + uri)
                target = (root / "lib" if package else path.parent) / relative
                if not target.is_file():
                    label = (
                        "missing package dependency" if package else "missing internal dependency"
                    )
                    raise ValueError(label + ": " + uri)
                visit(target)

    paths = [p for p in core.rglob("*.dart") if not in_adapter(p)]
    if not paths:
        raise ValueError("quant core is missing; cannot pass an empty architecture check")
    for path in paths:
        visit(path)
    return {
        "core_files": len(paths),
        "transitive_files": len(visited),
        "policy": str(POLICY),
        "external_packages": [],
    }
