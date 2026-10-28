#!/usr/bin/env python3
"""STANDS website builder.

Reads the editable content in /content (managed with Pages CMS) and writes the static site to /_site.
GitHub Actions runs this on every push to main and deploys _site to GitHub Pages.
Design lives here and in /assets; words and pictures live in /content.
"""
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
        return (f'<svg class="{cls}" viewBox="0 0 400 400" role="img" aria-label="{label}">'
                f'<rect x="{t/2:.2f}" y="{t/2:.2f}" width="{400-t:.2f}" height="{400-t:.2f}" fill="none" stroke="currentColor" stroke-width="{t*1.6:.2f}"/>'
                f'<g fill="currentColor">{BOX_PATHS}</g><rect x="{bx:.2f}" y="{by:.2f}" width="{bw:.2f}" height="{bh*1.3:.2f}" fill="currentColor"/></svg>')
    return (f'<svg class="{cls}" viewBox="0 0 400 400" role="img" aria-label="{label}"><defs>{df}{db}</defs>'
            f'<rect{fid} x="{t/2:.2f}" y="{t/2:.2f}" width="{400-t:.2f}" height="{400-t:.2f}" style="fill:var(--paper)" stroke="url(#{gf})" stroke-width="{t:.2f}"{frame_attrs}/>'
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
    <video id="loopvid" muted loop playsinline preload="none" poster="{P}img/park-poster.jpg"><source src="{P}video/park-loop.mp4" type="video/mp4"><source src="{P}video/park-loop.webm" type="video/webm"></video>
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
BASE_URL = os.environ.get('STANDS_URL', 'https://jenuek.github.io/stands-website/')
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
ARTISTS = collection('artists', 'artist', lambda d: (num(d.get('order')), d.get('name', '')))
ARTICLES = collection('editorial', 'article', lambda d: str(d.get('date', '')), )
ARTICLES.reverse()  # newest first
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
      <div>{legal}</div>
      <div><a href="privacy.html">{U('개인정보처리방침', 'Privacy Policy')}</a> · © 2026 STANDS</div>
    </div>
  </div>
</footer>
<script src="{P}assets/site.js?v={VER}"></script>
'''

def page(name, title, desc, cur, body, extra_js='', og=None):
    doc = head(title, desc, name, og) + header(name, cur) + '<main id="main">\n' + body + '\n</main>\n' + footer() + extra_js + '</body>\n</html>\n'
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

def artist_card(a):
    i = ARTISTS.index(a)
    photo = img(a.get('photo'))
    plate = (f'<img src="{E(photo)}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover">' if photo
             else f'<svg viewBox="0 0 100 100" aria-hidden="true">{SHAPES[i % 8]}</svg>')
    return (f'<a class="artist" href="{a["_url"]}"><div class="plate">{plate}</div>'
            f'<span class="meta">{E(L(a, "medium"))}</span><h3>{E(L(a, "name"))}{sample(a)}</h3></a>')

def article_row(a):
    return (f'<a href="{a["_url"]}"><span class="meta">Issue {E(str(a.get("issue", "")))}</span>'
            f'<h3>{E(L(a, "title"))}{sample(a)}</h3><span class="meta">{E(str(a.get("date", "")))}</span></a>')

# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def build_lang():
    # home
    fp = pick(H.get('featured_projects')) or PROJECTS[:3]
    fa = pick(H.get('featured_artists')) or ARTISTS[:4]
    fe = (pick(H.get('featured_article')) or ARTICLES[:1])
    services = H.get('services', []) or []
    svc = ''.join(f'<div class="svc"><span class="k">{E(LI(s, "label"))}</span><h3>{E(LI(s, "title"))}</h3><p>{T(LI(s, "text"))}</p><span class="plinth"></span></div>'
                  for s in services)
    ncls = ' three' if len(services) == 3 else ''
    ed = ''
    if fe:
        a = fe[0]
        cover = img(a.get('cover'))
        ed = f'''<section class="editorial-band" aria-labelledby="ed-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="ed-h">Where art<br>stands?</h2><a class="more accent-it" href="editorial.html">Editorial</a></div>
    <a class="ed-feature" href="{a['_url']}">
      <div class="ph">{f'<img src="{E(cover)}" alt="" loading="lazy">' if cover else ''}</div>
      <div><span class="issue">ISSUE {E(str(a.get('issue', '')))}</span><h3>{E(L(a, 'title'))}</h3><p>{T(L(a, 'summary'))}</p><span class="more">{U('읽기', 'Read')}</span></div>
    </a>
  </div>
</section>'''
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
      </div>
      <p><a class="more" href="about.html">About STANDS</a></p>
    </div>
  </div>
</section>

<section class="services" aria-labelledby="svc-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="svc-h">What we do</h2></div>
    <div class="svc-grid{ncls}">{svc}</div>
  </div>
</section>

<section aria-labelledby="pj-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="pj-h">Projects</h2><a class="more" href="projects.html">{U('전체 프로젝트', 'All projects')}</a></div>
    <div class="cards">{''.join(project_card(p) for p in fp)}</div>
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
    kv = ''.join(f'<dt>{E(LI(r, "label"))}</dt><dd>{T(LI(r, "text"))}</dd>' for r in (AB.get('what_we_do', []) or []))
    about = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">About</span><h1 class="long">Art is complete<br>where it <span class="ul">stands</span>.</h1></div></div>
<section>
  <div class="wrap two-col">
    <span class="eyebrow">STANDS</span>
    <div class="prose about-copy">
      {paras}
      <p class="close">{E(L(AB, 'closing'))}</p>
    </div>
  </div>
</section>
<section class="services" style="padding-top:clamp(56px,8vw,110px)">
  <div class="wrap">
    <div class="sec-head"><h2>What we do</h2></div>
    <dl class="kv">{kv}</dl>
  </div>
</section>
<section class="cta"><div class="wrap"><h2>{T(L(AB, 'cta_title'))}</h2><a class="btn" href="contact.html">{E(L(AB, 'cta_button', U('문의하기', 'Get in touch')))}</a></div></section>'''
    page('about.html', 'About', U('Art is complete where it stands. 작품 선정부터 설치까지, 한 팀이 맡는 아트 컴퍼니 STANDS.',
                                  'Art is complete where it stands. STANDS is an art company where one team takes a work from selection to installation.'),
         'about.html', about)

    # artists
    artists = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Artists</span><h1>Artists</h1>
<p class="lead">{T(L(PG, 'artists_lead'))}</p></div></div>
<section><div class="wrap"><div class="artist-grid">{''.join(artist_card(a) for a in ARTISTS)}</div></div></section>'''
    page('artists.html', 'Artists', U('STANDS 작가.', 'Artists of STANDS.'), 'artists.html', artists)

    for a in ARTISTS:
        works = [p for p in PROJECTS if ref(p.get('artist')) is a]
        hist = ''.join(f'<a href="{a["_url"]}"><span class="meta">{E(str(h.get("year", "")))}</span><h3>{E(LI(h, "title"))}</h3><span class="meta">{E(LI(h, "place"))}</span></a>'
                       for h in (a.get('history') or []))
        photo = img(a.get('photo'))
        name = L(a, 'name')
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Artist · {E(L(a, 'medium'))}</span><h1>{E(name)}</h1>
<p class="lead">{T(L(a, 'summary'))}{sample(a)}</p></div></div>
{f'<div class="full-ph"><img src="{E(photo)}" alt="{E(name)}"></div>' if photo else ''}
<section><div class="wrap two-col">
  <dl class="kv"><dt>Born</dt><dd>{E(str(L(a, 'born')))}</dd><dt>Based</dt><dd>{E(L(a, 'based'))}</dd><dt>Media</dt><dd>{E(L(a, 'medium'))}</dd><dt>Contact</dt><dd><a class="more" href="contact.html">{U('작품 문의', 'Inquire about works')}</a></dd></dl>
  <div class="prose">{rich(BODY(a))}</div>
</div></section>
{f'<section style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>Projects</h2></div><div class="cards">{"".join(project_card(p) for p in works)}</div></div></section>' if works else ''}
{f'<section style="padding-top:0"><div class="wrap two-col"><span class="eyebrow">Exhibitions</span><div class="list">{hist}</div></div></section>' if hist else ''}'''
        page(a['_url'], name or 'Artist', L(a, 'summary') or U('STANDS 작가.', 'Artist of STANDS.'), 'artists.html', body)

    # projects
    used = [k for k in TYPES if any(p.get('type') == k for p in PROJECTS)]
    chips = f'<button class="chip" type="button" data-filter="all" aria-pressed="true">{U("전체", "All")}</button>' + ''.join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="false">{type_name(k)}</button>' for k in used)
    projects = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Projects</span><h1>Projects</h1>
<p class="lead">{T(L(PG, 'projects_lead'))}</p></div></div>
<section><div class="wrap"><div class="filters" role="group" aria-label="{U('프로젝트 유형', 'Project type')}">{chips}</div>
<div class="cards">{''.join(project_card(p) for p in PROJECTS)}</div></div></section>'''
    page('projects.html', 'Projects', U('STANDS 프로젝트.', 'Projects by STANDS.'), 'projects.html', projects)

    for i, p in enumerate(PROJECTS):
        art = ref(p.get('artist'))
        art_dd = f'<a href="{art["_url"]}">{E(L(art, "name"))}</a>' if art else E(str(p.get('artist') or ''))
        rows = [('Location', E(L(p, 'location'))), ('Year', E(str(p.get('year', '')))), ('Artist', art_dd),
                ('Size', E(L(p, 'size'))), ('Client', E(L(p, 'client'))), ('Scope', E(L(p, 'scope')))]
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
{f'<section style="padding-top:0"><div class="wrap"><div class="cards gallery">{gal}</div></div></section>' if gal else ''}
{f'<section style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>Next</h2></div><div class="cards">{"".join(project_card(q) for q in nxt)}</div></div></section>' if nxt else ''}'''
        page(p['_url'], title or 'Project', L(p, 'summary') or U('STANDS 프로젝트.', 'Project by STANDS.'), 'projects.html', body, og=cover or None)

    # editorial
    editorial = f'''<div class="page-head" style="background:var(--sky)"><div class="wrap"><span class="eyebrow" style="color:var(--black)">Editorial</span><h1>Where art<br>stands?</h1>
<p class="lead">{T(L(PG, 'editorial_lead'))}</p></div></div>
<section><div class="wrap"><div class="list">{''.join(article_row(a) for a in ARTICLES)}</div></div></section>'''
    page('editorial.html', 'Editorial', U('WHERE ART STANDS? — STANDS 에디토리얼.', 'WHERE ART STANDS? — the STANDS editorial.'), 'editorial.html', editorial)

    for a in ARTICLES:
        cover = img(a.get('cover'))
        title = L(a, 'title')
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Issue {E(str(a.get('issue', '')))} · Where art stands?</span>
<h1 style="font-family:var(--body);font-weight:700;text-transform:none;font-size:clamp(36px,6vw,84px);line-height:1.15;letter-spacing:-.03em">{E(title)}</h1>
<p class="lead">{T(L(a, 'summary'))}</p></div></div>
{f'<div class="full-ph"><img src="{E(cover)}" alt=""></div>' if cover else ''}
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
                        ('article.html', ARTICLES[0]['_url'] if ARTICLES else 'editorial.html')):
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
