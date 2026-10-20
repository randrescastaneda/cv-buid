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
                fields = copy.deepcopy(entry["fields"])
            overrides = selection.get("field_overrides", {}).get(entry_id, {})
            allowed = {"title", "organization", "when", "description", "highlights", "url"}
            if not isinstance(overrides, dict) or set(overrides) - allowed:
                raise ValueError(f"Only display fields may be overridden: {entry_id}")
            fields.update(copy.deepcopy(overrides))
            if entry["status"] == "proposed" and review_candidates:
                # A display override cannot erase the review warning.
                if "owner review pending" not in fields.get("title", ""):
                    fields["title"] = fields.get("title", "") + " [owner review pending]"
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
    if style == "classic":
        return classic_quarto(profile, selection, rows)
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


def classic_quarto(profile, selection, rows):
    """Delegate a compact serif CV to Quarto, with grouped career entries."""
    out = ["---", "execute:", "  enabled: false", "format:", "  pdf:",
           "    pdf-engine: pdflatex", "    documentclass: article",
           '    fontsize: "11pt"', "    papersize: letter",
           '    geometry: "left=0.75in,right=0.75in,top=0.6in,bottom=0.6in"',
           "    latex-auto-install: false", "    keep-tex: true", "    toc: false",
           "    colorlinks: true", '    linkcolor: "blue"', '    urlcolor: "blue"',
           "include-in-header:", "  text: |",
           r"    \usepackage{titlesec,enumitem,needspace,array}",
           r"    \titleformat{\section}{\normalfont\normalsize\bfseries}{}{0pt}{\MakeUppercase}[\titlerule]",
           r"    \titlespacing*{\section}{0pt}{1em}{0.4em}",
           r"    \setlength{\parindent}{0pt}", r"    \setlength{\parskip}{0.25em}",
           r"    \setlist[itemize]{leftmargin=1.6em,topsep=0.15em,itemsep=0pt,parsep=0pt}",
           r"    \pagestyle{empty}", "---", ""]

    def raw(value):
        out.extend(["```{=latex}", value, "```", ""])

    person = profile["person"]
    raw(r"\begin{center}{\fontsize{20.66}{24}\selectfont\bfseries")
    out.extend([text(person["name"].upper()), ""])
    raw(r"\par}\vspace{0.2em}{\small")
    contact = [text(person[k]) for k in selection.get("contact_fields", []) if person.get(k)]
    out.extend([" | ".join(contact), ""])
    raw(r"\par}{\footnotesize")
    out.extend(["Draft for review | " + text(profile.get("as_of", "")), ""])
    raw(r"\par}\end{center}\vspace{-0.5em}")
    for section, entries in rows:
        if section.get("page_break_before"):
            out.extend(["{{< pagebreak >}}", ""])
        out.extend(["# " + text(section["title"]), ""])
        raw(r"\begin{list}{}{\setlength{\leftmargin}{1.5em}\setlength{\rightmargin}{0pt}\setlength{\topsep}{0pt}}\item\relax")
        last_group = None
        for entry_id, fields in entries:
            kind = profile["entries"][entry_id]["kind"]
            organization = fields.get("organization", "")
            career = kind in {"experience", "education"}
            if career:
                if kind == "education":
                    group, _, detail = organization.partition(",")
                else:
                    group, _, detail = organization.partition("|")
                group, detail = group.strip(), detail.strip()
                group_key = (group, detail) if kind == "education" else (group,)
                if group_key != last_group:
                    raw(r"\needspace{5\baselineskip}")
                    heading = "**" + text(group) + "**" if group else ""
                    if kind == "education" and detail:
                        heading += r" `\hfill`{=latex} " + text(detail)
                    out.extend([heading, ""])
                    last_group = group_key
            else:
                last_group = None
            raw(r"\noindent\begin{minipage}{\linewidth}")
            title = text(fields.get("title", ""))
            date = text(fields.get("when", ""))
            if career:
                raw(r"\begin{tabular*}{\linewidth}{@{\hspace{1em}}p{0.73\linewidth}@{\extracolsep{\fill}}>{\raggedleft\arraybackslash}p{0.23\linewidth}@{}}")
                line = "*" + title + "*"
                if kind == "experience" and detail:
                    line += " - " + text(detail)
                out.extend([line + r" `&`{=latex} " + date + r" `\\`{=latex}", ""])
                raw(r"\end{tabular*}")
                if fields.get("description"):
                    out.extend([text(fields["description"]), ""])
            else:
                line = title
                if organization:
                    line += ". " + text(organization)
                if date:
                    line += " (" + date + ")"
                if line:
                    line += "."
                if fields.get("description"):
                    line += " " + text(fields["description"])
                if fields.get("url"):
                    line += " " + linked_title({"title": "link", "url": fields["url"]})
                out.extend([line.strip(), ""])
            for bullet in fields.get("highlights", []):
                out.append("- " + text(bullet))
            if fields.get("highlights"):
                out.append("")
            if career and fields.get("url"):
                out.extend([linked_title({"title": "link", "url": fields["url"]}), ""])
            raw(r"\end{minipage}\par\smallskip")
        for note in section.get("review_notes", []):
            out.extend(["**Review required:** " + text(note), ""])
        raw(r"\end{list}")
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
    p = sub.add_parser("quarto"); p.add_argument("profile"); p.add_argument("selection"); p.add_argument("--out", required=True); p.add_argument("--style", choices=["plain", "classic", "hyndman"], default="plain"); p.add_argument("--review-candidates", action="store_true", help="Include proposed entries with visible owner-review labels; conflicts remain blocked")
    p = sub.add_parser("public-export"); p.add_argument("profile"); p.add_argument("policy"); p.add_argument("--out", required=True)
    p = sub.add_parser("docx", help="Export editable paragraphs with a separate style policy")
    p.add_argument("profile"); p.add_argument("selection"); p.add_argument("--out", required=True)
    p.add_argument("--style", help="JSON style policy; defaults to the professional sans-serif style")
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
            write(args.out, quarto(load(args.profile), load(args.selection), args.style, args.review_candidates))
        elif args.command == "public-export":
            write(args.out, json.dumps(public_export(load(args.profile), load(args.policy)), ensure_ascii=False, indent=2) + "\n")
        elif args.command == "docx":
            from .word import export_docx
            export_docx(load(args.profile), load(args.selection), args.out, load(args.style) if args.style else None)
    except (ValueError, KeyError, TypeError, OSError, ImportError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"cv-buid: {exc}\n")


if __name__ == "__main__":
    main()
