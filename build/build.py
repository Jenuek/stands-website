#!/usr/bin/env python3
"""STANDS website builder.

Reads the editable content in /content (managed with Pages CMS) and writes the static site to /_site.
GitHub Actions runs this on every push to main and deploys _site to GitHub Pages.
Design lives here and in /assets; words and pictures live in /content.
"""
import json
import os, re, html, shutil, hashlib, sys
import yaml, markdown
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logo_new import BOX_PATHS, BOX_BAR, BOX_FRAME, WM_PATHS, WM_VIEW, WM_BAR, HERO_WA, HERO_WA_VIEW, HERO_ST, HERO_ST_VIEW

_gid = [0]
def _grad(x1, y1, x2, y2, start='currentColor'):
    _gid[0] += 1
    i = f'sg{_gid[0]}'
    return i, (f'<linearGradient id="{i}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
               f'<stop offset="0" stop-color="{start}"/><stop offset="1" stop-color="#7D7889"/></linearGradient>')

def logo_svg(cls='', label='WHERE ART STANDS', frame_attrs='', bar_attrs='', bar_w=None, ids=False, mono=False):
    """Box logo (slogan type) from the brand guide: gradient frame, letters, gradient underbar."""
    t = BOX_FRAME
    bx, by, bw, bh = BOX_BAR
    gf, df = _grad(0, 0, 400, 400)
    gb, db = _grad(round(bx, 2), 0, round(bx + bw, 2), 0)
    fid = ' id="frame"' if ids else ''
    bid = ' id="lbar"' if ids else ''
    w = bw if bar_w is None else bar_w
    if mono:  # header: drawn with mix-blend-mode difference, so one colour, no fill
        # The third line (STANDS, the last 6 glyphs) sits in its own clipped group, so site.js can wipe it out and in
        # and swap in other words set in Archivo 800 at 75% width (sized to match the logo glyphs: 80 units, -2.7 tracking).
        ps = re.findall(r'<path[^>]*/>', BOX_PATHS)
        return (f'<svg class="{cls}" viewBox="0 0 400 400" role="img" aria-label="{label}">'
                f'<defs><clipPath id="lw-clip"><rect class="lw-clip" x="30" y="240" width="340" height="80"/></clipPath></defs>'
                f'<rect x="{t/2:.2f}" y="{t/2:.2f}" width="{400-t:.2f}" height="{400-t:.2f}" fill="none" stroke="currentColor" stroke-width="{t*1.6:.2f}"/>'
                f'<g fill="currentColor">{"".join(ps[:-6])}</g>'
                f'<g class="lw-line" clip-path="url(#lw-clip)" fill="currentColor"><g class="lw-base">{"".join(ps[-6:])}</g>'
                f'<text class="lw-word" x="35.8" y="306.5" aria-hidden="true" style="display:none;font-family:var(--display);font-weight:800;font-stretch:75%;font-size:80px;letter-spacing:-2.7px"></text></g>'
                f'<rect class="lw-bar" x="{bx:.2f}" y="{by:.2f}" width="{bw:.2f}" height="{bh*1.3:.2f}" fill="currentColor"/></svg>')
    return (f'<svg class="{cls}" viewBox="0 0 400 400" role="img" aria-label="{label}"><defs>{df}{db}</defs>'
            f'<rect{fid} x="{t/2:.2f}" y="{t/2:.2f}" width="{400-t:.2f}" height="{400-t:.2f}" style="fill:var(--paper){";fill-opacity:.72" if ids else ""}" stroke="url(#{gf})" stroke-width="{t:.2f}"{frame_attrs}/>'
            f'<g fill="currentColor">{BOX_PATHS}</g>'
            f'<rect{bid} x="{bx:.2f}" y="{by:.2f}" width="{w:.2f}" height="{bh:.2f}" fill="url(#{gb})" data-w="{bw:.2f}"{bar_attrs}/></svg>')

def wordmark_svg():
    """Basic wordmark: STANDS with the black-to-lavender underbar (text colour to lavender on dark grounds)."""
    x, y, w, h = WM_BAR
    g, d = _grad(round(x, 2), 0, round(x + w, 2), 0)
    return (f'<svg class="wordmark" viewBox="{WM_VIEW}" role="img" aria-label="STANDS"><defs>{d}</defs>'
            f'<g fill="currentColor">{WM_PATHS}</g><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="url(#{g})"/></svg>')


SHAPES = [
    '<path d="M18 100V46a32 32 0 0 1 64 0v54H66V48a16 16 0 0 0-32 0v52z" fill="#111"/>',
    '<ellipse cx="50" cy="90" rx="30" ry="10" fill="#6E6B66"/><ellipse cx="52" cy="72" rx="22" ry="9" fill="#6E6B66"/><ellipse cx="48" cy="57" rx="15" ry="7" fill="#6E6B66"/><ellipse cx="51" cy="45" rx="9" ry="5" fill="#6E6B66"/>',
    '<rect x="30" y="62" width="40" height="38" fill="#C9C7C2"/><circle cx="50" cy="43" r="19" fill="#7D7889"/>',
    '<rect x="42" y="0" width="16" height="100" fill="#111"/>',
    '<circle cx="50" cy="44" r="30" fill="none" stroke="#7D7889" stroke-width="12"/><rect x="40" y="72" width="20" height="28" fill="#7D7889"/>',
    '<polygon points="50,100 82,60 50,20 18,60" fill="#6E6B66"/>',
    '<rect x="46" y="20" width="8" height="80" fill="#111"/><ellipse cx="50" cy="14" rx="6" ry="8" fill="#111"/>',
    '<rect x="26" y="40" width="20" height="60" fill="#8FCAD8"/><rect x="54" y="20" width="20" height="80" fill="#111"/>',
]


# ---------------------------------------------------------------------------
# language
# The site is built twice: Korean at the root, English under /en/.
# English text lives next to the Korean text in /content:
#   - plain fields:  an `en:` block in the same entry (e.g. en.title, en.summary, en.body)
#   - list items:    `<field>_en` inside the item (e.g. services[].title_en)
# An empty English field falls back to the Korean text, so translations can be filled in gradually.
# ---------------------------------------------------------------------------
LANG = 'ko'   # current build language
P = ''        # path prefix back to the site root ('' for Korean, '../' for English)

def EN():
    return LANG == 'en'

def U(ko, en):
    """Fixed interface text."""
    return en if EN() else ko

def _filled(v):
    return v not in (None, '', [], {}) and not (isinstance(v, str) and not v.strip())

def L(d, key, default=''):
    """A content field in the current language (falls back to Korean)."""
    d = d or {}
    if EN():
        v = (d.get('en') or {}).get(key)
        if _filled(v):
            return v
    v = d.get(key)
    return default if v is None else v

def LI(item, key, default=''):
    """A field of a list item in the current language (`key_en` falls back to `key`)."""
    item = item or {}
    if EN() and _filled(item.get(key + '_en')):
        return item.get(key + '_en')
    v = item.get(key)
    return default if v is None else v

def BODY(d):
    if EN():
        v = (d.get('en') or {}).get('body')
        if _filled(v):
            return v
    return d.get('_body')

def head(title, desc, name, og=None):
    t = 'STANDS' if title == 'STANDS' else f'{title} — STANDS'
    ko_url = f'{BASE_URL}{name}'
    en_url = f'{BASE_URL}en/{name}'
    canon = en_url if EN() else ko_url
    return f'''<!doctype html>
<html lang="{LANG}" data-base="{P}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(t)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">
<link rel="alternate" hreflang="ko" href="{ko_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{ko_url}">
<meta property="og:title" content="{E(t)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:image" content="{og or P + 'img/gallery.jpg'}">
<meta property="og:locale" content="{'en_US' if EN() else 'ko_KR'}">
<meta name="theme-color" content="#F0F0EE">
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4HENTDTYNP"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-4HENTDTYNP',{{site_language:'{LANG}'}});</script>
<!-- Microsoft Clarity -->
<script>(function(c,l,a,r,i,t,y){{c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);}})(window,document,"clarity","script","z46038c0ok");</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,800..900&family=Newsreader:ital,opsz,wght@1,6..72,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{P}assets/site.css?v={VER}">
</head>
<body>
'''


def hero():
    return f'''<section class="hero" id="hero" aria-label="WHERE ART STANDS">
  <div class="bg plain" id="bg"><img id="bgimg" alt="" hidden></div>
  <div class="tag" id="tag"></div>
  <div class="line" id="line" role="img" aria-label="WHERE ART STANDS">
    <span id="wa"><svg class="gl" width="4.9285em" height="0.74em" viewBox="{HERO_WA_VIEW}" aria-hidden="true" fill="currentColor" overflow="visible">{HERO_WA}</svg></span>
    <span class="slot"><span class="word" id="word"><svg class="gl" width="3.3249em" height="0.74em" viewBox="{HERO_ST_VIEW}" aria-hidden="true" fill="currentColor" overflow="visible">{HERO_ST}</svg></span><span class="ubar" id="ubar"></span><span class="obj" id="obj"></span></span>
  </div>
  <div class="loop" id="loop" aria-hidden="true">
    <video id="loopvid" muted loop playsinline preload="none" poster="{P}img/courtyard-poster.jpg"><source src="{P}video/courtyard-loop-v2.mp4" type="video/mp4"><source src="{P}video/courtyard-loop-v2.webm" type="video/webm"></video>
  </div>
  <div class="lockup" id="lockup">
    {logo_svg(ids=True, bar_w=0, frame_attrs=' pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"')}
  </div>
  <div class="scroll">SCROLL</div>
  <div class="controls"><button id="replay" type="button">{U('다시 보기', 'Replay')}</button></div>
</section>'''


