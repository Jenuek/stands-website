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

def head(title, desc, og=None):
    t = 'STANDS' if title == 'STANDS' else f'{title} — STANDS'
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{og or 'img/gallery.jpg'}">
<meta name="theme-color" content="#F0F0EE">
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4HENTDTYNP"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-4HENTDTYNP');</script>
<!-- Microsoft Clarity -->
<script>(function(c,l,a,r,i,t,y){{c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);}})(window,document,"clarity","script","z46038c0ok");</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,800..900&family=Newsreader:ital,opsz,wght@1,6..72,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="assets/site.css?v={VER}">
</head>
<body>
'''


HERO = f'''<section class="hero" id="hero" aria-label="WHERE ART STANDS">
  <div class="bg plain" id="bg"><img id="bgimg" alt="" hidden></div>
  <div class="tag" id="tag"></div>
  <div class="line" id="line" role="img" aria-label="WHERE ART STANDS">
    <span id="wa"><svg class="gl" width="4.9285em" height="0.74em" viewBox="{HERO_WA_VIEW}" aria-hidden="true" fill="currentColor" overflow="visible">{HERO_WA}</svg></span>
    <span class="slot"><span class="word" id="word"><svg class="gl" width="3.3249em" height="0.74em" viewBox="{HERO_ST_VIEW}" aria-hidden="true" fill="currentColor" overflow="visible">{HERO_ST}</svg></span><span class="ubar" id="ubar"></span><span class="obj" id="obj"></span></span>
  </div>
  <div class="loop" id="loop" aria-hidden="true">
    <video id="loopvid" muted loop playsinline preload="none" poster="img/park-poster.jpg"><source src="video/park-loop.mp4" type="video/mp4"><source src="video/park-loop.webm" type="video/webm"></video>
  </div>
  <div class="lockup" id="lockup">
    {logo_svg(ids=True, bar_w=0, frame_attrs=' pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"')}
  </div>
  <div class="scroll">SCROLL</div>
  <div class="controls"><button id="replay" type="button">다시 보기</button></div>
</section>'''



# ---------------------------------------------------------------------------
# content loading
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, 'content')
OUT = os.environ.get('STANDS_OUT', os.path.join(ROOT, '_site'))
VER = os.environ.get('STANDS_VER', '20261028')
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
    """CMS stores '/img/x.jpg'; the site lives in a sub-folder, so use relative paths."""
    p = (p or '').strip()
    return p[1:] if p.startswith('/') else p

def rich(md_text):
    out = markdown.markdown(md_text or '', extensions=['extra', 'sane_lists', 'nl2br'])
    return out.replace('src="/img/', 'src="img/').replace('href="/img/', 'href="img/')

def para(text):
    return ''.join(f'<p>{T(t)}</p>' for t in re.split(r'\n\s*\n', text or '') if t.strip())

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

TYPES = {'space': '공간 프로젝트', 'public': '공공미술', 'exhibition': '전시', 'trade': '거래 · 자문', 'handling': '제작 · 설치'}
S = '<span class="sample">예시</span>'
def sample(d):
    return S if d.get('sample') else ''

# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------
NAV = [('about.html', 'About'), ('artists.html', 'Artists'), ('projects.html', 'Projects'),
       ('editorial.html', 'Editorial'), ('contact.html', 'Contact')]

def header(cur):
    AC = ' aria-current="page"'
    links = ''.join(f'<a href="{h}"{AC if h == cur else ""}>{n}</a>' for h, n in NAV)
    mlinks = ''.join(f'<a href="{h}">{n}</a>' for h, n in NAV)
    return f'''<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="index.html" aria-label="STANDS 홈">{logo_svg(label="STANDS", mono=True)}</a>
    <nav class="nav" aria-label="주요 메뉴">{links}<span class="lang">KO / EN</span></nav>
    <button class="menu-btn" id="menu-open" type="button" aria-label="메뉴 열기" aria-controls="mobile-nav"><span></span><span></span></button>
  </div>
