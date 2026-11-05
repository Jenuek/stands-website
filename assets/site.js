// STANDS — shared behaviour: mobile menu, project filters, draft contact form.
(function(){
  const menu=document.getElementById('mobile-nav'), open=document.getElementById('menu-open'), close=document.getElementById('menu-close');
  if(menu&&open&&close){
    open.addEventListener('click',()=>{ menu.hidden=false; document.body.style.overflow='hidden'; close.focus(); });
    close.addEventListener('click',()=>{ menu.hidden=true; document.body.style.overflow=''; open.focus(); });
    document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&!menu.hidden) close.click(); });
  }

  // home statement photo: the reveal follows the scroll position (it rises as you scroll down and
  // lowers again as you scroll back), and the image drifts a little slower than the page
  // (also used for the About photo)
  const revs=[...document.querySelectorAll('.statement-img,.about-img')];
  if(revs.length&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
    document.documentElement.classList.add('js');
    let raf=0;
    const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
    const update=()=>{ raf=0; const vh=innerHeight;
      revs.forEach(el=>{ const r=el.getBoundingClientRect(), im=el.querySelector('img');
        // 0 when the top of the photo reaches the bottom of the screen, 1 when 60% of the screen further.
        const p=clamp((vh-r.top)/(vh*.6),0,1), e=1-Math.pow(1-p,2);
        el.style.setProperty('--reveal',((1-e)*100).toFixed(2)+'%');
        const k=clamp(((r.top+r.height/2)-vh/2)/(vh/2+r.height/2),-1,1);
        im.style.setProperty('--drift',(k*r.height*.025).toFixed(1)+'px'); }); };
    addEventListener('scroll',()=>{ if(!raf) raf=requestAnimationFrame(update); },{passive:true});
    addEventListener('resize',update); update();
  }

  // header logo: the third line keeps changing. STANDS, then places from the hero and now and then a verb,
  // each wiped out right to left and revealed left to right like the hero underbar; the bar follows the word.
  const lw=document.querySelector('.brand svg');
  if(lw&&lw.querySelector('.lw-line')&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
    const clip=lw.querySelector('.lw-clip'), base=lw.querySelector('.lw-base'), word=lw.querySelector('.lw-word'), bar=lw.querySelector('.lw-bar');
    const X0=30, FULL=340, BAR0=+bar.getAttribute('width'), MAXW=322;
    const SEQ=['STANDS','GALLERY','PLAZA','BELONGS','STANDS','GARDEN','COAST','BREATHES','STANDS','MUSEUM','FOREST','REMAINS',
               'STANDS','ATRIUM','PARK','LIVES','STANDS','LOFT','TERRACE','MEETS'];
    const HOLD_STANDS=2600, HOLD=1300, OUT=300, IN=420, GAP=80;
    const ease=x=>x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;
    let i=0, timer=0, raf=0, barW=BAR0;
    const tween=(ms,fn)=>new Promise(res=>{const t0=performance.now();const step=now=>{const k=Math.min(1,(now-t0)/ms);fn(ease(k));if(k<1) raf=requestAnimationFrame(step); else res();};raf=requestAnimationFrame(step);});
    const setWord=w=>{ if(w==='STANDS'){ base.style.display=''; word.style.display='none'; return BAR0; }
      base.style.display='none'; word.style.display=''; word.textContent=w; word.removeAttribute('textLength'); word.removeAttribute('lengthAdjust');
      let wd=word.getComputedTextLength(); if(wd>MAXW){ word.setAttribute('textLength',MAXW); word.setAttribute('lengthAdjust','spacingAndGlyphs'); wd=MAXW; }
      return Math.max(60,wd-4); };
    const next=async()=>{ if(document.hidden){ timer=setTimeout(next,600); return; }
      // wipe out, right to left
      await tween(OUT,k=>{ clip.setAttribute('x',X0); clip.setAttribute('width',FULL*(1-k)); });
      await new Promise(r=>setTimeout(r,GAP));
      i=(i+1)%SEQ.length; const w=SEQ[i], from=barW, to=setWord(w);
      // reveal, left to right; the bar grows or shrinks to the new word
      await tween(IN,k=>{ clip.setAttribute('x',X0); clip.setAttribute('width',FULL*k); bar.setAttribute('width',(from+(to-from)*k).toFixed(2)); });
      barW=to; timer=setTimeout(next,w==='STANDS'?HOLD_STANDS:HOLD); };
    (document.fonts?document.fonts.ready:Promise.resolve()).then(()=>{ timer=setTimeout(next,HOLD_STANDS); });
  }

  // project filters
  const chips=document.querySelectorAll('[data-filter]');
  chips.forEach(ch=>ch.addEventListener('click',()=>{
    const f=ch.dataset.filter;
    chips.forEach(c=>c.setAttribute('aria-pressed',String(c===ch)));
    document.querySelectorAll('[data-type]').forEach(card=>{ card.hidden = !(f==='all' || card.dataset.type===f); });
  }));

  // contact form (draft: nothing is sent)
  const form=document.getElementById('contact-form');
  if(form){
    form.addEventListener('submit',e=>{
      e.preventDefault();
      const n=document.getElementById('form-note');
      n.hidden=false;
      n.textContent=document.documentElement.lang==='en'?'This is a draft site, so inquiries are not sent yet. Email delivery will be connected before launch.':'초안 사이트라 문의가 전송되지 않습니다. 오픈 전에 메일 연동을 연결할 예정입니다.';
    });
  }
})();

