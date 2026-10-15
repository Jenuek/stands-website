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
