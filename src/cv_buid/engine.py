#!/usr/bin/env python3
"""Shared staged Quarto engine, ported from the reviewed project renderer.

The MIT project license applies. Source prose and presentation stay in each
private project; no personal CV content is included in this module.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path.cwd()
PROJECT = ROOT / 'private' / 'quarto'
VARIANTS = ('resume', 'full-cv')
OUTPUTS = tuple(f'{name}.{fmt}' for name in VARIANTS for fmt in ('pdf', 'docx'))
MAC_FONTS = Path('/Applications/Microsoft Word.app/Contents/Resources/DFonts')
NOISE = {'.aux', '.log', '.out', '.toc', '.fls', '.fdb_latexmk', '.swp', '.tmp'}


class SourceUnavailable(OSError):
    """An editor temporarily prevents a complete source snapshot."""


def say(message):
    print(message, flush=True)


def snapshot():
    """Read source/presentation bytes, excluding outputs and editor/build noise."""
    files = {}
    for path in sorted(PROJECT.rglob('*')):
        rel = path.relative_to(PROJECT)
        if any(part in {'output', '__pycache__'} or part.startswith('.') for part in rel.parts):
            continue
        if not path.is_file() or path.name.endswith(('~', '.synctex.gz')) or path.suffix in NOISE:
            continue
        if len(rel.parts) == 1 and path.name in {f'{v}.{ext}' for v in VARIANTS for ext in ('tex', 'pdf', 'docx')}:
            continue
        try:
            files[rel.as_posix()] = path.read_bytes()
        except OSError as error:
            raise SourceUnavailable(f'Cannot read {rel}: {error}') from error
    digest = hashlib.sha256()
    for name, data in files.items():
        digest.update(name.encode() + b'\0' + hashlib.sha256(data).digest())
    return files, digest.hexdigest()


def prerequisites(profile):
    if not shutil.which('quarto'):
        raise RuntimeError('quarto is missing from PATH. Configure Quarto first; nothing is installed automatically.')
    # Quarto discovers its managed TinyTeX without adding TeX engines to PATH.
    # Let its render step validate TeX rather than rejecting that valid setup.
    if profile == 'auto':
        profile = 'mac' if sys.platform == 'darwin' else 'default'
    if not re.fullmatch(r'[A-Za-z0-9_-]+', profile):
        raise RuntimeError('Use a simple Quarto profile name containing letters, numbers, _ or -.')
    if profile != 'default' and not (PROJECT / f'_quarto-{profile}.yml').is_file():
        raise RuntimeError(f'Quarto profile _quarto-{profile}.yml is missing.')
    # The declared Quarto/TeX font settings are authoritative. The compiler
    # reports missing fonts; this engine never substitutes or installs them.
    return profile


def temporary_project():
    """Use a private ASCII scratch path around Quarto's Windows Lua limitation."""
    parent = os.environ.get('CV_RENDER_TEMP')
    if os.name == 'nt':
        candidates = [Path(parent)] if parent else [Path(tempfile.gettempdir()),
            Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Temp']
        candidates = [path.absolute() for path in candidates]
        for candidate in candidates:
            if str(candidate).isascii() and candidate.is_dir():
                parent = str(candidate)
                break
        else:
            import ctypes
            from ctypes import wintypes as w
            api = ctypes.WinDLL('kernel32', use_last_error=True).GetShortPathNameW
            api.argtypes, api.restype = [w.LPCWSTR, w.LPWSTR, w.DWORD], w.DWORD
            path = str(candidates[0])
            size = api(path, None, 0)
            buffer = ctypes.create_unicode_buffer(size or 1)
            if not size or not api(path, buffer, size) or not buffer.value.isascii():
                raise RuntimeError('Windows Quarto requires an ASCII scratch path. Set CV_RENDER_TEMP to an existing writable private folder with an ASCII path, then retry. No system settings are changed.')
            parent = buffer.value
    return tempfile.TemporaryDirectory(prefix='cv-render-', dir=parent)


@contextlib.contextmanager
def exclusive():
    # Keep the inode: unlinking a lock could allow two owners after a race.
    with (ROOT / '.cv-render.lock').open('a+b') as lock:
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)  # May lock past EOF.
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError('Another CV build/watch is already running in this checkout. Stop it with Ctrl+C before starting another.') from None
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


