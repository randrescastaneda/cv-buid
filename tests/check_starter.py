"""Actual installed-command Quarto/watch acceptance using synthetic workspaces."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def wait(check, process=None, log=None, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check(): return
        if process is not None and process.poll() is not None:
            raise RuntimeError(log.read_text(encoding='utf-8', errors='replace'))
        time.sleep(.2)
    raise RuntimeError('Timed out waiting for acceptance event: ' + (log.read_text(encoding='utf-8', errors='replace')[-4000:] if log else ''))


def processes():
    if os.name == 'nt':
        command = ['powershell', '-NoProfile', '-Command',
                   'Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name | ConvertTo-Json -Compress']
        rows = json.loads(subprocess.check_output(command, text=True, encoding='utf-8'))
        return {int(r['ProcessId']): (int(r['ParentProcessId']), r['Name']) for r in rows}
    output = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,comm='], text=True)
    return {int(parts[0]): (int(parts[1]), parts[2]) for line in output.splitlines() if len(parts := line.strip().split(None, 2)) == 3}


def descendants(pid):
    all_processes = processes(); found = set()
    while True:
        new = {p for p, (parent, _) in all_processes.items() if parent == pid or parent in found}
        if new <= found: return {p: all_processes[p] for p in found}
        found |= new


def alive(pid):
    if os.name == 'nt':
        import ctypes
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.restype = ctypes.c_void_p
        api.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = api.OpenProcess(0x100000, False, pid)
        if not handle: return False
        try: return api.WaitForSingleObject(handle, 0) == 258
        finally: api.CloseHandle(handle)
    result = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True)
    return bool(result.stdout.strip()) and not result.stdout.strip().startswith('Z')


def run_case(root, mode, report, artifacts):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONPATH='')
    cli = [sys.executable, '-m', 'cv_buid.cli']
    subprocess.run(cli + ['init', str(root)], env=env, check=True)
    if mode == 'script':
        (root / 'render.py').write_text(
            "from pathlib import Path\nfrom cv_buid.engine import run\n"
            "root=Path(__file__).resolve().parent\nraise SystemExit(run(root,root/'private/quarto',('resume','full-cv')))\n", encoding='utf-8')
        path = root / 'cv-buid.json'; config = json.loads(path.read_text());config['renderer'] = 'render.py';path.write_text(json.dumps(config))
    command = cli + ['build', '--project', str(root)]
    project = root / 'private/quarto'; output = project / 'output'
    sources = {p: digest(p) for p in root.rglob('*') if p.is_file()}
    if sys.platform == 'win32':
        # Exercise Unicode/spaces paths without changing global temp settings.
        scratch = root / 'scratch 測試 spaces';scratch.mkdir()
        env.update(TMP=str(scratch), TEMP=str(scratch), TMPDIR=str(scratch))
    env['PATH'] = os.pathsep.join(p for p in env['PATH'].split(os.pathsep)
                                if not shutil.which('xelatex', path=p) and not shutil.which('pdflatex', path=p))
    assert shutil.which('quarto', path=env['PATH'])
    assert not shutil.which('pdflatex', path=env['PATH'])
    events = []
    def build():
        result = subprocess.run(command, env=env, capture_output=True, text=True, encoding='utf-8', timeout=240)
        if result.returncode:
            print(result.stdout + result.stderr)
            if (root / '.cv-build/last-build.log').exists():print((root / '.cv-build/last-build.log').read_text(encoding='utf-8'))
        assert result.returncode == 0
    build();events.append('installed_command_four_outputs_without_tex_on_path')
    header = project / 'styles/pdf-header.tex'; original_header = header.read_bytes()
    qmd = project / 'resume.qmd'; original_qmd = qmd.read_bytes()
    log = root / 'watch.log'
    hashes = lambda: {p.name: digest(p) for p in output.iterdir() if p.suffix in ('.pdf', '.docx')}
    def start(log):
        stream = log.open('w', encoding='utf-8')
        child = subprocess.Popen(command + ['--watch'], env=env, stdout=stream, stderr=subprocess.STDOUT,
                                 creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        return child, stream
    def stop(child, stream):
        if child.poll() is None:child.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGINT)
        child.wait(timeout=20);stream.close()
        assert child.returncode == 130, child.returncode
    child, stream = start(log)
    try:
        count = lambda: log.read_text(encoding='utf-8', errors='replace').count('Built:')
        wait(lambda: count() == 1, child, log)
        header.write_bytes(original_header + b'\n% synthetic save\n')
        wait(lambda: count() == 2, child, log)
        time.sleep(1.2);assert count() == 2
        events.append('save_rebuild_no_output_loop')
        before = hashes()
        qmd.write_bytes(original_qmd + b'\n```{=latex}\n\\missingAcceptanceCommand\n```\n')
        wait(lambda: 'Build failed:' in log.read_text(encoding='utf-8', errors='replace'), child, log)
        assert hashes() == before
        events.append('real_latex_failure_retains_every_output')
        qmd.write_bytes(original_qmd)
        wait(lambda: count() == 3, child, log)
        events.append('corrected_save_recovers')
        second = subprocess.run(command, env=env, capture_output=True, text=True, encoding='utf-8', timeout=15)
        assert second.returncode == 2 and 'already running' in second.stderr
        events.append('second_builder_rejected')
    finally:
        stop(child, stream)
        qmd.write_bytes(original_qmd);header.write_bytes(original_header)
    events.append('clean_watch_shutdown')
    # Stop during an actual, deliberately busy TeX process, then prove its tree is gone.
    qmd.write_bytes(original_qmd + b'\n```{=latex}\n\\loop\\iftrue\\repeat\n```\n')
    interrupt_log = root / 'interrupt.log';child, stream = start(interrupt_log)
    captured = {}
    try:
        def tex_running():
            nonlocal captured
            captured = descendants(child.pid)
            return any(('pdflatex' in name.lower() or 'pdftex' in name.lower()) for _, name in captured.values())
        wait(tex_running, child, interrupt_log, timeout=90)
    finally:
        stop(child, stream);qmd.write_bytes(original_qmd)
    wait(lambda: not any(alive(pid) for pid in captured), timeout=20)
    build();events.append('active_tex_interrupt_reaps_descendants_and_releases_lock')
    for name in ['resume', 'full-cv']:
        assert (output / (name + '.pdf')).read_bytes().startswith(b'%PDF-')
        with zipfile.ZipFile(output / (name + '.docx')) as z:
            assert 'Alex Example' in z.read('word/document.xml').decode()
        if artifacts:
            dest = artifacts / mode;dest.mkdir(parents=True, exist_ok=True)
            for extension in ['pdf', 'docx']:shutil.copy2(output / (name + '.' + extension), dest / (name + '.' + extension))
    assert all(digest(p) == value for p, value in sources.items())
    report['cases'][mode] = {'events': events, 'source_integrity': True,
                              'outputs': hashes(), 'tex_on_path': False}


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--artifacts', type=Path)
    args = parser.parse_args()
    report = {'platform': platform.platform(), 'python': platform.python_version(), 'cases': {}}
    with tempfile.TemporaryDirectory(prefix='cv-buid installed Alex 測試 ') as temp:
        for mode in ['builtin', 'script']:
            run_case(Path(temp) / (mode + ' private space'), mode, report, args.artifacts)
    if args.artifacts:
        args.artifacts.mkdir(parents=True, exist_ok=True)
        (args.artifacts / 'native-evidence.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
