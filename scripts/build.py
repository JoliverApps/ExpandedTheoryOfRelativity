#!/usr/bin/env python3
"""Build the manuscript PDF and the complete reader website from the LaTeX source."""
from pathlib import Path
from lxml import etree, html
from reader import enhance_reader
import argparse
import hashlib
import io
import os
import re
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'ExpandedTheoryOfRelativity'
BUILD = ROOT / '_build'
REPO_URL = 'https://github.com/JoliverApps/ExpandedTheoryOfRelativity'
SITE_URL = 'https://joliverapps.github.io/ExpandedTheoryOfRelativity/'


def run(command, cwd, env=None, log=None):
    print('+', ' '.join(map(str, command)), flush=True)
    if log:
        with open(log, 'w') as stream:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            print(Path(log).read_text()[-12000:])
            raise RuntimeError(f'Build failed; see {log}')
    else:
        subprocess.run(command, cwd=cwd, env=env, check=True)


def install_fonts():
    """Keep external TeX dependencies in the disposable build directory."""
    dest = BUILD / 'texmf'
    marker = dest / '.ready'
    if marker.exists():
        return dest
    for package in ['boondox', 'mathalpha']:
        request = urllib.request.Request(
            f'https://ctan.math.illinois.edu/{"fonts" if package == "boondox" else "macros/latex/contrib"}/{package}.zip',
            headers={'User-Agent': 'ExpandedTheoryOfRelativity-build/1.0'})
        with urllib.request.urlopen(request, timeout=90) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        for entry in archive.infolist():
            parts = Path(entry.filename).parts
            if entry.is_dir() or '..' in parts:
                continue
            suffix = Path(entry.filename).suffix
            if suffix in ('.sty', '.fd'):
                target = dest / 'tex/latex' / package / Path(entry.filename).name
            elif suffix in ('.tfm', '.vf', '.pfb', '.map'):
                folder = {'.tfm': 'tfm', '.vf': 'vf', '.pfb': 'type1', '.map': 'map/dvips'}[suffix]
                target = dest / 'fonts' / folder / package / Path(entry.filename).name
            else:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(entry))
    marker.touch()
    return dest


def stage_source(destination):
    destination.mkdir(parents=True, exist_ok=True)
    for source in ROOT.glob('*.tex'):
        shutil.copy2(source, destination / source.name)
    shutil.copy2(ROOT / 'Bibliography.bib', destination / 'Bibliography.bib')
    shutil.copytree(ROOT / 'figs', destination / 'figs', dirs_exist_ok=True)


def prepare_web_source(pdf_dir, web_dir):
    stage_source(web_dir)
    shutil.copy2(pdf_dir / f'{NAME}.bbl', web_dir / f'{NAME}.bbl')
    source = web_dir / f'{NAME}.tex'
    text = source.read_text()
    # This unused xparse macro triggers an incompatibility in LaTeXML 0.8.8
    # with recent expl3 releases. The canonical manuscript remains untouched.
    if re.search(r'\\diff\b', ''.join(p.read_text() for p in ROOT.glob('ch_*.tex'))):
        raise RuntimeError('The manuscript now uses \\diff; add a LaTeXML binding before publishing.')
    text = re.sub(r'\\usepackage\{xparse\}.*?(?=\\usepackage\{amsthm\})', '', text, flags=re.S)
    text = text.replace('\\usepackage[cal=boondox]{mathalfa}', '')
    text = text.replace('\\preprint{APS/123-QED}', '')
    text = text.replace('\\input{LatestVersionNote}', '')
    text = text.replace('\\begin{document}', '\\begin{document}\n'
                        '\\setcitestyle{numbers,square}\n'
                        '\\renewcommand{\\thesubsection}{\\Alph{subsection}}\n'
                        '\\renewcommand{\\thesubsubsection}{\\arabic{subsubsection}}')
    text = text.replace('\\appendix', '\\appendix\n\\numberwithin{equation}{section}\n'
                        '\\renewcommand{\\theequation}{\\thesection\\arabic{equation}}')
    # Use BibTeX's actual output so citation order is identical to the PDF.
    text = text.replace('\\bibliography{Bibliography}', f'\\input{{{NAME}.bbl}}')
    source.write_text(text)