</header>
<div class="mobile-nav" id="mobile-nav" hidden>
  <button class="close" id="menu-close" type="button">닫기</button>
  <a href="index.html">Home</a>{mlinks}
</div>
'''

FOOTER = f'''<footer class="site-footer">
  <div class="wrap">
    <div class="top">
      <div class="logo-col"><a class="logo" href="index.html" aria-label="STANDS 홈">{wordmark_svg()}</a><span class="descriptor">Office for Art</span></div>
      <div><h4>Menu</h4><ul>{''.join(f'<li><a href="{h}">{n}</a></li>' for h, n in NAV)}</ul></div>
      <div><h4>Contact</h4><ul><li>{E(CT.get('email', ''))}</li><li>{E(CT.get('address', ''))}</li><li>{E(CT.get('tel', ''))}</li></ul></div>
      <div><h4>Follow</h4><ul><li>Instagram {E(CT.get('instagram', ''))}</li><li><a href="editorial.html">Editorial</a></li></ul></div>
    </div>
    <div class="legal">
      <div>주식회사 {E(CO.get('name', ''))} · 대표 {E(CO.get('ceo', ''))} · 사업자등록번호 <span class="ph">{E(CO.get('business_no', ''))}</span><br>
      미술서비스업 신고번호 <span class="ph">{E(CO.get('art_service_no', ''))}</span> · 통신판매업 신고번호 <span class="ph">{E(CO.get('ecommerce_no', ''))}</span></div>
      <div><a href="privacy.html">개인정보처리방침</a> · © 2026 STANDS</div>
    </div>
  </div>
</footer>
<script src="assets/site.js?v={VER}"></script>
'''

def page(name, title, desc, cur, body, extra_js='', og=None):
    doc = head(title, desc, og) + header(cur) + '<main id="main">\n' + body + '\n</main>\n' + FOOTER + extra_js + '</body>\n</html>\n'
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(doc)

# ---------------------------------------------------------------------------
# cards
# ---------------------------------------------------------------------------
def project_card(p):
    i = PROJECTS.index(p)
    typ = p.get('type', 'space')
    meta = ' · '.join(x for x in (f'No.{i+1:03d}', TYPES.get(typ, ''), p.get('location', ''), p.get('size', '')) if x)
    cover = img(p.get('cover'))
    ph = f'<img src="{E(cover)}" alt="" loading="lazy">' if cover else ''
    return (f'<a class="card" href="{p["_url"]}" data-type="{E(typ)}"><div class="ph">{ph}</div>'
            f'<span class="meta">{E(meta)}</span><h3>{E(p.get("title", ""))}{sample(p)}</h3></a>')

def artist_card(a):
    i = ARTISTS.index(a)
    photo = img(a.get('photo'))
    plate = (f'<img src="{E(photo)}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover">' if photo
             else f'<svg viewBox="0 0 100 100" aria-hidden="true">{SHAPES[i % 8]}</svg>')
    return (f'<a class="artist" href="{a["_url"]}"><div class="plate">{plate}</div>'
            f'<span class="meta">{E(a.get("medium", ""))}</span><h3>{E(a.get("name", ""))}{sample(a)}</h3></a>')

def article_row(a):
    return (f'<a href="{a["_url"]}"><span class="meta">Issue {E(str(a.get("issue", "")))}</span>'
            f'<h3>{E(a.get("title", ""))}{sample(a)}</h3><span class="meta">{E(str(a.get("date", "")))}</span></a>')

# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for d in ('assets', 'img', 'video'):
        if os.path.isdir(os.path.join(ROOT, d)):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT, d))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    # home
    fp = pick(H.get('featured_projects')) or PROJECTS[:3]
    fa = pick(H.get('featured_artists')) or ARTISTS[:4]
    fe = (pick(H.get('featured_article')) or ARTICLES[:1])
    svc = ''.join(f'<div class="svc"><span class="k">{E(s.get("label", ""))}</span><h3>{E(s.get("title", ""))}</h3><p>{T(s.get("text", ""))}</p><span class="plinth"></span></div>'
                  for s in H.get('services', []))
    ncls = ' three' if len(H.get('services', [])) == 3 else ''
    ed = ''
    if fe:
        a = fe[0]
        cover = img(a.get('cover'))
        ed = f'''<section class="editorial-band" aria-labelledby="ed-h">
  <div class="wrap">
    <div class="sec-head"><h2 id="ed-h">Where art<br>stands?</h2><a class="more accent-it" href="editorial.html">Editorial</a></div>
    <a class="ed-feature" href="{a['_url']}">
      <div class="ph">{f'<img src="{E(cover)}" alt="" loading="lazy">' if cover else ''}</div>
      <div><span class="issue">ISSUE {E(str(a.get('issue', '')))}</span><h3>{E(a.get('title', ''))}</h3><p>{T(a.get('summary', ''))}</p><span class="more">읽기</span></div>
    </a>
  </div>
