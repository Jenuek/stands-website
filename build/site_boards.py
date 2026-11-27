"""Site analysis boards for case studies (figure-ground, green and water, movement, sun path).

Draws four square SVG panels per case study from OpenStreetMap data (OpenFreeMap vector tiles) around the
project's `lat` / `lng`, and writes them to img/projects/<slug>/board-*.svg. The site build only links them.
Run it again when a case is added or moved:

    pip install mapbox-vector-tile pyyaml
    python build/site_boards.py            # all case studies
    python build/site_boards.py lagoon-interrace

Optional per case in the front matter: `board_radius` (metres, default 500).
"""
import math, os, sys, glob, json, urllib.request, hashlib
import yaml, mapbox_vector_tile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'stands-tiles')
TILEJSON = 'https://tiles.openfreemap.org/planet'
Z = 14
UA = {'User-Agent': 'Mozilla/5.0 stands-site-build'}
INK, PAPER, ACC, MUTED, LINE = '#000000', '#F0F0EE', '#7D7889', '#6C6A71', '#D3D2CE'
FONT = "font-family=\"'IBM Plex Mono',ui-monospace,Menlo,monospace\""
S = 1000  # panel size in SVG units


def get(url, binary=True):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(p):
        return open(p, 'rb').read()
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    open(p, 'wb').write(d)
    return d


def tile_url():
    return json.loads(urllib.request.urlopen(urllib.request.Request(TILEJSON, headers=UA), timeout=30).read())['tiles'][0]


def tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile_ll(z, x, y, px, py, ext=4096):
    n = 2 ** z
    lon = (x + px / ext) / n * 360 - 180
    yy = (y + 1 - py / ext) / n
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy)))), lon


class Frame:
    """Local metres around the site, mapped to a 0..S square (north up)."""
    def __init__(self, lat, lng, r):
        self.lat, self.lng, self.r = lat, lng, r
        self.k = (S / 2) / r
        self.kx = math.cos(math.radians(lat)) * 111320
        self.ky = 110540

    def xy(self, la, lo):
        return S / 2 + (lo - self.lng) * self.kx * self.k, S / 2 - (la - self.lat) * self.ky * self.k

    def dist(self, la, lo):
        return math.hypot((lo - self.lng) * self.kx, (la - self.lat) * self.ky)


def features(fr, url):
    dlat = fr.r * 1.3 / fr.ky
    dlng = fr.r * 1.3 / fr.kx
    x0, y0 = tile_xy(fr.lat + dlat, fr.lng - dlng, Z)
    x1, y1 = tile_xy(fr.lat - dlat, fr.lng + dlng, Z)
    out = []
    for tx in range(int(x0), int(x1) + 1):
        for ty in range(int(y0), int(y1) + 1):
            m = mapbox_vector_tile.decode(get(url.format(z=Z, x=tx, y=ty)))
            for layer, L in m.items():
                ext = L.get('extent', 4096)
                for f in L['features']:
                    out.append((layer, f['properties'], f['geometry'], (tx, ty, ext)))
    return out


def rings(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon':
        return c
    if t == 'MultiPolygon':
        return [r for poly in c for r in poly]
    if t == 'LineString':
        return [c]
    if t == 'MultiLineString':
        return c
    return []


def path(fr, geom, tile, close):
    tx, ty, ext = tile
    d = []
    for ring in rings(geom):
        pts = [fr.xy(*tile_ll(Z, tx, ty, px, py, ext)) for px, py in ring]
        if len(pts) < 2 or all(x < -150 or x > S + 150 or y < -150 or y > S + 150 for x, y in pts):
            continue  # outside the panel: leave it out of the file
        d.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + (' Z' if close else ''))
    return ' '.join(d)


