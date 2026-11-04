#!/usr/bin/env python3
"""STANDS brand brochure (company profile) — layout generator.

Writes _brochure/brochure-<lang>.html (A4 landscape, one <section> per page) from content/site.yml.
Laid out like a magazine issue: cover, contents, four chapters (Practice, Method, Works, People), masthead, back cover.
Words that already exist on the website are filled in; everything else is a visible placeholder (lavender, dashed),
so the layout can be reviewed before the copy is written.

    python build/brochure.py            # Korean
    python build/brochure.py --lang en  # English (empty English falls back to Korean, like the site)
    node build/brochure_pdf.mjs         # renders every _brochure/*.html to PDF with Chromium

Not part of the GitHub Pages deploy.
"""
import os, sys, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B   # reuses the logo, wordmark, content and language helpers (build.py only builds under __main__)

OUT = os.path.join(B.ROOT, '_brochure')
VERSION = 'v0.2 layout'
ISSUE = 'ISSUE 01'
E = lambda s: html.escape(str(s or ''), quote=True)
U = lambda ko, en: B.U(ko, en)


def is_tbd(s):
    s = str(s or '').strip()
    return not s or (s.startswith('[') and s.endswith(']'))

def T(s, ph=None, tag='span'):
    """Content text; empty or '[입력]' values turn into a placeholder."""
    if is_tbd(s):
        return f'<{tag} class="tbd">{E(ph or s or U("[입력]", "[TBD]"))}</{tag}>'
    return f'<{tag}>{E(s)}</{tag}>'

def PARA(s):
    out = []
    for block in str(s or '').strip().split('\n\n'):
        lines = [E(l.strip()) for l in block.split('\n') if l.strip()]
        if lines:
            out.append('<p>' + '<br>'.join(lines) + '</p>')
    return ''.join(out)

def PH(text, cls=''):
    """Text placeholder block: what goes here."""
    return f'<p class="tbd {cls}">{E(text)}</p>'

def DUMMY(n, cls='dummy'):
    """Stand-in body copy, to show text density. Rendered in muted lavender so it can't pass for real copy."""
    s = U('본문이 들어갈 자리입니다. 실제 문구는 프로젝트의 과제와 판단, 현장에서의 실행과 결과를 순서대로 담습니다. ',
          'Body copy goes here. The real text follows the brief, the decisions, the work on site and the result. ')
    return ''.join(f'<p class="{cls}">{E(s * 3)}</p>' for _ in range(n))

def IMG(label, cls='', src=None, temp=False, num=None):
    """Image slot. With src: a stand-in photo, marked as temporary. Without: a hatched placeholder.
    num adds a magazine-style numbered caption under the image."""
    cap = f'<figcaption>{f"<b>{num:02d}</b> — " if num else ""}{E(label)}</figcaption>'
    if src:
        badge = f'<span class="badge">{E(U("임시 이미지", "Temporary image"))}</span>' if temp else ''
        return f'<figure class="img {cls}"><img src="../{src}" alt="">{badge}{cap}</figure>'
    return f'<figure class="img ph {cls}">{cap}</figure>'

def split_dash(t):
    for sep in (' — ', ' - '):
        if sep in t:
            a, b = t.split(sep, 1)
            return a.strip(), b.strip()
    return t.strip(), ''


# ---------------------------------------------------------------------------
# pages: each page is (css class, chapter label, inner html); ('toc', …) is filled in after numbering
# ---------------------------------------------------------------------------
CHAPTERS = [  # number, title, Korean/English subtitle placeholder, opener photo (temporary)
    ('01', 'Practice', ('하는 일', 'What we do'), 'img/hero/01-loft.jpg'),
    ('02', 'Method', ('일하는 방식', 'How we work'), 'img/hero/07-garden.jpg'),
    ('03', 'Works', ('프로젝트', 'Projects'), 'img/hero/09-museum.jpg'),
    ('04', 'People', ('작가와 파트너', 'Artists & partner'), 'img/hero/06-terrace.jpg'),
]

