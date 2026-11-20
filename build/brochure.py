#!/usr/bin/env python3
"""STANDS brand brochure (company profile) — generator.

Writes _brochure/brochure-<lang>.html (A4 landscape, one <section> per page) from the site content:
content/site.yml, content/projects/*.md, content/artists/*.md, img/illust/*.svg.
Laid out like a magazine issue: cover, contents, three chapters (Practice, Works, People), masthead, back cover.
Fields still empty on the site (or dummy numbers like 000-000000) show as lavender dashed placeholders.

The PDF is meant to be opened and edited in Illustrator: fonts are static, named TTFs (build/brochure_fonts.py),
images carry no CSS filters or shadows (those get rasterised), and text stays live text.

    python build/brochure_fonts.py      # once: static fonts into _brochure/fonts/
    python build/brochure.py            # Korean   (--lang en for English)
    node build/brochure_pdf.mjs         # renders every _brochure/*.html to PDF (--png for page previews)

Not part of the GitHub Pages deploy.
"""
import os, re, sys, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B   # reuses the logo, wordmark, content and language helpers (build.py only builds under __main__)

OUT = os.path.join(B.ROOT, '_brochure')
VERSION = 'v1.0'
ISSUE = 'ISSUE 01'
E = lambda s: html.escape(str(s or ''), quote=True)
U = lambda ko, en: B.U(ko, en)


def is_tbd(s):
    s = str(s or '').strip()
    return not s or (s.startswith('[') and s.endswith(']')) or bool(re.fullmatch(r'[0\-\s]+', s))

def T(s, tag='span'):
    """Content text; empty, '[입력]' or dummy-number values turn into a placeholder."""
    if is_tbd(s):
        return f'<{tag} class="tbd">{E(U("[입력]", "[To be added]"))}</{tag}>'
    return f'<{tag}>{E(s)}</{tag}>'

def PARA(s, cls=''):
    out = []
    for block in re.split(r'\n\s*\n', str(s or '').strip()):
        block = re.sub(r'\*\*(.+?)\*\*', r'\1', block)
        lines = [E(l.strip()) for l in block.split('\n') if l.strip()]
        if lines:
            out.append(f'<p{f" class=\"{cls}\"" if cls else ""}>' + '<br>'.join(lines) + '</p>')
    return ''.join(out)

def SRC(path):
    return '../' + str(path or '').lstrip('/')

def IMG(src, cls='', cap='', num=None, pos=None):
    """Photo with an optional magazine caption below it (no overlay text, no filters: keeps the PDF clean)."""
    style = f' style="object-position:{pos}"' if pos else ''
    c = f'<figcaption>{f"<b>{num:02d}</b>" if num else ""}{E(cap)}</figcaption>' if (cap or num) else ''
    return f'<figure class="img {cls}"><div class="frame"><img src="{SRC(src)}" alt=""{style}></div>{c}</figure>'


# ---------------------------------------------------------------------------
# content
# ---------------------------------------------------------------------------
def entries(folder):
    out = []
    for name in sorted(os.listdir(os.path.join(B.CONTENT, folder))):
        if name.endswith('.md'):
            d = B.read_md(os.path.join(B.CONTENT, folder, name)) if hasattr(B, 'read_md') else None
            if d is None:
                txt = open(os.path.join(B.CONTENT, folder, name), encoding='utf-8').read()
                m = re.match(r'^---\n(.*?)\n---\n?(.*)$', txt, re.S)
                d = B.yaml.safe_load(m.group(1)) or {}
                d['_body'] = m.group(2)
            d['_file'] = f'content/{folder}/{name}'
            if not d.get('hidden') and not d.get('sample'):
                out.append(d)
    return sorted(out, key=lambda d: d.get('order', 99))

def work_line(p):
    """'233개의 수평정원, 2023 · 김병호 · 재료 · 크기' from the '작품 정보' / 'Work' line of the body."""
    body = B.BODY(p) or ''
    m = re.search(r'\*\*(?:작품 정보|Work)\*\*\s*\n(.+)', body)
    return [x.strip() for x in m.group(1).split(' · ')] if m else []

def work_title(p):
    w = work_line(p)
    return re.sub(r',\s*\d{4}$', '', w[0]) if w else B.L(p, 'title')

def work_artist(p, artists):
    a = str(p.get('artist') or '')
    if a.startswith('content/'):
        for d in artists:
            if d['_file'] == a:
                return B.L(d, 'name')
    w = work_line(p)
    return w[1] if len(w) > 1 else a

def body_paras(p):
    """Body without the trailing work-info block."""
    body = B.BODY(p) or ''
    return re.split(r'\*\*(?:작품 정보|Work)\*\*', body)[0].strip()