</section>'''
    home = HERO + f'''
<section class="statement">
  <div class="wrap">
    <span class="eyebrow">STANDS · Office for Art</span>
    <h1 class="reveal">{E(H.get('headline', ''))} <span class="en ul">STANDS</span>.</h1>
    <div class="grid">
      <div class="story">
        <p>{T(H.get('story_1', ''))}</p>
        <p class="slogan">WHERE ART STANDS</p>
        <p>{T(H.get('story_2', ''))}</p>
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
    <div class="sec-head"><h2 id="pj-h">Projects</h2><a class="more" href="projects.html">전체 프로젝트</a></div>
    <div class="cards">{''.join(project_card(p) for p in fp)}</div>
  </div>
</section>

<section aria-labelledby="ar-h" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><h2 id="ar-h">Artists</h2><a class="more" href="artists.html">전체 작가</a></div>
    <div class="artist-grid">{''.join(artist_card(a) for a in fa)}</div>
  </div>
</section>

{ed}

<section class="cta">
  <div class="wrap">
    <span class="eyebrow" style="color:#9A98A0">Contact</span>
    <h2>{T(H.get('cta_title', ''))}</h2>
    <a class="btn" href="contact.html">{E(H.get('cta_button', '문의'))}</a>
  </div>
</section>'''
    page('index.html', 'STANDS', f"{H.get('headline', '')} STANDS. 작품 선정 · 거래, 아트 프로젝트 기획, 건축물 미술작품 제작 · 설치를 직접 수행하는 아트 컴퍼니.",
         'index.html', home, f'<script src="assets/hero.js?v={VER}"></script>\n')

    # about
    paras = ''.join(f'<p>{T(t)}</p>' for t in AB.get('paragraphs', []))
    kv = ''.join(f'<dt>{E(r.get("label", ""))}</dt><dd>{T(r.get("text", ""))}</dd>' for r in AB.get('what_we_do', []))
    about = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">About</span><h1 class="long">Art is complete<br>where it <span class="ul">stands</span>.</h1></div></div>
<section>
  <div class="wrap two-col">
    <span class="eyebrow">STANDS</span>
    <div class="prose about-copy">
      {paras}
      <p class="close">{E(AB.get('closing', ''))}</p>
    </div>
  </div>
</section>
<section class="services" style="padding-top:clamp(56px,8vw,110px)">
  <div class="wrap">
    <div class="sec-head"><h2>What we do</h2></div>
    <dl class="kv">{kv}</dl>
  </div>
</section>
<section class="cta"><div class="wrap"><h2>{T(AB.get('cta_title', ''))}</h2><a class="btn" href="contact.html">{E(AB.get('cta_button', '문의하기'))}</a></div></section>'''
    page('about.html', 'About', 'Art is complete where it stands. 작품 선정부터 설치까지, 한 팀이 맡는 아트 컴퍼니 STANDS.', 'about.html', about)

    # artists
    artists = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Artists</span><h1>Artists</h1>