def opener(ch):
    n, title, sub, img = ch
    return ('opener dark', title, f'''
      <img class="bleed" src="../{img}" alt=""><span class="badge">{E(U("임시 이미지", "Temporary image"))}</span>
      <div class="op-text">
        <span class="op-num display">{n}</span>
        <div><h2 class="display op-title">{E(title)}</h2>
        <p class="op-sub">{E(U(*sub))}</p>
        <p class="tbd op-lede">{E(U("[장을 여는 한 문장]", "[One line that opens the chapter]"))}</p></div>
      </div>''')


def pages():
    S = B.SITE
    home, about, contact, company = S.get('home', {}), S.get('about', {}), S.get('contact', {}), S.get('company', {})
    services = home.get('services', []) or []
    wwd = about.get('what_we_do', []) or []

    def scope(i):
        t = B.LI(wwd[i], 'text') if i < len(wwd) else ''
        return [x.strip() for x in split_dash(t)[1].split(',') if x.strip()]

    P = []

    # cover --------------------------------------------------------------------
    P.append(('cover', '', f'''
      <div class="cover-logo">{B.logo_svg('box')}</div>
      <div class="cover-top mono"><span>{U("회사 소개서", "Company Profile")}</span><span>{ISSUE} · 2026</span></div>
      <div class="cover-bottom">
        <p class="cover-line">{E(B.L(home, 'headline'))}</p>
        <p class="mono">Art Dealing · Art Projects · Architectural Art</p>
      </div>'''))

    P.append(('contents', U('차례', 'Contents'), None))

    # intro --------------------------------------------------------------------
    P.append(('dark', U('질문', 'The question'), f'''
      <div class="grid g-question">
        <div class="year display">1917</div>
        <div class="story">{PARA(B.L(home, 'story_1'))}</div>
        {IMG(U("뒤샹 〈샘〉 — 사용 권리 확인 후 배치", "Duchamp, Fountain — place after rights check"), 'q-img')}
      </div>'''))

    P.append(('', U('STANDS의 뜻', 'The name'), f'''
      <div class="meaning-mark">{B.wordmark_svg()}</div>
      <div class="cols-2 story">{PARA(B.L(home, 'story_2'))}</div>'''))

    # 01 Practice --------------------------------------------------------------
    P.append(opener(CHAPTERS[0]))

    cells = ''
    wimgs = ['img/hero/10-gallery.jpg', 'img/hero/04-atrium.jpg', 'img/hero/11-plaza.jpg', 'img/hero/08-park.jpg']
    for i, it in enumerate(wwd[:4]):
        title, rest = split_dash(B.LI(it, 'text'))
        cells += f'''<div class="wwd">{IMG('', '', wimgs[i], temp=True)}<span class="mono num">{E(str(it.get('label', '')).strip())}</span><h3>{E(title)}</h3><p>{E(rest)}</p></div>'''
    P.append(('', 'Practice', f'''
      <h2 class="display h2">What we do</h2>
      <div class="wwd-row">{cells}</div>
      <p class="closing">{E(B.L(about, 'closing'))}</p>'''))

    photos = ['img/hero/10-gallery.jpg', 'img/hero/04-atrium.jpg', 'img/hero/11-plaza.jpg']
    for i, sv in enumerate(services[:3]):
        items = ''.join(f'<li>{E(x)}</li>' for x in scope(i)) or f'<li class="tbd">{E(U("[수행 범위]", "[Scope]"))}</li>'
        flip = ' flip' if i == 1 else ''
        P.append(('', 'Practice', f'''
          <div class="grid g-service{flip}">
            <div class="sv-text">
              <span class="mono num">{E(str(sv.get('label', '')).strip())}</span>
              <h2 class="h-ko">{E(B.LI(sv, 'title'))}</h2>
              <p class="lead">{E(B.LI(sv, 'text'))}</p>
              <div class="facts">
                <div><span class="mono k">{U("수행 범위", "Scope")}</span><ul>{items}</ul></div>
                <div><span class="mono k">{U("산출물", "Deliverables")}</span>{PH(U("제안서, 작품 리스트, 견적, 설치 도면 등 고객이 받는 것", "What the client receives: proposal, work list, estimate, drawings…"))}</div>
                <div><span class="mono k">{U("이런 분께", "For")}</span>{PH(U("이 서비스가 맞는 고객과 상황 2–3가지", "2–3 client types or situations"))}</div>
              </div>
            </div>
            {IMG(U("대표 사례 — 장소, 연도", "Key project — place, year"), 'sv-img', photos[i], temp=True, num=i + 1)}
          </div>'''))

    # 02 Method ----------------------------------------------------------------
    P.append(opener(CHAPTERS[1]))

    steps = [U('상담 · 진단', 'Brief'), U('기획 · 제안', 'Proposal'), U('작가 · 작품 선정', 'Artist & work selection'),
             U('심의 · 계약', 'Review & contract'), U('제작', 'Fabrication'), U('운송 · 설치', 'Transport & installation'),
             U('관리 · 리세일', 'Care & resale')]
    st = ''.join(f'''<li><span class="step-num display">{i+1:02d}</span><div><h4>{E(s)}</h4>{PH(U("단계 설명 한 줄", "One line"), "sm")}</div></li>''' for i, s in enumerate(steps))
    P.append(('', 'Method', f'''
      <div class="grid g-method">
        <div class="m-left">
          <h2 class="display h2">How we work</h2>
          <p class="standfirst tbd">{E(U("[도입문 — 예술적 판단과 현장의 실행을 하나의 흐름으로 잇는 방식]", "[Standfirst — judgment and execution as one process]"))}</p>
          <blockquote class="pull">“{E(B.L(about, 'closing'))}”</blockquote>
        </div>
        <ol class="steps-v">{st}</ol>
      </div>'''))

    qa = [(U('어떤 건축물이 대상인가요?', 'Which buildings are covered?'), U('설치 의무 대상과 기준 (법령 확인 후 기재)', 'Scope and threshold (verify the law)')),
          (U('비용은 어떻게 정해지나요?', 'How is the budget set?'), U('작품 설치 비용 산정 기준', 'How the art budget is calculated')),
          (U('얼마나 걸리나요?', 'How long does it take?'), U('기획부터 설치까지 일반적인 기간', 'Typical time from planning to installation')),
          (U('STANDS는 무엇을 맡나요?', 'What does STANDS handle?'), U('대행 범위: 심의 서류, 작가 섭외, 제작 관리 등', 'Scope: review documents, artists, fabrication'))]
    qh = ''.join(f'<div class="qa"><span class="mono num">Q{i+1}</span><h4>{E(q)}</h4>{PH(a)}</div>' for i, (q, a) in enumerate(qa))
    P.append(('', 'Method', f'''
      <div class="grid g-guide">
        <div>
          <span class="mono num">GUIDE · {U("건축물 미술작품", "Architectural art")}</span>
          <h2 class="h-ko big">{U("건축물 미술작품,<br>무엇을 준비해야<br>하나", "Architectural art:<br>what to<br>prepare")}</h2>
          <p class="note mono">{U("법령 기준과 수치는 확인 후 기재", "Verify legal thresholds before writing")}</p>
        </div>
        <div class="qa-grid">{qh}</div>
      </div>'''))

    # 03 Works -----------------------------------------------------------------
    P.append(opener(CHAPTERS[2]))

    meta = [(U('클라이언트', 'Client'), U('[클라이언트]', '[Client]')), (U('장소', 'Location'), U('[장소]', '[Location]')),
            (U('연도', 'Year'), '[2026]'), (U('작가', 'Artist'), U('[작가]', '[Artist]')), (U('범위', 'Scope'), U('[수행 범위]', '[Scope]'))]
    dl = ''.join(f'<div><dt class="mono">{E(k)}</dt><dd class="tbd">{E(v)}</dd></div>' for k, v in meta)
    P.append(('bleed-left', 'Works', f'''
      {IMG(U("대표 프로젝트 전경 — 세로 고해상도", "Featured project — portrait, high resolution"), 'ft-img', num=1)}
      <div class="ft-text">
        <span class="mono num">FEATURE · PROJECT 01</span>
        <h2 class="feature-title tbd">{E(U("[프로젝트명]", "[Project title]"))}</h2>
        <p class="standfirst tbd">{E(U("[도입문 — 이 프로젝트가 풀어야 했던 질문을 두세 줄로]", "[Standfirst — the question this project had to answer, in two or three lines]"))}</p>
        <dl class="meta">{dl}</dl>
      </div>'''))

    P.append(('', 'Works', f'''
      <div class="grid g-article">
        <div class="article-body">{DUMMY(1, 'dummy dropcap')}{DUMMY(3)}</div>
        <div class="article-side">
          <blockquote class="pull">{E(U("[작가나 클라이언트의 한마디를 크게 인용]", "[A line from the artist or client, set large]"))}</blockquote>
          {IMG(U("설치 과정", "Installation"), 'a-img', num=2)}
        </div>
      </div>'''))

    P.append(('', 'Works', f'''
      <div class="grid g-seq">
        {IMG(U("디테일", "Detail"), 's1', num=3)}
        {IMG(U("작품과 공간", "Work and space"), 's2', num=4)}
        {IMG(U("야간 전경", "At night"), 's3', num=5)}
      </div>'''))

    cards = ''.join(f'''<div class="card">{IMG(U("사례 사진", "Project photo"))}<span class="mono num">PROJECT {i:02d}</span>
        <h4 class="tbd">{E(U("[프로젝트명]", "[Project title]"))}</h4><p class="mono tbd">{E(U("[장소 · 연도 · 범위]", "[Location · Year · Scope]"))}</p></div>''' for i in (2, 3, 4))
    P.append(('', 'Works', f'''
      <h2 class="display h2">Also in this issue</h2>
      <div class="cards-3">{cards}</div>'''))

    # 04 People ----------------------------------------------------------------
    P.append(opener(CHAPTERS[3]))

    prof = ''.join(f'''<article class="profile">
        {IMG(U("작가 인물 또는 작업실", "Portrait or studio"), 'pf-img')}
        <div><span class="mono num">ARTIST {i:02d}</span>
        <h3 class="tbd">{E(U("[작가명]", "[Name]"))}</h3>
        <p class="mono tbd">{E(U("[매체 · 활동 지역]", "[Medium · Based in]"))}</p>
        <blockquote class="pull sm">{E(U("[작가의 말 한 줄]", "[One line from the artist]"))}</blockquote>
        {PH(U("작업 소개 2–3문장과 주요 이력", "2–3 sentences on the work, key exhibitions"))}</div>
      </article>''' for i in (1, 2))
    P.append(('', 'People', f'''<div class="profiles">{prof}</div>'''))

    pt = wwd[3] if len(wwd) > 3 else {}
    pname, pdesc = split_dash(B.LI(pt, 'text'))
    works = ''.join(f'''<div class="card">{IMG(U("Partner Work", "Partner Work"), num=k)}<h4 class="tbd">{E(U("[작품명 · 장소 · 연도]", "[Title · Place · Year]"))}</h4></div>''' for k in range(1, 5))
    P.append(('', 'People', f'''
      <div class="grid g-partner">
        <div>
          <span class="mono num">PARTNER</span>
          <h2 class="h-ko big">{E(pname)}</h2>
          <p class="lead">{E(pdesc)}</p>
          {PH(U("STANDS와의 관계, 역할 분담 2–3문장", "Relationship and division of roles, 2–3 sentences"))}
          <p class="note mono">{U("Partner Works · 수행 주체: 마롱컴퍼니", "Partner Works · Carried out by Malong Company")}</p>
        </div>
        <div class="cards-2x2">{works}</div>
      </div>'''))

    # masthead -----------------------------------------------------------------
    rows = [(U('상호', 'Company'), B.L(company, 'name')), (U('대표', 'CEO'), B.L(company, 'ceo')),
            (U('사업자등록번호', 'Business reg. no.'), company.get('business_no')), (U('미술품 유통업 신고번호', 'Art dealer reg. no.'), company.get('art_service_no')),
            (U('주소', 'Address'), B.L(contact, 'address')), (U('대표 전화', 'Tel'), contact.get('tel')), (U('이메일', 'Email'), contact.get('email')),
            ('Instagram', contact.get('instagram'))]
    issue = [(U('발행', 'Published'), f'{ISSUE} · {datetime.date.today():%Y.%m}'), (U('발행처', 'Publisher'), 'STANDS'),
             (U('편집 · 디자인', 'Editing · Design'), ''), (U('사진', 'Photography'), ''), (U('파트너', 'Partner'), pname)]
    col = lambda rs: ''.join(f'<div><dt>{E(k)}</dt><dd>{T(v)}</dd></div>' for k, v in rs)
    P.append(('masthead-page', U('판권', 'Masthead'), f'''
      <div class="masthead">
        <div class="mh-logo">{B.wordmark_svg()}</div>
        <dl class="mh-col">{col(issue)}</dl>
        <dl class="mh-col">{col(rows)}</dl>
        <p class="mh-fine">{E(U("이 소개서에 실린 이미지와 글의 저작권은 각 작가와 STANDS에 있습니다. 사전 허락 없이 복제하거나 배포할 수 없습니다.", "All images and texts are copyright of the artists and STANDS. Do not reproduce without permission."))}</p>
      </div>'''))

    # back cover ---------------------------------------------------------------
    site_url = B.BASE_URL + ('en/' if B.EN() else '')
    P.append(('dark back', '', f'''
      <img class="bleed back-bg" src="../img/courtyard-poster.jpg" alt="">
      <div class="back-inner">
        <h2 class="headline">{E(B.L(home, 'cta_title'))}</h2>
        <dl class="contact">
          <div><dt class="mono">Email</dt><dd>{T(contact.get('email'))}</dd></div>
          <div><dt class="mono">Tel</dt><dd>{T(contact.get('tel'))}</dd></div>
          <div><dt class="mono">Instagram</dt><dd>{T(contact.get('instagram'))}</dd></div>
          <div><dt class="mono">Web</dt><dd>{E(site_url.replace('https://', ''))}</dd></div>
        </dl>
      </div>
      <div class="back-logo">{B.wordmark_svg()}</div>'''))
    return P