def facts(p, artists):
    rows = [(U('작가', 'Artist'), work_artist(p, artists)), (U('장소', 'Location'), B.L(p, 'location')),
            (U('연도', 'Year'), p.get('year')), (U('크기', 'Size'), B.L(p, 'size')),
            (U('유형', 'Type'), B.L(p, 'place_type')), (U('범위', 'Scope'), B.L(p, 'scope'))]
    return ''.join(f'<div><dt>{E(k)}</dt><dd>{E(v)}</dd></div>' for k, v in rows if not is_tbd(v))


# ---------------------------------------------------------------------------
# pages: (css class, running-head label, inner html, contents entry or None)
# ---------------------------------------------------------------------------
CHAPTERS = [  # number, title, subtitle (ko, en), opener photo, focus
    ('01', 'Practice', ('하는 일', 'What we do'), 'img/home/statement.jpg', '50% 62%'),
    ('02', 'Works', ('프로젝트', 'Projects'), 'img/projects/horizontal-gardens/main.jpg', '50% 40%'),
    ('03', 'People', ('작가와 파트너', 'Artists & partner'), 'img/artists/kim-byoungho/silent-propagations-236-2022.jpg', '50% 50%'),
]

def opener(ch):
    n, title, sub, img, pos = ch
    return ('opener dark', title, f'''
      <img class="bleed" src="{SRC(img)}" alt="" style="object-position:{pos}">
      <div class="op-text">
        <span class="op-num display">{n}</span>
        <div><h2 class="display op-title">{E(title)}</h2><p class="op-sub">{E(U(*sub))}</p></div>
      </div>''', ('chapter', ch))


