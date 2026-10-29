"""Bring the piece's sections into the narrative page.

Usage: python3 build.py

Copies each section the narrative uses from its owner's folder (read only) into narrative/sections/<id>/, exactly as
assembly/build.py does for the joined page: section.js at the top of each copy, the section's adapter.js at the bottom
until the owner adopts it. It also copies section.js and tokens.css beside index.html, and fills index.html's sources panel
from assembly/sources-panel/*.md for the sections used here plus narrative/sources.md for this page's own footage.
"""
import glob, html, importlib.util, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ASM = '/mnt/project-files/assembly'
spec = importlib.util.spec_from_file_location('assembly_build', f'{ASM}/build.py')
ab = importlib.util.module_from_spec(spec); spec.loader.exec_module(ab)

USED = ['opening', 'loops', 'earbyarea', 'chartminute', 'bump', 'loop']
# the sources-panel files for those sections, in the order they appear in the narrative
PANEL = ['00-piece', '05-open', '20-opening', '65-loops', '25-earbyarea', '50-chartminute', '55-bump', '27-loop']


def copy_sections():
    for sid in USED:
        src, skip = ab.SECTIONS[sid]
        dst = f'{HERE}/sections/{sid}'
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*skip, 'mock'))
        page = open(f'{dst}/index.html', encoding='utf-8').read()
        for f in skip:
            page = re.sub(r'<source[^>]*src="%s"[^>]*>' % re.escape(f), '', page)
        for old, new in ab.PATCHES.get(sid, []):
            page = page.replace(old, new)
        if not re.match(r'\s*<!doctype', page, re.I):
            page = ab.SKELETON + page + '\n</body></html>\n'
        if 'section.js' not in page:
            page = re.sub(r'(<head[^>]*>)', r'\1<script src="../../section.js"></script>', page, count=1, flags=re.I)
            adapter = f'{ASM}/sections/{sid}/adapter.js'
            if os.path.exists(adapter):
                shutil.copy(adapter, f'{dst}/adapter.js')
                i = page.lower().rfind('</body>')
                page = page[:i] + '<script src="adapter.js"></script>\n' + page[i:]
        open(f'{dst}/index.html', 'w', encoding='utf-8').write(page)
    for f in ('section.js', 'tokens.css'):
        shutil.copy(f'{ASM}/{f}', f'{HERE}/{f}')
    pages = ''.join(open(f, encoding='utf-8').read() for f in glob.glob(f'{HERE}/sections/*/index.html'))
    if '../../shared/' in pages:
        shutil.copytree(f'{ASM}/shared', f'{HERE}/shared', dirs_exist_ok=True, ignore=shutil.ignore_patterns('README.md'))


def panel_files():
    return [f'{ASM}/sources-panel/{n}.md' for n in PANEL] + [f'{HERE}/sources.md']


def sources_html():
    credits, method = [], []
    for f in panel_files():
        head, cred, meth, into = '', [], [], None
        for line in open(f, encoding='utf-8').read().splitlines():
            line = html.escape(line.strip(), quote=False)
            if line.startswith('## '):
                head, into = line[3:], cred
            elif line == 'Methodology:':
                into = meth
            elif line and into is not None:
                into.append(f'<p>{line}</p>')
        if cred:
            credits += [f'<h3>{head}</h3>'] + cred
        if meth:
            method += [f'<h3>{head}</h3>'] + meth
    out = credits
    if method:
        out += ['<details class="method"><summary>Methodology</summary>'] + method + ['</details>']
    return '\n'.join(out)


def fill_sources():
    p = f'{HERE}/index.html'
    s = open(p, encoding='utf-8').read()
    s = re.sub(r'<!-- SOURCES -->.*?<!-- /SOURCES -->', lambda m: '<!-- SOURCES -->\n' + sources_html() + '\n<!-- /SOURCES -->', s, flags=re.S)
    open(p, 'w', encoding='utf-8').write(s)


if __name__ == '__main__':
    copy_sections()
    fill_sources()
    total = sum(os.path.getsize(f) for f in glob.glob(f'{HERE}/sections/**/*', recursive=True) if os.path.isfile(f))
    print(f'sections: {total / 1e6:.1f} MB')