# ---------------------------------------------------------------------------
# content loading
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, 'content')
OUT_ROOT = os.environ.get('STANDS_OUT', os.path.join(ROOT, '_site'))
OUT = OUT_ROOT
VER = os.environ.get('STANDS_VER', '20261028')
BASE_URL = os.environ.get('STANDS_URL', 'https://stands.art/')
E = html.escape

def T(v):
    """Escape text and keep the line breaks typed in the CMS."""
    return E(str(v or '').strip()).replace('\r\n', '\n').replace('\n', '<br>')

def read_md(path):
    raw = open(path, encoding='utf-8').read()
    data, body = {}, raw
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', raw, re.S)
    if m:
        data = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
    data['_path'] = os.path.relpath(path, ROOT).replace(os.sep, '/')
    # Pages CMS keeps the rich-text field named `body` below the front matter; accept either place.
    data['_body'] = data.get('body') or body
    return data

def slug_of(path, prefix):
    stem = os.path.splitext(os.path.basename(path))[0]
    if re.fullmatch(r'[a-z0-9-]+', stem):
        return stem if stem.startswith(prefix + '-') else f'{prefix}-{stem}'
    return f'{prefix}-' + hashlib.sha1(stem.encode('utf-8')).hexdigest()[:8]

def collection(name, prefix, sort):
    folder = os.path.join(CONTENT, name)
    items = []
    if os.path.isdir(folder):
        for fn in os.listdir(folder):
            if fn.endswith('.md') and not fn.startswith('_'):
                d = read_md(os.path.join(folder, fn))
                if d.get('hidden'):
                    continue
                d['_url'] = slug_of(fn, prefix) + '.html'
                items.append(d)
    return sorted(items, key=sort)

def img(p):
    """CMS stores '/img/x.jpg'; the site lives in a sub-folder, so use paths relative to the page."""
    p = (p or '').strip()
    if not p or re.match(r'^(https?:|data:)', p):
        return p
    return P + (p[1:] if p.startswith('/') else p)

def rich(md_text):
    out = markdown.markdown(md_text or '', extensions=['extra', 'sane_lists', 'nl2br'])
    return out.replace('src="/img/', f'src="{P}img/').replace('href="/img/', f'href="{P}img/')

def num(v, d=9999):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d

SITE = yaml.safe_load(open(os.path.join(CONTENT, 'site.yml'), encoding='utf-8')) or {}
H, AB, PG, CT, CO = (SITE.get(k, {}) or {} for k in ('home', 'about', 'pages', 'contact', 'company'))

PROJECTS = collection('projects', 'project', lambda d: (num(d.get('order')), d.get('title', '')))
for _p in PROJECTS:  # map-only entries get no page of their own; their links open the map
    if _p.get('map_only'):
        _p['_url'] = 'projects.html#map'
ARTISTS = collection('artists', 'artist', lambda d: (num(d.get('order')), d.get('name', '')))
ARTICLES = collection('editorial', 'article', lambda d: str(d.get('date', '')), )
ARTICLES.reverse()  # newest first
PUBLISHED = [a for a in ARTICLES if not a.get('upcoming')]  # upcoming issues are listed but get no page
BY_PATH = {d['_path']: d for d in PROJECTS + ARTISTS + ARTICLES}
BY_STEM = {}
for _d in PROJECTS + ARTISTS + ARTICLES:
    BY_STEM.setdefault(os.path.splitext(os.path.basename(_d['_path']))[0], _d)

def ref(r):
    """A CMS reference may be saved as a repo path, a leading-slash path or just the file name."""
    if not r:
        return None
    r = str(r).strip().lstrip('/')
    return BY_PATH.get(r) or BY_STEM.get(os.path.splitext(os.path.basename(r))[0])

def pick(refs):
    if isinstance(refs, str):
        refs = [refs]
    return [d for d in (ref(r) for r in (refs or [])) if d]

TYPES = {'space': ('공간 프로젝트', 'Space'), 'public': ('공공미술', 'Public Art'), 'exhibition': ('전시', 'Exhibition'),
         'trade': ('거래 · 자문', 'Dealing · Advisory'), 'handling': ('제작 · 설치', 'Fabrication · Installation')}
def type_name(k):
    t = TYPES.get(k)
    return U(*t) if t else ''

def sample(d):
    return f'<span class="sample">{U("예시", "Sample")}</span>' if d.get('sample') else ''

# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------
NAV = [('about.html', 'About'), ('artists.html', 'Artists'), ('projects.html', 'Projects'),
       ('editorial.html', 'Editorial'), ('contact.html', 'Contact')]

def lang_switch(name):
    """KO / EN links to the same page in the other language."""
    ko = (P + name) if EN() else name
    en = name if EN() else 'en/' + name
    on = ' aria-current="true"'
    return (f'<span class="lang"><a href="{ko}" hreflang="ko" lang="ko" data-lang="ko"{on if not EN() else ""}>KO</a> / '
            f'<a href="{en}" hreflang="en" lang="en" data-lang="en"{on if EN() else ""}>EN</a></span>')

def header(name, cur):
    AC = ' aria-current="page"'
    links = ''.join(f'<a href="{h}"{AC if h == cur else ""}>{n}</a>' for h, n in NAV)
    mlinks = ''.join(f'<a href="{h}">{n}</a>' for h, n in NAV)
    return f'''<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="index.html" aria-label="{U('STANDS 홈', 'STANDS home')}">{logo_svg(label="STANDS", mono=True)}</a>
    <nav class="nav" aria-label="{U('주요 메뉴', 'Main menu')}">{links}{lang_switch(name)}</nav>
    <button class="menu-btn" id="menu-open" type="button" aria-label="{U('메뉴 열기', 'Open menu')}" aria-controls="mobile-nav"><span></span><span></span></button>
  </div>
</header>
<div class="mobile-nav" id="mobile-nav" hidden>
  <button class="close" id="menu-close" type="button">{U('닫기', 'Close')}</button>
  <a href="index.html">Home</a>{mlinks}
  {lang_switch(name)}
</div>
'''

def footer():
    c = {k: L(CO, k) for k in ('name', 'ceo', 'business_no', 'art_service_no', 'ecommerce_no')}
    if EN():
        legal = (f'{E(c["name"])} · CEO {E(c["ceo"])} · Business Registration No. <span class="ph">{E(c["business_no"])}</span><br>'
                 f'Art Service Business Reg. No. <span class="ph">{E(c["art_service_no"])}</span> · E-commerce Reg. No. <span class="ph">{E(c["ecommerce_no"])}</span>')
    else:
        legal = (f'주식회사 {E(c["name"])} · 대표 {E(c["ceo"])} · 사업자등록번호 <span class="ph">{E(c["business_no"])}</span><br>'
                 f'미술서비스업 신고번호 <span class="ph">{E(c["art_service_no"])}</span> · 통신판매업 신고번호 <span class="ph">{E(c["ecommerce_no"])}</span>')
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="top">
      <div class="logo-col"><a class="logo" href="index.html" aria-label="{U('STANDS 홈', 'STANDS home')}">{wordmark_svg()}</a><span class="descriptor">Office for Art</span></div>
      <div><h4>Menu</h4><ul>{''.join(f'<li><a href="{h}">{n}</a></li>' for h, n in NAV)}</ul></div>
      <div><h4>Contact</h4><ul><li>{E(CT.get('email', ''))}</li><li>{E(L(CT, 'address'))}</li><li>{E(CT.get('tel', ''))}</li></ul></div>
      <div><h4>Follow</h4><ul><li>Instagram {E(CT.get('instagram', ''))}</li><li><a href="editorial.html">Editorial</a></li></ul></div>
    </div>
    <div class="legal">
      <div>{legal}{f'<br>{E(L(CO, "copyright"))}' if L(CO, 'copyright') else ''}</div>
      <div><a href="privacy.html">{U('개인정보처리방침', 'Privacy Policy')}</a> · © 2026 STANDS</div>
    </div>
  </div>
