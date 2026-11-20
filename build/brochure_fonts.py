#!/usr/bin/env python3
"""Static fonts for the brochure PDF, so Illustrator sees real, named fonts it can edit with.

Variable fonts (Archivo, Newsreader) are cut into the exact static instances the brochure uses, with plain names:
  ArchivoCondensed-Black / -ExtraBold   (Archivo wdth 75, wght 900 / 800: the brand's "Archivo at 75% width")
  Newsreader-Italic                     (opsz 16, wght 400)
  IBMPlexMono-Regular / -Medium
  Pretendard-Regular / -Medium / -SemiBold / -Bold
  NotoSansKR-Regular / -SemiBold        (only the hanja the content uses, e.g. 色 形態 結晶: Pretendard has none)
Sources come from npm (pretendard, @fontsource*). All are SIL Open Font License.
Writes _brochure/fonts/*.ttf. Needs: pip install fonttools brotli; npm.

    python build/brochure_fonts.py
"""
import os, sys, glob, shutil, subprocess, tarfile
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '_brochure', 'fonts')
SRC = os.path.join(ROOT, '_brochure', 'fonts-src')
PKGS = ['@fontsource/noto-sans-kr@5.3.1', 'pretendard@1.3.9', '@fontsource-variable/archivo@5.3.0', '@fontsource-variable/newsreader@5.3.0', '@fontsource/ibm-plex-mono@5.3.0']


def fetch():
    os.makedirs(SRC, exist_ok=True)
    for p in PKGS:
        name = p.rsplit('@', 1)[0].lstrip('@').replace('/', '-')
        dest = os.path.join(SRC, name)
        if os.path.isdir(dest):
            continue
        tgz = subprocess.check_output(['npm', 'pack', '-q', p], cwd=SRC, text=True).strip().splitlines()[-1]
        os.makedirs(dest)
        with tarfile.open(os.path.join(SRC, tgz)) as t:
            t.extractall(dest, filter='data')
        os.remove(os.path.join(SRC, tgz))
    return lambda pattern: glob.glob(os.path.join(SRC, pattern), recursive=True)[0]


def rename(font, family, style, ps):
    """Plain names: family + style, so Illustrator lists them like the desktop versions."""
    n = font['name']
    for rec in list(n.names):
        if rec.nameID in (1, 2, 3, 4, 6, 16, 17, 25):
            n.removeNames(nameID=rec.nameID)
    full = f'{family} {style}'
    ribbi = style in ('Regular', 'Italic', 'Bold', 'Bold Italic')
    for nid, val in ((1, family if ribbi else full), (2, style if ribbi else 'Regular'), (3, f'{ps};STANDS-brochure'), (4, full), (6, ps), (16, family), (17, style)):
        n.setName(val, nid, 3, 1, 0x409)
        n.setName(val, nid, 1, 0, 0)
    for t in ('STAT', 'fvar', 'avar'):
        if t in font:
            del font[t]


def save(font, ps):
    font.flavor = None
    path = os.path.join(OUT, ps + '.ttf')
    font.save(path)
    print('font', os.path.relpath(path, ROOT))


def hanja_font(find, weight, style):
    """Noto Sans KR cut down to the characters in /content that Pretendard lacks (fontsource splits it into ~120 files)."""
    from fontTools.merge import Merger
    from fontTools import subset
    have = set(TTFont(find('pretendard/**/static/alternative/Pretendard-Regular.ttf')).getBestCmap())
    text = ''
    for f in glob.glob(os.path.join(ROOT, 'content', '**', '*.*'), recursive=True):
        if f.endswith(('.md', '.yml')):
            text += open(f, encoding='utf-8').read()
    need = {ord(c) for c in text if ord(c) > 0x2E7F and ord(c) not in have}
    if not need:
        return
    parts = []
    for f in sorted(glob.glob(os.path.join(SRC, f'fontsource-noto-sans-kr/**/noto-sans-kr-*-{weight}-normal.woff2'), recursive=True)):
        hit = need & set(TTFont(f).getBestCmap())
        if hit:
            t = TTFont(f)
            sub = subset.Subsetter(subset.Options())
            sub.populate(unicodes=hit)
            sub.subset(t)
            t.flavor = None
            tmp = os.path.join(SRC, f'part-{weight}-{len(parts)}.ttf')
            t.save(tmp)
            parts.append(tmp)
    if not parts:
        return
    f = Merger().merge(parts) if len(parts) > 1 else TTFont(parts[0])
    rename(f, 'Noto Sans KR', style, f'NotoSansKR-{style}')
    save(f, f'NotoSansKR-{style}')


def main():
    find = fetch()
    for w, style in ((400, 'Regular'), (600, 'SemiBold')):
        hanja_font(find, w, style)
    os.makedirs(OUT, exist_ok=True)
    for style in ('Regular', 'Medium', 'SemiBold', 'Bold'):
        shutil.copy(find(f'pretendard/**/static/alternative/Pretendard-{style}.ttf'), os.path.join(OUT, f'Pretendard-{style}.ttf'))
        print('font', f'_brochure/fonts/Pretendard-{style}.ttf')
    arch = find('fontsource-variable-archivo/**/archivo-latin-wdth-normal.woff2')
    for wght, style in ((900, 'Black'), (800, 'ExtraBold')):
        f = instancer.instantiateVariableFont(TTFont(arch), {'wdth': 75, 'wght': wght})
        f['OS/2'].usWeightClass, f['OS/2'].usWidthClass = wght, 3
        rename(f, 'Archivo Condensed', style, f'ArchivoCondensed-{style}')
        save(f, f'ArchivoCondensed-{style}')
    nr = TTFont(find('fontsource-variable-newsreader/**/newsreader-latin-opsz-italic.woff2'))
    axes = {a.axisTag: a for a in nr['fvar'].axes}
    loc = {'wght': 400}
    if 'opsz' in axes:
        loc['opsz'] = 16
    f = instancer.instantiateVariableFont(nr, loc)
    rename(f, 'Newsreader', 'Italic', 'Newsreader-Italic')
    save(f, 'Newsreader-Italic')
    for w, style in ((400, 'Regular'), (500, 'Medium')):
        f = TTFont(find(f'fontsource-ibm-plex-mono/**/ibm-plex-mono-latin-{w}-normal.woff2'))
        rename(f, 'IBM Plex Mono', style, f'IBMPlexMono-{style}')
        save(f, f'IBMPlexMono-{style}')


if __name__ == '__main__':
    main()
