// Process pictograms for the About page (01 site study ... 06 in place).
// Geometry only: lines, circles and arcs, dashed guides and dimension lines, one shared ground line.
// The work is a vesica (two circular arcs) that firms up step by step: marked spot, construction,
// drawing, half-built structure, hung outline, standing form.
// Run: node build/process.js  -> img/illust/process-01..06.svg (commit the output; the site build only links them)
const fs=require('fs');
const path=require('path');
const OUT=path.join(__dirname,'..','img','illust');const f=n=>(+n.toFixed(2)).toString();
const G=100; // ground
// vesica (two circular arcs), centred on cx, bottom at yb, height h, width w
function vesica(cx,yb,h,w){const yt=yb-h,R=(w*w/4+h*h/4)/w; // circle radius through the 3 points
  return `M${f(cx)} ${f(yb)}A${f(R)} ${f(R)} 0 0 1 ${f(cx)} ${f(yt)}A${f(R)} ${f(R)} 0 0 1 ${f(cx)} ${f(yb)}Z`;}
// the two construction circles whose overlap makes the vesica
function vesicaCircles(cx,yb,h,w){const R=(w*w/4+h*h/4)/w,yc=yb-h/2,d=R-w/2;return [[cx+d,yc,R],[cx-d,yc,R]];}
const V={h:46,w:20}; const PL={w:22,h:8};
const plinth=(cx,cls='l')=>`<rect class="${cls}" x="${cx-PL.w/2}" y="${G-PL.h}" width="${PL.w}" height="${PL.h}"/>`;
const work=(cx,yb,cls)=>`<path class="${cls}" d="${vesica(cx,yb,V.h,V.w)}"/>`;
const ground=`<path class="g" d="M8 ${G}H112"/>`;
const arrowH=(x1,x2,y)=>`<path class="dim" d="M${x1} ${y}H${x2}M${x1} ${y-3}V${y+3}M${x2} ${y-3}V${y+3}"/>`;
const arrowV=(x,y1,y2)=>`<path class="dim" d="M${x} ${y1}V${y2}M${x-3} ${y1}H${x+3}M${x-3} ${y2}H${x+3}"/>`;
const CX=60, YB=G-PL.h;
// 01 SITE: the place, measured. A wall edge, the footprint marked, width and height dimensions.
// the room in section: walls and ceiling, a window on the left wall, its light falling toward the spot.
// The spot where the work will stand is marked, with its width and height measured.
const SX=66, SW=22, SH=V.h+PL.h;
const s1=ground+
 `<path class="b" d="M14 ${G}V16H106V${G}"/>`+
 `<path class="b" d="M10 34H18M10 58H18M14 34V58" style="stroke:#F0F0EE;stroke-width:2.4"/>`+
 `<path class="l" style="fill:none" d="M11.5 34H16.5M11.5 58H16.5"/><path class="l2" d="M14 36V56"/>`+
 `<path class="ray" d="M15 36L${SX-SW/2} ${G-SH*.18}M15 56L${SX-SW/2} ${G}M15 46L${SX-SW/2+4} ${G}"/>`+
 `<rect class="dash" x="${SX-SW/2}" y="${G-SH}" width="${SW}" height="${SH}"/>`+
 arrowH(SX-SW/2,SX+SW/2,G+8)+arrowV(SX+SW/2+9,G-SH,G)+
 `<path class="acc" d="M${SX-4} ${G-SH/2}H${SX+4}M${SX} ${G-SH/2-4}V${G-SH/2+4}"/>`;
// 02 PROPOSAL: the form constructed on a sheet: two circles, their overlap is the work
const sh=(x,y,w,h)=>`<path class="l" d="M${x} ${y}H${x+w-10}L${x+w} ${y+10}V${y+h}H${x}Z"/><path class="l2" d="M${x+w-10} ${y}V${y+10}H${x+w}"/>`;
const c2=vesicaCircles(CX,78,40,18);
const s2=ground+sh(28,14,64,80)+c2.map(([x,y,r])=>`<circle class="gd" cx="${f(x)}" cy="${f(y)}" r="${f(r)}"/>`).join('')+
 `<path class="accf" d="${vesica(CX,78,40,18)}"/><path class="l" style="fill:none" d="${vesica(CX,78,40,18)}"/>`+
 `<path class="gd" d="M${CX} 26V86"/>`;
// 03 REVIEW: the drawing reviewed: sheet with lines, small form, approval mark
const s3=ground+sh(24,12,58,84)+
 `<path class="l2" d="M32 26H62M32 32H70M32 38H56"/>`+
 `<path class="l" style="fill:none" d="${vesica(44,82,30,13)}"/><path class="l2" d="M36 82H52"/>`+
 `<path class="l2" d="M58 52H74M58 58H70M58 64H74M58 70H66"/>`+
 `<circle class="acc" cx="84" cy="80" r="13"/><path class="acc" d="M77.5 80.5L82 85L90.5 75.5"/>`;