<p class="lead">{T(PG.get('artists_lead', ''))}</p></div></div>
<section><div class="wrap"><div class="artist-grid">{''.join(artist_card(a) for a in ARTISTS)}</div></div></section>'''
    page('artists.html', 'Artists', 'STANDS 작가.', 'artists.html', artists)

    for a in ARTISTS:
        works = [p for p in PROJECTS if ref(p.get('artist')) is a]
        hist = ''.join(f'<a href="{a["_url"]}"><span class="meta">{E(str(h.get("year", "")))}</span><h3>{E(h.get("title", ""))}</h3><span class="meta">{E(h.get("place", ""))}</span></a>'
                       for h in (a.get('history') or []))
        photo = img(a.get('photo'))
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Artist · {E(a.get('medium', ''))}</span><h1>{E(a.get('name', ''))}</h1>
<p class="lead">{T(a.get('summary', ''))}{sample(a)}</p></div></div>
{f'<div class="full-ph"><img src="{E(photo)}" alt="{E(a.get("name", ""))}"></div>' if photo else ''}
<section><div class="wrap two-col">
  <dl class="kv"><dt>Born</dt><dd>{E(str(a.get('born', '')))}</dd><dt>Based</dt><dd>{E(a.get('based', ''))}</dd><dt>Media</dt><dd>{E(a.get('medium', ''))}</dd><dt>Contact</dt><dd><a class="more" href="contact.html">작품 문의</a></dd></dl>
  <div class="prose">{rich(a.get('_body'))}</div>
</div></section>
{f'<section style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>Projects</h2></div><div class="cards">{"".join(project_card(p) for p in works)}</div></div></section>' if works else ''}
{f'<section style="padding-top:0"><div class="wrap two-col"><span class="eyebrow">Exhibitions</span><div class="list">{hist}</div></div></section>' if hist else ''}'''
        page(a['_url'], a.get('name', 'Artist'), a.get('summary', '') or 'STANDS 작가.', 'artists.html', body)

    # projects
    used = [k for k in TYPES if any(p.get('type') == k for p in PROJECTS)]
    chips = '<button class="chip" type="button" data-filter="all" aria-pressed="true">전체</button>' + ''.join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="false">{TYPES[k]}</button>' for k in used)
    projects = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Projects</span><h1>Projects</h1>
<p class="lead">{T(PG.get('projects_lead', ''))}</p></div></div>
<section><div class="wrap"><div class="filters" role="group" aria-label="프로젝트 유형">{chips}</div>
<div class="cards">{''.join(project_card(p) for p in PROJECTS)}</div></div></section>'''
    page('projects.html', 'Projects', 'STANDS 프로젝트.', 'projects.html', projects)

    for i, p in enumerate(PROJECTS):
        art = ref(p.get('artist'))
        art_dd = f'<a href="{art["_url"]}">{E(art.get("name", ""))}</a>' if art else E(str(p.get('artist') or ''))
        rows = [('Location', E(p.get('location', ''))), ('Year', E(str(p.get('year', '')))), ('Artist', art_dd),
                ('Size', E(p.get('size', ''))), ('Client', E(p.get('client', ''))), ('Scope', E(p.get('scope', '')))]
        kv = ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows if v)
        cover = img(p.get('cover'))
        gal = ''.join(f'<div class="ph"><img src="{E(img(g))}" alt="" loading="lazy"></div>' for g in (p.get('gallery') or []) if g)
        nxt = [PROJECTS[(i + k) % len(PROJECTS)] for k in (1, 2, 3) if len(PROJECTS) > k]
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">No.{i+1:03d} · {E(TYPES.get(p.get('type', ''), ''))}</span><h1>{E(p.get('title', ''))}</h1>
<p class="lead">{T(p.get('summary', ''))}{sample(p)}</p></div></div>
{f'<div class="full-ph"><img src="{E(cover)}" alt="{E(p.get("title", ""))}"></div>' if cover else ''}
<section><div class="wrap two-col">
  <dl class="kv">{kv}</dl>
  <div class="prose">{rich(p.get('_body'))}</div>
</div></section>
{f'<section style="padding-top:0"><div class="wrap"><div class="cards gallery">{gal}</div></div></section>' if gal else ''}
{f'<section style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>Next</h2></div><div class="cards">{"".join(project_card(q) for q in nxt)}</div></div></section>' if nxt else ''}'''
        page(p['_url'], p.get('title', 'Project'), p.get('summary', '') or 'STANDS 프로젝트.', 'projects.html', body, og=cover or None)

    # editorial
    editorial = f'''<div class="page-head" style="background:var(--sky)"><div class="wrap"><span class="eyebrow" style="color:var(--black)">Editorial</span><h1>Where art<br>stands?</h1>
<p class="lead">{T(PG.get('editorial_lead', ''))}</p></div></div>
<section><div class="wrap"><div class="list">{''.join(article_row(a) for a in ARTICLES)}</div></div></section>'''
    page('editorial.html', 'Editorial', 'WHERE ART STANDS? — STANDS 에디토리얼.', 'editorial.html', editorial)

    for a in ARTICLES:
        cover = img(a.get('cover'))
        body = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Issue {E(str(a.get('issue', '')))} · Where art stands?</span>