def toc(P):
    """Contents page, built after numbering so page numbers stay right."""
    start = {}
    for i, (cls, label, _) in enumerate(P, 1):
        if 'opener' in cls:
            start[label] = i
    rows = ''
    for n, title, sub, img in CHAPTERS:
        rows += f'''<li><span class="t-num display">{n}</span>
          <div class="t-title"><h3 class="display">{E(title)}</h3><p>{E(U(*sub))}</p></div>
          <img src="../{img}" alt=""><span class="t-page mono">{start.get(title, 0):02d}</span></li>'''
    return f'''
      <div class="grid g-toc">
        <div><h2 class="display h2">Contents</h2>
          <p class="standfirst tbd">{E(U("[이번 호 소개 한두 문장]", "[One or two lines introducing this issue]"))}</p>
          <p class="mono toc-issue">{ISSUE} · 2026</p></div>
        <ol class="toc">{rows}</ol>
      </div>'''


# ---------------------------------------------------------------------------
CSS = r'''
@page{size:297mm 210mm;margin:0}
:root{--black:#000;--paper:#F0F0EE;--paper-2:#E5E5E2;--line:#D3D2CE;--muted:#6C6A71;--accent:#7D7889;--sky:#8FCAD8;
  --display:"Archivo","Arial Narrow",Arial,sans-serif;--accent-font:"Newsreader",Georgia,serif;
  --body:"Pretendard Variable","Pretendard","Apple SD Gothic Neo","Noto Sans KR",sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
  --m:15mm;--gap:8mm}
*{box-sizing:border-box}
html,body{margin:0;background:#9a989e}
body{font-family:var(--body);color:var(--black);font-size:9.5pt;line-height:1.6;-webkit-font-smoothing:antialiased;-webkit-print-color-adjust:exact;print-color-adjust:exact}
p{margin:0 0 .8em}
h1,h2,h3,h4{margin:0;font-weight:700}
blockquote{margin:0}
.page{width:297mm;height:210mm;position:relative;overflow:hidden;background:var(--paper);padding:calc(var(--m) + 7mm) var(--m) calc(var(--m) + 6mm);margin:0 auto 10mm;break-after:page}
@media print{html,body{background:none}.page{margin:0}}
.page.dark{background:var(--black);color:var(--paper)}
/* running heads and folios */
.chrome{position:absolute;left:var(--m);right:var(--m);display:flex;justify-content:space-between;font-family:var(--mono);font-size:6.5pt;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);z-index:3}
.chrome.top{top:9mm}.chrome.bottom{bottom:8mm}
.chrome .folio{font-family:var(--display);font-stretch:75%;font-weight:900;font-size:9pt;letter-spacing:0;color:var(--black)}
.dark .chrome,.opener .chrome{color:rgba(240,240,238,.75)}
.dark .chrome .folio,.opener .chrome .folio{color:var(--paper)}
.bleed-left .chrome.top span:first-child,.bleed-left .chrome.bottom span:first-child{visibility:hidden}
/* type */
.mono{font-family:var(--mono);font-size:7pt;letter-spacing:.08em;text-transform:uppercase}
.display{font-family:var(--display);font-stretch:75%;font-weight:900;text-transform:uppercase;letter-spacing:-.01em;line-height:.92;word-spacing:.12em}
.h2{font-size:38pt;margin-bottom:8mm}
.h-ko{font-size:20pt;line-height:1.3;letter-spacing:-.02em;margin:3mm 0 5mm}
.h-ko.big{font-size:26pt;line-height:1.25}
.headline{font-family:var(--body);font-weight:700;font-size:30pt;letter-spacing:-.03em;line-height:1.2}
.lead{font-size:10.5pt;line-height:1.7}
.standfirst{font-family:var(--accent-font);font-style:italic;font-size:14pt;line-height:1.45;margin-bottom:8mm}
.pull{font-family:var(--accent-font);font-style:italic;font-size:19pt;line-height:1.35;padding-top:4mm;border-top:2px solid;border-image:linear-gradient(90deg,#000,var(--accent)) 1}
.pull.sm{font-size:13pt;margin:4mm 0 5mm;padding-top:3mm}
.num{color:var(--accent);display:block}
.dark .num{color:#a9a4b6}
.k{display:block;color:var(--muted);margin-bottom:1.5mm}
.closing{position:absolute;left:var(--m);right:var(--m);bottom:calc(var(--m) + 6mm);font-family:var(--accent-font);font-style:italic;font-size:15pt;margin:0;padding-top:4mm;border-top:1px solid var(--line)}
.note{color:var(--muted);margin-top:6mm}
/* placeholders */
.tbd{color:var(--accent);background:repeating-linear-gradient(90deg,transparent 0 3px,rgba(125,120,137,.07) 3px 6px);outline:1px dashed rgba(125,120,137,.55);outline-offset:1.5mm;border-radius:.5mm}
p.tbd{margin:2mm 1.5mm 4mm}
.tbd.sm{font-size:7.5pt}
.dark .tbd,.opener .tbd{color:#cfcad9}
.dummy{color:#a7a3b0;text-align:justify;font-size:9pt;line-height:1.75}
.dropcap::first-letter{float:left;font-family:var(--display);font-stretch:75%;font-weight:900;font-size:46pt;line-height:.8;margin:1.2mm 2.5mm 0 0;color:var(--black)}
.img{margin:0;position:relative;overflow:hidden;background:var(--paper-2)}
.img img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(.8)}
.img figcaption{position:absolute;left:3mm;bottom:2.5mm;font-family:var(--mono);font-size:6.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.img figcaption b{font-weight:500;color:var(--black)}
.img:not(.ph) figcaption,.img:not(.ph) figcaption b{color:#fff;text-shadow:0 0 3px rgba(0,0,0,.6)}
.img.ph{border:1px dashed var(--accent);background:repeating-linear-gradient(135deg,rgba(125,120,137,.09) 0 1px,transparent 1px 7px),var(--paper-2)}
.img.ph figcaption{color:var(--accent)}
.badge{position:absolute;right:3mm;top:3mm;font-family:var(--mono);font-size:6pt;letter-spacing:.08em;text-transform:uppercase;background:var(--paper);color:var(--accent);padding:.8mm 1.6mm;border:1px dashed var(--accent);z-index:2}
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
.g-toc{grid-template-columns:4fr 7fr;gap:14mm}
.toc-issue{color:var(--muted)}
.toc{list-style:none;margin:0;padding:0;border-top:1px solid var(--black)}
.toc li{display:grid;grid-template-columns:20mm 1fr 34mm 12mm;align-items:center;gap:5mm;padding:3.2mm 0;border-bottom:1px solid var(--line)}
.t-num{font-size:30pt;color:var(--accent)}
.t-title h3{font-size:20pt}
.t-title p{margin:1mm 0 0;color:var(--muted)}
.toc img{width:34mm;height:21mm;object-fit:cover;filter:saturate(.8)}
.t-page{text-align:right;font-size:9pt}
/* chapter opener */
.opener{padding:0;color:var(--paper)}
.opener .bleed{filter:saturate(.75) brightness(.8)}
.opener::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05) 40%,rgba(0,0,0,.6));z-index:1}
.op-text{position:absolute;left:var(--m);right:var(--m);bottom:calc(var(--m) + 6mm);display:flex;align-items:flex-end;gap:8mm;z-index:2}
.op-num{font-size:150pt;line-height:.72}
.op-title{font-size:56pt;margin-bottom:2mm}
.op-sub{font-family:var(--accent-font);font-style:italic;font-size:15pt;margin:0 0 3mm}
.op-lede{display:inline-block;margin:0}
.opener > .badge{top:auto;bottom:9mm;right:var(--m);z-index:3;background:transparent;color:#cfcad9;border-color:#cfcad9}
/* question / meaning */
.g-question{grid-template-columns:1fr 1fr;grid-template-rows:auto 1fr}
.year{font-size:120pt;color:var(--paper);line-height:.8}
.g-question .story{grid-column:1;align-self:end;font-size:12pt;line-height:1.75;max-width:120mm}
.q-img{grid-column:2;grid-row:1/3}
.dark .img.ph{background:repeating-linear-gradient(135deg,rgba(240,240,238,.08) 0 1px,transparent 1px 7px),#141414}
.meaning-mark .wordmark{width:100%;height:auto;display:block;margin:2mm 0 12mm}
.cols-2{columns:2;column-gap:14mm;font-size:11pt;line-height:1.8}
.cols-2 p{break-inside:avoid}
/* practice */
.wwd-row{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap)}
.wwd{border-top:2px solid;border-image:linear-gradient(90deg,#000,var(--accent)) 1;padding-top:4mm}
.wwd .img{aspect-ratio:4/3;margin-bottom:4mm}
.wwd h3{font-size:12pt;line-height:1.35;margin:2mm 0 3mm;letter-spacing:-.01em}
.wwd p{font-size:8.5pt;color:#333}
.g-service{grid-template-columns:5fr 6fr;gap:12mm}
.g-service.flip{grid-template-columns:6fr 5fr}
.g-service.flip .sv-img{order:-1}
.sv-img{height:100%}
.facts{display:grid;gap:4mm;margin-top:6mm;border-top:1px solid var(--line);padding-top:5mm}
.facts ul{margin:0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:1.5mm}
.facts li{border:1px solid var(--line);padding:.5mm 2.5mm;font-size:8.5pt;border-radius:10mm}
/* method */
.g-method{grid-template-columns:5fr 6fr;gap:14mm}
.m-left{display:flex;flex-direction:column}
.m-left .pull{margin-top:auto}
.steps-v{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;justify-content:space-between;border-top:1px solid var(--black)}
.steps-v li{display:grid;grid-template-columns:22mm 1fr;align-items:center;border-bottom:1px solid var(--line);padding:1.5mm 0;flex:1}
.step-num{font-size:30pt;color:var(--accent)}
.steps-v h4{font-size:11pt;margin-bottom:.5mm}
.steps-v p.tbd{margin:1mm 1.5mm;display:inline-block}
.g-guide{grid-template-columns:4fr 7fr;gap:14mm}
.qa-grid{display:grid;grid-template-columns:1fr 1fr;gap:8mm 10mm;align-content:start}
.qa{border-top:1px solid var(--black);padding-top:3mm}
.qa h4{font-size:12pt;margin:1.5mm 0 2mm}
/* works */
.bleed-left{padding-left:calc(148.5mm + 10mm)}
.ft-img{position:absolute;left:0;top:0;bottom:0;width:148.5mm}
.ft-text{display:flex;flex-direction:column;height:100%}
.feature-title{font-size:30pt;letter-spacing:-.03em;line-height:1.2;margin:4mm 0 6mm;display:inline-block}
.ft-text .meta{margin-top:auto}
.meta{margin:6mm 0 0;display:grid;gap:2.5mm;border-top:1px solid var(--line);padding-top:4mm}
.meta div{display:grid;grid-template-columns:28mm 1fr;align-items:baseline}
.meta dt{color:var(--muted)}.meta dd{margin:0}
.g-article{grid-template-columns:7fr 4fr;gap:12mm}
.article-body{columns:2;column-gap:9mm}
.article-side{display:flex;flex-direction:column;gap:8mm}
.a-img{flex:1}
.g-seq{grid-template-columns:5fr 3fr;grid-template-rows:1fr 1fr;gap:5mm}
.g-seq .s1{grid-row:1/3}
.cards-3{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--gap)}
.card .img{aspect-ratio:4/3;margin-bottom:3mm}
.card h4{font-size:10.5pt;margin:1mm 0 1.5mm;display:inline-block}
.card p{margin:0;display:inline-block}
/* people */
.profiles{display:grid;grid-template-columns:1fr 1fr;gap:14mm;height:100%}
.profile{display:grid;grid-template-columns:1fr 1fr;gap:6mm}
.pf-img{height:100%}
.profile h3{font-size:18pt;margin:2mm 0 1.5mm;display:inline-block}
.g-partner{grid-template-columns:5fr 6fr;gap:12mm}
.cards-2x2{display:grid;grid-template-columns:1fr 1fr;gap:5mm var(--gap);align-content:start}
.cards-2x2 .img{aspect-ratio:16/10}
/* masthead */
.masthead{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12mm;height:100%;align-content:start;font-size:9pt}
.mh-logo{grid-column:1/-1;width:70mm;margin-bottom:6mm}
.mh-logo .wordmark{width:100%;height:auto;display:block}
.mh-col{margin:0;display:grid;gap:3.5mm;align-content:start;border-top:1px solid var(--black);padding-top:3mm}
.mh-col dt{font-family:var(--mono);font-size:6.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.mh-col div{display:grid;grid-template-columns:34mm 1fr;align-items:baseline}
.mh-col dd{margin:0}
.mh-fine{align-self:start;border-top:1px solid var(--line);padding-top:3mm;color:var(--muted);font-size:7pt}
/* back cover */
.back{padding:0}
.back-bg{opacity:.38;filter:saturate(.7)}
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
    P = [(c, l, toc(P) if c == 'contents' else x) for c, l, x in P]
    total = len(P)
    body = []
    for i, (cls, label, inner) in enumerate(P, 1):
        if cls in ('cover',) or 'back' in cls.split():
            top = bottom = ''
        else:
            top = f'<div class="chrome top"><span>STANDS — {ISSUE}</span><span>{E(label)}</span></div>'
            bottom = f'<div class="chrome bottom"><span>{U("회사 소개서", "Company Profile")} · {VERSION}</span><span class="folio">{i:02d}</span></div>'
        body.append(f'<section class="page {E(cls)}">{top}{inner}{bottom}</section>')
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<title>STANDS — {U("회사 소개서", "Company Profile")} ({VERSION})</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,700..900&family=Newsreader:ital,opsz,wght@1,6..72,400&family=IBM+Plex+Mono:wght@400;500&display=block">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>{CSS}</style></head>
<body>{''.join(body)}</body></html>'''


if __name__ == '__main__':
    lang = 'en' if '--lang' in sys.argv and sys.argv[sys.argv.index('--lang') + 1] == 'en' else 'ko'
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'brochure-{lang}.html')
    open(path, 'w', encoding='utf-8').write(render(lang))
    print('wrote', os.path.relpath(path, B.ROOT))
