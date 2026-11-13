"""A small, offline CLI. Agents propose facts; people resolve uncertainty."""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

STATUSES = {"imported", "corroborated", "confirmed", "conflict", "proposed"}
RENDERABLE = {"imported", "corroborated", "confirmed"}
RESERVED = {"sources", "evidence", "notes", "review_questions", "private", "status"}


def load(path):
    path = Path(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def validate(profile):
    if profile.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(profile.get("person", {}).get("name"), str):
        raise ValueError("person.name is required")
    sources = profile.get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError("sources must be an ID-indexed object")
    entries = profile.get("entries", {})
    if not isinstance(entries, dict):
        raise ValueError("entries must be an ID-indexed object")
    for entry_id, entry in entries.items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", entry_id):
            raise ValueError(f"Invalid stable entry ID: {entry_id}")
        if entry.get("status") not in STATUSES:
            raise ValueError(f"Invalid status: {entry_id}")
        if not isinstance(entry.get("fields"), dict):
            raise ValueError(f"fields required: {entry_id}")
        if not entry.get("evidence"):
            raise ValueError(f"Evidence required: {entry_id}")
        for ev in entry["evidence"]:
            if ev.get("source_id") not in sources or not ev.get("locator"):
                raise ValueError(f"Unresolved evidence reference: {entry_id}")
    return profile


def select(profile, selection, review_candidates=False):
    validate(profile)
    selected = []
    seen = set()
    for section in selection["sections"]:
        rows = []
        for entry_id in section["entry_ids"]:
            if entry_id in seen:
                raise ValueError(f"Duplicate selection: {entry_id}")
            seen.add(entry_id)
            entry = profile["entries"][entry_id]
            if entry["status"] == "proposed" and review_candidates:
                fields = copy.deepcopy(entry["fields"])
                fields["title"] = fields.get("title", "") + " [owner review pending]"
            elif entry["status"] not in RENDERABLE:
                raise ValueError(f"Resolve {entry['status']} before rendering: {entry_id}")
            else:
                fields = entry["fields"]
            rows.append((entry_id, fields))
        selected.append((section, rows))
    return selected


def text(value):
    """Treat profile content as text, never as executable QMD or raw markup."""
    value = str(value).replace("\n", " ").replace("\r", " ")
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
    return re.sub(r"([\\`*_{}\[\]<>|#$~])", r"\\\1", value)


def quarto(profile, selection, style="plain", review_candidates=False):
    rows = select(profile, selection, review_candidates)
    person = profile["person"]
    # Generated source contains no code cells and never executes imported CVs.
    metadata = ["---",
                "execute:", "  enabled: false", "format:", "  pdf:",
                "    pdf-engine: xelatex", "    documentclass: article",
                "    latex-auto-install: false",
                "    papersize: letter", '    fontsize: "10pt"',
                '    geometry: "margin=0.65in"', "    toc: false", "    colorlinks: true",
                "    keep-tex: true", "  html:", "    embed-resources: true", "    toc: false", "---", ""]
    if style == "hyndman":
        metadata = ["---", "name: " + json.dumps(person["name"], ensure_ascii=False),
                    'docname: "Curriculum vitae | Draft for review"',
                    "date: " + json.dumps(profile.get("as_of", "")),
                    'headcolor: "244A63"', 'papersize: "letter"',
                    'fontfamily: "lmodern"', 'latex-auto-install: false',
                    'geometry: "margin=0.65in"', "execute:", "  enabled: false",
                    "format: hyndmancv-pdf", "---", ""]
    contact = [person.get(k) for k in selection.get("contact_fields", []) if person.get(k)]
    out = metadata
    if style == "plain":
        out += ["# " + text(person["name"]) + " {.unnumbered}", "",
                "Curriculum vitae | Draft for review | " + text(profile.get("as_of", "")), ""]
    out += [" | ".join(text(c) for c in contact), ""]
    for section, entries in rows:
        if section.get("page_break_before"):
            out += ["{{< pagebreak >}}", ""]
        out += ["# " + text(section["title"]), ""]
        if style == "hyndman":
            out += ['::: {.entries style="detailed"}',
                    "| when | what | with | why |", "|---|---|---|---|"]
            for _, f in entries:
                title = linked_title(f)
                why = " ".join([f.get("description", "")] + f.get("highlights", []))
                cells = [text(f.get("when", "")), title, text(f.get("organization", "")), text(why)]
                out.append("| " + " | ".join(cells) + " |")
            out += [":::", ""]
        else:
            for _, f in entries:
                title = linked_title(f)
                org = text(f.get("organization", ""))
                date = text(f.get("when", ""))
                out += ["```{=latex}", "\\noindent\\begin{minipage}{\\linewidth}", "```", ""]
                if title:
                    out += ["**" + title + "**" + (" | " + org if org else "") + (" | " + date if date else ""), ""]
                if f.get("description"):
                    out += [text(f["description"]), ""]
                for bullet in f.get("highlights", []):
                    out += ["- " + text(bullet)]
                if f.get("highlights"):
                    out += [""]
                out += ["```{=latex}", "\\end{minipage}\\par\\smallskip", "```", ""]
        for note in section.get("review_notes", []):
            out += ["**Review required:** " + text(note), ""]
    return "\n".join(out)


def linked_title(fields):
    title = text(fields.get("title", ""))
    if not fields.get("url"):
        return title
    url = str(fields["url"])
    if not re.fullmatch(r"https://[^\s<>\\{}()]+", url):
        raise ValueError("Only plain HTTPS links are supported")
    return "[" + title + "](" + url + ")"


def public_export(profile, policy):
    """Copy only exact, approved scalar leaves; reject objects and wildcards."""
    validate(profile)
    result = {}
    for pointer in policy.get("fields", []):
        if not pointer.startswith("/") or "*" in pointer:
            raise ValueError("Use exact JSON pointers, without wildcards")
        parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer[1:].split("/")]
        if any(p in RESERVED for p in parts):
            raise ValueError("Private metadata cannot be publicly exported")
        if parts[0] == "entries":
            if len(parts) < 4 or parts[2] != "fields":
                raise ValueError("Export only explicit entry fields")
            entry = profile["entries"][parts[1]]
            if entry.get("public") is not True or entry["status"] not in {"confirmed", "corroborated"}:
                raise ValueError("Entry requires public approval and corroboration")
        elif parts[0] != "person" or len(parts) != 2:
            raise ValueError("Only explicit person or entry fields are exportable")
        current = profile
        for p in parts:
            current = current[p]
        if current is not None and type(current) not in {str, int, float, bool}:
            raise ValueError("Allowlist must select scalar leaves")
        dest = result
        for p in parts[:-1]:
            dest = dest.setdefault(p, {})
        dest[parts[-1]] = copy.deepcopy(current)
    return result


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).splitlines(True)