def pages():
    S = B.SITE
    home, about, contact, company = S.get('home', {}), S.get('about', {}), S.get('contact', {}), S.get('company', {})
    services = home.get('services', []) or []
    wwd = about.get('what_we_do', []) or []
    projects = entries('projects')
    artists = [a for a in entries('artists') if not is_tbd(a.get('summary')) and 'goes here' not in B.L(a, 'summary') and '자리입니다' not in str(a.get('summary'))]
    byfile = {p['_file']: p for p in projects}
    featured = [byfile[f] for f in home.get('featured_projects', []) if f in byfile] or projects[:2]

    P = []

    # cover --------------------------------------------------------------------
    P.append(('cover', '', f'''
      <div class="cover-logo">{B.logo_svg('box')}</div>
      <div class="cover-top mono"><span>{U("회사 소개서", "Company Profile")}</span><span>{ISSUE} · 2026</span></div>
      <div class="cover-bottom">
        <p class="cover-line">{E(B.L(home, 'headline'))}</p>
        <p class="mono">Art Dealing · Art Projects · Architectural Art</p>
      </div>''', None))

    P.append(('contents', U('차례', 'Contents'), None, None))

    # intro --------------------------------------------------------------------
    P.append(('dark', U('질문', 'The question'), f'''
      <div class="grid g-question">
        <div class="year display">1917</div>
        <div class="story">{PARA(B.L(home, 'story_1'))}</div>
      </div>''', None))

    P.append(('', U('STANDS의 뜻', 'The name'), f'''
      <div class="grid g-meaning">
        <div>
          <div class="meaning-mark">{B.wordmark_svg()}</div>
          <div class="story">{PARA(B.L(home, 'story_2'))}</div>
        </div>
        {IMG(home.get('statement_image'), 'm-img')}
      </div>''', None))

    # 01 Practice --------------------------------------------------------------
    P.append(opener(CHAPTERS[0]))

    P.append(('', 'Practice', f'''
      <div class="grid g-about">
        {IMG(about.get('intro_image'), 'ab-img')}
        <div>
          <span class="mono num">About</span>
          <h2 class="display h2 ab-h">Art is complete<br>where it stands.</h2>
          <div class="cols-2 ab-copy">{''.join(PARA(x) for x in B.L(about, 'paragraphs') or [])}</div>
        </div>
      </div>
      <p class="closing">{E(B.L(about, 'closing'))}</p>''', ('entry', 'About')))

    cells = ''
    for it in wwd[:4]:
        items = B.LI(it, 'items') or []
        lis = ''.join(f'<li>{E(x)}</li>' for x in items)
        cells += f'''<div class="wwd"><span class="mono num">{E(str(it.get('label', '')).strip())}</span><h3>{E(B.LI(it, 'title'))}</h3><ul>{lis}</ul></div>'''
    P.append(('', 'Practice', f'''
      <div class="scope">
        <div class="scope-head"><h2 class="display h2">Scope</h2>{PARA((B.L(about, 'paragraphs') or [''])[-1], 'lead scope-lead')}</div>
        <div class="wwd-row">{cells}</div>
      </div>''', ('entry', 'Scope')))

    for i, sv in enumerate(services[:3]):
        items = B.LI(wwd[i], 'items') if i < len(wwd) else []
        chips = ''.join(f'<li>{E(x)}</li>' for x in items or [])
        flip = ' flip' if i == 1 else ''
        ill = f'img/illust/service-0{i+1}.svg'
        art = f'<div class="sv-ill"><img src="{SRC(ill)}" alt=""></div>' if os.path.exists(os.path.join(B.ROOT, ill)) else ''
        label = str(sv.get('label', '')).strip()
        P.append(('', 'Practice', f'''
          <div class="grid g-service{flip}">
            <div class="sv-text">
              <span class="sv-num display">{E(label.split('.')[0])}</span>
              <span class="mono num">{E(label.split('. ', 1)[-1])}</span>
              <h2 class="h-ko">{E(B.LI(sv, 'title'))}</h2>
              <p class="lead">{E(B.LI(sv, 'text'))}</p>
              <ul class="chips">{chips}</ul>
            </div>
            {art}
          </div>''', ('entry', B.LI(sv, 'title').split('·')[0].strip()) if i == 0 else None))

    PROCESS = [('01', '공간 분석', 'Site study'), ('02', '작품 제안', 'Proposal'), ('03', '심의', 'Review'),
               ('04', '제작', 'Fabrication'), ('05', '운송 · 설치', 'Transport · installation'), ('06', '완성', 'In place')]
    st = ''.join(f'''<li><div><span class="display step-num">{n}</span><h4>{E(U(ko, en))}</h4></div><img src="{SRC(f"img/illust/process-{n}.svg")}" alt=""></li>'''
                 for n, ko, en in PROCESS if os.path.exists(os.path.join(B.ROOT, f'img/illust/process-{n}.svg')))
    P.append(('', 'Practice', f'''
      <h2 class="display h2">Process</h2>
      <ol class="process">{st}</ol>
      <p class="closing">{E(B.L(about, 'closing'))}</p>''', ('entry', 'Process')))

    # 02 Works -----------------------------------------------------------------
    P.append(opener(CHAPTERS[1]))

    def feature(p, n):
        """Three pages: portrait-crop opener with facts, article with pull quote, photo sequence."""
        gal = p.get('gallery') or []
        paras = body_paras(p)
        sentences = re.split(r'(?<=[.다])\s+', paras.replace('\n', ' '))
        quote = next((s for s in sentences if 20 <= len(s) <= 90 and s[0] not in '\'"‘“'), sentences[0] if sentences else '')
        title = work_title(p)
        out = [('bleed-left', 'Works', f'''
          {IMG(p.get('cover'), 'ft-img')}
          <div class="ft-text">
            <span class="mono num">FEATURE {n:02d} · {E(B.L(p, 'place_type'))}</span>
            <h2 class="feature-title">{E(title)}</h2>
            <p class="standfirst">{E(B.L(p, 'summary'))}</p>
            <dl class="meta">{facts(p, artists)}</dl>
          </div>''', ('entry', title))]
        img2 = gal[1] if len(gal) > 1 else (gal[0] if gal else None)
        out.append(('', 'Works', f'''
          <div class="grid g-article">
            <div class="article-body">{PARA(paras, 'body')}</div>
            <div class="article-side">
              <blockquote class="pull">{E(quote)}</blockquote>
              {IMG(img2, 'a-img', U('설치 전경', 'In place'), 1) if img2 else ''}
            </div>
          </div>''', None))
        rest = [g for g in gal if g != img2][:3]
        if rest:
            caps = [U('디테일', 'Detail'), U('작품과 공간', 'Work and space'), U('주변 풍경', 'Surroundings')]
            figs = ''.join(IMG(g, f's{k+1}', caps[k], k + 2) for k, g in enumerate(rest))
            out.append(('', 'Works', f'''<div class="grid g-seq n{len(rest)}">{figs}</div>''', None))
        return out

    def feature_short(p, n):
        gal = p.get('gallery') or []
        title = work_title(p)
        figs = ''.join(IMG(g, '', '', k + 2) for k, g in enumerate(gal[:2]))
        return [('', 'Works', f'''
          <div class="grid g-short">
            {IMG(p.get('cover'), 'sh-main', '', 1)}
            <div class="sh-text">
              <span class="mono num">FEATURE {n:02d} · {E(B.L(p, 'place_type'))}</span>
              <h2 class="feature-title sm">{E(title)}</h2>
              <div class="sh-body">{PARA(body_paras(p), 'body')}</div>
              <dl class="meta">{facts(p, artists)}</dl>
            </div>
            <div class="sh-figs">{figs}</div>
          </div>''', ('entry', title))]

    if featured:
        P += feature(featured[0], 1)
    for k, p in enumerate(featured[1:3], 2):
        P += feature_short(p, k)
    others = [p for p in projects if p not in featured[:3]]
    for chunk in [others[i:i + 4] for i in range(0, len(others), 4)]:
        cards = ''.join(f'''<article class="card">{IMG(p.get('cover'))}
            <h4>{E(work_title(p))}</h4>
            <p class="mono">{E(' · '.join(x for x in (work_artist(p, artists), B.L(p, 'location'), B.L(p, 'place_type')) if not is_tbd(x)))}</p>
            <p class="card-sum">{E(B.L(p, 'summary'))}</p></article>''' for p in chunk)
        P.append(('', 'Works', f'''
          <h2 class="display h2">Selected projects</h2>
          <div class="cards-{len(chunk)}">{cards}</div>''', ('entry', 'Selected projects') if chunk is others[:4] or True else None))
    # only the first "Selected projects" page goes in the contents
    seen = False
    for i, pg in enumerate(P):
        if pg[3] == ('entry', 'Selected projects'):
            if seen:
                P[i] = pg[:3] + (None,)
            seen = True

    # 03 People ----------------------------------------------------------------
    P.append(opener(CHAPTERS[2]))

    def profile(a, n):
        q = B.L(a, 'quote')
        quote = f'<blockquote class="pull sm">“{E(q)}”</blockquote>' if not is_tbd(q) and '자리입니다' not in q else ''
        meta = ' · '.join(x for x in (B.L(a, 'medium'), B.L(a, 'based')) if not is_tbd(x))
        img = a.get('hero_image') or a.get('photo')
        return f'''<article class="profile">
          {IMG(img, 'pf-img', B.L(a, 'hero_caption'))}
          <div class="pf-text"><span class="mono num">ARTIST {n:02d}</span>
            <h3>{E(B.L(a, 'name'))}</h3><p class="mono">{E(meta)}</p>
            {quote}<p class="pf-sum">{E(B.L(a, 'summary'))}</p></div>
        </article>'''
    for i in range(0, len(artists), 2):
        pair = artists[i:i + 2]
        P.append(('', 'People', f'''<div class="profiles n{len(pair)}">{''.join(profile(a, i + k + 1) for k, a in enumerate(pair))}</div>''',
                  ('entry', ' · '.join(B.L(a, 'name') for a in pair))))

    pt = wwd[3] if len(wwd) > 3 else {}
    pitems = ''.join(f'<li>{E(x)}</li>' for x in (B.LI(pt, 'items') or []))
    alist = ''.join(f'<li><span>{E(B.L(a, "name"))}</span><span class="mono">{E(B.L(a, "medium"))}</span></li>' for a in artists)
    P.append(('', 'People', f'''
      <div class="grid g-index">
        <div><h2 class="display h2">Artists</h2><ol class="a-index">{alist}</ol></div>
        <div class="partner">
          <span class="mono num">PARTNER</span>
          <h2 class="partner-name">{E(B.LI(pt, 'title'))}</h2>
          <ul class="chips">{pitems}</ul>
        </div>
      </div>''', ('entry', 'Partner')))

    # masthead -----------------------------------------------------------------
    rows = [(U('상호', 'Company'), B.L(company, 'name')), (U('대표', 'CEO'), B.L(company, 'ceo')),
            (U('사업자등록번호', 'Business reg. no.'), company.get('business_no')), (U('미술품 유통업 신고번호', 'Art dealer reg. no.'), company.get('art_service_no')),
            (U('주소', 'Address'), B.L(contact, 'address')), (U('대표 전화', 'Tel'), contact.get('tel'))]
    issue = [(U('발행', 'Published'), f'{ISSUE} · {datetime.date.today():%Y.%m}'), (U('발행처', 'Publisher'), 'STANDS'),
             (U('이메일', 'Email'), contact.get('email')), ('Instagram', contact.get('instagram')),
             ('Web', B.BASE_URL.replace('https://', '').rstrip('/') + ('/en/' if B.EN() else ''))]
    col = lambda rs: ''.join(f'<div><dt>{E(k)}</dt><dd>{T(v)}</dd></div>' for k, v in rs)
    P.append(('masthead-page', U('판권', 'Masthead'), f'''
      <div class="masthead">
        <div class="mh-logo">{B.wordmark_svg()}</div>
        <dl class="mh-col">{col(issue)}</dl>
        <dl class="mh-col">{col(rows)}</dl>
        <p class="mh-fine">{E(U("이 소개서에 실린 작품 이미지와 글의 저작권은 각 작가와 STANDS에 있습니다. 사전 허락 없이 복제하거나 배포할 수 없습니다.", "All images of works and all texts are copyright of the artists and STANDS. Do not reproduce without permission."))}</p>
      </div>''', None))

    # back cover ---------------------------------------------------------------
    P.append(('dark back', '', f'''
      <img class="bleed back-bg" src="{SRC('img/courtyard-poster.jpg')}" alt="">
      <div class="back-shade"></div>
      <div class="back-inner">
        <h2 class="headline">{E(B.L(home, 'cta_title'))}</h2>
        <dl class="contact">
          <div><dt class="mono">Email</dt><dd>{T(contact.get('email'))}</dd></div>
          <div><dt class="mono">Tel</dt><dd>{T(contact.get('tel'))}</dd></div>
          <div><dt class="mono">Instagram</dt><dd>{T(contact.get('instagram'))}</dd></div>
          <div><dt class="mono">Web</dt><dd>{E(B.BASE_URL.replace('https://', '').rstrip('/'))}</dd></div>
        </dl>
      </div>
      <div class="back-logo">{B.wordmark_svg()}</div>''', None))
    return P


