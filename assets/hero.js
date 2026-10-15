// STANDS home hero — "WHERE ART ____" sequence (15s), plays once and rests on the box logo.
(function(){
  const hero=document.getElementById('hero'); if(!hero) return;
  const $=id=>document.getElementById(id);
  const bg=$('bg'), bgimg=$('bgimg'), tag=$('tag'), line=$('line'), wa=$('wa'), word=$('word'), bar=$('ubar'), obj=$('obj'),
        lockup=$('lockup'), frame=$('frame'), lbar=$('lbar'), replay=$('replay');
  const DUR=15000, ACCENT='#7D7889';

  const IW=1376, IH=768;
  const places=[
    {k:'RESIDENCE',ko:'컬렉터 거실',src:'img/living.jpg',h:.60},
    {k:'GALLERY',ko:'갤러리',src:'img/gallery.jpg',h:.69},
    {k:'STORAGE',ko:'수장고',src:'img/storage.jpg',h:.635},
    {k:'LOBBY',ko:'로비',src:'img/lobby.jpg',h:.645},
    {k:'COMPLEX',ko:'단지 광장',src:'img/apartment.jpg',h:.58},
    {k:'PLAZA',ko:'도심 광장',src:'img/plaza.jpg',h:.47},
    {k:'RIVERSIDE',ko:'한강변',src:'img/river.jpg',h:.585,dark:true},
    {k:'FOREST',ko:'숲',src:'img/forest.jpg',h:.585,dark:true},
  ];
  const ready=Promise.all(places.map(p=>{const i=new Image(); i.src=p.src; return i.decode().catch(()=>{});}));

  // placeholder sculptures, standing on y=100
  const A=ACCENT, S='#6E6B66', K='#111111', P='#D9D7D2';
  const shapes=[
    `<path d="M18 100V46a32 32 0 0 1 64 0v54H66V48a16 16 0 0 0-32 0v52z" fill="${K}"/>`,
    `<ellipse cx="50" cy="90" rx="30" ry="10" fill="${S}"/><ellipse cx="52" cy="72" rx="22" ry="9" fill="${S}"/><ellipse cx="48" cy="57" rx="15" ry="7" fill="${S}"/><ellipse cx="51" cy="45" rx="9" ry="5" fill="${S}"/>`,
    `<rect x="30" y="62" width="40" height="38" fill="${P}"/><circle cx="50" cy="43" r="19" fill="${A}"/>`,
    `<rect x="42" y="-30" width="16" height="130" fill="${K}"/>`,
    `<circle cx="50" cy="44" r="30" fill="none" stroke="${A}" stroke-width="12"/><rect x="40" y="72" width="20" height="28" fill="${A}"/>`,
    `<polygon points="50,100 82,60 50,20 18,60" fill="${S}"/>`,
    `<ellipse cx="50" cy="96" rx="20" ry="4" fill="${K}"/><rect x="46" y="20" width="8" height="76" fill="${K}"/><ellipse cx="50" cy="14" rx="6" ry="8" fill="${K}"/>`,
    `<rect x="22" y="40" width="22" height="60" fill="${A}" transform="rotate(-8 33 100)"/><rect x="54" y="20" width="22" height="80" fill="${K}" transform="rotate(6 65 100)"/>`,
  ];
    // on night scenes, dark sculptures turn light so they stay visible
  const lighten=svg=>svg.split('#111111').join('#F0F0EE').split('#6E6B66').join('#D3D1CC');
  const sizes=['H 3,200','H 1,450','H 2,100','H 6,000','H 2,800','H 1,800','H 2,400','H 3,600'];

  const cuts=[]; {let t=1800,d=900,i=0; while(t<9000){cuts.push({t,i}); t+=d; d=Math.max(170,d*.86); i++;}}
  const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v)), prog=(t,a,b)=>clamp((t-a)/(b-a));
  const easeOut=x=>1-Math.pow(1-x,3), easeInOut=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;

  let cur=null;
  function placeBg(p){
    const W=hero.clientWidth,H=hero.clientHeight,hr=hero.getBoundingClientRect(),br=bar.getBoundingClientRect();
    const target=(br.top-hr.top)||H*.55, s=Math.max(W/IW,H/IH)*1.12, w=IW*s, h=IH*s;
    let top=target-p.h*h; top=Math.min(0,Math.max(H-h,top));
    Object.assign(bgimg.style,{width:w+'px',height:h+'px',left:((W-w)/2)+'px',top:top+'px'});
  }
  new ResizeObserver(()=>{ if(cur) placeBg(cur); }).observe(hero);

  let lastCut=-2;
  function render(t){
    wa.style.opacity=easeOut(prog(t,250,900));
    bar.style.transform=`scaleX(${easeInOut(prog(t,500,1200))})`;
    bar.style.opacity=(t>=9000&&t<10300)?((Math.floor((t-9000)/420)%2===0)?1:.15):1;
    bar.style.background=t>=10300?ACCENT:'currentColor';

    let idx=-1;
    if(t>=1800&&t<9000){ for(let k=cuts.length-1;k>=0;k--){ if(t>=cuts[k].t){idx=k;break;} } }
    if(idx!==lastCut){
      if(idx>=0){
        const n=places.length,last=cuts.length-1,c=cuts[idx];
        const pi=c.i<n?c.i:(((c.i-last+n-1)%n)+n)%n, p=places[pi];
        cur=p; bgimg.src=p.src; bgimg.hidden=false; bg.classList.remove('plain'); placeBg(p); hero.classList.toggle('dark',!!p.dark);
        obj.innerHTML=`<svg viewBox="0 -30 100 130" preserveAspectRatio="xMidYMax meet" aria-hidden="true">${p.dark ? lighten(shapes[c.i%shapes.length]) : shapes[c.i%shapes.length]}</svg>`;
        tag.textContent=`No.${String(c.i+1).padStart(3,'0')} · ${p.k} ${p.ko} · ${sizes[c.i%sizes.length]}`;
      } else { cur=null; bgimg.hidden=true; bg.classList.add('plain'); hero.classList.remove('dark'); obj.innerHTML=''; tag.textContent=''; }
      lastCut=idx;
    }
    if(idx>=0){ const dt=t-cuts[idx].t; obj.style.transform=`translateX(-50%) translateY(${(1-easeOut(clamp(dt/140)))*-6}%)`; }

    hero.classList.toggle('inv',t>=9000&&t<11100);
    word.style.visibility=t>=10300?'visible':'hidden';

    line.style.opacity=1-easeInOut(prog(t,12000,12450));
    lockup.style.opacity=easeInOut(prog(t,12150,12650));
    const fp=easeInOut(prog(t,12150,13150));
    frame.setAttribute('stroke-dashoffset',String(1000*(1-fp)));
    frame.setAttribute('stroke-dasharray',fp>=1?'none':'1000');
    lbar.setAttribute('width',String(312*easeOut(prog(t,12900,13400))));
    hero.classList.toggle('done',t>=DUR);
  }

  let t=0, playing=false, prev=null;
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  function loop(now){
    if(playing){ if(prev!=null){ t+=now-prev; if(t>=DUR){t=DUR; playing=false;} } prev=now; }
    render(t); requestAnimationFrame(loop);
  }
  if(reduce) t=DUR;
  render(t); requestAnimationFrame(loop);
  ready.then(()=>{ if(!reduce){ playing=true; prev=null; } });
  replay.addEventListener('click',()=>{ t=0; lastCut=-2; prev=null; playing=true; });
})();