def finish_website(html_dir):
    document = html.parse(str(html_dir / 'index.html'))
    head, body = document.find('head'), document.find('body')
    # Remove generator comments from the delivered markup.
    for comment in document.xpath('//comment()'):
        comment.getparent().remove(comment)
    for link in head.findall('link'):
        if link.get('rel') == 'stylesheet':
            file = link.get('href')
            target = ROOT / 'assets' / file
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(html_dir / file, target)
            link.set('href', 'assets/' + file)
    css_version = hashlib.sha256((ROOT / 'web/paper.css').read_bytes()).hexdigest()[:12]
    etree.SubElement(head, 'link', rel='stylesheet', href=f'assets/paper.css?v={css_version}')
    etree.SubElement(head, 'link', rel='canonical', href=SITE_URL)
    abstract = document.xpath('//*[contains(concat(" ",@class," ")," ltx_abstract ")]')[0]
    abstract_text = ' '.join(''.join(abstract.itertext()).split())
    etree.SubElement(head, 'meta', name='description', content=abstract_text.removeprefix('Abstract ')[:300])
    etree.SubElement(head, 'meta', name='citation_title', content=''.join(head.find('title').itertext()).strip())
    etree.SubElement(head, 'meta', name='citation_author', content='Oliveira, J. Manuel')
    etree.SubElement(head, 'meta', name='citation_pdf_url', content=SITE_URL + NAME + '.pdf')
    etree.SubElement(head, 'meta', name='citation_public_url', content=SITE_URL)
    dates = document.xpath('//*[contains(concat(" ",@class," ")," ltx_dates ")]')
    if dates:
        etree.SubElement(head, 'meta', name='citation_date', content=''.join(dates[0].itertext()).strip('() '))
    top = html.fragment_fromstring(f'''<header class="reader-header"><a class="site-name" href="./">Expanded Theory of Relativity</a><nav aria-label="Paper formats"><a class="pdf-button" href="{NAME}.pdf" download>Download PDF</a></nav></header>''')
    body.insert(0, top)
    toc = document.xpath('//nav[contains(@class,"ltx_TOC")]')
    if toc:
        sidebar = etree.Element('aside', {'class': 'reader-contents', 'aria-label': 'Contents'})
        toc[0].getparent().remove(toc[0])
        contents_list = toc[0].find('ol')
        if contents_list is not None:
            entry = etree.SubElement(contents_list, 'li', {'class': 'ltx_tocentry'})
            etree.SubElement(entry, 'a', href='#bib').text = 'References'
        sidebar.append(toc[0])
        body.insert(1, sidebar)
    # REVTeX's optional author/year bibitem metadata is parsed separately by
    # LaTeXML. Display the numeric labels used by the PDF and inline citations.
    for number, item in enumerate(document.xpath('//*[contains(concat(" ",@class," ")," ltx_bibitem ")]'), 1):
        labels = item.xpath('.//*[contains(@class,"ltx_tag_bibitem")]')
        if labels:
            labels[0].clear()
            labels[0].set('class', 'ltx_tag ltx_tag_bibitem')
            labels[0].text = f'[{number}]'
    for footer in document.xpath('//*[contains(@class,"ltx_page_footer")]'):
        footer.getparent().remove(footer)
    # Ensure SVG text and shapes keep the original figure proportions.
    for svg in document.xpath('//*[local-name()="svg"]'):
        if not svg.get('viewBox'):
            svg.set('viewBox', f'0 0 {svg.get("width")} {svg.get("height")}')
        svg.set('role', 'img')
        svg.set('aria-label', 'Flag-and-Pole geometric framework')
    for node in document.xpath('//*[contains(concat(" ",@class," ")," ltx_equation ") or contains(concat(" ",@class," ")," ltx_equationgroup ")]'):
        if node.tag == 'table':
            parent = node.getparent()
            wrapper = etree.Element('div', {'class': 'equation-scroll'})
            parent.replace(node, wrapper)
            wrapper.append(node)
    enhance_reader(document, ROOT)
    output = etree.tostring(document, method='html', encoding='unicode', doctype='<!DOCTYPE html>')
    (ROOT / 'index.html').write_text(output)
    shutil.copy2(ROOT / 'web/paper.css', ROOT / 'assets/paper.css')