</footer>
<script src="{P}assets/site.js?v={VER}"></script>
'''

def page(name, title, desc, cur, body, extra_js='', og=None):
    doc = head(title, desc, name, og) + header(name, cur) + '<main id="main">\n' + body + '\n</main>\n' + footer() + extra_js + '</body>\n</html>\n'
    if EN():  # Korean placeholders such as [입력] or [대표 전화 입력] read as [To be added] on the English site
        doc = re.sub(r'\[[^\]<>]*[가-힣][^\]<>]*\]', '[To be added]', doc)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(doc)

# ---------------------------------------------------------------------------
# cards
# ---------------------------------------------------------------------------
def project_card(p):
    i = PROJECTS.index(p)
    typ = p.get('type', 'space')
    meta = ' · '.join(x for x in (f'No.{i+1:03d}', type_name(typ), L(p, 'location'), L(p, 'size')) if x)
    cover = img(p.get('cover'))
    ph = f'<img src="{E(cover)}" alt="" loading="lazy">' if cover else ''
    return (f'<a class="card" href="{p["_url"]}" data-type="{E(typ)}"><div class="ph">{ph}</div>'
            f'<span class="meta">{E(meta)}</span><h3>{E(L(p, "title"))}{sample(p)}</h3></a>')

def p_artists(p):
    """A project names one artist (`artist`) or several (`artists`, case studies)."""
    refs = list(p.get('artists') or []) or ([p.get('artist')] if p.get('artist') else [])
    return [ref(r) for r in refs if ref(r)]

# case study facts table: fixed keys and order, shared with the planned art map
FACTS = [('building', '건축물', 'Building'), ('location', '위치', 'Location'), ('context', '입지', 'Setting'),
         ('station', '가까운 역', 'Nearest station'), ('owner', '건축주', 'Client'),
         ('use', '용도', 'Use'), ('scale', '규모', 'Scale'), ('area', '면적', 'Area'), ('completed', '준공', 'Completed'), ('year', '연도', 'Year'),
         ('works', '미술작품', 'Artworks'), ('size', '규격', 'Dimensions'), ('material', '재료', 'Materials'),
         ('scope', '수행 범위', 'Scope'), ('budget', '총 예산', 'Total budget')]

def fact(p, k):
    ko = p.get('facts') or {}
    en = (p.get('en') or {}).get('facts') or {}
    v = en.get(k) if EN() and _filled(en.get(k)) else ko.get(k)
    return str(v).strip() if _filled(v) else ''

def map_group(p):
    """Filter group for the map, from the place type."""
    t = str(p.get('place_type') or '')
    if '업무' in t:
        return 'office', U('업무시설', 'Office')
    if '공동주택' in t or '주거' in t or '오피스텔' in t:
        return 'residential', U('주거', 'Residential')
    return 'mixed', U('복합 · 상업', 'Mixed-use')

def map_section():
    """Projects map (MapLibre): a list beside the map, pins, clusters and a summary card per pin."""
    pts = []
    for p in PROJECTS:
        if p.get('lat') in (None, '') or p.get('lng') in (None, ''):
            continue
        arts = p_artists(p)
        names = [L(a, 'name') for a in arts] + [str(n) for n in (L(p, 'artist_names') or []) if n]
        if not names and p.get('artist') and not ref(p.get('artist')):
            names = [L(p, 'artist')]
        g, gl = map_group(p)
        pts.append({'id': os.path.splitext(p['_path'].split('/')[-1])[0], 'lat': float(p['lat']), 'lng': float(p['lng']),
                    'title': L(p, 'title'), 'work': L(p, 'work'), 'artist': ', '.join(names), 'location': L(p, 'location'),
                    'year': str(p.get('year') or ''), 'type': L(p, 'place_type'), 'scope': L(p, 'scope'),
                    'group': g, 'groupLabel': gl, 'img': img(p.get('cover')), 'case': bool(p.get('case_study')),
                    'building': fact(p, 'building'), 'use': fact(p, 'use'), 'scale': fact(p, 'scale') or fact(p, 'area'),
                    'context': fact(p, 'context'), 'station': fact(p, 'station'), 'completed': fact(p, 'completed'),
                    'tags': [str(x) for x in (p.get('site_tags_en') if EN() else p.get('site_tags')) or (p.get('site_tags') or [])],
                    'source': L(p, 'facts_source'),
                    'url': '' if p.get('map_only') else p['_url']})
    if not pts:
        return ''
    groups = []
    for x in pts:
        if (x['group'], x['groupLabel']) not in groups:
            groups.append((x['group'], x['groupLabel']))
    chips = f'<button class="chip" type="button" data-mfilter="all" aria-pressed="true">{U("전체", "All")}</button>' + ''.join(
        f'<button class="chip" type="button" data-mfilter="{g}" aria-pressed="false">{E(l)}</button>' for g, l in groups)
    # location tags, in order of first appearance; a second row of chips that combines with the place type
    tags = []
    for x in pts:
        for tg in x['tags']:
            if tg not in tags:
                tags.append(tg)
    tag_html = (f'<div class="filters pmap-tags-f" role="group" aria-label="{U("입지", "Setting")}"><span class="k">{U("입지", "Setting")}</span>'
                + ''.join(f'<button class="chip sm" type="button" data-mtag="{E(tg)}" aria-pressed="false">{E(tg)}</button>' for tg in tags)
                + '</div>') if tags else ''
    data = json.dumps(pts, ensure_ascii=False).replace('</', '<\\/')
    i18n = json.dumps({'view': U('사례 보기', 'View case'), 'work': U('작품', 'Work'), 'use': U('용도', 'Use'),
                       'scale': U('규모', 'Scale'), 'context': U('입지', 'Setting'), 'station': U('교통', 'Transit'),
                       'completed': U('준공', 'Completed'), 'source': U('출처', 'Source'), 'count': U('{n}건', '{n} projects'), 'case': U('심층 사례', 'Case study'),
                       'artist': U('작가', 'Artist'), 'year': U('연도', 'Year'), 'type': U('용도', 'Use'), 'scope': U('수행 범위', 'Scope'),
                       'lang': LANG}, ensure_ascii=False)
    return (f'<section class="pmap-sec" id="map"><div class="wrap"><div class="sec-head"><h2>Project Map</h2>'
            f'<span class="meta pmap-total">{U("STANDS 프로젝트 위치", "STANDS project sites")} · <b>{len(pts)}</b>{U("건", "")}</span></div>'
            f'<div class="pmap"><aside class="pmap-side"><div class="filters pmap-filters" role="group" aria-label="{U("공간 유형", "Place type")}">{chips}</div>'
            f'{tag_html}'
            f'<p class="meta pmap-visible" aria-live="polite"></p><ol class="pmap-list"></ol></aside>'
            f'<div class="pmap-canvas" id="pmap" role="region" aria-label="{U("프로젝트 지도", "Project map")}"></div></div></div>'
            f'<script type="application/json" id="pmap-data">{data}</script><script type="application/json" id="pmap-i18n">{i18n}</script></section>')

def case_feature(p, n, total):
    """Case study on the Projects page: one full-bleed photo per case, title laid over the bottom."""
    cover = img(p.get('cover'))
    tall = img(p.get('cover_tall'))  # optional portrait crop for phones
    cf = str(p.get('cover_focus') or '').strip()
    focus = f' style="object-position:{E(cf)}"' if re.fullmatch(r'\d{1,3}% \d{1,3}%', cf) else ''
    meta = ' · '.join(x for x in (L(p, 'location'), str(p.get('year') or ''), L(p, 'place_type')) if x)
    # cases sit side by side in tall frames, so the portrait photo (when there is one) is used everywhere
    pic = f'<picture><img src="{E(tall or cover)}" alt="{E(L(p, "title"))}"{"" if tall else focus} loading="lazy"></picture>' if cover else ''
    return (f'<a class="case-hero{" on" if n == 1 else ""}" href="{p["_url"]}"><div class="ph">{pic}</div>'
            f'<span class="case-hero-spine" aria-hidden="true"><b>{n:02d}</b>{E(L(p, "title"))}</span>'
            f'<div class="case-hero-txt"><div class="wrap">'
            f'<span class="case-hero-no">{n:02d} / {total:02d}</span>'
            f'<span class="case-label">{U("STANDS 프로젝트", "STANDS Project")} · Case Study</span>'
            f'<h3{" class=" + chr(34) + "long" + chr(34) if len(L(p, "title")) > 10 else ""}>{E(L(p, "title"))}</h3>'
            f'<div class="case-hero-foot"><span class="meta">{E(meta)}</span><span class="more">{U("사례 보기", "View case")}</span></div>'
            f'</div></div></a>')

def case_stats(p):
    """Overview: the key figures as large numbers (from `stats[]`, up to 4)."""
    items = [x for x in (p.get('stats') or []) if x.get('value')][:4]
    if not items:
        return ''
    return '<ul class="case-stats">' + ''.join(
        f'<li><b>{E(str(x.get("value")))}<small>{E(str(LI(x, "unit") or ""))}</small></b><span>{E(LI(x, "label"))}</span></li>' for x in items) + '</ul>'

def case_locator(p):
    """Site analysis: a map with the site, the nearest station(s) and switchable analysis layers (green and water,
    road hierarchy, transit, buildings), with the site facts in a card laid over it. Drawn by assets/locator.js."""
    if p.get('lat') in (None, '') or p.get('lng') in (None, ''):
        return ''
    st = [{'name': LI(x, 'name'), 'lat': float(x['lat']), 'lng': float(x['lng'])} for x in (p.get('stations') or []) if x.get('lat') and x.get('lng')]
    d = json.dumps({'lat': float(p['lat']), 'lng': float(p['lng']), 'label': fact(p, 'building') or L(p, 'title'), 'stations': st,
                    'lang': LANG, 'km': U('직선 {d}km', '{d} km')}, ensure_ascii=False).replace('</', '<\\/')
    rows = [(U('용도', 'Use'), fact(p, 'use')), (U('규모', 'Scale'), fact(p, 'scale')), (U('입지', 'Setting'), fact(p, 'context')),
            (U('교통', 'Transit'), fact(p, 'station'))]
    tags = (p.get('site_tags_en') if EN() else p.get('site_tags')) or p.get('site_tags') or []
    card = (f'<div class="loc-card"><span class="meta">{U("대상지", "Site")}</span><h3>{E(fact(p, "building") or L(p, "title"))}</h3>'
            f'<p class="addr">{E(fact(p, "location"))}</p>'
            + (f'<ul class="loc-tags">{"".join(f"<li>{E(str(t))}</li>" for t in tags)}</ul>' if tags else '')
            + '<dl>' + ''.join(f'<dt>{k}</dt><dd>{E(v)}</dd>' for k, v in rows if v) + '</dl></div>')
    layers = [('green', U('녹지 · 수변', 'Green · water'), True), ('roads', U('도로 위계', 'Road hierarchy'), False),
              ('transit', U('대중교통', 'Transit'), True), ('buildings', U('건물', 'Buildings'), False)]
    chips = ''.join(f'<button type="button" class="chip sm" data-layer="{k}" aria-pressed="{"true" if on else "false"}">{E(n)}</button>' for k, n, on in layers)
    return (f'<figure class="case-fig locator"><div class="loc-wrap"><div class="locator-map" role="region" aria-label="{U("입지 분석 지도", "Site analysis map")}"></div>'
            f'<div class="loc-layers" role="group" aria-label="{U("분석 레이어", "Analysis layers")}">{chips}</div>{card}</div>'
            f'<script type="application/json" class="locator-data">{d}</script>'
            f'<figcaption>{U("입지 분석 지도 · 레이어를 켜고 끌 수 있습니다 · 지도 데이터 OpenStreetMap", "Site analysis map · switch the layers on and off · map data OpenStreetMap")}</figcaption></figure>')

def _dims(size):
    """'12,000 × 2,200 × 4,000(H)' -> (W, H) in mm, or None."""
    nums = [float(n.replace(',', '')) for n in re.findall(r'\d[\d,]*(?:\.\d+)?', str(size or ''))]
    return (nums[0], nums[2]) if len(nums) >= 3 else None

def case_scale(p):
    """Specifications: the works' outer dimensions (W × H) drawn to one scale beside a 1.7 m person, wrapped into rows."""
    works = [(LI(x, 'work'), _dims(LI(x, 'size') or x.get('size'))) for x in (p.get('specs') or [])]
    works = [(n, d) for n, d in works if d]
    if not works:
        return ''
    gap, row_max, person = 2500, 40000, 1700
    u = max(sum(W for _, (W, _) in works), 14000) / 640  # first guess of one screen pixel, refined below
    for _ in range(2):
        fs = 13 * u
        slot = lambda n, W: max(W, len(str(n)) * fs * 0.62 + fs)
        rows, cur, w = [], [], person + gap
        for n, (W, H) in works:
            if cur and w + slot(n, W) > row_max:
                rows.append(cur); cur, w = [], 0
            cur.append((n, W, H)); w += slot(n, W) + gap
        rows.append(cur)
        width = max(14000, max(sum(slot(n, W) + gap for n, W, _ in r) + (person + gap if k == 0 else 0) for k, r in enumerate(rows)))
        u = width / 640   # one screen pixel at the usual column width, so labels and lines stay the same size in every case
    fs, fd, sw = 13 * u, 11 * u, 1.3 * u
    tallest = max([H for r in rows for _, _, H in r] + [person])
    row_h = tallest + 4.2 * fs
    out = []
    for k, r in enumerate(rows):
        base = k * row_h + tallest
        x = 0
        out.append(f'<line x1="0" y1="{base:.0f}" x2="{width:.0f}" y2="{base:.0f}" stroke-width="{sw:.0f}" class="g"/>')
        if k == 0:  # a person, 1.7 m
            out.append(f'<g class="p" stroke-width="{1.6 * sw:.0f}" transform="translate(300 {base:.0f})"><circle cx="300" cy="-1550" r="150"/>'
                       f'<path d="M300 -1400 V-750 M300 -1250 L60 -900 M300 -1250 L540 -900 M300 -750 L120 0 M300 -750 L480 0"/></g>')
            x = person + gap
        for n, W, H in r:
            slot = max(W, len(str(n)) * fs * 0.62 + fs)  # never let a label run into the next work
            out.append(f'<rect x="{x:.0f}" y="{base - H:.0f}" width="{W:.0f}" height="{H:.0f}" stroke-width="{sw:.0f}" class="w"/>'
                       f'<text x="{x:.0f}" y="{base + 1.6 * fs:.0f}" font-size="{fs:.0f}" class="t">{E(n)}</text>'
                       f'<text x="{x:.0f}" y="{base + 2.9 * fs:.0f}" font-size="{fd:.0f}" class="d">{W / 1000:g} × {H / 1000:g}m</text>')
            x += slot + gap
    h = len(rows) * row_h
    return (f'<figure class="case-fig scale"><svg viewBox="{-u * 4:.0f} {-u * 10:.0f} {width + u * 8:.0f} {h + u * 10:.0f}" role="img" aria-label="{U("작품 크기 비교 도식", "Scale diagram of the works")}">{"".join(out)}</svg>'
            f'<figcaption>{U("작품 외곽 치수 (가로 × 높이), 같은 축척 · 사람 1.7m", "Outer dimensions of the works (width × height) to one scale · person 1.7 m")}</figcaption></figure>')

def case_daynight(p):
    dn = p.get('day_night') or {}
    if not (dn.get('day') and dn.get('night')):
        return ''
    cap = LI(dn, 'caption')
    return (f'<figure class="case-fig daynight"><div class="dn"><div><img src="{E(img(dn["day"]))}" alt="" loading="lazy"><span>{U("주간", "Day")}</span></div>'
            f'<div><img src="{E(img(dn["night"]))}" alt="" loading="lazy"><span>{U("야간", "Night")}</span></div></div>'
            f'{f"<figcaption>{E(cap)}</figcaption>" if cap else ""}</figure>')

def case_decisions(p):
    """Conditions -> decisions: each card links one site condition (and how STANDS read it) to one decision about the work.
    `draft: true` cards are kept out of the site until confirmed."""
    items = [x for x in (p.get('decisions') or []) if not x.get('draft') and x.get('condition') and x.get('decision')]
    if not items:
        return ''
    cards = ''.join(
        f'<li class="dcard"><div class="dhead"><span class="meta">{k:02d}</span><span class="dkind">{E(LI(x, "kind"))}</span></div>'
        f'<div class="dcond"><span class="meta">{U("조건", "Condition")}</span><p>{E(LI(x, "condition"))}</p>'
        f'{f"<p class={chr(34)}dread{chr(34)}>{E(LI(x, chr(114)+chr(101)+chr(97)+chr(100)+chr(105)+chr(110)+chr(103)))}</p>" if x.get("reading") else ""}</div>'
        f'<div class="darrow" aria-hidden="true">→</div>'
        f'<div class="ddec"><span class="meta">{U("결정", "Decision")}</span><p>{E(LI(x, "decision"))}</p>'
        f'{f"<span class={chr(34)}dsrc{chr(34)}>{E(LI(x, chr(101)+chr(118)+chr(105)+chr(100)+chr(101)+chr(110)+chr(99)+chr(101)))}</span>" if x.get("evidence") else ""}</div></li>'
        for k, x in enumerate(items, 1))
    return f'<ol class="decisions">{cards}</ol>'

def case_page(i, p):
    """Case study: fixed sections in a fixed order, each hidden when empty."""
    title = L(p, 'title')
    cover = img(p.get('cover'))
    arts = p_artists(p)
    # linked artists first, then artists without a page (`artist_names`)
    names = [f'<a href="{a["_url"]}">{E(L(a, "name"))}</a>' for a in arts] + [E(str(n)) for n in (L(p, 'artist_names') or []) if n]
    arts_html = ', '.join(names) or E(str(p.get('artist') or ''))
    head_meta = ' · '.join(x for x in (L(p, 'location'), str(p.get('year') or ''), L(p, 'place_type')) if x)

    def sec(n, label_ko, label_en, inner):
        return (f'<section class="case-sec"><div class="wrap two-col"><span class="eyebrow">{n:02d} · {U(label_ko, label_en)}</span>'
                f'<div>{inner}</div></div></section>') if inner else ''

    facts = ''.join(f'<dt>{U(ko, en)}</dt><dd>{E(fact(p, k))}</dd>' for k, ko, en in FACTS if fact(p, k))
    src = L(p, 'facts_source')
    facts_html = ((f'<dl class="kv case-facts">{facts}</dl>' + (f'<p class="facts-src">{U("출처", "Source")} · {E(src)}</p>' if src else '')) if facts else '')

    site_imgs = ''.join(f'<figure class="case-fig"><img src="{E(img(x.get("image")))}" alt="" loading="lazy"><figcaption>{E(LI(x, "caption"))}</figcaption></figure>'
                        for x in (p.get('site_images') or []) if x.get('image'))
    site_html = case_locator(p) + (f'<div class="case-figs">{site_imgs}</div>' if site_imgs else '') + (f'<div class="prose site-text">{rich(L(p, "site"))}</div>' if L(p, 'site') else '')

    rows = ''.join(f'<div class="case-row"><span class="meta">{E(LI(c, "condition"))}</span><h3>{E(LI(c, "work"))}</h3><p>{E(LI(c, "response"))}</p></div>'
                   for c in (p.get('curation') or []))
    intro = L(p, 'curation_intro')
    body = BODY(p)
    cur_html = ((f'<p class="case-intro">{T(intro)}</p>' if intro else '') + (f'<div class="case-rows">{rows}</div>' if rows else '')
                + (f'<div class="prose case-note">{rich(body)}</div>' if body and str(body).strip() else ''))

    spec_rows = ''.join(f'<tr><th scope="row">{E(LI(x, "work"))}</th><td>{E(LI(x, "size"))}</td><td>{E(LI(x, "material"))}</td></tr>'
                        for x in (p.get('specs') or []))
    spec_html = ((f'<div class="case-table"><table><thead><tr><th scope="col">{U("작품", "Work")}</th><th scope="col">{U("규격 (mm)", "Dimensions (mm)")}</th>'
                  f'<th scope="col">{U("재료", "Materials")}</th></tr></thead><tbody>{spec_rows}</tbody></table></div>') if spec_rows else '') + \
                (f'<p class="case-intro">{T(L(p, "specs_note"))}</p>' if L(p, 'specs_note') else '') + case_scale(p)

    res = ''.join(f'<figure class="case-fig"><img src="{E(img(x.get("image")))}" alt="" loading="lazy"><figcaption>{E(LI(x, "caption"))}</figcaption></figure>'
                  for x in (p.get('results') or []) if x.get('image'))
    res_html = case_daynight(p) + (f'<div class="case-figs results">{res}</div>' if res else '')

    steps = ''.join(f'<li><span class="meta">{k:02d}</span><span>{E(LI(x, "title"))}</span></li>' for k, x in enumerate(p.get('process') or [], 1))
    proc_html = f'<ol class="case-steps">{steps}</ol>' if steps else ''

    dec = case_decisions(p)
    if dec:  # decisions replace the older condition / work / response rows
        cur_html = (dec
                    + (f'<div class="prose case-note">{rich(body)}</div>' if body and str(body).strip() else ''))
    blocks = [('사이트와 조건', 'Site and conditions', site_html), ('조건과 결정', 'Conditions → decisions', cur_html),
              ('작품 사양', 'Specifications', spec_html), ('결과', 'Result', res_html), ('프로세스 · 수행 범위', 'Process · Scope', proc_html),
              ('근거 자료', 'Reference data', facts_html)]
    secs, n = '', 0
    for ko, en, inner in blocks:
        if inner:
            n += 1
            secs += sec(n, ko, en, inner)
    cap = L(p, 'cover_caption')
    credit = L(p, 'credit')
    others = [q for q in PROJECTS if q is not p and not q.get('map_only')]
    nxt = [others[(i + k) % len(others)] for k in range(min(3, len(others)))] if others else []
    body_html = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">{U("STANDS 프로젝트", "STANDS Project")} · Case Study</span><h1 class="long">{E(title)}</h1>
<p class="case-head-meta"><span>{arts_html}</span><span class="meta">{E(head_meta)}</span></p>
<p class="lead">{T(L(p, 'summary'))}</p></div></div>
{f'<figure class="full-ph case-cover"><img src="{E(cover)}" alt="{E(title)}">{f"<figcaption>{E(cap)}</figcaption>" if cap else ""}</figure>' if cover else ''}
{f'<div class="wrap case-stats-wrap">{case_stats(p)}</div>' if case_stats(p) else ''}
{secs}
{f'<div class="wrap case-credit">{E(credit)}</div>' if credit else ''}
{f'<section><div class="wrap"><div class="sec-head"><h2>Next</h2></div><div class="cards">{"".join(project_card(q) for q in nxt)}</div></div></section>' if nxt else ''}'''
    loc_js = (f'<link rel="stylesheet" href="{P}assets/vendor/maplibre-gl.css?v={VER}">'
              f'<script src="{P}assets/vendor/maplibre-gl.js?v={VER}"></script><script src="{P}assets/locator.js?v={VER}"></script>') if 'locator-map' in body_html else ''
    page(p['_url'], title or 'Project', L(p, 'summary') or U('STANDS 프로젝트.', 'Project by STANDS.'), 'projects.html', body_html, extra_js=loc_js, og=cover or None)

