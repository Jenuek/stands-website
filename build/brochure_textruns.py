#!/usr/bin/env python3
"""Join Chromium's glyph-by-glyph text into one text run per line, so Illustrator opens each line as one text object.

Chromium (Skia) writes every glyph as its own show-text operator:
    <342B> Tj  3.23 0 Td <1B1C> Tj  12.67 0 Td <0CE4> Tj ...
Illustrator turns each of those into a separate point-text object: one letter each.
This rewrites every such sequence inside a BT…ET block as a single TJ array,
    [<342B> <1B1C> <0CE4> ...] TJ
with a number between two glyphs only where Chromium's step differs from the font's own advance width
(letter-spacing, justification: Illustrator reads those as kerning). Positions on the page stay the same.

    pip install pikepdf
    python build/brochure_textruns.py _brochure/brochure-ko.pdf [more.pdf …]   (rewrites in place)
"""
import sys
import pikepdf
from pikepdf import Name, Array, String, Operator, ContentStreamInstruction

MIN_GAP = 0.5   # TJ units (1/1000 em) below which a gap is rounding noise, not spacing


def widths(font):
    """code → advance width (1/1000 em), and bytes per code, for Type0 (Identity-H) and simple fonts."""
    if font.get('/Subtype') == Name.Type0:
        d = font.DescendantFonts[0]
        dw = float(d.get('/DW', 1000))
        w, table, i = list(d.get('/W', [])), {}, 0
        while i < len(w):
            c = int(w[i])
            if isinstance(w[i + 1], pikepdf.Array):
                for k, v in enumerate(w[i + 1]):
                    table[c + k] = float(v)
                i += 2
            else:
                for k in range(c, int(w[i + 1]) + 1):
                    table[k] = float(w[i + 2])
                i += 3
        return (lambda code: table.get(code, dw)), 2
    first = int(font.get('/FirstChar', 0))
    ws = [float(x) for x in font.get('/Widths', [])]
    return (lambda code: ws[code - first] if 0 <= code - first < len(ws) else 0.0), 1


def advance(raw, wfn, n):
    return sum(wfn(int.from_bytes(raw[i:i + n], 'big')) for i in range(0, len(raw), n))


def rewrite(instrs, fonts):
    out, run, consumed, pending = [], None, 0.0, None
    cur = {'w': None, 'n': 2, 'size': 1.0, 'plain': True}
    TJ, Td = Operator('TJ'), Operator('Td')

    def flush():
        nonlocal run, consumed
        if run:
            arr = Array()
            for k, (raw, gap) in enumerate(run['items']):
                if k and abs(gap) >= MIN_GAP:
                    arr.append(round(gap, 2))
                arr.append(String(raw))
            out.append(ContentStreamInstruction([arr], TJ))
            if abs(consumed) > 1e-6:          # put the line start where the original Td's left it
                out.append(ContentStreamInstruction([round(consumed, 4), 0], Td))
        run, consumed = None, 0.0

    def emit_pending():
        nonlocal pending
        if pending is not None:
            out.append(pending)
            pending = None

    for ins in instrs:
        op, ops = str(ins.operator), list(ins.operands)
        if op == 'Tj' and cur['w'] and cur['plain']:
            raw = bytes(ops[0])
            if run and pending is not None:
                dx = float(pending.operands[0])
                run['items'].append((raw, run['last_w'] - dx * 1000.0 / cur['size']))
                consumed += dx
                pending = None
            else:
                flush()
                emit_pending()
                run = {'items': [(raw, 0.0)]}
            run['last_w'] = advance(raw, cur['w'], cur['n'])
            continue
        if op == 'Td' and run is not None and pending is None and abs(float(ops[1])) < 1e-9:
            pending = ins
            continue
        flush()
        emit_pending()
        if op == 'Tf':
            f = fonts.get(str(ops[0]))
            cur['w'], cur['n'] = widths(f) if f is not None else (None, 2)
            cur['size'] = float(ops[1]) or 1.0
        elif op in ('Tc', 'Tw'):
            cur['plain'] = cur['plain'] and abs(float(ops[0])) < 1e-9
        elif op == 'Tz':
            cur['plain'] = cur['plain'] and abs(float(ops[0]) - 100) < 1e-9
        elif op == 'BT':
            cur['plain'] = True
        out.append(ins)
    flush()
    emit_pending()
    return out


def fonts_of(res):
    if res is None or '/Font' not in res:
        return {}
    return {str(k): v for k, v in res.Font.items()}


def count(instrs, names):
    return sum(1 for i in instrs if str(i.operator) in names)


def fix(path):
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    before = after = 0
    seen = set()

    def do_xobjects(res):
        nonlocal before, after
        if res is None or '/XObject' not in res:
            return
        for _, x in res.XObject.items():
            if x.get('/Subtype') != Name.Form or x.objgen in seen:
                continue
            seen.add(x.objgen)
            xres = x.get('/Resources')
            ins = pikepdf.parse_content_stream(x)
            new = rewrite(ins, fonts_of(xres))
            before, after = before + count(ins, ('Tj',)), after + count(new, ('Tj', 'TJ'))
            x.write(pikepdf.unparse_content_stream(new))
            do_xobjects(xres)

    for page in pdf.pages:
        res = page.obj.get('/Resources')
        ins = pikepdf.parse_content_stream(page)
        new = rewrite(ins, fonts_of(res))
        before, after = before + count(ins, ('Tj',)), after + count(new, ('Tj', 'TJ'))
        page.obj.Contents = pdf.make_stream(pikepdf.unparse_content_stream(new))
        do_xobjects(res)
    pdf.save(path, compress_streams=True)
    print(f'{path}: {before} glyph-by-glyph text operators → {after} text runs')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        fix(p)
