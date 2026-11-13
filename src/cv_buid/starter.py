"""Create a synthetic private workspace without overwriting any existing path."""
from importlib.resources import files
from pathlib import Path
import contextlib
from .project import adopt_project


def init_project(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    created = []
    directories = [root]
    def copy_tree(source, target):
        for entry in source.iterdir():
            dest = target / entry.name
            if entry.is_dir():
                dest.mkdir()
                directories.append(dest)
                copy_tree(entry, dest)
            else:
                with dest.open('xb') as stream:
                    stream.write(entry.read_bytes())
                created.append(dest)
    try:
        copy_tree(files('cv_buid').joinpath('assets/starter'), root)
        directories.extend([root / '.agents', root / '.agents/skills', root / '.agents/skills/cv-project'])
        adopt_project(root, 'builtin', 'private/profile.json',
                      ['private/quarto/resume.qmd','private/quarto/full-cv.qmd'])
    except BaseException:
        for item in reversed(created):
            with contextlib.suppress(OSError): item.unlink()
        for item in reversed(directories):
            with contextlib.suppress(OSError): item.rmdir()
        raise
    return root