def inspect_source(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() not in {".tex", ".bib", ".txt", ".md", ".pdf"}:
        raise ValueError("Supported inputs: LaTeX, BibTeX, text, Markdown, PDF")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    original = destination / (digest[:12] + "-" + source.name)
    if original == source:
        raise ValueError("Choose a separate import directory")
    if original.exists() and hashlib.sha256(original.read_bytes()).hexdigest() != digest:
        raise ValueError("Refusing to overwrite changed imported source")
    if not original.exists():
        shutil.copyfile(source, original)
    if source.suffix.lower() == ".pdf":
        content = subprocess.run(["pdftotext", str(source), "-"], check=True, capture_output=True, text=True).stdout
    else:
        content = source.read_text(encoding="utf-8")
    companions = re.findall(r"\\(?:documentclass|input|include|nobibliography|bibliography)(?:\[[^]]*\])?\{([^}]+)\}", content)
    write(destination / "extracted.txt", content)
    record = {"source_file": str(original), "sha256": digest, "size_bytes": original.stat().st_size,
              "companion_references": companions, "executed": False,
              "next_step": "Agent imports evidence-backed entries; do not infer unresolved bibliography keys"}
    write(destination / "import.json", json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect"); p.add_argument("source"); p.add_argument("--out", required=True)
    p = sub.add_parser("validate"); p.add_argument("profile")
    p = sub.add_parser("questions"); p.add_argument("profile")
    p = sub.add_parser("diff"); p.add_argument("before"); p.add_argument("after")
    p = sub.add_parser("quarto"); p.add_argument("profile"); p.add_argument("selection"); p.add_argument("--out", required=True); p.add_argument("--style", choices=["plain", "hyndman"], default="plain"); p.add_argument("--review-candidates", action="store_true", help="Include proposed entries with visible owner-review labels; conflicts remain blocked")
    p = sub.add_parser("public-export"); p.add_argument("profile"); p.add_argument("policy"); p.add_argument("--out", required=True)
    p = sub.add_parser("adopt", help="Add project config and a private agent skill without replacing existing files")
    p.add_argument("project", nargs="?", default="."); p.add_argument("--renderer", default="render.py")
    p.add_argument("--evidence-profile", required=True); p.add_argument("--qmd", action="append", required=True)
    p.add_argument("--instructions", action="append"); p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("build", help="Run the configured reviewed project renderer without regenerating QMD")
    p.add_argument("--project", default="."); p.add_argument("--watch", action="store_true"); p.add_argument("--profile")
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            print(json.dumps(inspect_source(args.source, args.out), indent=2))
        elif args.command == "validate":
            validate(load(args.profile)); print("Profile is valid")
        elif args.command == "questions":
            print(json.dumps(load(args.profile).get("review_questions", []), ensure_ascii=False, indent=2))
        elif args.command == "diff":
            print("".join(difflib.unified_diff(canonical(load(args.before)), canonical(load(args.after)), fromfile=args.before, tofile=args.after)), end="")
        elif args.command == "quarto":
            target = Path(args.out)
            if target.exists() or target.is_symlink():
                raise ValueError("Output QMD exists; edit it directly or choose a new draft path")
            content = quarto(load(args.profile), load(args.selection), args.style, args.review_candidates)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as stream:
                stream.write(content)
        elif args.command == "adopt":
            from .project import adopt_project
            print(json.dumps(adopt_project(args.project, args.renderer, args.evidence_profile,
                                           args.qmd, args.instructions, args.dry_run), indent=2))
        elif args.command == "build":
            from .project import build_project
            return build_project(args.project, args.watch, args.profile)
        elif args.command == "public-export":
            write(args.out, json.dumps(public_export(load(args.profile), load(args.policy)), ensure_ascii=False, indent=2) + "\n")
    except (ValueError, KeyError, TypeError, OSError, ImportError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"cv-buid: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