def validate_website():
    document = html.parse(str(ROOT / 'index.html'))
    ids = document.xpath('//*[@id]/@id')
    if len(ids) != len(set(ids)):
        raise RuntimeError('Duplicate HTML anchors')
    missing = {href for href in document.xpath('//a/@href') if href.startswith('#') and href[1:] not in ids}
    if missing:
        raise RuntimeError(f'Unresolved HTML links: {missing}')
    if document.xpath('//*[contains(@class,"ltx_ERROR")]'):
        raise RuntimeError('Unresolved LaTeXML elements')
    math_count = len(document.xpath('//*[local-name()="math"]'))
    if math_count < 500:
        raise RuntimeError(f'Missing rendered mathematics: {math_count}')
    if not document.xpath('//*[local-name()="svg"]'):
        raise RuntimeError('Missing Flag-and-Pole figure')
    def expanded_source(path):
        text = re.sub(r'(?<!\\)%.*', '', path.read_text())
        return re.sub(r'\\input\{([^}]+)\}',
                      lambda match: expanded_source(ROOT / (match[1] if match[1].endswith('.tex') else match[1] + '.tex')),
                      text)
    references = re.findall(r'\\(?:eqref|ref)\{(eq_[^}]+)\}', expanded_source(ROOT / f'{NAME}.tex'))
    aux_text = (BUILD / 'pdf' / f'{NAME}.aux').read_text()
    aux_labels = dict(re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]+)\}', aux_text))
    expected = [aux_labels[label] for label in references]
    actual = [''.join(link.itertext()).strip() for link in document.xpath('//a[starts-with(@href,"#") and contains(@href,".E")]')]
    if expected != actual:
        raise RuntimeError('Equation references differ between the PDF and HTML')
    bib_count = len(re.findall(r'\\bibcite\{', aux_text))
    bib_labels = [''.join(label.itertext()) for label in document.xpath('//*[contains(@class,"ltx_tag_bibitem")]')]
    if bib_labels != [f'[{number}]' for number in range(1, bib_count + 1)]:
        raise RuntimeError('Bibliography numbering differs between the PDF and HTML')
    print(f'Validated {math_count} mathematical expressions and {len(ids)} anchors.', flush=True)


def package_site():
    site = ROOT / '_site'
    site.mkdir(exist_ok=True)
    for name in ['index.html', NAME + '.pdf', '.nojekyll']:
        shutil.copy2(ROOT / name, site / name)
    shutil.copytree(ROOT / 'assets', site / 'assets', dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html-only', action='store_true', help='Reuse the previous PDF build for HTML styling changes')
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    pdf_dir, web_dir, html_dir = [BUILD / n for n in ['pdf', 'web-source', 'html']]
    if not args.html_only:
        fonts = install_fonts()
        environment = os.environ.copy()
        environment['TEXMFHOME'] = str(fonts)
        stage_source(pdf_dir)
        source = pdf_dir / f'{NAME}.tex'
        source.write_text('\\pdfmapfile{+boondox.map}\n' + source.read_text())
        run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', NAME + '.tex'], pdf_dir,
            environment, BUILD / 'pdf.log')
        shutil.copy2(pdf_dir / f'{NAME}.pdf', ROOT / f'{NAME}.pdf')
    prepare_web_source(pdf_dir, web_dir)
    converter = os.environ.get('LATEXMLC', 'latexmlc')
    command = ([converter] if not converter.endswith('.pl') else ['perl', converter])
    run(command + ['--format=html5', '--pmml', '--mathtex', '--svg', '--timeout=600',
                   '--destination=' + str(html_dir / 'index.html'), str(web_dir / f'{NAME}.tex')],
        ROOT, log=BUILD / 'html.log')
    finish_website(html_dir)
    validate_website()
    package_site()


if __name__ == '__main__':
    main()
