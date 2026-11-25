/* Projects map (MapLibre GL, OpenFreeMap tiles): list beside the map, clustered pins, summary card per pin */
(function () {
  var el = document.getElementById('pmap');
  if (!el || !window.maplibregl) return;
  var data = JSON.parse(document.getElementById('pmap-data').textContent);
  var t = JSON.parse(document.getElementById('pmap-i18n').textContent);
  var ko = t.lang !== 'en';
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var list = document.querySelector('.pmap-list');
  var visibleNote = document.querySelector('.pmap-visible');
  var filter = 'all';
  var popup = null;

  function esc(s) { return String(s || '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function shown() { return data.filter(function (d) { return filter === 'all' || d.group === filter; }); }
  function geo(items) {
    return { type: 'FeatureCollection', features: items.map(function (d) {
      return { type: 'Feature', geometry: { type: 'Point', coordinates: [d.lng, d.lat] },
        properties: { id: d.id, case: d.case ? 1 : 0, label: d.case ? d.title : '' } };
    }) };
  }
  // a case study is named by its building, other entries by the work
  function head(d) { return d.case ? d.title : (d.work || d.title); }
  function track(name, p) { if (window.gtag) gtag('event', name, p || {}); }

  var map = new maplibregl.Map({
    container: el,
    style: 'https://tiles.openfreemap.org/styles/positron',
    bounds: bounds(data), fitBoundsOptions: { padding: 60, maxZoom: 13 },
    attributionControl: { compact: true },
    cooperativeGestures: true,
    localIdeographFontFamily: '"Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif'
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

  function bounds(items) {
    var b = new maplibregl.LngLatBounds();
    items.forEach(function (d) { b.extend([d.lng, d.lat]); });
    return b;
  }

  map.on('load', function () {
    // quieter base: grey everything, Korean place names on the Korean site
    map.getStyle().layers.forEach(function (l) {
      if (l.type === 'symbol' && map.getLayoutProperty(l.id, 'text-field')) {
        map.setLayoutProperty(l.id, 'text-field', ko ? ['coalesce', ['get', 'name:ko'], ['get', 'name']] : ['coalesce', ['get', 'name:latin'], ['get', 'name_en'], ['get', 'name']]);
      }
      if (/shield|poi|airport/.test(l.id)) map.setLayoutProperty(l.id, 'visibility', 'none');
    });
    map.addSource('p', { type: 'geojson', data: geo(shown()), cluster: true, clusterRadius: 44, clusterMaxZoom: 12 });
    map.addLayer({ id: 'cl', type: 'circle', source: 'p', filter: ['has', 'point_count'],
      paint: { 'circle-color': '#000', 'circle-radius': ['step', ['get', 'point_count'], 17, 5, 21, 20, 26], 'circle-stroke-width': 3, 'circle-stroke-color': '#F0F0EE' } });
    map.addLayer({ id: 'cl-n', type: 'symbol', source: 'p', filter: ['has', 'point_count'],
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': ['Noto Sans Bold'], 'text-size': 13, 'text-allow-overlap': true },
      paint: { 'text-color': '#F0F0EE' } });
    map.addLayer({ id: 'pt', type: 'circle', source: 'p', filter: ['!', ['has', 'point_count']],
      paint: { 'circle-color': ['case', ['==', ['get', 'case'], 1], '#000', '#7D7889'],
        'circle-radius': ['case', ['==', ['get', 'case'], 1], 9, 7], 'circle-stroke-width': 2.5, 'circle-stroke-color': '#F0F0EE' } });
    map.addLayer({ id: 'pt-label', type: 'symbol', source: 'p', filter: ['all', ['!', ['has', 'point_count']], ['==', ['get', 'case'], 1]],
      layout: { 'text-field': ['get', 'label'], 'text-font': ['Noto Sans Bold'], 'text-size': 12, 'text-offset': [0, 1.3], 'text-anchor': 'top', 'text-max-width': 12 },
      paint: { 'text-color': '#000', 'text-halo-color': '#F0F0EE', 'text-halo-width': 1.6 } });

    map.on('click', 'cl', function (e) {
      var f = e.features[0];
      map.getSource('p').getClusterExpansionZoom(f.properties.cluster_id).then(function (z) {
        map[reduce ? 'jumpTo' : 'easeTo']({ center: f.geometry.coordinates, zoom: z });
      });
    });
    map.on('click', 'pt', function (e) { open(e.features[0].properties.id, false); });
    ['cl', 'pt'].forEach(function (id) {
      map.on('mouseenter', id, function () { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', id, function () { map.getCanvas().style.cursor = ''; });
    });
    renderList();
  });

  function card(d) {
    var rows = [[t.work, d.case ? d.work : ''], [t.artist, d.artist], [t.year, d.year], [t.type, d.type], [t.scope, d.scope]].filter(function (r) { return r[1]; });
    return '<div class="pmap-card">' + (d.img ? '<img src="' + esc(d.img) + '" alt="">' : '') +
      '<div class="pmap-card-txt">' + (d.case ? '<span class="case-label">' + esc(t.case) + '</span>' : '') +
      '<h3>' + esc(head(d)) + '</h3><span class="meta">' + esc(d.location) + '</span>' +
      '<dl>' + rows.map(function (r) { return '<dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd>'; }).join('') + '</dl>' +
      (d.url ? '<a class="more" href="' + esc(d.url) + '">' + esc(t.view) + '</a>' : '') + '</div></div>';
  }

  function open(id, fly) {
    var d = data.filter(function (x) { return x.id === id; })[0];
    if (!d) return;
    if (popup) popup.remove();
    popup = new maplibregl.Popup({ offset: 14, maxWidth: '300px', closeButton: true, focusAfterOpen: false }).setLngLat([d.lng, d.lat]).setHTML(card(d)).addTo(map);
    // keep the pin in the upper part of the map so the card below it fits
    map[reduce ? 'jumpTo' : (fly ? 'flyTo' : 'easeTo')]({ center: [d.lng, d.lat], zoom: fly ? Math.max(map.getZoom(), 14) : map.getZoom(), offset: [0, -Math.min(170, el.clientHeight * 0.3)] });
    // the page itself never jumps; only on phones, where the list sits under the map and the map is out of view, scroll back up to it
    var r = el.getBoundingClientRect();
    if (fly && list.getBoundingClientRect().top >= r.bottom - 1 && r.top < -40) window.scrollBy({ top: r.top - 16, behavior: reduce ? 'auto' : 'smooth' });
    [].forEach.call(list.children, function (li) {
      var on = li.dataset.id === id;
      li.classList.toggle('on', on);
      // scroll inside the list only (scrollIntoView would move the whole page too)
      if (on && !fly) {
        var top = li.offsetTop - list.offsetTop, bot = top + li.offsetHeight;
        if (top < list.scrollTop || bot > list.scrollTop + list.clientHeight) list.scrollTo({ top: top - 8, behavior: reduce ? 'auto' : 'smooth' });
      }
    });
    track('map_pin_click', { project: id });
  }

  function renderList() {
    // the whole (filtered) list stays put; moving or zooming the map never hides entries
    var items = shown();
    items.sort(function (a, c) { return (c.case - a.case) || (c.year > a.year ? 1 : -1); });
    list.innerHTML = items.map(function (d) {
      return '<li data-id="' + esc(d.id) + '"><button type="button">' + (d.img ? '<img src="' + esc(d.img) + '" alt="" loading="lazy">' : '<span class="ph"></span>') +
        '<span class="txt">' + (d.case ? '<span class="case-label">' + esc(t.case) + '</span>' : '<span class="meta">' + esc(d.groupLabel) + '</span>') +
        '<b>' + esc(head(d)) + '</b><span class="meta">' + esc([d.location, d.artist, d.year].filter(Boolean).join(' · ')) + '</span></span></button></li>';
    }).join('');
    visibleNote.textContent = t.count.replace('{n}', items.length);
    [].forEach.call(list.querySelectorAll('li'), function (li) {
      li.querySelector('button').addEventListener('click', function () { open(li.dataset.id, true); });
    });
  }

  [].forEach.call(document.querySelectorAll('[data-mfilter]'), function (b) {
    b.addEventListener('click', function () {
      filter = b.dataset.mfilter;
      [].forEach.call(document.querySelectorAll('[data-mfilter]'), function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      if (popup) popup.remove();
      var src = map.getSource('p');
      if (src) src.setData(geo(shown()));
      var s = shown();
      if (s.length) map.fitBounds(bounds(s), { padding: 60, maxZoom: 13, animate: !reduce });
      renderList();
      track('map_filter', { group: filter });
    });
  });
})();
