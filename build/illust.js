// Line illustrations for the home "What we do" cards.
// Free curves for the works, plain lines for frames, plinths and buildings, one shared ground line.
// Run: node build/illust.js   -> writes img/illust/*.svg (commit the output; the site build does not run this)
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, '..', 'img', 'illust');

const f = n => (+n.toFixed(2)).toString();
// Catmull-Rom through the points, as cubic Beziers (smooth curves from a few hand-placed points)
function cr(pts, closed, t = 0.5) {
  const P = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]];
  let d = `M${f(pts[0][0])} ${f(pts[0][1])}`;
  const n = closed ? pts.length : pts.length - 1;
  for (let i = 1; i <= n; i++) {
    const p0 = P[i - 1], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2];
    const c1 = [p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3];
    const c2 = [p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3];
    d += `C${f(c1[0])} ${f(c1[1])} ${f(c2[0])} ${f(c2[1])} ${f(p2[0])} ${f(p2[1])}`;
  }
  return d + (closed ? 'Z' : '');
}
const crg = pts => cr(pts, false) + 'Z';            // open curve closed by a straight base
const mv = (pts, dx, dy = 0) => pts.map(([x, y]) => [x + dx, y + dy]);

const BASE = 104;
const ground = (x0 = 10, x1 = 110) => `<path class="g" d="M${x0} ${BASE}H${x1}"/>`;
const person = (x, h = 30) => {
  const t = BASE - h;
  return `<circle class="l" cx="${x}" cy="${t + 3.4}" r="3.4"/><path class="l" d="M${x - 5.2} ${BASE}C${x - 5.6} ${t + 22} ${x - 5} ${t + 10} ${x} ${t + 9.2}C${x + 5} ${t + 10} ${x + 5.6} ${t + 22} ${x + 5.2} ${BASE}"/>`;
};
// the tall flowing sculpture on its plinth (base of plinth on the ground), centred around x
const TALL = [[78, 92], [75, 80], [73, 66], [75, 50], [81, 36], [90, 27], [95, 35], [93, 50], [89, 62], [91, 76], [90, 92]];
const TALL_IN = [[82, 86], [80, 70], [80, 56], [84, 44], [90, 33]];
function sculpture(cx, lift = 0) {
  const dx = cx - 84, o = mv(TALL, dx, -lift), i = mv(TALL_IN, dx, -lift);
  return `<path class="c" d="${crg(o.map(([x, y]) => [x + 5, y < 90 - lift ? y - 3 : y]))}"/>` +
    `<path class="l" d="${crg(o)}"/><path class="l2" d="${cr(i, false)}"/>`;
}
const plinth = cx => `<rect class="l" x="${cx - 12}" y="92" width="24" height="12"/>`;

// 01 ART DEALING: a crated work with its tag, sent to the place it should stand
const s1 = ground() +
  `<path class="c" d="${cr([[22, 60], [26, 40], [38, 34], [46, 44], [42, 60]], true)}"/>` +
  `<path class="l2" d="${cr([[24, 62], [27, 46], [35, 38], [43, 44], [40, 56], [46, 62]], false)}"/>` +
  `<rect class="l" x="12" y="60" width="42" height="44"/><path class="l2" d="M12 74.7H54M12 89.3H54M16 60V104M50 60V104"/>` +
  `<path class="l2" d="M54 66C58 66 60 68 60 72"/><path class="l" d="M56.5 72H63.5L63.5 82L60 85L56.5 82Z"/><circle class="l2" cx="60" cy="75.5" r="1"/>` +
  `<rect class="dash" x="72" y="30" width="34" height="44" rx="1.5"/><path class="g2" d="M66 22H112M89 22V30"/>` +
  `<path class="arr" d="${cr([[36, 30], [46, 16], [60, 12], [76, 24]], false)}"/><path class="arr" d="M70.6 21.6L76 24L76.6 18.2"/>`;

// 02 ART PROJECTS: a commissioned installation hung from the ceiling, with visitors beneath
const RIB = [[30, 34], [42, 24], [58, 30], [66, 44], [82, 48], [94, 36], [88, 26], [76, 32], [74, 46], [64, 58], [48, 60], [38, 52]];
const s2 = ground() + `<path class="g2" d="M10 8H110"/><path class="l2" d="M42 8V24M88 8V26"/>` +
  `<path class="c" d="${cr(mv(RIB, 4, 3), true)}"/>` +
  `<path class="l n" d="${cr(RIB, true)}"/>` +
  `<path class="l2" d="${cr([[36, 42], [50, 36], [62, 46], [78, 40]], false)}"/>` +
  person(40) + person(74, 26);

// 03 ARCHITECTURAL ART: a sculpture on a plinth beside a building entrance
const building = (x0, x1, top = 24) => {
  const w = x1 - x0, c = x0 + w / 2;
  return `<path class="b" d="M${x0} ${BASE}V${top}H${x1}V${BASE}M${x0} ${top + 20}H${x1}M${x0} ${top + 40}H${x1}M${f(x0 + w / 3)} ${top}V${top + 40}M${f(x0 + 2 * w / 3)} ${top}V${top + 40}M${c - 10} ${BASE}V80H${c + 10}V${BASE}M${c} 80V${BASE}"/>`;
};
const s3 = building(12, 60) + ground() + sculpture(84) + plinth(84) + person(104, 28);

const CSS = `.l{fill:#F0F0EE;stroke:#1C1A20;stroke-width:1.4;stroke-linecap:round;stroke-linejoin:round}.n{fill:none}
.l2{fill:none;stroke:#1C1A20;stroke-width:.9;stroke-linecap:round;stroke-linejoin:round}
.c{fill:#7D7889;fill-opacity:.28}
.g{fill:none;stroke:#1C1A20;stroke-width:1.2;stroke-linecap:round}
.b{fill:none;stroke:#9A97A2;stroke-width:.8;stroke-linecap:round;stroke-linejoin:round}
.g2{fill:none;stroke:#9A97A2;stroke-width:.8;stroke-linecap:round}
.dash{fill:none;stroke:#7D7889;stroke-width:1.1;stroke-dasharray:3 3}
.arr{fill:none;stroke:#7D7889;stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round}`;
const svg = (w, body) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} 120" width="${w * 2}" height="240"><style>${CSS}</style>${body}</svg>\n`;

fs.mkdirSync(OUT, { recursive: true });
const files = {
  'service-01.svg': svg(120, s1),
  'service-02.svg': svg(120, s2),
  'service-03.svg': svg(120, s3),
};
for (const [n, s] of Object.entries(files)) fs.writeFileSync(path.join(OUT, n), s);
console.log('wrote', Object.keys(files).join(', '));