def home_case(p, n):
    """Home: one selected project as two grid cells, matching the 4-column Artists grid: a tall photo (3:5, like the artist cards)
    and a text column beside it (number, title, a thick rule, place · year · use, setting; the key figure at the foot)."""
    cover = img(p.get('cover_tall')) or img(p.get('cover'))
    cf = str(p.get('home_focus') or ('' if p.get('cover_tall') else p.get('cover_focus')) or '').strip()
    focus = f' style="object-position:{E(cf)}"' if re.fullmatch(r'\d{1,3}% \d{1,3}%', cf) else ''
    meta = ' · '.join(x for x in (L(p, 'location'), str(p.get('year') or ''), L(p, 'place_type')) if x)
    fig = L(p, 'key_figure')
    ctx = fact(p, 'context')
    ph = f'<img src="{E(cover)}" alt="{E(L(p, "title"))}" loading="lazy"{focus}>' if cover else ''
    return (f'<a class="hcase" href="{p["_url"]}"><div class="ph">{ph}</div>'
            f'<div class="txt"><span class="meta">{n:02d} · {U("STANDS 프로젝트", "STANDS Project")}</span><h3>{E(L(p, "title"))}</h3>'
            f'<span class="meta sub">{E(meta)}</span>{f"<p class={chr(34)}ctx{chr(34)}>{E(ctx)}</p>" if ctx else ""}'
            f'<div class="foot">{f"<b class={chr(34)}fig{chr(34)}>{E(fig)}</b>" if fig else ""}<span class="more">{U("사례 보기", "View case")}</span></div></div></a>')