def frame_svg(title, body, fr, extra=''):
    bar = 100 if fr.r <= 600 else 200
    bl = bar * fr.k
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" {FONT}>'
            f'<defs><clipPath id="c"><rect width="{S}" height="{S}"/></clipPath>'
            f'<pattern id="h" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="{INK}" stroke-width="2.2"/></pattern></defs>'
            f'<rect width="{S}" height="{S}" fill="{PAPER}"/><g clip-path="url(#c)">{body}</g>{extra}'
            # site marker
            f'<circle cx="{S/2}" cy="{S/2}" r="30" fill="none" stroke="{ACC}" stroke-width="5"/><circle cx="{S/2}" cy="{S/2}" r="9" fill="{ACC}"/>'
            # north arrow, scale bar, title
            f'<g transform="translate({S-60} 70)"><path d="M0 -34 L14 10 L0 2 L-14 10 Z" fill="{INK}"/><text y="38" font-size="22" text-anchor="middle" fill="{INK}">N</text></g>'
            f'<g transform="translate(40 {S-46})"><rect x="-12" y="-34" width="{bl+90:.0f}" height="58" fill="{PAPER}" opacity=".9"/>'
            f'<line x1="0" y1="0" x2="{bl:.1f}" y2="0" stroke="{INK}" stroke-width="5"/><line x1="0" y1="-10" x2="0" y2="10" stroke="{INK}" stroke-width="3"/>'
            f'<line x1="{bl:.1f}" y1="-10" x2="{bl:.1f}" y2="10" stroke="{INK}" stroke-width="3"/><text x="{bl+12:.1f}" y="8" font-size="22" fill="{INK}">{bar} m</text></g>'
            f'<rect x="0" y="0" width="{S}" height="{S}" fill="none" stroke="{INK}" stroke-width="4"/></svg>')


def panel_ground(fr, F):
    b = ''.join(f'<path d="{path(fr, g, t, True)}"/>' for l, p, g, t in F if l == 'building')
    water = ''.join(f'<path d="{path(fr, g, t, True)}"/>' for l, p, g, t in F if l == 'water')
    return frame_svg('ground', f'<g fill="{LINE}">{water}</g><g fill="{INK}">{b}</g>', fr)


GREEN = {'grass', 'wood', 'forest', 'farmland', 'wetland', 'park', 'garden', 'meadow', 'scrub'}


def panel_green(fr, F):
    green = ''.join(f'<path d="{path(fr, g, t, True)}"/>' for l, p, g, t in F
                    if (l == 'landcover' and p.get('class') in GREEN) or (l == 'park') or (l == 'landuse' and p.get('class') in ('park', 'pitch', 'playground', 'cemetery')))
    water = ''.join(f'<path d="{path(fr, g, t, True)}"/>' for l, p, g, t in F if l == 'water')
    ww = ''.join(f'<path d="{path(fr, g, t, False)}"/>' for l, p, g, t in F if l == 'waterway')
    b = ''.join(f'<path d="{path(fr, g, t, True)}"/>' for l, p, g, t in F if l == 'building')
    return frame_svg('green', f'<g fill="{LINE}">{b}</g><g fill="url(#h)" stroke="{INK}" stroke-width="1.5" opacity=".75">{green}</g>'
                              f'<g fill="#8FCAD8" opacity=".85">{water}</g><g fill="none" stroke="#5FA7B8" stroke-width="5">{ww}</g>', fr)


ROADS = [('motorway', 15), ('trunk', 13), ('primary', 11), ('secondary', 9), ('tertiary', 6), ('minor', 4), ('service', 2)]