class WindowsJob:
    """A native Job Object owns render descendants, including after parent exit."""
    def __init__(self):
        import ctypes
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64), ('flags', w.DWORD),
                        ('min_working_set', ctypes.c_size_t), ('max_working_set', ctypes.c_size_t),
                        ('active_limit', w.DWORD), ('affinity', ctypes.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]
        class Io(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', Io), ('process_memory', ctypes.c_size_t),
                        ('job_memory', ctypes.c_size_t), ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]
        class Thread(ctypes.Structure):
            _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('id', w.DWORD), ('owner', w.DWORD),
                        ('priority', w.LONG), ('delta', w.LONG), ('flags', w.DWORD)]
        self.thread_type = Thread
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
                      'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
                      'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
                      'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
                      'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL), 'CloseHandle': ([w.HANDLE], w.BOOL),
                      'CreateToolhelp32Snapshot': ([w.DWORD, w.DWORD], w.HANDLE),
                      'Thread32First': ([w.HANDLE, ctypes.POINTER(Thread)], w.BOOL),
                      'Thread32Next': ([w.HANDLE, ctypes.POINTER(Thread)], w.BOOL),
                      'OpenThread': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE), 'ResumeThread': ([w.HANDLE], w.DWORD)}
        for name, (args, result) in signatures.items():
            getattr(self.api, name).argtypes, getattr(self.api, name).restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def attach(self, process):
        import ctypes
        handle = self.api.OpenProcess(0x0101, False, process.pid)  # SET_QUOTA | TERMINATE
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.api.AssignProcessToJobObject(self.handle, handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(handle)
        # The child starts suspended, so it cannot spawn unowned descendants
        # before assignment. Resume its initial thread using documented Win32 APIs.
        snapshot = self.api.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = self.thread_type()
            entry.size = ctypes.sizeof(entry)
            found = self.api.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner == process.pid:
                    thread = self.api.OpenThread(2, False, entry.id)  # SUSPEND_RESUME
                    if not thread:raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        if self.api.ResumeThread(thread) == 0xFFFFFFFF:
                            raise ctypes.WinError(ctypes.get_last_error())
                    finally:self.api.CloseHandle(thread)
                    return
                found = self.api.Thread32Next(snapshot, ctypes.byref(entry))
            raise RuntimeError('Could not find the suspended render thread.')
        finally:self.api.CloseHandle(snapshot)

    def terminate(self):
        if self.handle:
            self.api.TerminateJobObject(self.handle, 1)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def run_quarto(command, directory, log):
    executable = shutil.which(command[0])
    if not executable:
        raise RuntimeError('Quarto disappeared from PATH.')
    launch, options = [executable, *command[1:]], {}
    job = WindowsJob() if os.name == 'nt' else None
    if os.name == 'nt':
        options['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP | 4  # CREATE_SUSPENDED
        child_temp = directory / '_tmp'
        child_temp.mkdir(exist_ok=True)
        # Quarto's Lua filter converts filenames through the Windows code page.
        # Keep only this child's scratch paths ASCII; never change user settings.
        options['env'] = dict(os.environ, TMP=str(child_temp), TEMP=str(child_temp), TMPDIR=str(child_temp))
        if Path(executable).suffix.lower() in {'.cmd', '.bat'}:
            # Pass a native command string without CRT re-quoting. The variable
            # expansion keeps Unicode/spaces and literal % in launcher paths.
            shell = os.environ.get('COMSPEC', str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'System32/cmd.exe'))
            options['env']['CV_RENDER_LAUNCHER'] = executable
            body = '"%CV_RENDER_LAUNCHER%" ' + subprocess.list2cmdline(command[1:])
            launch = f'"{shell}" /d /s /v:off /c "{body}"'
            options['executable'] = shell
    else:
        options['start_new_session'] = True
    process = None
    try:
        process = subprocess.Popen(launch, cwd=directory, stdout=log, stderr=subprocess.STDOUT, **options)
        if job:
            job.attach(process)
        deadline = time.monotonic() + 180
        while True:
            # Short waits let Python handle console signals on Windows while
            # the native wait is otherwise uninterruptible.
            try:
                code = process.wait(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, 180)
    except BaseException:
        if process is not None:
            if job:
                job.terminate()
                # Also covers assignment errors before the job owned the child.
                if process.poll() is None:
                    with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=log, stderr=subprocess.STDOUT, timeout=10)
                    if process.poll() is None:
                        process.kill()
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if job:
                    process.kill()
                else:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        raise
    finally:
        if job:
            job.close()
    if code:
        raise RuntimeError(f'Quarto exited {code}: {command[2]} ({command[4]}).')


def publish(directory):
    """Prepare the whole batch; replace each file atomically and roll back errors."""
    target = PROJECT / 'output'
    target.mkdir(exist_ok=True)
    previous = {name: (target / name).read_bytes() if (target / name).exists() else None for name in OUTPUTS}
    prepared = {}
    try:
        for name in OUTPUTS:
            with tempfile.NamedTemporaryFile(dir=target, prefix='.' + name + '-', delete=False) as stream:
                stream.write((directory / name).read_bytes())
                prepared[name] = Path(stream.name)
        try:
            for name, path in prepared.items():
                os.replace(path, target / name)
        except BaseException:
            # An interrupt can arrive immediately after replace succeeds.
            # The consumed temporary file is the durable evidence of success.
            replaced = [name for name, path in prepared.items() if not path.exists()]
            for name in reversed(replaced):
                data = previous[name]
                if data is None:
                    (target / name).unlink(missing_ok=True)
                else:
                    with tempfile.NamedTemporaryFile(dir=target, delete=False) as backup:
                        backup.write(data)
                        backup_path = Path(backup.name)
                    os.replace(backup_path, target / name)
            raise
    finally:
        for path in prepared.values():
            path.unlink(missing_ok=True)


