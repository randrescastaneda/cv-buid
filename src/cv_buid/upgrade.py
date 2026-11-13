"""Plan and apply guarded config/generated-skill upgrades, never career prose."""
import difflib
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import tempfile
import uuid

from .project import CONFIG, SKILL, local_path, read_project, validate_config


def template_bytes(name):
    # Source checkouts can use CRLF while installed wheels and generated files
    # use LF. Compare only recognized templates, with line endings normalized.
    return files('cv_buid').joinpath('assets/' + name).read_bytes().replace(b'\r\n', b'\n')


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def plan_upgrade(project, candidate=None):
    root, current = read_project(project)
    desired = json.loads(Path(candidate).read_text(encoding='utf-8')) if candidate else current
    validate_config(root, desired)
    template = template_bytes('project-skill.md')
    old_template = template_bytes('project-skill-v1.md')
    skill = local_path(root, SKILL)
    previous = skill.read_bytes() if skill.is_file() else None
    after = {CONFIG: (json.dumps(desired, indent=2) + '\n').encode()}
    manual = []
    recognized = previous.replace(b'\r\n', b'\n') if previous is not None else None
    if recognized in (None, old_template, template):
        after[SKILL] = template
    else:
        manual.append(SKILL)
    changes = []
    for name, data in after.items():
        path = local_path(root, name)
        if path.is_symlink():
            raise ValueError('Upgrade targets cannot be symlinks')
        before = path.read_bytes() if path.is_file() else None
        if before == data:
            continue
        text = data.decode('utf-8')
        diff = ''.join(difflib.unified_diff((before or b'').decode('utf-8').splitlines(True), text.splitlines(True), fromfile=name, tofile=name))
        changes.append({'path': name, 'before_sha256': digest(before),
                        'after': text, 'after_sha256': digest(data), 'diff': diff})
    return {'schema_version': 1, 'changes': changes, 'manual_review': manual}


def apply_upgrade(project, plan, backup_directory=None):
    root, _ = read_project(project)
    if not isinstance(plan, dict) or set(plan) != {'schema_version', 'changes', 'manual_review'} or (type(plan['schema_version']) is not int or plan['schema_version'] != 1):
        raise ValueError('Unsupported upgrade plan')
    prepared, previous = {}, {}
    template = template_bytes('project-skill.md')
    for item in plan['changes']:
        name = item['path']
        if name not in {CONFIG, SKILL} or name in prepared:
            raise ValueError('Upgrade can change only config and the generated project skill')
        path = local_path(root, name)
        if path.is_symlink():
            raise ValueError('Upgrade targets cannot be symlinks')
        before = path.read_bytes() if path.is_file() else None
        if digest(before) != item['before_sha256']:
            raise ValueError('Stale upgrade plan; regenerate and review the diff')
        data = item['after'].encode('utf-8')
        if digest(data) != item['after_sha256']:
            raise ValueError('Upgrade plan content hash mismatch')
        if name == CONFIG:
            validate_config(root, json.loads(item['after']))
        else:
            legacy = template_bytes('project-skill-v1.md')
            recognized = before.replace(b'\r\n', b'\n') if before is not None else None
            if recognized not in (None, legacy, template):
                raise ValueError('Customized skill requires manual review')
            if data != template:
                raise ValueError('Only the installed generated skill template may be applied')
        prepared[name], previous[name] = data, before
    if not prepared:
        return {'changed': [], 'backup': None, 'manual_review': plan['manual_review']}
    parent = Path(backup_directory).resolve() if backup_directory else local_path(root, '.cv-buid-upgrades')
    backup = parent / uuid.uuid4().hex
    backup.mkdir(parents=True)
    for name, before in previous.items():
        if before is not None:
            dest = backup / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as stream:
                stream.write(before)
    changed = []
    def replace(name, data):
        target = local_path(root, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            stream.write(data)
            scratch = Path(stream.name)
        try:
            os.replace(scratch, target)
        finally:
            scratch.unlink(missing_ok=True)
    try:
        for name, data in prepared.items():
            path = local_path(root, name)
            current = path.read_bytes() if path.is_file() else None
            if current != previous[name]:
                raise ValueError('Target changed during upgrade; nothing further applied')
            changed.append(name)
            replace(name, data)
    except BaseException:
        for name in reversed(changed):
            path = local_path(root, name)
            # Never roll back an intervening user edit. Original bytes remain in backup.
            if path.read_bytes() == prepared[name]:
                if previous[name] is None:
                    path.unlink()
                else:
                    replace(name, previous[name])
        raise
    return {'changed': changed, 'backup': str(backup), 'manual_review': plan['manual_review']}