// 04 FABRICATION: half built. A spine and ribs (with their joints) give the shape; the skin is closed
// from the bottom up to about half the height, the rest of the form is still only its outline.
const s4=(()=>{const H=64,W=30, yb=G-14, yt=yb-H, R=(W*W/4+H*H/4)/W, yc=yb-H/2, d=R-W/2;
  const hw=y=>Math.max(0,Math.sqrt(R*R-(y-yc)*(y-yc))-d);
  const cut=yb-H*.5;
  let ribs='',nodes='';
  for(let i=1;i<6;i++){const y=yt+H*i/6, w=hw(y);
    ribs+=`<path class="rib" d="M${f(CX-w)} ${f(y)}H${f(CX+w)}"/>`;
    nodes+=`<circle class="node" cx="${f(CX-w)}" cy="${f(y)}" r="1.5"/><circle class="node" cx="${f(CX+w)}" cy="${f(y)}" r="1.5"/>`;}
  const ves=vesica(CX,yb,H,W);
  return ground+`<defs><clipPath id="skin4"><rect x="0" y="${f(cut)}" width="120" height="120"/></clipPath></defs>`+
   `<path class="accf" clip-path="url(#skin4)" d="${ves}"/>`+
   `<path class="dash" d="${ves}"/>`+
   `<path class="l" style="fill:none" clip-path="url(#skin4)" d="${ves}"/>`+
   `<path class="spine" d="M${CX} ${f(yt)}V${f(yb)}"/>`+ribs+nodes+
   `<path class="acc" d="M${f(CX-hw(cut)-7)} ${f(cut)}H${f(CX-hw(cut)-2)}M${f(CX+hw(cut)+2)} ${f(cut)}H${f(CX+hw(cut)+7)}"/>`+
   `<path class="l" d="M26 ${G-14}H94"/><path class="l" style="fill:none" d="M32 ${G-14}V${G}M88 ${G-14}V${G}"/>`;})();
// 05 INSTALLATION: lowered onto its plinth from a hook, on the centre line
const lift=20;
const s5=ground+`<path class="gd" d="M${CX} 4V${G}"/>`+
 `<path class="l" style="fill:none" d="M${CX} 4V${YB-V.h-lift-9}"/><circle class="l" style="fill:none" cx="${CX}" cy="${YB-V.h-lift-6.5}" r="2.5"/><path class="l" style="fill:none" d="M${CX} ${YB-V.h-lift-4}V${YB-V.h-lift}"/>`+
 `<path class="l" d="${vesica(CX,YB-lift,V.h,V.w)}"/>`+plinth(CX)+
 `<path class="acc" d="M${CX+18} ${YB-lift-14}V${YB-6}M${CX+14} ${YB-10}L${CX+18} ${YB-6}L${CX+22} ${YB-10}"/>`;
// 06 IN PLACE: standing, its guide circle faint behind it
const s6=ground+`<circle class="gd" cx="${CX}" cy="${YB-V.h/2}" r="34"/>`+
 `<path class="accf" d="${vesica(CX+3,YB,V.h,V.w)}"/>`+`<path class="l" d="${vesica(CX,YB,V.h,V.w)}"/>`+plinth(CX);
const css=`.l{fill:#F0F0EE;stroke:#1C1A20;stroke-width:1.3;stroke-linejoin:round;stroke-linecap:round}
.l2{fill:none;stroke:#1C1A20;stroke-width:.7;stroke-linecap:round}
.g{fill:none;stroke:#1C1A20;stroke-width:1.1}
.b{fill:none;stroke:#9A97A2;stroke-width:.8}
.gd{fill:none;stroke:#9A97A2;stroke-width:.6;stroke-dasharray:2 2}
.dash{fill:none;stroke:#1C1A20;stroke-width:1;stroke-dasharray:3 2.4}
.dim{fill:none;stroke:#6C6A71;stroke-width:.7}
.acc{fill:none;stroke:#7D7889;stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round}
.ray{fill:none;stroke:#7D7889;stroke-width:.7;stroke-dasharray:1.6 2;stroke-linecap:round}
.rib{fill:none;stroke:#1C1A20;stroke-width:.8}
.spine{fill:none;stroke:#1C1A20;stroke-width:1.1}
.node{fill:#F0F0EE;stroke:#1C1A20;stroke-width:.6}
.accf{fill:#7D7889;fill-opacity:.3;stroke:none}`;
const svg=b=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 116" width="240" height="232"><style>${css}</style>${b}</svg>`;
const S=[['01',s1],['02',s2],['03',s3],['04',s4],['05',s5],['06',s6]];
fs.mkdirSync(OUT,{recursive:true});
S.forEach(([n,b])=>fs.writeFileSync(path.join(OUT,`process-${n}.svg`),svg(b)+'\n'));
console.log('wrote process-01..06.svg');
