# STANDS website — notes for Claude Code

Brand site for **STANDS** (art company: art dealing, art projects, architectural art; partner 마롱컴퍼니).
Owner/designer: June. Talk to June in Korean. Copy tone: clear and assertive, never sentimental. Verify facts before writing them.

- Live: https://stands.art/ (Korean at root, English under `/en/`). Domain bought at 가비아; DNS: 4 A records on @ to GitHub Pages, `www` CNAME to `jenuek.github.io`. Custom domain is set in repo Settings → Pages (no CNAME file: the site deploys through Actions). Old address https://jenuek.github.io/stands-website/ redirects
- Repo: https://github.com/Jenuek/stands-website, branch `main`
- Deploy: every push to `main` runs `.github/workflows/deploy.yml` → `python build/build.py` → `_site/` → GitHub Pages (about 1 minute)
- **Always `git pull` before editing.** June edits content in Pages CMS (https://app.pagescms.org), which commits straight to `main`.

## Build and preview locally

```bash
pip install -r requirements.txt   # pyyaml, markdown (pinned)
python build/build.py                 # writes _site/ (env: STANDS_OUT, STANDS_VER, STANDS_URL)
python -m http.server 8000 -d _site   # http://localhost:8000
```

`assets/site.css` is grouped by page area (base, header, hero, home sections, footer, inner pages, about, editorial, contact form). Add new rules to their area, not at the end of the file.

## Layout

| Path | What |
| --- | --- |
| Home order | Hero → statement → **Selected Projects** (only case studies from `featured_projects`; on the same 4-column grid as the Artists cards: each case is a tall 3:5 photo (`cover_tall` if set, else `cover` with `cover_focus` / `home_focus`) plus a text column: number, title, thick rule, place · year · use, `facts.context`, and the `key_figure` (+ `en.key_figure`) with View case at the foot; `home_case()`; `stats[]` stays in the content but is not shown; the section head links to `projects.html#map`) → What we do → Artists (tall 3:5 cards) → Editorial → Contact. Hover (pointer devices only): a black pillar with a thin lavender top line rises from the bottom behind the project text column and behind the whole artist card (`clip-path`, .55s); text turns paper once the pillar has passed |
| `content/site.yml` | Home, About, list-page leads, contact, company info, home highlights (`featured_*`). `about.what_we_do[]` (About "Scope" section) = `label` ("01. ART DEALING"), `title`, `items[]`, `title_en`, `items_en[]`, shown as number cards (old single `text` "title - a, b" is still parsed) |
| `content/projects/*.md`, `artists/*.md`, `editorial/*.md` | One entry per file, YAML front matter + markdown body. Editorial `upcoming: true` lists the issue as "공개 예정 / Coming soon" (not a link, no page built); the newest published issue gets a LATEST tag automatically (list and home feature); `cover_focus` sets the crop of the cover |
| Artists list (`artist_spread()` in `build.py`) | Laid out like the company profile (2026-11): two per row (one on phones), each a tall detail crop (`photo`, 9:22) beside ARTIST 0n, name, medium · based, a thick rule, the artist's sentence (`quote`, from the profile), and the `summary` at the foot; on hover the photo fades to the work in place (`hero_image`). Home cards show the sentence over the photo on hover. A quote still holding placeholder text ("…자리입니다") is not shown |
| Artist page (`content/artists/*.md`) | Optional blocks, each hidden when empty: `hero_image` + `hero_caption`, `quote` (the artist's own sentence), `works[]` (image, title, year, material, size, optional `group` sub-heading and `contain` for wide pieces; a work without an image shows an empty frame), `note` + `fit[]` (STANDS note and where the work fits), `installs[]` (image, place, year), `body` (CV), `history[]` (solo shows). Images for 권치규 in `img/artists/kwon-chi-gyu/`, from his 2026 select portfolios (hanging, wall, public art proposals as renderings). Other artists hold placeholder text in the same fields until their material arrives. Sample projects are not listed on a real artist's page |
| Project page (`content/projects/*.md`) | Facts list: Location, Year, Artist, Size, Type (`place_type`, e.g. 상업시설 / Commercial), Scope. `gallery[]` photos sit in one sideways-scrolling row with ←/→ buttons that show only when it overflows (`site.js`) |
| Case study (`case_study: true`) | Shown under "Case Studies" at the top of Projects as an accordion of full-bleed frames on desktop (~75vh; the open case takes most of the width, the others fold into strips with a vertical spine label; hover or focus opens one and the last one opened stays open, `site.js`; 3:4 stacked on phones; title over a bottom gradient, "01 / 02" counter, "View case" on hover; reveal and drift on scroll via the `site.js` reveal, off with reduced motion). `cover_focus` sets the crop, `cover_tall` an optional portrait photo, used for the frame when present. The page head has jump links to Case Studies and Project Map. Every case also gets the shared visuals: **key figures** (`stats[]`, up to 4, large numbers above the overview table, `case_stats()`), a **location diagram** (static MapLibre map with the site, `stations[]` (name, lat, lng) and a dashed straight line with its length, `case_locator()` + `assets/locator.js`, loaded only on case pages), a **scale diagram** (every `specs[]` size parsed as W × D × H, outer width × height drawn to one scale beside a 1.7 m person, wrapped into rows, sizes in screen pixels kept equal across cases, `case_scale()`), and, when the photos exist, a **day / night pair** (`day_night` day, night, caption; `case_daynight()`). Planned when material arrives: review CG beside the built result, and a site plan diagram (only from a real plan). Section order (2026-11): key figures under the cover → 01 Site and conditions (location diagram, site images, site text) → 02 **Conditions → decisions** (`decisions[]`: kind (주제/배치/형태/규모/재료/빛/운영), condition, optional reading, decision, evidence, `_en` for each; `draft: true` keeps a card off the site until confirmed; when no confirmed card exists the older `curation[]` rows show instead; `case_decisions()`) → 03 Specifications → 04 Result → 05 Process → 06 Reference data (the facts table and its source). Every environmental fact on the page should lead to a decision; DMEC's four cards are drafts read from photos, waiting for confirmation. Map tags now name the conditions the works answer (보행로 면, 수변 시야 …), not real-estate labels. Older notes: Overview (`facts` with fixed keys building, location, owner, use, scale, area, year, works, size, material, scope, budget — `FACTS` in `build.py`; the same keys are meant for the planned art map), Site analysis (`site` markdown + `site_images[]`), Curation (`curation_intro`, `curation[]` condition/work/response, then the body), Specifications (`specs[]` + `specs_note`), Result (`results[]` image + caption), Process (`process[]`). Several artists via `artists[]`. Cases: DMEC (`horizontal-gardens.md`), Lagoon Interrace (`lagoon-interrace.md`, which also holds the two Ansan works by Kim Taeho and Kim Dohoon; artists without a page go in `artist_names`); brief on branch `case-study-brief` (`docs/case-studies/README.md`). Leave anything marked [확인 필요] there out of the site |
| Projects map (`assets/map.js`, `map_section()` in `build.py`) | The Projects page is Case Studies on top, then "Project Map": a list beside a MapLibre map (stacked on phones; the list always shows every entry of the current filter, the picked one highlighted), type filter chips (from `place_type`: 업무 / 주거 / else mixed-use) plus a second row of location-tag chips (from `site_tags`, in order of first appearance; combines with the type, click again to clear), clustered pins (case studies big and black with a label, others small lavender), a summary card per pin with a small photo. A project shows on the map when it has `lat` / `lng`; `map_only: true` builds no page (its links go to `projects.html#map`); `work` (+ `en.work`, `en.artist`) names the work on the card. MapLibre GL 4.7.1 is vendored in `assets/vendor/` (BSD licence); base map is OpenFreeMap Positron (no key, attribution shown). Coordinates come from OpenStreetMap place names near each site (bus stops named after the building), so they are approximate. Site facts (2026-11, step 1, filled by hand from public sources, no API): every project carries `facts` (building, location = street address, context, station = nearest station with straight-line distance from OSM, use, scale, completed …; keys in `FACTS`), `site_tags[]` / `site_tags_en[]` and `facts_source` (source and check date, shown under the case overview and on the map card). The map card reads like a listing: building, address, tags, use / scale / setting / transit / completed, then one work line and the source. Sites: HFR HQ, 40 Geumto-ro 80beon-gil (Pangyo Techno Valley 2 G2, coordinate approximate); Hillstate Pangyo Station, 136 Pangyoyeok-ro (officetel, 516 units, from a public listing, not yet matched to the building register); Dongtan Parkrix A55BL, 43 Dongtansinricheon-ro 5-gil. Step 2 (data.go.kr building-register API at build time) needs a service key and network access to that host |
| `.pages.yml` | Pages CMS field config. Field names must match what `build.py` reads |
| `build/build.py` | Whole site generator (pages, cards, header/footer, i18n, GA/Clarity snippets) |
| `build/logo_new.py` | Logo and hero glyph paths taken from the brand guide PDF |
| `assets/site.css`, `assets/site.js` | Styles; nav, filters, contact-form stub, GA4 events. Images can't be dragged or long-pressed (CSS) and their right-click menu is blocked (`site.js`); text and links keep theirs. Footer copyright line = `company.copyright` / `en.copyright` in `site.yml` |
| `assets/hero.js` | Home hero animation (see below) |
| `build/illust.js`, `img/illust/*.svg` | Line illustrations: `service-01..03` (home What we do cards, by order). Edit the script, run `node build/illust.js`, commit the SVGs; the site build only links them |
| `build/process.js`, `img/illust/process-01..06.svg` | About "Process" pictograms (geometry only; the work, a vesica, firms up step by step). Step names KO/EN are in `PROCESS` in `build.py`. Edit the script, run `node build/process.js`, commit the SVGs |
| `img/home/statement.jpg` | Home photo beside the story (`home.statement_image`, CMS field 소개글 오른쪽 사진). Slim and tall beside the story, a little longer than the text (5:4 under it on phones); reveals with the scroll position and drifts slightly (`site.js`, off with reduced motion); source with the Gemini mark removed , upscaled to 1200 × 1500, in `photos-src/home/` |
| `img/about/intro.jpg` | About photo under the STANDS label beside the copy (`about.intro_image`, CMS field 소개글 옆 사진). Cropped to the sculpture and its circular guide lines (660 × 755), exactly as tall as the copy, label above it; same scroll reveal as the home photo; 4:5 above the copy below 860 px. Source (Gemini mark removed) in `photos-src/about/` |
| `img/hero/01–12-*.jpg` | Hero photos, 2400 px wide, plus `-1600.jpg` copies for small/1x screens (`hero.js` picks by screen size × DPR). Originals (2752 px) in `photos-src/hero/`, not deployed |
| `video/courtyard-loop-v2.mp4/.webm`, `img/courtyard-poster.jpg` | Final loop film |

## Bilingual content

- English lives next to Korean: an `en:` block per entry/section (`en.title`, `en.summary`, `en.body`…), and `<field>_en` inside list items (`services[].title_en`, `history[].place_en`).
- Empty English falls back to Korean. Helpers in `build.py`: `L(d,key)`, `LI(item,key)`, `U(ko,en)`, `BODY(d)`. `P` is the path prefix (`''` or `'../'`).
- `BASE_URL` / env `STANDS_URL` feeds canonical and hreflang links. **Update it when a custom domain or the company GitHub org is set up.**

## Home hero (`assets/hero.js`)

1. "WHERE ART" plus an empty underbar.
2. Pass 1: each of 12 photos once, with its line pictogram standing on the underbar.
3. Pass 2: a fast burst of all 12 again.
4. Black answer scene: "STANDS" appears.
5. The box logo draws itself.
6. The courtyard loop film fades in behind the box.

- **`places`**, ordered bright → dark on purpose: fields
  - `g`: floor line as a share of image height, aligned to the underbar
  - `x`, `z`: optional horizontal anchor and zoom (the museum photo uses them)
  - `b`: brightness trim
  - `dark`: white text and pictogram
  - `p`: pictogram key
  - `size`: tag label
- **`PICTO`**: stroke paths (touching pieces joined into continuous paths; lines within 2° of vertical/horizontal straightened, since slight tilts render as stair-steps; absolute coords) from June's refined sheet (`~/Desktop/stands-website/pictograms`, source `STANDS_pictograms_sheet.svg`). `t` = translate x, y and scale into viewBox `-14 -22 128 122`, base on y = 100. Stroke `SW = 1.5` in `INK` `#2B2930` (paper on dark photos) plus a halo `SW + 1.1` wide at 85% with a ~0.4 px feathered edge (`pict-feather`). Lower contrast hides stair-stepping; a wide half-transparent halo read as blur. The `.obj` box is snapped to the device pixel grid (`snapObj`).
- **Timing**
  - One continuous tempo, no jump between passes.
  - Pass 1 cuts go from 650 ms to 330 ms (geometric, about 6% shorter each).
  - Pass 2 carries on from 310 ms down to 130 ms (about 13% shorter each), holds 130 ms twice, then lands at 142, 157, 178 ms.
  - Burst order rises from the dark end to the brightest and back (`burst`).
  - `A` = answer start, `DUR = A + 6000`, `LOOP_AT = A + 4500`.
  - All later events are offsets from `A`.
- **Look**
  - Crossfade 0.12 s; previous photo kept underneath (`bgprev`).
  - Tone: `saturate(.8)` plus the `.hero .bg .tone` lavender soft-light layer (opacity .42, in `site.css`).
  - Pass 2 adds push-in to 1.035 and blur up to 0.8 px.
- **Rules**
  - Keep big brightness swings under 3 per second (WCAG 2.3.1). Check by sampling screen luminance.
  - `prefers-reduced-motion` jumps straight to the end.
  - "다시 보기" and back/forward cache (`pageshow`) call `restart()`, which hides the film instantly.
- **Box logo**: `logo_svg()` in `build.py`. The hero lockup fill uses `fill-opacity:.72`; the outline stays opaque.

## Brand

- **Colours**: paper `#F0F0EE`, black `#000`, lavender accent `#7D7889`, sky `#8FCAD8`, line `#D3D2CE`, muted `#6C6A71`.
- **Fonts**: Archivo at 75% width for headings; Pretendard for Korean and body text; Newsreader italic for accents; IBM Plex Mono for labels.
- **Header**: uses the mono box logo with mix-blend-mode. Its third line keeps changing (`site.js`, `SEQ`): STANDS, hero place names and now and then a verb (BELONGS, BREATHES, REMAINS, LIVES, MEETS), each wiped out right to left and revealed left to right; the bar follows the word width. New words are Archivo 800, 75% width, 80 units, −2.7 tracking (matched to the logo glyphs); words wider than 322 units are squeezed. Off with reduced motion; `aria-label` stays STANDS.

## Analytics

- GA4 `G-4HENTDTYNP`, with `site_language` set per page. Microsoft Clarity `z46038c0ok`.
- Events: `ui_click`, `cta_contact_click`, `nav_click`, `project_click`, `artist_click`, `editorial_click`, `project_filter`, `scroll_depth`, `language_switch`, `hero_complete`, `hero_replay`, `contact_form_submit`.

## Open items before launch (target 2026-11-16)

- [ ] Contact form only shows a notice. Wire real delivery (e.g. Formspree) to the company inbox.
- [ ] Fill company info, phone and address. Finalise the privacy policy (KO/EN).
- [x] Sample projects and sample artists removed (2026-11-18). Projects now: 2 case studies (DMEC, Lagoon Interrace, which absorbed the Ansan works Forest of Dreams and Crystal gate) and 3 map-only entries (Polar Bear Family, Our Portrait, Nabillera), all Scope 심의 · 제작 · 설치. Home features the two case studies (DMEC, Lagoon Interrace).
- [ ] Check whether FRIENDSWITHYOU (overseas) can be listed. Fill missing year/size on projects.
- English site check (2026-11-18): no Korean text left on /en/ pages; Korean placeholders like [입력] render as [To be added] there (`page()` in build.py).
- [ ] Confirm English artist names (Kwon Chi-gyu, Kim Byoungho, Kim Woojin, Lee Sungok) and "Malong Company".
- [ ] Editorial issues 02/03 are listed as upcoming; their summaries are still planning memos (not shown while upcoming). Write them before switching `upcoming` off.
- [x] Custom domain stands.art (2026-11-18), `BASE_URL` default updated.
- [ ] Transfer the repo to the company org. Re-install the Pages CMS app on the org; change the `www` CNAME to `<org>.github.io`.
- [ ] Mark `cta_contact_click` as a GA4 key event. Register with Search Console and Naver Search Advisor.
- [ ] Optional: move hero timing values into `site.yml` / `.pages.yml` so June can tune them in the CMS.