<h1 style="font-family:var(--body);font-weight:700;text-transform:none;font-size:clamp(36px,6vw,84px);line-height:1.15;letter-spacing:-.03em">{E(a.get('title', ''))}</h1>
<p class="lead">{T(a.get('summary', ''))}</p></div></div>
{f'<div class="full-ph"><img src="{E(cover)}" alt=""></div>' if cover else ''}
<section><div class="wrap two-col"><span class="eyebrow">{E(str(a.get('date', '')))}</span>
<div class="prose">{rich(a.get('_body'))}</div></div></section>'''
        page(a['_url'], a.get('title', 'Editorial'), a.get('summary', '') or 'STANDS 에디토리얼.', 'editorial.html', body, og=cover or None)

    # contact
    types = CT.get('form_types', []) or ['기타']
    radios = ''.join(f'<input type="radio" name="type" id="t{i}" value="{E(t)}"{" checked" if i == 0 else ""}><label for="t{i}">{E(t)}</label>' for i, t in enumerate(types))
    contact = f'''<div class="page-head"><div class="wrap"><span class="eyebrow">Contact</span><h1>Contact</h1>
<p class="lead">{T(CT.get('lead', ''))}</p></div></div>
<section><div class="wrap two-col">
  <dl class="kv"><dt>Email</dt><dd>{E(CT.get('email', ''))}</dd><dt>Address</dt><dd>{E(CT.get('address', ''))}</dd><dt>Tel</dt><dd>{E(CT.get('tel', ''))}</dd><dt>Instagram</dt><dd>{E(CT.get('instagram', ''))}</dd></dl>
  <form class="form" id="contact-form" novalidate>
    <fieldset class="field"><legend>문의 유형</legend><div class="types">{radios}</div></fieldset>
    <div class="field"><label for="f-name">이름 · 회사</label><input id="f-name" name="name" autocomplete="name"></div>
    <div class="field"><label for="f-mail">이메일</label><input id="f-mail" name="email" type="email" autocomplete="email"></div>
    <div class="field"><label for="f-msg">내용</label><textarea id="f-msg" name="message" placeholder="공간, 일정, 예산 등 알고 계신 내용을 적어 주세요."></textarea></div>
    <div><button class="btn dark" type="submit">보내기</button></div>
    <p class="notice" id="form-note" role="status" hidden></p>
  </form>
</div></section>'''
    page('contact.html', 'Contact', 'STANDS 문의.', 'contact.html', contact)

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
            f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><link rel="canonical" href="{target}"><a href="{target}">이동</a>\n')
    print('built', len(os.listdir(OUT)), 'entries,', len(PROJECTS), 'projects,', len(ARTISTS), 'artists,', len(ARTICLES), 'articles ->', OUT)

if __name__ == '__main__':
    build()
