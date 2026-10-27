// STANDS — shared behaviour: mobile menu, project filters, draft contact form.
(function(){
  const menu=document.getElementById('mobile-nav'), open=document.getElementById('menu-open'), close=document.getElementById('menu-close');
  if(menu&&open&&close){
    open.addEventListener('click',()=>{ menu.hidden=false; document.body.style.overflow='hidden'; close.focus(); });
    close.addEventListener('click',()=>{ menu.hidden=true; document.body.style.overflow=''; open.focus(); });
    document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&!menu.hidden) close.click(); });
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
      n.textContent='초안 사이트라 문의가 전송되지 않습니다. 오픈 전에 메일 연동을 연결할 예정입니다.';
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
    if(el.closest('.nav,.mobile-nav')) send('nav_click',params);
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