def toc(P):
    """Contents page, built after numbering so page numbers stay right."""
    rows, cur = [], None
    for i, (cls, label, _, t) in enumerate(P, 1):
        if not t:
            continue
        if t[0] == 'chapter':
            cur = {'ch': t[1], 'page': i, 'items': []}
            rows.append(cur)
        elif cur:
            cur['items'].append((t[1], i))
    out = ''
    for r in rows:
        n, title, sub, img, pos = r['ch']
        items = ''.join(f'<li><span>{E(name)}</span><span class="dots"></span><span class="mono">{pg:02d}</span></li>' for name, pg in r['items'])
        out += f'''<li class="t-ch"><img src="{SRC(img)}" alt="" style="object-position:{pos}">
          <div><div class="t-head"><span class="t-num display">{n}</span><h3 class="display">{E(title)}</h3><span class="mono t-pg">{r["page"]:02d}</span></div>
          <p class="t-sub">{E(U(*sub))}</p><ol class="t-items">{items}</ol></div></li>'''
    return f'''
      <div class="grid g-toc">
        <div><h2 class="display h2">Contents</h2><p class="mono toc-issue">{ISSUE} · 2026</p></div>
        <ol class="toc">{out}</ol>
      </div>'''


# ---------------------------------------------------------------------------
FONTS = [('Pretendard', 400, 'normal', 'Pretendard-Regular'), ('Pretendard', 500, 'normal', 'Pretendard-Medium'),
         ('Pretendard', 600, 'normal', 'Pretendard-SemiBold'), ('Pretendard', 700, 'normal', 'Pretendard-Bold'),
         ('Archivo Condensed', 800, 'normal', 'ArchivoCondensed-ExtraBold'), ('Archivo Condensed', 900, 'normal', 'ArchivoCondensed-Black'),
         ('Newsreader', 400, 'italic', 'Newsreader-Italic'),
         ('Noto Sans KR', 400, 'normal', 'NotoSansKR-Regular'), ('Noto Sans KR', 600, 'normal', 'NotoSansKR-SemiBold'),
         ('IBM Plex Mono', 400, 'normal', 'IBMPlexMono-Regular'), ('IBM Plex Mono', 500, 'normal', 'IBMPlexMono-Medium')]
