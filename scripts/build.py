#!/usr/bin/env python3
"""Validate the living HTML manuscript and package its website for GitHub Pages."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'


class ManuscriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.math_count = 0
        self.title_count = 0
        self.main_count = 0
        self.language = None
        self.configuration = []
        self.in_configuration = False

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        identifier = attributes.get('id')
        if identifier:
            if identifier in self.ids:
                raise ValueError(f'Duplicate HTML identifier: {identifier}')
            self.ids.add(identifier)
        if tag == 'html':
            self.language = attributes.get('lang')
        elif tag == 'h1':
            self.title_count += 1
        elif tag == 'main':
            self.main_count += 1
        elif tag == 'math':
            self.math_count += 1
        elif tag == 'a':
            href = attributes.get('href', '')
            self.links.append(href)
            target = urlsplit(href)
            if not target.scheme and target.path.lower().endswith(('.pdf', '.tex', '.bib')):
                raise ValueError(f'Outdated manuscript download link: {href}')
        elif tag == 'meta' and attributes.get('name') == 'citation_pdf_url':
            raise ValueError('Remove obsolete downloadable-edition metadata.')
        if identifier == 'pdf-count' or 'data-goatcounter-click' in attributes:
            raise ValueError('Only visits are counted on this website.')
        if tag == 'script' and identifier == 'reader-config':
            self.in_configuration = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_configuration = False

    def handle_data(self, data):
        if self.in_configuration:
            self.configuration.append(data)

    def validate(self):
        if self.language != 'en' or self.title_count != 1 or self.main_count != 1:
            raise ValueError('Preserve the document language, title, and main landmark.')
        if not {'paper', 'contents', 'paper-title', 'visit-count'}.issubset(self.ids):
            raise ValueError('Preserve reader navigation and the visits counter.')
        missing = {href for href in self.links if href.startswith('#') and unquote(href[1:]) not in self.ids}
        if missing:
            raise ValueError(f'Broken internal references: {sorted(missing)}')
        if self.math_count < 500:
            raise ValueError('Unexpected loss of mathematical content.')
        settings = json.loads(''.join(self.configuration))['analytics']
        if 'event' in settings:
            raise ValueError('Remove the obsolete download-event configuration.')
        endpoint = settings.get('url', '')
        if endpoint:
            parts = urlsplit(endpoint)
            if (parts.scheme != 'https' or not parts.hostname or
                    not parts.hostname.endswith('.goatcounter.com') or
                    parts.username or parts.password or parts.port or
                    parts.path not in ('', '/') or parts.query or parts.fragment):
                raise ValueError('Use the public HTTPS address of the GoatCounter site.')
        print(f'Validated {self.math_count} MathML expressions, {len(self.ids)} identifiers, and all internal links.')


def fingerprint_asset(match):
    asset = match.group('asset')
    path = (ROOT / asset).resolve()
    if not path.is_relative_to((ROOT / 'assets').resolve()) or not path.is_file():
        raise ValueError(f'Missing website asset: {asset}')
    digest = sha256(path.read_bytes()).hexdigest()[:12]
    return f'{match.group("attribute")}="{asset}?v={digest}"'


def main():
    for path in ROOT.iterdir():
        if path.is_file() and path.suffix.lower() in ('.pdf', '.tex', '.bib'):
            raise ValueError(f'This repository contains only the web edition: remove {path.name}')
    for path in (ROOT / 'assets').rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.pdf', '.tex', '.bib'):
            raise ValueError(f'Do not package a manuscript download: {path.name}')
    source = (ROOT / 'index.html').read_text()
    parser = ManuscriptParser()
    parser.feed(source)
    parser.close()
    parser.validate()
    pattern = r'''(?P<attribute>\b(?:href|src))=(?P<quote>["'])(?P<asset>assets/[^"'?#]+)(?:\?[^"']*)?(?P=quote)'''
    output = re.sub(pattern, fingerprint_asset, source)
    # Always clear old artifacts, including files from the former document build.
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    (SITE / 'index.html').write_text(output)
    for filename in ('404.html', '.nojekyll'):
        shutil.copy2(ROOT / filename, SITE / filename)
    shutil.copytree(ROOT / 'assets', SITE / 'assets')
    print('Website packaged in _site/.')


if __name__ == '__main__':
    main()
