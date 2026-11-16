"""Build an offline, generic-only HTML preview for private artifact download."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import re
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
    documents = [(target / name).read_text(encoding='utf-8') for name in PAGES]
    head = re.search(r'<head>(.*?)</head>', documents[0], re.S).group(1)
    head = re.sub(r'<script\b.*?</script>', '', head, flags=re.S)
    body = []
    labels = ('Overview', 'Quick start', 'Project contract', 'Path to v1')
    for name, document in zip(PAGES, documents):
        slug = name.removesuffix('.html')
        main = re.search(r'<main\b[^>]*>(.*?)</main>', document, re.S).group(1)
        # Namespace all IDs so combined pages cannot shadow one another's anchors.
        main = re.sub(r'\bid="([^"]+)"', lambda m: 'id="' + slug + '-' + m.group(1) + '"', main)
        main = re.sub(r'href="#([^"]+)"', lambda m: 'href="#' + slug + '-' + m.group(1) + '"', main)
        main = main.replace('href="./', 'href="')
        for page in PAGES:
            page_slug = page.removesuffix('.html')
            main = main.replace('href="' + page + '#', 'href="#' + page_slug + '-')
            main = main.replace('href="' + page + '"', 'href="#guide-' + page_slug + '"')
        # Keep accessibility references aligned with namespaced IDs.
        main = re.sub(r'(aria-labelledby|aria-controls)="([^"]+)"', lambda m: m.group(1) + '="' + ' '.join(slug + '-' + value for value in m.group(2).split()) + '"', main)
        body.append('<section class="guide-section" id="guide-' + slug + '">' + main + '</section>')
    nav = '<header class="offline-header"><a class="offline-brand" href="#guide-index">▤ <span>cv-buid</span></a><nav aria-label="Documentation">' + ''.join('<a href="#guide-' + name.removesuffix('.html') + '">' + label + '</a>' for name, label in zip(PAGES, labels)) + '</nav></header>'
    style = """<style>
    body .panel-tabset .tab-content > .tab-pane{display:block!important;opacity:1!important;margin-top:1rem}
    .tab-pane[aria-labelledby$="-1-tab"]::before{content:"macOS";display:block;font-weight:700;font-size:.8rem}
    .tab-pane[aria-labelledby$="-2-tab"]::before{content:"Windows PowerShell";display:block;font-weight:700;font-size:.8rem}
    body .panel-tabset .nav-tabs{display:none!important}.guide-section{padding:2rem 0 3rem;border-bottom:1px solid #dce4df;scroll-margin-top:7rem}
    .guide-section:first-child{padding-top:0}main.content{display:block;max-width:68rem;margin:0 auto;padding:0 2rem 3rem}
    button{display:none!important}.offline-header{position:sticky;top:0;z-index:1000;background:rgba(251,250,247,.98);border-bottom:1px solid #dce4df;padding:1rem max(1.3rem,calc((100% - 64rem)/2));display:flex;align-items:center;justify-content:space-between;gap:1rem}
    .offline-brand{font-size:1.35rem;font-weight:800;letter-spacing:-.045em;white-space:nowrap;text-decoration:none;color:#183c37}
    .offline-header nav{display:flex;flex-wrap:wrap;gap:.45rem 1.3rem}.offline-header nav a{font-size:.8rem;font-weight:650;text-decoration:none;white-space:nowrap}.offline-header nav a:hover{text-decoration:underline;text-underline-offset:.3rem}
    .offline-footer{max-width:64rem;margin:0 auto;padding:1.5rem;color:#61716a;font-size:.75rem}
    @media(max-width:650px){.offline-header{align-items:flex-start;flex-direction:column;padding:.7rem 1rem;gap:.4rem}.offline-header nav{gap:.35rem 1rem}.offline-header nav a{font-size:.72rem}main.content{padding-inline:1rem}.guide-section{scroll-margin-top:9rem}}
    @media print{.offline-header{position:static}.guide-section{break-before:page}.guide-section:first-child{break-before:auto}}
    </style>"""
    combined = '<!doctype html><html lang="en"><head>' + head + style + '</head><body>' + nav + '<main class="content">' + ''.join(body) + '</main><footer class="offline-footer">cv-buid · Complete offline guide · Development preview</footer></body></html>'
    (target / 'preview-all.html').write_text(combined, encoding='utf-8')
    (target / 'OPEN-FIRST.txt').write_text(
        'Extract the folder, then open preview-all.html for the complete single-file guide.\n'
        'The four HTML files embed their display assets and work without a server.\n'
        'Keep the HTML files together so navigation between pages works.\n'
        'This bundle contains generic toolkit documentation only.\n', encoding='utf-8')
    with zipfile.ZipFile(ROOT / 'dist/docs-preview.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for file in target.iterdir():
            z.write(file, file.name)
    print('Offline preview:', target / 'index.html')


if __name__ == '__main__':
    main()
