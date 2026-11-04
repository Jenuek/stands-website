# STANDS website — notes for Claude Code

Brand site for **STANDS** (art company: art dealing, art projects, architectural art; partner 마롱컴퍼니).
Owner/designer: June. Talk to June in Korean. Copy tone: clear and assertive, never sentimental. Verify facts before writing them.

- Live: https://jenuek.github.io/stands-website/ (Korean at root, English under `/en/`)
- Repo: https://github.com/Jenuek/stands-website, branch `main`
- Deploy: every push to `main` runs `.github/workflows/deploy.yml` → `python build/build.py` → `_site/` → GitHub Pages (about 1 minute)
- **Always `git pull` before editing.** June edits content in Pages CMS (https://app.pagescms.org), which commits straight to `main`.

## Build and preview locally

```bash
pip install pyyaml markdown
python build/build.py                 # writes _site/ (env: STANDS_OUT, STANDS_VER, STANDS_URL)
python -m http.server 8000 -d _site   # http://localhost:8000
```

Root `*.html`, `park-loop.*` and `img/park-poster.jpg` are leftovers from the first static version; nothing serves them.

## Layout

| Path | What |
| --- | --- |
| `content/site.yml` | Home, About, list-page leads, contact, company info, home highlights (`featured_*`) |
| `content/projects/*.md`, `artists/*.md`, `editorial/*.md` | One entry per file, YAML front matter + markdown body |
| `.pages.yml` | Pages CMS field config. Field names must match what `build.py` reads |
| `build/build.py` | Whole site generator (pages, cards, header/footer, i18n, GA/Clarity snippets) |
| `build/logo_new.py` | Logo and hero glyph paths taken from the brand guide PDF |
| `assets/site.css`, `assets/site.js` | Styles; nav, filters, contact-form stub, GA4 events |
| `assets/hero.js` | Home hero animation (see below) |
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
  - Pass 1 cuts go from 650 ms to 400 ms (geometric).
  - Pass 2 cuts follow `130 + 50·(2k/11−1)²` ms: 180 → 130 → 180.
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
- **Header**: uses the mono box logo with mix-blend-mode.

## Analytics

- GA4 `G-4HENTDTYNP`, with `site_language` set per page. Microsoft Clarity `z46038c0ok`.
- Events: `ui_click`, `cta_contact_click`, `nav_click`, `project_click`, `artist_click`, `editorial_click`, `project_filter`, `scroll_depth`, `language_switch`, `hero_complete`, `hero_replay`, `contact_form_submit`.

## Open items before launch (target 2026-11-16)

- [ ] Contact form only shows a notice. Wire real delivery (e.g. Formspree) to the company inbox.
- [ ] Fill company info, phone and address. Finalise the privacy policy (KO/EN).
- [ ] Hide `sample: true` entries. Add real domestic artists and 3–5 마롱컴퍼니 Partner Works. Check whether FRIENDSWITHYOU (overseas) can be listed.
- [ ] Confirm English artist names (Kwon Chi-gyu, Kim Byoungho, Kim Woojin, Lee Sungok) and "Malong Company".
- [ ] Editorial issues 02/03 still hold planning memos as summaries. The issue 01 draft is in June's Claude Doc.
- [ ] Custom domain, then transfer the repo to the company org. Re-install the Pages CMS app on the org and update `STANDS_URL`.
- [ ] Mark `cta_contact_click` as a GA4 key event. Register with Search Console and Naver Search Advisor.
- [ ] Optional: move hero timing values into `site.yml` / `.pages.yml` so June can tune them in the CMS.