// ---------- analytics events (GA4) ----------
// Every link/button click is sent as `ui_click` with its label, destination and page section, so reports can show
// what people click and where. Key actions also get their own event names for quick counting.
(function(){
  const send=(name,params)=>{ if(typeof window.gtag==='function') window.gtag('event',name,params); };
  const sectionOf=el=>{
    const s=el.closest('section,header,footer,nav,.mobile-nav');
    if(!s) return 'page';
    return s.getAttribute('aria-label')||s.id||s.className.split(' ')[0]||s.tagName.toLowerCase();
  };
  document.addEventListener('click',e=>{
    const el=e.target.closest('a,button,[data-filter]');
    if(!el) return;
    const label=(el.getAttribute('aria-label')||el.textContent||'').replace(/\s+/g,' ').trim().slice(0,80);
    const href=el.getAttribute('href')||'';
    const params={link_text:label, link_url:href, section:sectionOf(el), page_path:location.pathname};
    send('ui_click',params);
    if(href.includes('contact.html')) send('cta_contact_click',params);
    if(el.dataset.lang) send('language_switch',{language:el.dataset.lang, page_path:location.pathname});
    else if(el.closest('.nav,.mobile-nav')) send('nav_click',params);
    if(el.classList.contains('card')) send('project_click',params);
    if(el.classList.contains('artist')) send('artist_click',params);
    if(el.classList.contains('ed-feature')||el.closest('.list')) send('editorial_click',params);
    if(el.dataset.filter) send('project_filter',{filter:el.dataset.filter});
  },{capture:true});

  // scroll depth: 25 / 50 / 75 / 100 %
  const marks=[25,50,75,100], hit=new Set();
  const onScroll=()=>{
    const h=document.documentElement, max=h.scrollHeight-h.clientHeight;
    const pct=max>0?Math.round((h.scrollTop||document.body.scrollTop)/max*100):100;
    marks.forEach(m=>{ if(pct>=m&&!hit.has(m)){ hit.add(m); send('scroll_depth',{percent:m, page_path:location.pathname}); } });
  };
  window.addEventListener('scroll',onScroll,{passive:true});

  // contact form submit attempt
  const form=document.getElementById('contact-form');
  if(form) form.addEventListener('submit',()=>send('contact_form_submit',{page_path:location.pathname}));
  window.__standsSend=send;
})();