def build(profile, state):
    files, signature = state
    log_dir = ROOT / '.cv-build'
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / 'last-build.log'
    say(f'Building both variants as PDF and Word (profile: {profile})...')
    try:
        for required in (*(name + '.qmd' for name in VARIANTS), '_quarto.yml', 'styles/reference.docx', 'styles/career.lua', 'styles/pdf-header.tex'):
            if required not in files:
                raise RuntimeError(f'Required source/presentation file missing: {required}')
        with temporary_project() as temp, log_path.open('w', encoding='utf-8') as log:
            stage = Path(temp)
            for name, data in files.items():
                path = stage / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            for name in VARIANTS:
                for fmt in ('pdf', 'docx'):
                    command = ['quarto', 'render', name + '.qmd', '--to', fmt, '--no-execute', '--syntax-highlighting', 'none']
                    if profile != 'default':
                        command += ['--profile', profile]
                    say(f'  {name} -> {fmt}')
                    run_quarto(command, stage, log)
            output = stage / 'output'
            for name in OUTPUTS:
                path = output / name
                if not path.is_file() or path.stat().st_size == 0:
                    raise RuntimeError(f'Expected output missing/empty: {name}')
                if path.suffix == '.pdf' and not path.read_bytes().startswith(b'%PDF-'):
                    raise RuntimeError(f'Invalid PDF output: {name}')
                if path.suffix == '.docx':
                    with zipfile.ZipFile(path) as archive:
                        if 'word/document.xml' not in archive.namelist():
                            raise RuntimeError(f'Invalid Word output: {name}')
            if snapshot()[1] != signature:
                say('Sources changed during rendering; discarded this batch. Existing outputs are unchanged.')
                return 'stale'
            publish(output)
        say(f'Built: {PROJECT / "output"} ({", ".join(OUTPUTS)})')
        return 'ok'
    except SourceUnavailable as error:
        say(f'{error}\nWaiting for readable sources; last successful outputs retained.')
        return 'unreadable'
    except (RuntimeError, OSError, subprocess.TimeoutExpired, zipfile.BadZipFile) as error:
        say(f'Build failed: {error}\nLast successful outputs retained. Log: {log_path}')
        if log_path.exists():
            say('\n'.join(log_path.read_text(encoding='utf-8', errors='replace').splitlines()[-16:]))
        return 'failed'


def watch(profile):
    observed, due, blocked = None, None, False
    say('Watching QMD and presentation files. Save to rebuild; Ctrl+C to stop.')
    while True:
        try:
            current = snapshot()
        except OSError as error:
            if not blocked:
                say(f'Waiting for readable sources: {error}')
            blocked = True
            time.sleep(0.2)
            continue
        if observed is None:
            observed, due = current, time.monotonic()
        elif current[1] != observed[1] or blocked:
            observed, due = current, time.monotonic() + 0.6
        blocked = False
        if due is not None and time.monotonic() >= due:
            status = build(profile, observed)
            # The next poll notices changes made during a render. A transient
            # source lock retries after release, unlike a genuine compile error.
            due, blocked = None, status == 'unreadable'
            say('Watching for the next save...')
        time.sleep(0.2)


def stop(*_):
    raise KeyboardInterrupt


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true', help='Build once, then rebuild on local source/style saves')
    parser.add_argument('--profile', default='default', help='Quarto profile: default or an explicit project profile')
    parser.add_argument('--word', action='store_true', help=argparse.SUPPRESS)  # compatibility: Word is now included by default
    args = parser.parse_args(argv)
    signal.signal(signal.SIGTERM, stop)
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, stop)
    try:
        with exclusive():
            profile = prerequisites(args.profile)
            if args.watch:
                watch(profile)
                return 0
            return 0 if build(profile, snapshot()) == 'ok' else 1
    except KeyboardInterrupt:
        say('Stopped. No render process remains running.')
        return 130
    except (RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2



def run(root, project, variants, argv=None):
    """Configure one CLI build in-process; the existing OS lock owns concurrency."""
    global ROOT, PROJECT, VARIANTS, OUTPUTS
    previous = ROOT, PROJECT, VARIANTS, OUTPUTS
    ROOT, PROJECT = Path(root).resolve(), Path(project).resolve()
    VARIANTS = tuple(variants)
    if not VARIANTS or any(not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', name) for name in VARIANTS):
        ROOT, PROJECT, VARIANTS, OUTPUTS = previous
        raise ValueError('Use simple lowercase QMD stems')
    OUTPUTS = tuple(f'{name}.{fmt}' for name in VARIANTS for fmt in ('pdf', 'docx'))
    try:
        return main(argv)
    finally:
        ROOT, PROJECT, VARIANTS, OUTPUTS = previous