# reference places for the home map teaser (lon, lat, KO, EN)
def map_teaser():
    """Home: one quiet line under the selected projects that leads to the Projects map."""
    if not any(p.get('lat') not in (None, '') for p in PROJECTS):
        return ''
    return (f'<p class="map-line"><a href="projects.html#map"><span class="meta">Project Map</span>'
            f'<span>{U("프로젝트 위치 전체 보기", "See all project sites")}</span><span aria-hidden="true">→</span></a></p>')

def artist_card(a):
    i = ARTISTS.index(a)
    photo = img(a.get('photo'))
    plate = (f'<img src="{E(photo)}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover">' if photo
             else f'<svg viewBox="0 0 100 100" aria-hidden="true">{SHAPES[i % 8]}</svg>')
    q = real_quote(a)
    plate += f'<span class="plate-q">{E(q)}</span>' if q and photo else ''
    return (f'<a class="artist" href="{a["_url"]}"><div class="plate">{plate}</div>'
            f'<span class="meta">{E(L(a, "medium"))}</span><h3>{E(L(a, "name"))}{sample(a)}</h3></a>')

def real_quote(a):
    """The artist's own sentence, unless it is still the placeholder text."""
    q = L(a, 'quote')
    return '' if not q or '자리입니다' in str(a.get('quote') or '') else q

def artist_spread(a, n):
    """Artists page entry laid out like the company profile: tall detail crop, number, name, rule, the artist's sentence, short bio at the foot."""
    photo = img(a.get('photo'))
    alt = img(a.get('hero_image'))  # the work in place, shown on hover
    pic = (f'<img class="a" src="{E(photo)}" alt="" loading="lazy">' if photo else '') + \
          (f'<img class="b" src="{E(alt)}" alt="" loading="lazy">' if alt and alt != photo else '')
    sub = ' · '.join(x for x in (L(a, 'medium'), L(a, 'based')) if x)
    q = real_quote(a)
    return (f'<a class="artist-spread" href="{a["_url"]}"><div class="ph">{pic}</div>'
            f'<div class="txt"><span class="meta">Artist {n:02d}</span><h2>{E(L(a, "name"))}{sample(a)}</h2>'
            f'<span class="meta sub">{E(sub)}</span>'
            f'{f"<p class={chr(34)}q{chr(34)}>{E(q)}</p>" if q else ""}'
            f'<p class="bio">{T(L(a, "summary"))}</p><span class="more">{U("작가 보기", "View artist")}</span></div></a>')

