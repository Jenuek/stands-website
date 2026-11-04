#!/usr/bin/env python3
"""STANDS brand brochure (company profile) — layout generator.

Writes _brochure/brochure-<lang>.html (A4 landscape, one <section> per page) from content/site.yml.
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
VERSION = 'v0.1 layout'
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

def IMG(label, cls='', src=None, temp=False):
    """Image slot. With src: a stand-in photo, marked as temporary. Without: a hatched placeholder."""
    if src:
        badge = f'<span class="badge">{E(U("임시 이미지", "Temporary image"))}</span>' if temp else ''
        return f'<figure class="img {cls}"><img src="../{src}" alt="">{badge}<figcaption>{E(label)}</figcaption></figure>'
    return f'<figure class="img ph {cls}"><figcaption>{E(label)}</figcaption></figure>'


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def pages():
    S = B.SITE
    home, about, contact, company = S.get('home', {}), S.get('about', {}), S.get('contact', {}), S.get('company', {})
    services = home.get('services', []) or []
    wwd = about.get('what_we_do', []) or []

    def scope(i):
        """'아트 프로젝트 기획 - 작가 커미션, 브랜드 …' → ['작가 커미션', '브랜드 …']"""
        t = B.LI(wwd[i], 'text') if i < len(wwd) else ''
        for sep in (' — ', ' - '):
            if sep in t:
                return [x.strip() for x in t.split(sep, 1)[1].split(',') if x.strip()]
        return []

    P = []

    # 01 cover -----------------------------------------------------------------
    P.append(('cover', '', f'''
      <div class="cover-logo">{B.logo_svg('box')}</div>
      <div class="cover-top mono"><span>{U("회사 소개서", "Company Profile")}</span><span>2026</span></div>
      <div class="cover-bottom">
        <p class="cover-line">{E(B.L(home, 'headline'))}</p>
        <p class="mono">Art Dealing · Art Projects · Architectural Art</p>
      </div>'''))

    # 02 question --------------------------------------------------------------
    P.append(('dark', U('질문', 'The question'), f'''
      <div class="grid g-question">
        <div class="year display">1917</div>
        <div class="story">{PARA(B.L(home, 'story_1'))}</div>
        {IMG(U("뒤샹 〈샘〉 이미지 — 사용 권리 확인 후 배치", "Duchamp, Fountain — place after rights check"), 'q-img')}
      </div>'''))

    # 03 meaning ---------------------------------------------------------------
    P.append(('', U('STANDS의 뜻', 'The name'), f'''
      <div class="meaning-mark">{B.wordmark_svg()}</div>
      <div class="cols-2 story">{PARA(B.L(home, 'story_2'))}</div>'''))

    # 04 what we do ------------------------------------------------------------
    cells = ''
    wimgs = ['img/hero/10-gallery.jpg', 'img/hero/04-atrium.jpg', 'img/hero/11-plaza.jpg', 'img/hero/08-park.jpg']
    for i, it in enumerate(wwd[:4]):
        label = str(it.get('label', '')).strip()
        text = B.LI(it, 'text')
        title, rest = (text.split(' - ', 1) + [''])[:2] if ' - ' in text else ((text.split(' — ', 1) + [''])[:2] if ' — ' in text else (text, ''))
        cells += f'''<div class="wwd">{IMG('', '', wimgs[i], temp=True)}<span class="mono num">{E(label)}</span><h3>{E(title.strip())}</h3><p>{E(rest.strip())}</p></div>'''
    P.append(('', U('하는 일', 'What we do'), f'''
      <h2 class="display h2">What we do</h2>
      <div class="wwd-row">{cells}</div>
      <p class="closing">{E(B.L(about, 'closing'))}</p>'''))

    # 05–07 service detail -----------------------------------------------------
    photos = ['img/hero/10-gallery.jpg', 'img/hero/04-atrium.jpg', 'img/hero/11-plaza.jpg']
    for i, sv in enumerate(services[:3]):
        items = ''.join(f'<li>{E(x)}</li>' for x in scope(i)) or f'<li class="tbd">{E(U("[수행 범위]", "[Scope]"))}</li>'
        P.append(('', str(sv.get('label', '')).strip(), f'''
          <div class="grid g-service">
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
            {IMG(U("대표 사례 사진", "Key project photo"), 'sv-img', photos[i], temp=True)}
          </div>'''))

    # 08 process ---------------------------------------------------------------
    steps = [U('상담 · 진단', 'Brief'), U('기획 · 제안', 'Proposal'), U('작가 · 작품 선정', 'Artist & work selection'),
             U('심의 · 계약', 'Review & contract'), U('제작', 'Fabrication'), U('운송 · 설치', 'Transport & installation'),
             U('관리 · 리세일', 'Care & resale')]
    st = ''.join(f'''<li><span class="mono num">{i+1:02d}</span><h4>{E(s)}</h4>{PH(U("단계 설명 1–2줄", "1–2 lines"), "sm")}</li>''' for i, s in enumerate(steps))
    P.append(('', U('일하는 방식', 'How we work'), f'''
      <h2 class="display h2">How we work</h2>
      <p class="sub tbd">{E(U("[도입 문장 — 판단과 실행을 한 흐름으로 잇는다는 점]", "[Intro line — judgment and execution as one process]"))}</p>
      <ol class="steps">{st}</ol>
      <p class="closing">{E(B.L(about, 'closing'))}</p>'''))

    # 09 architectural art guide -----------------------------------------------
    flow = [U('기획', 'Planning'), U('작가 선정', 'Artist selection'), U('심의', 'Review'), U('제작', 'Fabrication'), U('설치', 'Installation'), U('준공 · 사후 관리', 'Completion · care')]
    fl = ''.join(f'<li>{E(x)}</li>' for x in flow)
    P.append(('', U('건축물 미술작품', 'Architectural art'), f'''
      <div class="grid g-guide">
        <div>
          <span class="mono num">GUIDE</span>
          <h2 class="h-ko">{U("건축물 미술작품,<br>무엇을 준비해야 하나", "Architectural art:<br>what to prepare")}</h2>
          {PH(U("시행사·건축주가 알아야 할 핵심 한 문단", "One paragraph for developers and owners"))}
          <p class="note mono">{U("법령 기준과 수치는 확인 후 기재", "Verify legal thresholds before writing")}</p>
        </div>
        <div class="guide-table">
          <div><span class="mono k">{U("대상", "Applies to")}</span>{PH(U("설치 의무 대상 건축물과 기준", "Which buildings, which threshold"))}</div>
          <div><span class="mono k">{U("비용", "Budget")}</span>{PH(U("작품 설치 비용 산정 기준", "How the budget is set"))}</div>
          <div><span class="mono k">{U("기간", "Timeline")}</span>{PH(U("기획부터 설치까지 일반적인 기간", "Typical time from planning to installation"))}</div>
          <div><span class="mono k">{U("STANDS가 맡는 일", "What STANDS does")}</span>{PH(U("대행 범위: 심의 서류, 작가 섭외, 제작 관리 등", "Scope: review documents, artists, fabrication"))}</div>
        </div>
      </div>
      <ol class="flow">{fl}</ol>'''))

    # 10 featured project ------------------------------------------------------
    meta = [(U('클라이언트', 'Client'), U('[클라이언트]', '[Client]')), (U('장소', 'Location'), U('[장소]', '[Location]')),
            (U('연도', 'Year'), '[2026]'), (U('작가', 'Artist'), U('[작가]', '[Artist]')), (U('범위', 'Scope'), U('[수행 범위]', '[Scope]'))]
    dl = ''.join(f'<div><dt class="mono">{E(k)}</dt><dd class="tbd">{E(v)}</dd></div>' for k, v in meta)
    P.append(('', U('프로젝트', 'Projects'), f'''
      <div class="grid g-feature">
        {IMG(U("대표 프로젝트 사진 — 가로 고해상도", "Featured project photo — landscape, high resolution"), 'ft-img')}
        <div class="ft-text">
          <span class="mono num">PROJECT 01</span>
          <h2 class="h-ko tbd">{E(U("[프로젝트명]", "[Project title]"))}</h2>
          {PH(U("과제 → 판단 → 결과를 3–4문장으로", "Brief → decision → result, in 3–4 sentences"))}
          <dl class="meta">{dl}</dl>
        </div>
      </div>'''))

    # 11 more projects ---------------------------------------------------------
    cards = ''.join(f'''<div class="card">{IMG(U("사례 사진", "Project photo"))}<span class="mono num">PROJECT {i:02d}</span>
        <h4 class="tbd">{E(U("[프로젝트명]", "[Project title]"))}</h4><p class="mono tbd">{E(U("[장소 · 연도 · 범위]", "[Location · Year · Scope]"))}</p></div>''' for i in (2, 3, 4))
    P.append(('', U('프로젝트', 'Projects'), f'''
      <h2 class="display h2">Selected projects</h2>
      <div class="cards-3">{cards}</div>'''))

    # 12 artists ---------------------------------------------------------------
    ac = ''.join(f'''<div class="artist">{IMG(U("작가 · 작품", "Artist · work"))}<h4 class="tbd">{E(U("[작가명]", "[Name]"))}</h4><p class="mono tbd">{E(U("[매체]", "[Medium]"))}</p></div>''' for _ in range(8))
    P.append(('', U('작가', 'Artists'), f'''
      <div class="head-row"><h2 class="display h2">Artists</h2>{PH(U("함께하는 작가 소개 한 줄", "One line on the artists we work with"), "sub")}</div>
      <div class="artists">{ac}</div>'''))

    # 13 partner ---------------------------------------------------------------
    pt = wwd[3] if len(wwd) > 3 else {}
    ptext = B.LI(pt, 'text')
    pname, pdesc = (ptext.split(' - ', 1) + [''])[:2] if ' - ' in ptext else ((ptext.split(' — ', 1) + [''])[:2] if ' — ' in ptext else (ptext, ''))
    works = ''.join(f'''<div class="card">{IMG(U("Partner Work 사진", "Partner Work photo"))}<h4 class="tbd">{E(U("[작품명 · 장소 · 연도]", "[Title · Place · Year]"))}</h4></div>''' for _ in range(4))
    P.append(('', U('파트너', 'Partner'), f'''
      <div class="grid g-partner">
        <div>
          <span class="mono num">{E(str(pt.get('label', '04. PARTNER')).strip())}</span>
          <h2 class="h-ko">{E(pname.strip())}</h2>
          <p class="lead">{E(pdesc.strip())}</p>
          {PH(U("STANDS와의 관계, 역할 분담 2–3문장", "Relationship and division of roles, 2–3 sentences"))}
          <p class="note mono">{U("Partner Works · 수행 주체: 마롱컴퍼니", "Partner Works · Carried out by Malong Company")}</p>
        </div>
        <div class="cards-2x2">{works}</div>
      </div>'''))

    # 14 company ---------------------------------------------------------------
    rows = [(U('상호', 'Company'), B.L(company, 'name')), (U('대표', 'CEO'), B.L(company, 'ceo')),
            (U('사업자등록번호', 'Business reg. no.'), company.get('business_no')), (U('미술품 유통업 신고번호', 'Art dealer reg. no.'), company.get('art_service_no')),
            (U('설립', 'Founded'), ''), (U('주소', 'Address'), B.L(contact, 'address')), (U('대표 전화', 'Tel'), contact.get('tel')),
            (U('이메일', 'Email'), contact.get('email'))]
    dl = ''.join(f'<div><dt class="mono">{E(k)}</dt><dd>{T(v)}</dd></div>' for k, v in rows)
    P.append(('', U('회사 정보', 'Company'), f'''
      <div class="grid g-company">
        <div><h2 class="display h2">Company</h2>{PH(U("연혁·팀 소개 (선택)", "History · team (optional)"))}</div>
        <dl class="meta big">{dl}</dl>
      </div>'''))

    # 15 contact / back cover --------------------------------------------------
    site_url = B.BASE_URL + ('en/' if B.EN() else '')
    P.append(('dark back', '', f'''
      <img class="back-bg" src="../img/courtyard-poster.jpg" alt="">
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
.page{width:297mm;height:210mm;position:relative;overflow:hidden;background:var(--paper);padding:calc(var(--m) + 7mm) var(--m) calc(var(--m) + 6mm);margin:0 auto 10mm;break-after:page}
@media print{html,body{background:none}.page{margin:0}}
.page.dark{background:var(--black);color:var(--paper)}
/* running chrome */
.chrome{position:absolute;left:var(--m);right:var(--m);display:flex;justify-content:space-between;font-family:var(--mono);font-size:6.5pt;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.chrome.top{top:9mm}.chrome.bottom{bottom:8mm}
.dark .chrome{color:#8b8892}
/* type */
.mono{font-family:var(--mono);font-size:7pt;letter-spacing:.08em;text-transform:uppercase}
.eyebrow{font-family:var(--mono);font-size:7.5pt;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:5mm}
.display{font-family:var(--display);font-stretch:75%;font-weight:900;text-transform:uppercase;letter-spacing:-.01em;line-height:.92;word-spacing:.12em}
.h2{font-size:34pt;margin-bottom:8mm}
.h-ko{font-size:20pt;line-height:1.3;letter-spacing:-.02em;margin:3mm 0 5mm}
.headline{font-family:var(--body);font-weight:700;font-size:30pt;letter-spacing:-.03em;line-height:1.2}
.lead{font-size:10.5pt;line-height:1.7}
.num{color:var(--accent);display:block}
.dark .num{color:#a9a4b6}
.k{display:block;color:var(--muted);margin-bottom:1.5mm}
.closing{position:absolute;left:var(--m);right:var(--m);bottom:calc(var(--m) + 6mm);font-family:var(--accent-font);font-style:italic;font-size:15pt;margin:0;padding-top:4mm;border-top:1px solid var(--line)}
.note{color:var(--muted);margin-top:6mm}
/* placeholders */
.tbd{color:var(--accent);background:repeating-linear-gradient(90deg,transparent 0 3px,rgba(125,120,137,.07) 3px 6px);outline:1px dashed rgba(125,120,137,.55);outline-offset:1.5mm;border-radius:.5mm}
p.tbd{margin:2mm 1.5mm 4mm}
.tbd.sm{font-size:7.5pt}
.dark .tbd{color:#b6b1c3}
.img{margin:0;position:relative;overflow:hidden;background:var(--paper-2)}
.img img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(.8)}
.img figcaption{position:absolute;left:3mm;bottom:2.5mm;font-family:var(--mono);font-size:6.5pt;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.img:not(.ph) figcaption{color:#fff;text-shadow:0 0 3px rgba(0,0,0,.6)}
.img.ph{border:1px dashed var(--accent);background:repeating-linear-gradient(135deg,rgba(125,120,137,.09) 0 1px,transparent 1px 7px),var(--paper-2)}
.img.ph figcaption{color:var(--accent)}
.dark .img.ph{background:repeating-linear-gradient(135deg,rgba(240,240,238,.08) 0 1px,transparent 1px 7px),#141414}
.badge{position:absolute;right:3mm;top:3mm;font-family:var(--mono);font-size:6pt;letter-spacing:.08em;text-transform:uppercase;background:var(--paper);color:var(--accent);padding:.8mm 1.6mm;border:1px dashed var(--accent)}
/* grids */
.grid{display:grid;gap:var(--gap);height:100%}
/* cover */
.cover{display:flex;align-items:center;justify-content:center}
.cover-logo .box{width:44mm;height:44mm;display:block}
.cover-top,.cover-bottom{position:absolute;left:var(--m);right:var(--m);display:flex;justify-content:space-between;align-items:baseline;color:var(--muted)}
.cover-top{top:var(--m)}
.cover-bottom{bottom:calc(var(--m) + 4mm);border-top:1px solid var(--line);padding-top:3mm}
.cover-bottom p{margin:0}
.cover-line{font-size:9pt;letter-spacing:-.01em;color:var(--black)}
/* question */
.g-question{grid-template-columns:1fr 1fr;grid-template-rows:auto 1fr}
.year{font-size:120pt;color:var(--paper);line-height:.8}
.g-question .story{grid-column:1;align-self:end;font-size:12pt;line-height:1.75;max-width:120mm}
.q-img{grid-column:2;grid-row:1/3}
/* meaning */
.meaning-mark .wordmark{width:100%;height:auto;display:block;margin:2mm 0 12mm}
.cols-2{columns:2;column-gap:14mm;font-size:11pt;line-height:1.8}
.cols-2 p{break-inside:avoid}
/* what we do */
.wwd-row{display:grid;grid-template-columns:repeat(4,1fr);gap:var(--gap)}
.wwd{border-top:2px solid;border-image:linear-gradient(90deg,#000,var(--accent)) 1;padding-top:4mm}
.wwd .img{aspect-ratio:4/3;margin-bottom:4mm}
.wwd h3{font-size:12pt;line-height:1.35;margin:2mm 0 3mm;letter-spacing:-.01em}
.wwd p{font-size:8.5pt;color:#333}
/* service */
.g-service{grid-template-columns:5fr 6fr;gap:12mm}
.sv-img{height:100%}
.facts{display:grid;gap:4mm;margin-top:6mm;border-top:1px solid var(--line);padding-top:5mm}
.facts ul{margin:0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:1.5mm}
.facts li{border:1px solid var(--line);padding:.5mm 2.5mm;font-size:8.5pt;border-radius:10mm}
/* process */
.sub{font-size:10pt;display:inline-block;margin-bottom:24mm}
.steps li p.tbd{min-height:18mm}
.steps{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(7,1fr);gap:4mm}
.steps li{border-top:2px solid var(--black);padding-top:3mm;position:relative}
.steps li::before{content:"";position:absolute;top:-4px;left:0;width:6px;height:6px;border-radius:50%;background:var(--accent)}
.steps h4{font-size:10pt;margin:1.5mm 0 2mm}
/* guide */
.g-guide{grid-template-columns:5fr 7fr;gap:12mm;height:auto}
.guide-table{display:grid;grid-template-columns:1fr 1fr;gap:6mm 8mm;border-top:1px solid var(--line);padding-top:5mm}
.flow{list-style:none;padding:0;margin:0;position:absolute;left:var(--m);right:var(--m);bottom:calc(var(--m) + 6mm);display:flex}
.flow li{flex:1;font-family:var(--mono);font-size:7pt;letter-spacing:.06em;text-transform:uppercase;padding:3mm 0 0;border-top:2px solid;border-image:linear-gradient(90deg,#000,var(--accent)) 1;position:relative}
.flow li:not(:last-child)::after{content:"→";position:absolute;right:3mm;top:2.6mm;color:var(--accent)}
/* projects */
.g-feature{grid-template-columns:2fr 1fr;gap:10mm}
.ft-img{height:100%}
.meta{margin:6mm 0 0;display:grid;gap:2.5mm;border-top:1px solid var(--line);padding-top:4mm}
.meta div{display:grid;grid-template-columns:28mm 1fr;align-items:baseline}
.meta dt{color:var(--muted)}.meta dd{margin:0}
.meta.big{font-size:10.5pt;gap:4mm}
.meta.big div{grid-template-columns:48mm 1fr;border-bottom:1px solid var(--line);padding-bottom:3mm}
.cards-3{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--gap)}
.card .img{aspect-ratio:4/3;margin-bottom:3mm}
.card h4{font-size:10.5pt;margin:1mm 0 1.5mm;display:inline-block}
.card p{margin:0;display:inline-block}
/* artists */
.head-row{display:flex;align-items:baseline;gap:10mm}
.head-row .h2{margin-bottom:6mm}
.artists{display:grid;grid-template-columns:repeat(4,1fr);gap:5mm var(--gap)}
.artist .img{aspect-ratio:16/10;margin-bottom:2mm}
.artist h4{font-size:9.5pt;display:inline-block;margin-right:3mm}
.artist p{display:inline-block;margin:0}
/* partner */
.g-partner{grid-template-columns:5fr 6fr;gap:12mm}
.cards-2x2{display:grid;grid-template-columns:1fr 1fr;gap:5mm var(--gap);align-content:start}
.cards-2x2 .img{aspect-ratio:16/10}
/* company */
.g-company{grid-template-columns:1fr 1.4fr;gap:14mm;height:auto}
/* back cover */
.back{padding:0}
.back-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.38;filter:saturate(.7)}
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
    total = len(P)
    today = datetime.date.today().strftime('%Y.%m')
    body = []
    for i, (cls, section, inner) in enumerate(P, 1):
        kind = 'cover' if cls == 'cover' else ''
        top = '' if cls in ('cover',) else f'<div class="chrome top"><span>STANDS</span><span>{E(section)}</span></div>'
        bottom = '' if cls == 'cover' else f'<div class="chrome bottom"><span>{U("회사 소개서", "Company Profile")} · {VERSION} · {today}</span><span>{i:02d} / {total:02d}</span></div>'
        body.append(f'<section class="page {E(cls)} {kind}">{top}{inner}{bottom}</section>')
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
