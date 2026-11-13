"""Build an offline, generic-only HTML preview for private artifact download."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index.html', 'quick-start.html', 'project-contract.html', 'v1.html')


class Assets(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        value = attrs.get('src') if tag in ('script', 'img') else attrs.get('href') if tag == 'link' and attrs.get('rel') in ('stylesheet', 'icon') else None
        if value and not value.startswith(('data:', '#')):
            raise ValueError('Preview has an unembedded display dependency: ' + value)


def main():
    subprocess.run(['quarto', 'render', 'docs', '--to', 'html', '--no-execute'], cwd=ROOT, check=True)
    target = ROOT / 'dist/docs-preview'
    target.mkdir(parents=True, exist_ok=True)
    for name in PAGES:
        content = (ROOT / 'docs/_site' / name).read_text(encoding='utf-8')
        content = content.replace('href="./"', 'href="index.html"')
        Assets().feed(content)
        (target / name).write_text(content, encoding='utf-8')
    (target / 'OPEN-FIRST.txt').write_text(
        'Extract this entire folder, then double-click index.html.\n'
        'The four HTML files embed their display assets and work without a server.\n'
        'Keep the HTML files together so navigation between pages works.\n'
        'This bundle contains generic toolkit documentation only.\n', encoding='utf-8')
    with zipfile.ZipFile(ROOT / 'dist/docs-preview.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for file in target.iterdir():
            z.write(file, file.name)
    print('Offline preview:', target / 'index.html')


if __name__ == '__main__':
    main()
