"""Adopt a private QMD project and delegate to its reviewed local renderer.

This adapter deliberately keeps the existing render engine in the project.
It does not seed QMD, read profile facts, install software or publish anything.
"""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import runpy
import signal
import sys
from importlib.resources import files

CONFIG = 'cv-buid.json'
SKILL = '.agents/skills/cv-project/SKILL.md'
KEYS = {'schema_version', 'renderer', 'evidence_profile', 'qmd', 'instructions'}


def local_path(root, value):
    """Use portable, repository-relative paths; reject escapes on either OS."""
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Use nonempty repository-relative paths with / separators')
    posix, windows = PurePosixPath(value), PureWindowsPath(value)
    if posix.is_absolute() or windows.drive or windows.is_absolute() or '..' in posix.parts:
        raise ValueError('Paths must stay inside the private project')
    candidate = root.joinpath(*posix.parts)
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('A project path resolves outside the private project')
    return candidate


def validate_config(root, config):
    if not isinstance(config, dict) or set(config) != KEYS:
        raise ValueError('Expected schema_version, renderer, evidence_profile, qmd and instructions')
    if type(config['schema_version']) is not int or config['schema_version'] != 1:
        raise ValueError('Unsupported cv-buid project schema')
    renderer = local_path(root, config['renderer'])
    if renderer.suffix != '.py' or not renderer.is_file():
        raise ValueError('renderer must name an existing, reviewed project Python script')
    if not local_path(root, config['evidence_profile']).is_file():
        raise ValueError('evidence_profile must name an existing private evidence profile')
    qmd = config['qmd']
    if not isinstance(qmd, list) or not qmd or not all(isinstance(p, str) for p in qmd):
        raise ValueError('qmd must list existing authoritative source paths')
    if len(set(qmd)) != len(qmd):
        raise ValueError('Duplicate authoritative QMD path')
    for item in qmd:
        path = local_path(root, item)
        if path.suffix != '.qmd' or not path.is_file():
            raise ValueError('qmd must list existing authoritative .qmd files')
    if not isinstance(config['instructions'], list):
        raise ValueError('instructions must be a list of private project instruction files')
    for item in config['instructions']:
        if not local_path(root, item).is_file():
            raise ValueError('An instruction file is missing')
    return config


def read_project(project):
    root = Path(project).resolve()
    path = local_path(root, CONFIG)
    with path.open(encoding='utf-8') as stream:
        config = validate_config(root, json.load(stream))
    return root, config


def adopt_project(project, renderer, evidence_profile, qmd, instructions=None, dry_run=False):
    root = Path(project).resolve()
    if not root.is_dir():
        raise ValueError('Choose an existing private project directory')
    instructions = instructions if instructions is not None else (['AGENTS.md'] if (root / 'AGENTS.md').is_file() else [])
    config = validate_config(root, {'schema_version': 1, 'renderer': renderer,
                                   'evidence_profile': evidence_profile, 'qmd': qmd,
                                   'instructions': instructions})
    content = {CONFIG: json.dumps(config, indent=2) + '\n',
               SKILL: files('cv_buid').joinpath('assets/project-skill.md').read_text(encoding='utf-8')}
    targets = {name: local_path(root, name) for name in content}
    # Refuse the entire plan before writing, including dangling symlinks.
    if any(path.exists() or path.is_symlink() for path in targets.values()):
        raise ValueError('Adoption target already exists; review it manually. No overwrite is supported')
    if not dry_run:
        created = []
        try:
            for name, path in targets.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    created.append(path)
                    stream.write(content[name])
        except BaseException:
            for path in reversed(created):
                path.unlink()
            raise
    return {'project': str(root), 'dry_run': dry_run, 'files': list(content), 'config': config}


def build_project(project='.', watch=False, profile=None):
    root, config = read_project(project)
    if profile is not None and not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]*', profile):
        raise ValueError('Use a simple Quarto profile name')
    renderer = local_path(root, config['renderer'])
    arguments = [str(renderer)]
    if watch:
        arguments.append('--watch')
    if profile is not None:
        arguments += ['--profile', profile]
    old_argv, old_cwd, old_path = sys.argv, Path.cwd(), sys.path[:]
    signals = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, 'SIGBREAK'):
        signals.append(signal.SIGBREAK)
    handlers = {sig: signal.getsignal(sig) for sig in signals}
    try:
        # No shell and no additional wrapper child: the proven renderer remains
        # the process that owns its OS locks, console signals and render children.
        os.chdir(root)
        sys.argv = arguments
        sys.path.insert(0, str(root))
        try:
            runpy.run_path(str(renderer), run_name='__main__')
        except SystemExit as error:
            if error.code is None:
                return 0
            if isinstance(error.code, int):
                return error.code
            raise RuntimeError(str(error.code)) from error
        return 0
    finally:
        sys.argv = old_argv
        sys.path[:] = old_path
        os.chdir(old_cwd)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