FONT_CSS = ''.join(f"@font-face{{font-family:'{f}';font-weight:{w};font-style:{s};src:url('fonts/{ps}.ttf') format('truetype')}}\n"
                   for f, w, s, ps in FONTS if os.path.exists(os.path.join(OUT, 'fonts', ps + '.ttf')))

CSS = r'''
@page{size:297mm 210mm;margin:0}
:root{--black:#000;--paper:#F0F0EE;--paper-2:#E5E5E2;--line:#D3D2CE;--muted:#6C6A71;--accent:#7D7889;--sky:#8FCAD8;
  --display:"Archivo Condensed",sans-serif;--accent-font:"Newsreader",serif;--body:"Pretendard","Noto Sans KR",sans-serif;--mono:"IBM Plex Mono","Pretendard","Noto Sans KR",monospace;
  --m:15mm;--gap:8mm}
*{box-sizing:border-box;font-synthesis:none}
html,body{margin:0;background:#9a989e}
body{font-family:var(--body);color:var(--black);font-size:9.5pt;line-height:1.6;-webkit-print-color-adjust:exact;print-color-adjust:exact}
p{margin:0 0 .8em}
h1,h2,h3,h4{margin:0;font-weight:700}
ul,ol{margin:0;padding:0;list-style:none}
blockquote{margin:0}
.page{width:297mm;height:210mm;position:relative;overflow:hidden;background:var(--paper);padding:calc(var(--m) + 7mm) var(--m) calc(var(--m) + 6mm);margin:0 auto 10mm;break-after:page}
@media print{html,body{background:none}.page{margin:0}}
.page.dark{background:var(--black);color:var(--paper)}
/* running heads and folios */
.chrome{position:absolute;left:var(--m);right:var(--m);display:flex;justify-content:space-between;font-family:var(--mono);font-size:6.5pt;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);z-index:3}
.chrome.top{top:9mm}.chrome.bottom{bottom:8mm}
.chrome .folio{font-family:var(--display);font-weight:900;font-size:9pt;letter-spacing:0;color:var(--black)}
.dark .chrome{color:#a9a6b0}
.dark .chrome .folio{color:var(--paper)}
.bleed-left .chrome span:first-child{visibility:hidden}
/* type */
.mono{font-family:var(--mono);font-size:7pt;letter-spacing:.08em;text-transform:uppercase}
.display{font-family:var(--display);font-weight:900;text-transform:uppercase;letter-spacing:-.01em;line-height:.92;word-spacing:.12em}
.h2{font-size:38pt;margin-bottom:8mm}
.h-ko{font-size:21pt;line-height:1.3;letter-spacing:-.02em;margin:3mm 0 5mm}
.headline{font-family:var(--body);font-weight:700;font-size:30pt;letter-spacing:-.03em;line-height:1.2}
.lead{font-size:10.5pt;line-height:1.75}
.standfirst{font-family:var(--accent-font);font-style:italic;font-size:13pt;line-height:1.5;margin-bottom:8mm}
:lang(ko) .standfirst{font-family:var(--body);font-style:normal;font-weight:500;font-size:12pt;line-height:1.65;letter-spacing:-.01em}
.pull{font-family:var(--accent-font);font-style:italic;font-size:17pt;line-height:1.4;padding-top:4mm;border-top:2px solid var(--black)}
:lang(ko) .pull{font-family:var(--body);font-style:normal;font-weight:600;font-size:15pt;line-height:1.55;letter-spacing:-.02em}
.pull.sm{font-size:12pt;margin:4mm 0 4mm;padding-top:3mm;border-top-width:1px}
:lang(ko) .pull.sm{font-size:11pt}
.num{color:var(--accent);display:block}
.dark .num{color:#a9a4b6}
.closing{position:absolute;left:var(--m);right:var(--m);bottom:calc(var(--m) + 6mm);font-family:var(--body);font-weight:500;font-size:13pt;letter-spacing:-.01em;margin:0;padding-top:4mm;border-top:1px solid var(--line)}
.tbd{color:var(--accent);outline:1px dashed var(--accent);outline-offset:1mm}
.body{font-size:9.5pt;line-height:1.85}
/* images: frame clips, caption sits below */
.img{margin:0;display:flex;flex-direction:column;min-height:0}
.img .frame{flex:1;min-height:0;overflow:hidden;background:var(--paper-2)}
.img img{width:100%;height:100%;object-fit:cover;display:block}
.img figcaption{font-family:var(--mono);font-size:6.5pt;letter-spacing:.06em;color:var(--muted);margin-top:1.8mm;line-height:1.4}
.img figcaption b{font-weight:500;color:var(--black);margin-right:2mm}
.dark .img figcaption b{color:var(--paper)}
.grid{display:grid;gap:var(--gap);height:100%}
.bleed{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
/* cover */
.cover{display:flex;align-items:center;justify-content:center}
.cover-logo .box{width:44mm;height:44mm;display:block}
.cover-top,.cover-bottom{position:absolute;left:var(--m);right:var(--m);display:flex;justify-content:space-between;align-items:baseline;color:var(--muted)}
.cover-top{top:var(--m)}
.cover-bottom{bottom:calc(var(--m) + 4mm);border-top:1px solid var(--line);padding-top:3mm}
.cover-bottom p{margin:0}
.cover-line{font-size:9pt;letter-spacing:-.01em;color:var(--black)}
/* contents */
.g-toc{grid-template-columns:4fr 8fr;gap:14mm}
.toc-issue{color:var(--muted)}
.toc{border-top:1px solid var(--black)}
.t-ch{display:grid;grid-template-columns:38mm 1fr;gap:7mm;padding:4mm 0;border-bottom:1px solid var(--line)}
.t-ch > img{width:38mm;height:30mm;object-fit:cover}
.t-head{display:flex;align-items:baseline;gap:4mm}
.t-num{font-size:22pt;color:var(--accent)}
.t-head h3{font-size:22pt;flex:1}
.t-pg{font-size:9pt}
.t-sub{color:var(--muted);margin:1mm 0 2mm;font-size:8.5pt}
.t-items{columns:2;column-gap:8mm}
.t-items li{display:flex;gap:2mm;font-size:8pt;line-height:1.9;break-inside:avoid}
.t-items .dots{flex:1;border-bottom:1px dotted var(--line);margin-bottom:1.6mm}
/* chapter opener */
.opener{padding:0}
.opener::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 45%,rgba(0,0,0,.62));z-index:1}
.op-text{position:absolute;left:var(--m);right:var(--m);bottom:calc(var(--m) + 6mm);display:flex;align-items:flex-end;gap:8mm;z-index:2;color:var(--paper)}
.op-num{font-size:150pt;line-height:.72}
.op-title{font-size:56pt;margin-bottom:2mm}
.op-sub{font-size:13pt;font-weight:500;margin:0 0 1mm}
/* question / meaning */
.g-question{grid-template-columns:1fr 1fr;align-items:end}
.year{font-size:150pt;color:var(--paper);line-height:.8;align-self:start}
.g-question .story{font-size:12.5pt;line-height:1.85}
.g-meaning{grid-template-columns:7fr 3fr;gap:12mm}
.meaning-mark .wordmark{width:100%;height:auto;display:block;margin:0 0 10mm}
.g-meaning .story{columns:2;column-gap:10mm;font-size:10.5pt;line-height:1.85}
.g-meaning .story p{break-inside:avoid}
.m-img{height:100%}
/* practice */
.g-about{grid-template-columns:4fr 7fr;gap:12mm;height:calc(100% - 18mm)}
.ab-img{height:100%}
.ab-h{font-size:30pt;margin:2mm 0 7mm}
.cols-2{columns:2;column-gap:9mm;font-size:9.5pt;line-height:1.85}
.cols-2 p{break-inside:avoid}
.scope{display:flex;flex-direction:column;justify-content:space-between;height:100%}
.scope-head{display:grid;grid-template-columns:4fr 7fr;gap:14mm;align-items:start}
.scope-lead{font-size:12pt;line-height:1.8;margin-top:1mm}
.wwd-row{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap)}
.wwd{border-top:2px solid var(--black);padding-top:4mm}
.wwd h3{font-size:14pt;line-height:1.35;margin:2mm 0 5mm;letter-spacing:-.01em;min-height:13mm}
.wwd li{font-size:10pt;padding:2.2mm 0;border-bottom:1px solid var(--line)}
.g-service{grid-template-columns:5fr 6fr;gap:14mm;align-items:center}
.g-service.flip{grid-template-columns:6fr 5fr}
.g-service.flip .sv-ill{order:-1}
.sv-num{font-size:90pt;line-height:.8;color:var(--accent);display:block;margin-bottom:4mm}
.sv-ill{height:100%;background:var(--paper-2);display:flex;align-items:center;justify-content:center}
.sv-ill img{width:72%;height:auto}
.chips{display:flex;flex-wrap:wrap;gap:1.8mm;margin-top:6mm}
.chips li{border:1px solid var(--black);padding:.6mm 3mm;font-size:8.5pt;border-radius:10mm}
.process{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:1fr 1fr;gap:5mm 10mm;position:absolute;left:var(--m);right:var(--m);top:calc(var(--m) + 7mm + 22mm);bottom:calc(var(--m) + 22mm)}
.process li{border-top:1px solid var(--black);padding-top:3mm;display:grid;grid-template-columns:1fr 1.3fr;gap:4mm;align-items:start;min-height:0}
.process img{width:100%;height:auto;max-height:100%;display:block;order:2}
.step-num{font-size:30pt;color:var(--accent);display:block}
.process h4{font-size:12pt;margin-top:2mm}
/* works */
.bleed-left{padding-left:calc(148.5mm + 11mm)}
.ft-img{position:absolute;left:0;top:0;bottom:0;width:148.5mm}
.ft-text{display:flex;flex-direction:column;height:100%}
.feature-title{font-size:28pt;letter-spacing:-.03em;line-height:1.2;margin:4mm 0 6mm}
.feature-title.sm{font-size:20pt;margin:3mm 0 4mm}
.ft-text .meta{margin-top:auto}
.meta{margin:5mm 0 0;display:grid;gap:2mm;border-top:1px solid var(--black);padding-top:3mm;font-size:8.5pt}
.meta div{display:grid;grid-template-columns:20mm 1fr;align-items:baseline}
.meta dt{font-family:var(--mono);font-size:6.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.meta dd{margin:0}
.g-article{grid-template-columns:6fr 5fr;gap:14mm}
.article-body{padding-right:6mm}
.article-body .body{font-size:11pt;line-height:1.95;text-align:left;margin-bottom:1.2em}
.article-body p:first-child{font-size:13pt;font-weight:500;line-height:1.8;letter-spacing:-.01em}
.article-side{display:flex;flex-direction:column;gap:8mm;min-height:0}
.a-img{flex:1}
.g-seq{grid-template-columns:5fr 3fr;grid-template-rows:1fr 1fr;gap:6mm 6mm}
.g-seq .s1{grid-row:1/3}
.g-seq.n1{grid-template-columns:1fr;grid-template-rows:1fr}
.g-seq.n2{grid-template-columns:1fr 1fr;grid-template-rows:1fr}.g-seq.n2 .s1{grid-row:auto}
.g-short{grid-template-columns:6fr 4fr 2.4fr;gap:8mm}
.sh-main{height:100%}
.sh-text{display:flex;flex-direction:column}
.sh-body .body{font-size:8.8pt;line-height:1.8}
.sh-text .meta{margin-top:auto}
.sh-figs{display:grid;grid-template-rows:1fr 1fr;gap:6mm;min-height:0}
.cards-4{display:grid;grid-template-columns:repeat(4,1fr);gap:7mm}
.cards-3{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--gap)}
.cards-2{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--gap)}
.card .img{height:auto}.card .frame{aspect-ratio:4/5;flex:none}
.card h4{font-size:11pt;margin:3mm 0 1mm}
.card .mono{color:var(--muted);font-size:6.5pt;margin-bottom:2mm}
.card-sum{font-size:8pt;line-height:1.7;color:#333}
/* people */
.profiles{display:grid;grid-template-columns:1fr 1fr;gap:14mm;height:100%}
.profile{display:grid;grid-template-rows:56% 1fr;gap:5mm;min-height:0}
.pf-img{min-height:0}
.profile h3{font-size:18pt;margin:1.5mm 0 1mm}
.pf-text .mono{color:var(--muted)}
.pf-sum{font-size:9pt;line-height:1.8;margin-top:3mm}
.g-index{grid-template-columns:1fr 1fr;gap:16mm}
.a-index{border-top:1px solid var(--black)}
.a-index li{display:flex;justify-content:space-between;align-items:baseline;padding:3.5mm 0;border-bottom:1px solid var(--line);font-size:15pt;font-weight:600;letter-spacing:-.01em}
.a-index .mono{color:var(--muted);font-weight:400}
.partner{border-left:1px solid var(--line);padding-left:12mm}
.partner-name{font-size:34pt;letter-spacing:-.03em;line-height:1.2;margin:4mm 0 4mm}
/* masthead */
.masthead{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12mm;height:100%;align-content:start;font-size:9pt}
.mh-logo{grid-column:1/-1;width:70mm;margin-bottom:6mm}
.mh-logo .wordmark{width:100%;height:auto;display:block}
.mh-col{margin:0;display:grid;gap:3.5mm;align-content:start;border-top:1px solid var(--black);padding-top:3mm}
.mh-col div{display:grid;grid-template-columns:34mm 1fr;align-items:baseline}
.mh-col dt{font-family:var(--mono);font-size:6.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.mh-col dd{margin:0}
.mh-fine{align-self:start;border-top:1px solid var(--line);padding-top:3mm;color:var(--muted);font-size:7pt}
/* back cover */
.back{padding:0}
.back-shade{position:absolute;inset:0;background:rgba(0,0,0,.6)}
.back-inner{position:absolute;left:var(--m);bottom:calc(var(--m) + 4mm);width:150mm}
.back .headline{font-size:28pt;margin-bottom:10mm}
.contact{display:grid;grid-template-columns:1fr 1fr;gap:4mm 10mm;margin:0}
.contact dt{color:#a9a4b6;margin-bottom:.5mm}.contact dd{margin:0;font-size:11pt}
.back-logo{position:absolute;right:var(--m);bottom:calc(var(--m) + 5mm);width:62mm;color:var(--paper)}
.back-logo .wordmark{width:100%;height:auto;display:block}
'''