def latest(a):
    """LATEST tag on the newest published issue (moves on by itself when the next one is published)."""
    return '<span class="latest">Latest</span>' if PUBLISHED and a is PUBLISHED[0] else ''

def article_row(a):
    if a.get('upcoming'):  # listed as a teaser: not a link, no page built yet
        return (f'<div class="row upcoming" aria-disabled="true"><span class="meta">Issue {E(str(a.get("issue", "")))}</span>'
                f'<h3>{E(L(a, "title"))}</h3><span class="meta soon">{U("공개 예정", "Coming soon")}</span></div>')
    return (f'<a href="{a["_url"]}"><span class="meta">Issue {E(str(a.get("issue", "")))}</span>'
            f'<h3>{E(L(a, "title"))}{sample(a)}{latest(a)}</h3><span class="meta">{E(str(a.get("date", "")))}</span></a>')

# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def build_lang():
    # home
    fp = [p for p in (pick(H.get('featured_projects')) or PROJECTS) if p.get('case_study')] or [p for p in PROJECTS if p.get('case_study')]
    fa = pick(H.get('featured_artists')) or ARTISTS[:4]
    fe = [a for a in (pick(H.get('featured_article')) or PUBLISHED[:1]) if not a.get('upcoming')] or PUBLISHED[:1]
    services = H.get('services', []) or []
    # line illustrations from build/illust.js (img/illust/service-01..03.svg), one per card in order
    def svc_ill(i):
        fn = f'img/illust/service-{i + 1:02d}.svg'
        return f'<img class="ill" src="{P}{fn}" alt="" width="240" height="240" loading="lazy">' if os.path.exists(os.path.join(ROOT, fn)) else ''
    svc = ''.join(f'<div class="svc">{svc_ill(i)}<span class="k">{E(LI(s, "label"))}</span><h3>{E(LI(s, "title"))}</h3><p>{T(LI(s, "text"))}</p><span class="plinth"></span></div>'
                  for i, s in enumerate(services))
    ncls = ' three' if len(services) == 3 else ''
    ed = ''
    if fe:
        a = fe[0]
        cover = img(a.get('cover'))
        _cf = str(a.get('cover_focus') or '').strip()
        cfocus = f' style="object-position:{E(_cf)}"' if re.fullmatch(r'\d{1,3}% \d{1,3}%', _cf) else ''
        ed = f'''<section class="editorial-band" aria-labelledby="ed-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="ed-h">Where art<br>stands?</h2><a class="more accent-it" href="editorial.html">Editorial</a></div>
    <a class="ed-feature" href="{a['_url']}">
      <div class="ph">{f'<img src="{E(cover)}" alt="" loading="lazy"{cfocus}>' if cover else ''}</div>
      <div><span class="issue">ISSUE {E(str(a.get('issue', '')))}</span>{latest(a)}<h3>{E(L(a, 'title'))}</h3><p>{T(L(a, 'summary'))}</p><span class="more">{U('읽기', 'Read')}</span></div>
    </a>
  </div>
</section>'''
    st_src = img(H.get('statement_image'))
    st_img = f'<figure class="statement-img"><img src="{E(st_src)}" alt="" width="1200" height="1500" loading="lazy"></figure>' if st_src else ''
    home = hero() + f'''
<section class="statement">
  <div class="wrap">
    <span class="eyebrow">STANDS · Office for Art</span>
    <h1 class="reveal">{E(L(H, 'headline'))} <span class="en ul">STANDS</span>.</h1>
    <div class="grid">
      <div class="story">
        <p>{T(L(H, 'story_1'))}</p>
        <p class="slogan">WHERE ART STANDS</p>
        <p>{T(L(H, 'story_2'))}</p>
        {'<p class="story-more"><a class="more" href="about.html">About STANDS</a></p>' if st_img else ''}
      </div>
      {f'<div class="statement-side">{st_img}</div>' if st_img else '<p><a class="more" href="about.html">About STANDS</a></p>'}
    </div>
  </div>
</section>

<section class="home-projects" aria-labelledby="pj-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="pj-h">Selected Projects</h2><a class="more" href="projects.html#map">{U('프로젝트 맵', 'Project Map')}</a></div>
    <div class="hcases">{''.join(home_case(p, k) for k, p in enumerate(fp, 1))}</div>
  </div>
</section>

<section class="services" aria-labelledby="svc-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="svc-h">What we do</h2><a class="more" href="about.html#scope">{U('업무 범위', 'Scope')}</a></div>
    <div class="svc-grid{ncls}">{svc}</div>
  </div>
</section>

<section aria-labelledby="ar-h" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><h2 id="ar-h">Artists</h2><a class="more" href="artists.html">{U('전체 작가', 'All artists')}</a></div>
    <div class="artist-grid">{''.join(artist_card(a) for a in fa)}</div>
  </div>
</section>

{ed}

<section class="cta">
  <div class="wrap">
    <span class="eyebrow" style="color:#9A98A0">Contact</span>
    <h2>{T(L(H, 'cta_title'))}</h2>
    <a class="btn" href="contact.html">{E(L(H, 'cta_button', U('문의', 'Contact')))}</a>
  </div>
</section>'''
    page('index.html', 'STANDS',
         U(f"{H.get('headline', '')} STANDS. 작품 선정 · 거래, 아트 프로젝트 기획, 건축물 미술작품 제작 · 설치를 직접 수행하는 아트 컴퍼니.",
           f"{L(H, 'headline')} STANDS. An art company that selects and deals works, plans art projects, and fabricates and installs architectural art."),
         'index.html', home, f'<script src="{P}assets/hero.js?v={VER}"></script>\n')

    # about
    paras = ''.join(f'<p>{T(t)}</p>' for t in (L(AB, 'paragraphs', []) or []))
    # What we do cards: big number, label, title and the list of services.
    # Older entries with a single `text` ("title - a, b, c") are still read.
    def wwd_card(r, last):
        lab = str(LI(r, 'label') or '').strip()
        m = re.match(r'^(\d+)\.?\s*(.*)$', lab)
        num, name = (m.group(1), m.group(2)) if m else ('', lab)
        title, items = LI(r, 'title'), LI(r, 'items', []) or []
        if not title and LI(r, 'text'):
            parts = re.split(r'\s+[-–—]\s+', str(LI(r, 'text')).strip(), maxsplit=1)
            title, items = parts[0], (re.split(r'\s*[,;]\s*', parts[1]) if len(parts) > 1 else [])
        lis = ''.join(f'<li>{E(str(i).strip())}</li>' for i in items if str(i).strip())
        return (f'<div class="wwd-card{" partner" if last and "PARTNER" in name.upper() else ""}">'
                f'<span class="n">{E(num)}</span><span class="k">{E(name)}</span><h3>{E(str(title).strip())}</h3>'
                f'{f"<ul>{lis}</ul>" if lis else ""}</div>')
    wwd = AB.get('what_we_do', []) or []
    kv = ''.join(wwd_card(r, i == len(wwd) - 1) for i, r in enumerate(wwd))
    # process pictograms from build/process.js (img/illust/process-01..06.svg)
    PROCESS = [('01', '공간 분석', 'Site study'), ('02', '작품 제안', 'Proposal'), ('03', '심의', 'Review'),
               ('04', '제작', 'Fabrication'), ('05', '운송 · 설치', 'Transport · installation'), ('06', '완성', 'In place')]
    steps = ''.join(f'<li><img src="{P}img/illust/process-{n}.svg" alt="" width="240" height="232" loading="lazy">'
                    f'<span class="k">{n}</span><span class="t">{U(ko, en)}</span></li>'
                    for n, ko, en in PROCESS if os.path.exists(os.path.join(ROOT, f'img/illust/process-{n}.svg')))
    process_band = f'''<section class="process" aria-labelledby="pr-h" style="padding-top:clamp(56px,8vw,110px)">
  <div class="wrap">
    <div class="sec-head"><h2 id="pr-h">Process</h2></div>
    <ol class="process-steps">{steps}</ol>
  </div>
</section>''' if steps else ''
    ab_src = img(AB.get('intro_image'))
    ab_img = f'<figure class="about-img"><img src="{E(ab_src)}" alt="" width="660" height="755" loading="lazy"></figure>' if ab_src else ''
    about = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">About</span><h1 class="long">Art is complete<br>where it <span class="ul">stands</span>.</h1></div></div>
<section>
  <div class="wrap two-col{' has-img' if ab_img else ''}">
    <div class="about-side"><span class="eyebrow">STANDS</span>{ab_img}</div>
    <div class="prose about-copy">
      {paras}
      <p class="close">{E(L(AB, 'closing'))}</p>
    </div>
  </div>
