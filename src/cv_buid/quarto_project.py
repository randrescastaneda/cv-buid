"""Seed editable QMD once, then render QMD without regenerating its content."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

from .cli import linked_title, select, text


def draft_qmd(profile, selection):
    rows = select(profile, selection)
    out = ['---', 'lang: en', 'execute:', '  enabled: false', '---', '',
           '<!-- Authoritative variant prose. Edit this QMD; outputs are derived. -->', '']

    def div(content, attributes):
        return ['::: {' + attributes + '}', '', *content, '', ':::', '']

    out += div([text(profile['person']['name'])], '.cv-name custom-style="Title"')
    person = profile['person']
    for contact in selection.get('contact_rows', [selection.get('contact_fields', [])]):
        values = []
        for key in contact:
            if not person.get(key): continue
            value = str(person[key])
            url = 'mailto:' + value if key == 'email' else 'tel:' + value.replace(' ', '') if key == 'phone' else value
            if not re.fullmatch(r'(?:https://|mailto:|tel:)[^\s<>(){}\\]+', url):
                raise ValueError('Unsupported contact URL')
            values.append('[' + text(value) + '](' + url + ')')
        out += div([' | '.join(values)], '.cv-contact custom-style="CV Contact"')
    for section, entries in rows:
        out += ['# ' + text(section['title'].upper()), '']
        last_employer = None
        for entry_id, f in entries:
            kind = profile['entries'][entry_id]['kind']
            title, org, when = (f.get(k, '') for k in ['title', 'organization', 'when'])
            content = []
            if kind == 'experience':
                employer, _, department = org.partition('|')
                if employer.strip() != last_employer:
                    content += div([text(employer.strip())], '.cv-employer custom-style="CV Employer"')
                    last_employer = employer.strip()
                line = linked_title(f) if f.get('url') else text(title)
                if when: line += ' [' + text(when) + ']{.cv-date}'
                content += div([line], '.cv-career custom-style="CV Career"')
                if department.strip(): content += div([text(department.strip())], '.cv-support custom-style="CV Support"')
            elif kind == 'education':
                line = '**' + text(title) + '**'
                if when: line += ' [' + text(when) + ']{.cv-date}'
                content += div([line], '.cv-degree custom-style="CV Degree"')
                if org: content += div([text(org)], '.cv-institution custom-style="CV Institution"')
            elif title:
                label = title + (' | ' + org if kind == 'software' and org else '')
                line = text(label)
                if f.get('url'):
                    # Validate the target with the shared URL guard. Never derive
                    # a software date from its version, title or current year.
                    linked_title({'title': label, 'url': f['url']})
                    if when and re.search(r'\b(?:19|20)\d{2}\b', when):
                        match = re.search(r'\b(?:19|20)\d{2}\b', when)
                        date = text(when[:match.start()]) + '[' + match.group() + '](' + f['url'] + ')' + text(when[match.end():])
                        line += ' (' + date + ')'
                    else:
                        if when: line += ' (' + text(when) + ')'
                        line += ' [' + ('Repository' if kind == 'software' else 'Source') + '](' + f['url'] + ')'
                elif when: line += ' (' + text(when) + ')'
                content += [line, '']
                if org and kind != 'software': content += div([text(org)], '.cv-support custom-style="CV Support"')
            if f.get('description'):
                content += div([text(f['description'])], '.cv-support custom-style="CV Support"') if title else [text(f['description']), '']
            if f.get('highlights'):
                content += ['- ' + text(b) for b in f['highlights']] + ['']
            out += div(content, '#entry-' + entry_id + ' .cv-entry')
    return '\n'.join(out)


def init_project(profile, selection, directory, name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name):
        raise ValueError('Use a lowercase file stem')
    directory = Path(directory)
    target = directory / (name + '.qmd')
    if target.exists():
        raise ValueError('QMD already exists; edit it directly or choose a new draft path')
    content = draft_qmd(profile, selection)
    directory.mkdir(parents=True, exist_ok=True)
    assets = files('cv_buid').joinpath('assets/quarto')
    (directory / 'styles').mkdir(exist_ok=True)
    for asset in assets.iterdir():
        destination = directory / asset.name if asset.name.startswith('_quarto') else directory / 'styles' / asset.name
        if not destination.exists(): destination.write_bytes(asset.read_bytes())
    target.write_text(content, encoding='utf-8')
    return target


def render_source(source, output_format='pdf', profile=None):
    if output_format not in {'pdf', 'docx'}:
        raise ValueError('Choose pdf or docx')
    source = Path(source).resolve()
    if source.suffix != '.qmd' or not source.is_file():
        raise ValueError('An existing authoritative QMD is required')
    command = ['quarto', 'render', source.name, '--to', output_format,
               '--no-execute', '--syntax-highlighting', 'none']
    if profile: command += ['--profile', profile]
    subprocess.run(command, cwd=source.parent, check=True)