def panel_move(fr, F, stations):
    b = ''.join(f'<path d="{path(fr, g, t, True)}"/>' for l, p, g, t in F if l == 'building')
    layers = []
    for cls, w in reversed(ROADS):
        d = ''.join(f'<path d="{path(fr, g, t, False)}"/>' for l, p, g, t in F if l == 'transportation' and p.get('class') == cls)
        if d:
            layers.append(f'<g fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round">{d}</g>')
    paths = ''.join(f'<path d="{path(fr, g, t, False)}"/>' for l, p, g, t in F if l == 'transportation' and p.get('class') in ('path', 'pedestrian', 'footway'))
    rail = ''.join(f'<path d="{path(fr, g, t, False)}"/>' for l, p, g, t in F if l == 'transportation' and p.get('class') in ('rail', 'transit'))
    stops = []
    for l, p, g, t in F:
        if l == 'poi' and p.get('class') == 'bus' and g['type'] == 'Point':
            x, y = fr.xy(*tile_ll(Z, t[0], t[1], *g['coordinates'], t[2]))
            stops.append(f'<rect x="{x-6:.1f}" y="{y-6:.1f}" width="12" height="12" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>')
    extra = ''
    for st in stations:
        x, y = fr.xy(st['lat'], st['lng'])
        d = fr.dist(st['lat'], st['lng'])
        label = f"{st['name']} {d/1000:.1f}km"
        if 30 < x < S - 30 and 30 < y < S - 30:
            extra += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{PAPER}" stroke="{INK}" stroke-width="5"/>'
                      f'<text x="{x+24:.1f}" y="{y+8:.1f}" font-size="24" fill="{INK}">{label}</text>')
        else:  # station outside the frame: an arrow at the edge pointing towards it
            ang = math.atan2(y - S / 2, x - S / 2)
            ex, ey = S / 2 + math.cos(ang) * (S / 2 - 70), S / 2 + math.sin(ang) * (S / 2 - 70)
            deg = math.degrees(ang)
            tx = ex - math.cos(ang) * 30
            ty = ey - math.sin(ang) * 30
            anchor = 'end' if math.cos(ang) > 0.3 else ('start' if math.cos(ang) < -0.3 else 'middle')
            extra += (f'<line x1="{S/2 + math.cos(ang)*60:.1f}" y1="{S/2 + math.sin(ang)*60:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{ACC}" stroke-width="4" stroke-dasharray="14 10"/>'
                      f'<path d="M0 0 L-26 -12 L-26 12 Z" fill="{ACC}" transform="translate({ex:.1f} {ey:.1f}) rotate({deg:.1f})"/>'
                      f'<rect x="{(tx - 250 if anchor == "end" else (tx - 125 if anchor == "middle" else tx)) - 6:.1f}" y="{ty - (40 if math.sin(ang) > 0 else -14):.1f}" width="262" height="36" fill="{PAPER}" opacity=".92"/>'
                      f'<text x="{tx:.1f}" y="{ty - (12 if math.sin(ang) > 0 else -42):.1f}" font-size="24" fill="{INK}" text-anchor="{anchor}">{label} →</text>')
    body = (f'<g fill="#E2E1DD">{b}</g>{"".join(layers)}'
            f'<g fill="none" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="6 6">{paths}</g>'
            f'<g fill="none" stroke="{ACC}" stroke-width="6" stroke-dasharray="18 10">{rail}</g>{"".join(stops)}')
    return frame_svg('move', body, fr, extra)


def sun(lat, decl):
    """(azimuth, altitude) points of the sun's path for one day, in degrees."""
    phi, d = math.radians(lat), math.radians(decl)
    pts = []
    for m in range(-720, 721, 10):
        H = math.radians(m / 4)
        alt = math.asin(math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.cos(H))
        az = math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(d) * math.cos(phi)) + math.pi
        if alt > 0:
            pts.append((math.degrees(az), math.degrees(alt)))
    return pts