</section>
{process_band}
<section class="services" id="scope" aria-labelledby="scope-h" style="padding-top:clamp(56px,8vw,110px)">
  <div class="wrap">
    <div class="sec-head"><h2 id="scope-h">Scope</h2></div>
    <div class="wwd-grid">{kv}</div>
  </div>
</section>
<section class="cta"><div class="wrap"><h2>{T(L(AB, 'cta_title'))}</h2><a class="btn" href="contact.html">{E(L(AB, 'cta_button', U('문의하기', 'Get in touch')))}</a></div></section>'''
    page('about.html', 'About', U('작품 선정부터 설치까지, 한 팀이 맡는 아트 컴퍼니 STANDS.',
                                  'STANDS is an art company where one team takes a work from selection to installation.'),
         'about.html', about)

    # artists
    artists = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Artists</span><h1>Artists</h1>
<p class="lead">{T(L(PG, 'artists_lead'))}</p></div></div>
<section><div class="wrap"><div class="artist-spreads">{''.join(artist_spread(a, k) for k, a in enumerate(ARTISTS, 1))}</div></div></section>'''
    page('artists.html', 'Artists', U('STANDS 작가.', 'Artists of STANDS.'), 'artists.html', artists)

    for a in ARTISTS:
        # sample projects are placeholders, so they are not shown on a real artist's page
        works = [p for p in PROJECTS if any(x is a for x in p_artists(p)) and not (p.get('sample') and not a.get('sample'))]
        hist = ''.join(f'<div class="row"><span class="meta">{E(str(h.get("year", "")))}</span><h3>{E(LI(h, "title"))}</h3><span class="meta">{E(LI(h, "place"))}</span></div>'
                       for h in (a.get('history') or []))
        photo = img(a.get('photo'))
        name = L(a, 'name')
        # every block below is optional: an artist with only a name and a summary still gets a tidy page
        hero_src = img(a.get('hero_image')) or photo
        cap = L(a, 'hero_caption')
        hero_html = (f'<figure class="full-ph artist-hero"><img src="{E(hero_src)}" alt="{E(cap or name)}">'
                     f'{f"<figcaption>{E(cap)}</figcaption>" if cap else ""}</figure>') if hero_src else ''
        quote = L(a, 'quote')
        quote_html = (f'<section class="artist-quote"><div class="wrap"><blockquote><p>{E(quote)}</p>'
                      f'<cite>— {E(name)}</cite></blockquote></div></section>') if quote else ''
        # works: optional `group` starts a sub-heading when it changes (e.g. hanging / wall / proposals);
        # `contain` shows the whole photo (wide panels); a work without a photo keeps an empty frame as a placeholder
        wlist = [w for w in (a.get('works') or []) if w.get('image') or w.get('title')]
        works_html, cur = '', None
        for w in wlist:
            g = LI(w, 'group')
            if g != cur:
                works_html += f'<h3 class="works-group">{E(g)}</h3>' if g else ''
                cur = g
            pic = (f'<img src="{E(img(w["image"]))}" alt="{E(LI(w, "title"))}" loading="lazy">' if w.get('image') else '')
            meta = " · ".join(x for x in (str(w.get("year") or ""), LI(w, "material"), LI(w, "size")) if x)
            works_html += (f'<figure class="work{" contain" if w.get("contain") else ""}{" empty" if not w.get("image") else ""}"><div class="ph">{pic}</div>'
                           f'<figcaption><span class="t">{E(LI(w, "title"))}</span><span class="m">{E(meta)}</span></figcaption></figure>')
        works_sec = (f'<section class="artist-works"><div class="wrap"><div class="sec-head"><h2>Selected Works</h2>'
                     f'<a class="more" href="contact.html">{U("작품 문의", "Inquire about works")}</a></div><div class="works-grid">{works_html}</div></div></section>') if works_html else ''
        note, fit = L(a, 'note'), [x for x in (L(a, 'fit', []) or []) if x]
        note_sec = (f'<section class="artist-note"><div class="wrap two-col"><span class="eyebrow">STANDS Note</span><div>'
                    f'{f"<p class=\"note\">{T(note)}</p>" if note else ""}'
                    f'{("<div class=\"fit\"><span class=\"k\">" + U("어울리는 자리", "Where it fits") + "</span><ul>" + "".join(f"<li>{E(x)}</li>" for x in fit) + "</ul></div>") if fit else ""}'
                    f'</div></div></section>') if (note or fit) else ''
        inst = [i for i in (a.get('installs') or []) if i.get('image')]
        inst_html = ''.join(f'<figure><div class="ph"><img src="{E(img(i["image"]))}" alt="{E(LI(i, "place"))}" loading="lazy"></div>'
                            f'<figcaption><span class="t">{E(LI(i, "place"))}</span><span class="m">{E(str(i.get("year") or ""))}</span></figcaption></figure>' for i in inst)
        inst_sec = (f'<section class="artist-installs"><div class="wrap"><div class="sec-head"><h2>Installed</h2></div>'
                    f'<div class="installs">{inst_html}</div></div></section>') if inst_html else ''
        facts = [(k, v) for k, v in (('Born', str(L(a, 'born') or '')), ('Based', L(a, 'based')), ('Media', L(a, 'medium'))) if v and not str(v).startswith('[')]
        kv = ''.join(f'<dt>{k}</dt><dd>{E(v)}</dd>' for k, v in facts)
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Artist · {E(L(a, 'medium'))}</span><h1>{E(name)}</h1>
<p class="lead">{T(L(a, 'summary'))}{sample(a)}</p></div></div>
{hero_html}
{quote_html}
{works_sec}
{note_sec}
{inst_sec}
{f'<section style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>Projects</h2></div><div class="cards">{"".join(project_card(p) for p in works)}</div></div></section>' if works else ''}
<section class="artist-cv"><div class="wrap two-col">
  <div><span class="eyebrow">Profile</span><dl class="kv">{kv}<dt>Contact</dt><dd><a class="more" href="contact.html">{U('작품 문의', 'Inquire about works')}</a></dd></dl></div>
  <div class="prose">{rich(BODY(a))}</div>
</div></section>
{f'<section style="padding-top:0"><div class="wrap two-col"><span class="eyebrow">Solo Exhibitions</span><div class="list">{hist}</div></div></section>' if hist else ''}'''
        page(a['_url'], name or 'Artist', L(a, 'summary') or U('STANDS 작가.', 'Artist of STANDS.'), 'artists.html', body)

    # projects
    used = [k for k in TYPES if any(p.get('type') == k for p in PROJECTS)]
    chips = f'<button class="chip" type="button" data-filter="all" aria-pressed="true">{U("전체", "All")}</button>' + ''.join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="false">{type_name(k)}</button>' for k in used)
    CASES = [p for p in PROJECTS if p.get('case_study')]
    case_list = (f'<section class="case-list" id="cases"><div class="wrap"><div class="sec-head"><h2>Case Studies</h2></div></div>'
                 f'<div class="case-heroes" style="--n:{min(len(CASES), 3)}">{"".join(case_feature(p, k, len(CASES)) for k, p in enumerate(CASES, 1))}</div></section>') if CASES else ''
    projects = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Projects</span><h1>Projects</h1>
<p class="lead">{T(L(PG, 'projects_lead'))}</p>
<nav class="page-jump" aria-label="{U('이 페이지', 'On this page')}">{'<a href="#cases">Case Studies</a>' if CASES else ''}<a href="#map">Project Map</a></nav></div></div>
{case_list}
{map_section()}'''
    map_js = (f'<link rel="stylesheet" href="{P}assets/vendor/maplibre-gl.css?v={VER}">'
              f'<script src="{P}assets/vendor/maplibre-gl.js?v={VER}"></script><script src="{P}assets/map.js?v={VER}"></script>')
    page('projects.html', 'Projects', U('STANDS 프로젝트.', 'Projects by STANDS.'), 'projects.html', projects, extra_js=map_js)

    for i, p in enumerate(PROJECTS):
        if p.get('map_only'):
            continue
        if p.get('case_study'):
            case_page(i, p)
            continue
        art = ref(p.get('artist'))
        art_dd = f'<a href="{art["_url"]}">{E(L(art, "name"))}</a>' if art else E(str(p.get('artist') or ''))
        rows = [('Location', E(L(p, 'location'))), ('Year', E(str(p.get('year', '')))), ('Artist', art_dd),
                ('Size', E(L(p, 'size'))), ('Type', E(L(p, 'place_type'))), ('Scope', E(L(p, 'scope')))]
        kv = ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows if v)
        cover = img(p.get('cover'))
        title = L(p, 'title')
        gal = ''.join(f'<div class="ph"><img src="{E(img(g))}" alt="" loading="lazy"></div>' for g in (p.get('gallery') or []) if g)
        nxt = [PROJECTS[(i + k) % len(PROJECTS)] for k in (1, 2, 3) if len(PROJECTS) > k]
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">No.{i+1:03d} · {E(type_name(p.get('type', '')))}</span><h1>{E(title)}</h1>
<p class="lead">{T(L(p, 'summary'))}{sample(p)}</p></div></div>
{f'<div class="full-ph"><img src="{E(cover)}" alt="{E(title)}"></div>' if cover else ''}
<section><div class="wrap two-col">
  <dl class="kv">{kv}</dl>
  <div class="prose">{rich(BODY(p))}</div>
