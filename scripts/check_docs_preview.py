"""Validate generated offline documentation navigation and embedded assets."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build_docs_preview import Assets, PAGES, ROOT

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.links=[]; self.navs=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
        if tag == 'nav': self.navs += 1

def main():
    root=ROOT/'dist/docs-preview'
    for name in (*PAGES, 'preview-all.html'):
        html=(root/name).read_text(); Assets().feed(html)
        page=Links(); page.feed(html)
        assert page.navs, f'{name}: missing navigation'
        assert not [k for k,n in Counter(page.ids).items() if n>1], f'{name}: duplicate IDs'
        for link in page.links:
            if link.startswith('#'):
                assert link[1:] in page.ids, f'{name}: missing anchor {link}'
            elif not urlsplit(link).scheme and not link.startswith('//'):
                parsed = urlsplit(link)
                target = root / unquote(parsed.path)
                assert target.is_file(), f'{name}: missing local page {link}'
                if parsed.fragment:
                    destination = Links(); destination.feed(target.read_text())
                    assert unquote(parsed.fragment) in destination.ids, f'{name}: missing target anchor {link}'
        if name == 'preview-all.html':
            for source in PAGES:
                assert '#guide-'+source.removesuffix('.html') in page.links
            assert 'offline-header' in html
            assert not any(x.endswith('.html') or '.html#' in x for x in page.links), 'Combined guide should navigate internally'
    print('PASS: five previews, navigation, unique IDs, anchor targets, embedded display dependencies')

if __name__=='__main__': main()
