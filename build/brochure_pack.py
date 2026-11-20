#!/usr/bin/env python3
"""Package the brochure for editing in Illustrator.

_brochure/STANDS_Company-Profile_<date>.zip with
  STANDS_Company-Profile_KO.pdf / _EN.pdf   whole brochure
  pages-KO/, pages-EN/                       one PDF per page (Illustrator opens one page per file)
  fonts/                                     the static fonts the PDF uses (install before opening)
  README.txt

    python build/brochure_pack.py      (after build/brochure_pdf.mjs; needs pypdf, pikepdf)
"""
import os, shutil, zipfile, datetime
from pypdf import PdfReader, PdfWriter
import brochure_textruns

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_brochure')
NAME = f'STANDS_Company-Profile_{datetime.date.today():%Y%m%d}'
DST = os.path.join(SRC, NAME)

README = '''STANDS 회사 소개서 — 일러스트레이터 편집용

1. 먼저 fonts 폴더의 폰트를 모두 설치하세요 (더블클릭 → 설치).
   PDF에 같은 이름의 폰트가 들어 있어, 설치하면 글자를 그대로 고칠 수 있습니다.
   Pretendard, Archivo Condensed, IBM Plex Mono, Noto Sans KR (한자 몇 자) — 모두 SIL Open Font License.

2. Illustrator에서 PDF를 엽니다.
   - pages-KO / pages-EN: 한 페이지씩 나눈 파일. 파일마다 바로 열립니다.
   - 전체 PDF: 열 때 나오는 [PDF 가져오기] 창에서 페이지를 고릅니다.
     Illustrator 버전에 따라 모든 페이지를 아트보드로 한 번에 불러올 수도 있습니다.

3. 편집 메모
   - 글자는 한 줄이 하나의 텍스트 개체로 들어 있습니다. 문단을 크게 고칠 때는 한 줄씩 지우고 영역 텍스트로 다시 흘리는 편이 빠릅니다.
   - 사진은 클리핑 마스크 안에 들어 있습니다. 마스크 안 사진을 바꾸거나 위치를 옮기면 됩니다.
   - 로고와 선 일러스트는 벡터입니다.
   - 판형: A4 가로 297 × 210mm, 재단 여백 없음. 인쇄소에 맡길 때는 재단 여백(보통 3mm)을 따로 확인하세요.
   - 사진은 사이트용 해상도(가로 1,500–1,800px)라 화면·PDF 배포에는 충분하지만, 인쇄용으로는 원본 사진으로 바꾸는 것이 좋습니다.
   - 사업자등록번호, 미술품 유통업 신고번호는 아직 비어 있어 점선 상자로 표시했습니다 (판권 페이지).
'''


def main():
    shutil.rmtree(DST, ignore_errors=True)
    os.makedirs(DST)
    for lang in ('ko', 'en'):
        pdf = os.path.join(SRC, f'brochure-{lang}.pdf')
        if not os.path.exists(pdf):
            continue
        brochure_textruns.fix(pdf)   # one text object per line in Illustrator, not one per letter
        L = lang.upper()
        shutil.copy(pdf, os.path.join(DST, f'STANDS_Company-Profile_{L}.pdf'))
        pdir = os.path.join(DST, f'pages-{L}')
        os.makedirs(pdir)
        r = PdfReader(pdf)
        for i, page in enumerate(r.pages, 1):
            w = PdfWriter()
            w.add_page(page)
            with open(os.path.join(pdir, f'STANDS_{L}_p{i:02d}.pdf'), 'wb') as f:
                w.write(f)
    shutil.copytree(os.path.join(SRC, 'fonts'), os.path.join(DST, 'fonts'))
    open(os.path.join(DST, 'README.txt'), 'w', encoding='utf-8').write(README)
    z = DST + '.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for base, _, files in os.walk(DST):
            for fn in sorted(files):
                p = os.path.join(base, fn)
                zf.write(p, os.path.relpath(p, SRC))
    print('wrote', os.path.relpath(z, ROOT), f'{os.path.getsize(z) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