</div></section>
{f'<section class="proj-gallery" style="padding-top:0"><div class="wrap"><div class="gallery-strip" tabindex="0" aria-label="{U("추가 사진", "More photos")}">{gal}</div></div></section>' if gal else ''}
{f'<section style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>Next</h2></div><div class="cards">{"".join(project_card(q) for q in nxt)}</div></div></section>' if nxt else ''}'''
        page(p['_url'], title or 'Project', L(p, 'summary') or U('STANDS 프로젝트.', 'Project by STANDS.'), 'projects.html', body, og=cover or None)

    # editorial
    editorial = f'''<div class="page-head" style="background:var(--sky)"><div class="wrap"><span class="eyebrow" style="color:var(--black)">Editorial</span><h1>Where art<br>stands?</h1>
<p class="lead">{T(L(PG, 'editorial_lead'))}</p></div></div>
<section><div class="wrap"><div class="list">{''.join(article_row(a) for a in ARTICLES)}</div></div></section>'''
    page('editorial.html', 'Editorial', U('WHERE ART STANDS? — STANDS 에디토리얼.', 'WHERE ART STANDS? — the STANDS editorial.'), 'editorial.html', editorial)

    for a in PUBLISHED:
        cover = img(a.get('cover'))
        # optional cover_focus ("50% 46%"): which part of the photo stays in frame in the wide crops
        cf = str(a.get('cover_focus') or '').strip()
        focus = f' style="object-position:{E(cf)}"' if re.fullmatch(r'\d{1,3}% \d{1,3}%', cf) else ''
        title = L(a, 'title')
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Issue {E(str(a.get('issue', '')))} · Where art stands?</span>
<h1 style="font-family:var(--body);font-weight:700;text-transform:none;font-size:clamp(36px,6vw,84px);line-height:1.15;letter-spacing:-.03em">{E(title)}</h1>
<p class="lead">{T(L(a, 'summary'))}</p></div></div>
{f'<div class="full-ph ed-cover"><img src="{E(cover)}" alt=""{focus}><span class="ed-cover-tag">Issue {E(str(a.get("issue", "")))} · Where art stands</span></div>' if cover else ''}
<section><div class="wrap two-col"><span class="eyebrow">{E(str(a.get('date', '')))}</span>
<div class="prose">{rich(BODY(a))}</div></div></section>'''
        page(a['_url'], title or 'Editorial', L(a, 'summary') or U('STANDS 에디토리얼.', 'The STANDS editorial.'), 'editorial.html', body, og=cover or None)

    # contact
    types = L(CT, 'form_types', []) or [U('기타', 'Other')]
    radios = ''.join(f'<input type="radio" name="type" id="t{i}" value="{E(t)}"{" checked" if i == 0 else ""}><label for="t{i}">{E(t)}</label>' for i, t in enumerate(types))
    contact = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Contact</span><h1>Contact</h1>
<p class="lead">{T(L(CT, 'lead'))}</p></div></div>
<section><div class="wrap two-col">
  <dl class="kv"><dt>Email</dt><dd>{E(CT.get('email', ''))}</dd><dt>Address</dt><dd>{E(L(CT, 'address'))}</dd><dt>Tel</dt><dd>{E(CT.get('tel', ''))}</dd><dt>Instagram</dt><dd>{E(CT.get('instagram', ''))}</dd></dl>
  <form class="form" id="contact-form" novalidate>
    <fieldset class="field"><legend>{U('문의 유형', 'Inquiry type')}</legend><div class="types">{radios}</div></fieldset>
    <div class="field"><label for="f-name">{U('이름 · 회사', 'Name · Company')}</label><input id="f-name" name="name" autocomplete="name"></div>
    <div class="field"><label for="f-mail">{U('이메일', 'Email')}</label><input id="f-mail" name="email" type="email" autocomplete="email"></div>
    <div class="field"><label for="f-msg">{U('내용', 'Message')}</label><textarea id="f-msg" name="message" placeholder="{U('공간, 일정, 예산 등 알고 계신 내용을 적어 주세요.', 'Tell us what you know so far: the space, schedule, budget and so on.')}"></textarea></div>
    <div><button class="btn dark" type="submit">{U('보내기', 'Send')}</button></div>
    <p class="notice" id="form-note" role="status" hidden></p>
  </form>
</div></section>'''
    page('contact.html', 'Contact', U('STANDS 문의.', 'Contact STANDS.'), 'contact.html', contact)

    if EN():
        privacy = '''<div class="page-head"><div class="wrap"><span class="eyebrow">Policy</span><h1 style="font-size:clamp(40px,7vw,96px)">Privacy</h1>
<p class="lead">The full privacy policy will be published here before launch, covering what the contact form collects (name, company, email and message), how long it is kept and how it is deleted. The Korean version is the governing text.</p></div></div>
<section><div class="wrap two-col"><span class="eyebrow">Analytics</span><div class="prose">
<h2 style="margin-top:0">Visitor analytics</h2>
<p>To improve the site, STANDS uses Google Analytics 4 and Microsoft Clarity to collect records of visits (behavioral data): pages viewed, menus and buttons clicked, click and scroll positions on the page, time of visit, referral source, device and browser type, and approximate region. We do not collect information that directly identifies you, such as your name or contact details.</p>
<p>This information is collected through cookies. You can refuse it by blocking cookies in your browser settings or by installing the <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">Google Analytics opt-out add-on</a>. In Microsoft Clarity session recordings, anything typed into input fields is masked and not stored.</p>
</div></div></section>'''
        page('privacy.html', 'Privacy Policy', 'STANDS privacy policy (in preparation).', '', privacy)
    else:
        privacy = '''<div class="page-head"><div class="wrap"><span class="eyebrow">Policy</span><h1 style="font-size:clamp(40px,7vw,96px)">Privacy</h1>
<p class="lead">개인정보처리방침이 들어갈 자리입니다. 문의 폼에서 수집하는 항목(이름, 회사, 이메일, 문의 내용)과 보관 기간, 파기 절차를 오픈 전에 확정해 게시합니다.</p></div></div>
<section><div class="wrap two-col"><span class="eyebrow">Analytics</span><div class="prose">
<h2 style="margin-top:0">방문 통계 수집</h2>
<p>STANDS 웹사이트는 서비스 개선을 위해 Google Analytics 4와 Microsoft Clarity를 사용해 방문 기록(행태정보)을 수집합니다. 수집 항목은 방문한 페이지, 클릭한 메뉴와 버튼, 화면 내 클릭·스크롤 위치, 방문 시간, 유입 경로, 기기·브라우저 종류, 대략적인 지역이며, 이름이나 연락처처럼 개인을 직접 식별하는 정보는 수집하지 않습니다.</p>
<p>이 정보는 쿠키를 통해 수집되며, 브라우저 설정에서 쿠키 저장을 거부하거나 <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">Google Analytics 차단 부가기능</a>을 설치해 수집을 거부할 수 있습니다. Microsoft Clarity의 화면 기록에서는 입력란에 적은 내용이 가려져 저장되지 않습니다.</p>
</div></div></section>'''
        page('privacy.html', '개인정보처리방침', 'STANDS 개인정보처리방침 (준비 중).', '', privacy)

    # old single example pages -> redirect to the first real entry
    for old, target in (('project.html', PROJECTS[0]['_url'] if PROJECTS else 'projects.html'),
                        ('artist.html', ARTISTS[0]['_url'] if ARTISTS else 'artists.html'),
                        ('article.html', PUBLISHED[0]['_url'] if PUBLISHED else 'editorial.html')):
        open(os.path.join(OUT, old), 'w', encoding='utf-8').write(
            f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><link rel="canonical" href="{target}"><a href="{target}">{U("이동", "Continue")}</a>\n')


def build():
    global LANG, P, OUT
    if os.path.isdir(OUT_ROOT):
        shutil.rmtree(OUT_ROOT)
    os.makedirs(OUT_ROOT)
    for d in ('assets', 'img', 'video'):
        if os.path.isdir(os.path.join(ROOT, d)):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT_ROOT, d))
    open(os.path.join(OUT_ROOT, '.nojekyll'), 'w').close()
    for LANG, P, OUT in (('ko', '', OUT_ROOT), ('en', '../', os.path.join(OUT_ROOT, 'en'))):
        os.makedirs(OUT, exist_ok=True)
        build_lang()
    LANG, P, OUT = 'ko', '', OUT_ROOT
    print('built', len(os.listdir(OUT_ROOT)), 'entries (+ /en),', len(PROJECTS), 'projects,', len(ARTISTS), 'artists,', len(ARTICLES), 'articles ->', OUT_ROOT)

if __name__ == '__main__':
    build()
