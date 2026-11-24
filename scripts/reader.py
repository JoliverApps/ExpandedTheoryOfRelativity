"""Accessible reader structure and optional public readership statistics."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree, html


def enhance_reader(document, root):
    root = Path(root)
    body, head = document.find('body'), document.find('head')
    document.getroot().set('lang', 'en')
    main = document.xpath('//*[contains(concat(" ", @class, " "), " ltx_page_main ")]')[0]
    main.tag = 'main'
    main.set('id', 'paper')
    main.set('tabindex', '-1')
    main.set('aria-labelledby', 'paper-title')
    document.xpath('//h1')[0].set('id', 'paper-title')
    shortcuts = html.fragment_fromstring('''<div class="skip-links">
      <a href="#paper">Skip to paper</a><a href="#contents">Skip to contents</a>
    </div>''')
    body.insert(0, shortcuts)
    for heading in document.xpath('//*[contains(@class,"ltx_title_abstract")]'):
        heading.tag = 'h2'
        heading.set('id', 'abstract-title')
        heading.getparent().tag = 'section'
        heading.getparent().set('aria-labelledby', 'abstract-title')
    for heading in document.xpath('//*[contains(@class,"ltx_title_contents")]'):
        heading.tag = 'h2'
        heading.set('id', 'contents-title')
        heading.getparent().set('aria-labelledby', 'contents-title')
    sidebar = document.xpath('//aside[contains(@class,"reader-contents")]')[0]
    sidebar.set('id', 'contents')
    sidebar.set('tabindex', '-1')
    options = html.fragment_fromstring('''<details class="reading-options">
      <summary>Reading options</summary>
      <label for="reader-text-size">Text size</label>
      <select id="reader-text-size" disabled>
        <option value="1">Standard</option><option value="1.15">Large</option>
        <option value="1.3">Larger</option>
      </select>
      <label for="reader-theme">Colour scheme</label>
      <select id="reader-theme" disabled>
        <option value="auto">Use device setting</option><option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
      <noscript>Use your browser's zoom and colour settings to adjust the page.</noscript>
    </details>''')
    sidebar.append(options)
    status = etree.SubElement(sidebar, 'p', {'id': 'reader-status', 'class': 'sr-only', 'role': 'status'})
    status.text = ''
    for table in document.xpath('//table[contains(@class,"ltx_eqn_table")]'):
        # These tables arrange equations; they do not represent tabular data.
        table.set('role', 'presentation')
    for figure in document.xpath('//figure'):
        captions = figure.xpath('.//*[contains(@class,"ltx_caption")]')
        if captions:
            caption = captions[0]
            caption_id = caption.get('id') or figure.get('id') + '-caption'
            caption.set('id', caption_id)
            for svg in figure.xpath('.//*[local-name()="svg"]'):
                svg.set('aria-describedby', caption_id)
    for keyword_block in document.xpath('//*[contains(concat(" ",@class," ")," ltx_keywords ")]'):
        label = etree.Element('span', {'class': 'sr-only'})
        label.text = 'Keywords: '
        keyword_block.insert(0, label)
    for link in document.xpath('//a[contains(@class,"pdf-button")]'):
        link.set('type', 'application/pdf')
        link.set('data-goatcounter-click', 'expanded-relativity-pdf-download')
        link.set('data-goatcounter-title', 'PDF download click')
        link.set('data-goatcounter-no-session', '1')

    settings = json.loads((root / 'web/analytics.json').read_text())
    site = settings.get('goatcounter_url', '').strip().rstrip('/')
    if site:
        parts = urlsplit(site)
        if (parts.scheme != 'https' or not parts.hostname or
                not parts.hostname.endswith('.goatcounter.com') or
                parts.username or parts.password or parts.port or
                parts.path not in ('', '/count') or parts.query or parts.fragment):
            raise ValueError('Use the public HTTPS address of your hosted GoatCounter site.')
        site = 'https://' + parts.hostname
    analytics = {'url': site, 'public_totals': bool(settings.get('public_totals', False)),
                 'path': '/ExpandedTheoryOfRelativity/', 'event': 'expanded-relativity-pdf-download'}
    if site and analytics['public_totals']:
        statistics = html.fragment_fromstring('''<section class="reader-statistics" aria-labelledby="statistics-title">
          <h2 id="statistics-title">Readership</h2>
          <dl><div><dt>Visits</dt><dd id="visit-count" aria-busy="true" aria-label="Total not available yet">—</dd></div>
          <div><dt>PDF download clicks</dt><dd id="pdf-count" aria-busy="true" aria-label="Total not available yet">—</dd></div></dl>
          <p>Totals update periodically.</p>
          <p>Cookie-free aggregate statistics. <a href="https://www.goatcounter.com/help/privacy" rel="noreferrer">Privacy</a></p>
        </section>''')
        sidebar.append(statistics)
    config = etree.SubElement(body, 'script', {'id': 'reader-config', 'type': 'application/json'})
    config.text = json.dumps({'analytics': analytics}).replace('<', '\\u003c')
    script = root / 'web/reader.js'
    target = root / 'assets/reader.js'
    target.write_bytes(script.read_bytes())
    version = hashlib.sha256(script.read_bytes()).hexdigest()[:12]
    etree.SubElement(head, 'script', {'defer': 'defer', 'src': f'assets/reader.js?v={version}'})