def render(lang):
    B.LANG = lang
    P = pages()
    P = [(c, l, toc(P) if c == 'contents' else x, t) for c, l, x, t in P]
    body = []
    for i, (cls, label, inner, _) in enumerate(P, 1):
        if cls == 'cover' or 'back' in cls.split():
            top = bottom = ''
        else:
            top = f'<div class="chrome top"><span>STANDS — {ISSUE}</span><span>{E(label)}</span></div>'
            bottom = f'<div class="chrome bottom"><span>{U("회사 소개서", "Company Profile")} · {datetime.date.today():%Y.%m}</span><span class="folio">{i:02d}</span></div>'
        body.append(f'<section class="page {E(cls)}">{top}{inner}{bottom}</section>')
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<title>STANDS — {U("회사 소개서", "Company Profile")} {ISSUE}</title>
<style>{FONT_CSS}{CSS}</style></head>
<body>{''.join(body)}</body></html>'''


if __name__ == '__main__':
    lang = 'en' if '--lang' in sys.argv and sys.argv[sys.argv.index('--lang') + 1] == 'en' else 'ko'
    if not os.path.isdir(os.path.join(OUT, 'fonts')):
        sys.exit('Fonts missing: run  python build/brochure_fonts.py  first.')
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'brochure-{lang}.html')
    open(path, 'w', encoding='utf-8').write(render(lang))
    print('wrote', os.path.relpath(path, B.ROOT))