def panel_sun(lat, labels):
    R, c = 400, S / 2
    def p(az, alt):
        r = (90 - alt) / 90 * R
        return c + r * math.sin(math.radians(az)), c - r * math.cos(math.radians(az))
    g = ''.join(f'<circle cx="{c}" cy="{c}" r="{(90-a)/90*R:.1f}" fill="none" stroke="{LINE}" stroke-width="2"/>' for a in (0, 30, 60))
    g += ''.join(f'<line x1="{c}" y1="{c}" x2="{p(az,0)[0]:.1f}" y2="{p(az,0)[1]:.1f}" stroke="{LINE}" stroke-width="2"/>' for az in range(0, 360, 45))
    g += ''.join(f'<text x="{p(az,-8)[0]:.1f}" y="{p(az,-8)[1]+9:.1f}" font-size="26" text-anchor="middle" fill="{INK}">{t}</text>'
                 for az, t in ((0, 'N'), (90, 'E'), (180, 'S'), (270, 'W')))
    g += ''.join(f'<text x="{c+6}" y="{c-(90-a)/90*R+26:.1f}" font-size="18" fill="{MUTED}">{a}°</text>' for a in (30, 60))
    curves = ''
    for decl, w, dash, key in ((23.44, 5, '', 'summer'), (0, 4, '12 8', 'equinox'), (-23.44, 5, '4 8', 'winter')):
        pts = sun(lat, decl)
        d = 'M' + ' L'.join(f'{p(az, alt)[0]:.1f} {p(az, alt)[1]:.1f}' for az, alt in pts)
        noon = 90 - lat + decl
        nx, ny = p(180, noon)
        curves += (f'<path d="{d}" fill="none" stroke="{ACC if key == "summer" else INK}" stroke-width="{w}" stroke-dasharray="{dash}"/>'
                   f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="8" fill="{ACC if key == "summer" else INK}"/>'
                   f'<text x="{nx+22:.1f}" y="{ny+30:.1f}" font-size="22" fill="{INK}">{labels[key]} {noon:.0f}°</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" {FONT}><rect width="{S}" height="{S}" fill="{PAPER}"/>'
            f'{g}{curves}<circle cx="{c}" cy="{c}" r="9" fill="{ACC}"/>'
            f'<text x="40" y="{S-40}" font-size="22" fill="{MUTED}">{labels["lat"]} {lat:.2f}°N</text>'
            f'<rect x="0" y="0" width="{S}" height="{S}" fill="none" stroke="{INK}" stroke-width="4"/></svg>')


def main(only=None):
    url = tile_url()
    for f in sorted(glob.glob(os.path.join(ROOT, 'content', 'projects', '*.md'))):
        slug = os.path.splitext(os.path.basename(f))[0]
        d = yaml.safe_load(open(f, encoding='utf-8').read().split('---')[1])
        if not d.get('case_study') or d.get('lat') in (None, '') or (only and slug not in only):
            continue
        lat, lng = float(d['lat']), float(d['lng'])
        fr = Frame(lat, lng, float(d.get('board_radius') or 500))
        F = features(fr, url)
        out = os.path.join(ROOT, 'img', 'projects', slug)
        os.makedirs(out, exist_ok=True)
        stations = [{'name': s.get('name'), 'lat': float(s['lat']), 'lng': float(s['lng'])} for s in (d.get('stations') or [])]
        stations_en = [{'name': s.get('name_en') or s.get('name'), 'lat': float(s['lat']), 'lng': float(s['lng'])} for s in (d.get('stations') or [])]
        # figure-ground only where OpenStreetMap maps the buildings well enough to read the urban fabric
        nb = sum(1 for l, p, g, t in F if l == 'building' and fr.dist(*tile_ll(Z, t[0], t[1], *rings(g)[0][0], t[2])) < fr.r)
        gp = os.path.join(out, 'board-ground.svg')
        if nb >= 12:
            open(gp, 'w').write(panel_ground(fr, F))
        elif os.path.exists(gp):
            os.remove(gp)
        print(slug, nb, 'buildings mapped in the frame')
        open(os.path.join(out, 'board-green.svg'), 'w').write(panel_green(fr, F))
        open(os.path.join(out, 'board-move.svg'), 'w').write(panel_move(fr, F, stations))
        open(os.path.join(out, 'board-move-en.svg'), 'w').write(panel_move(fr, F, stations_en))
        open(os.path.join(out, 'board-sun.svg'), 'w').write(panel_sun(lat, {'summer': '하지', 'equinox': '춘·추분', 'winter': '동지', 'lat': '위도'}))
        open(os.path.join(out, 'board-sun-en.svg'), 'w').write(panel_sun(lat, {'summer': 'Jun', 'equinox': 'Mar/Sep', 'winter': 'Dec', 'lat': 'Latitude'}))
        print(slug, len(F), 'features ->', out)


if __name__ == '__main__':
    main(sys.argv[1:] or None)
