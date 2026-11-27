/* Case study site analysis map: the site (black), the nearest station(s) with a dashed straight line and its length,
   and switchable analysis layers drawn from the OpenFreeMap tiles: green and water, road hierarchy, transit, buildings.
   The site facts sit in a card over the map (CSS). */
(function () {
  if (!window.maplibregl) return;
  [].forEach.call(document.querySelectorAll('.locator'), function (fig) {
    var el = fig.querySelector('.locator-map');
    var d = JSON.parse(fig.querySelector('.locator-data').textContent);
    var ko = d.lang !== 'en';
    var wide = window.matchMedia('(min-width: 861px)').matches;
    function km(a, b) {
      var R = 6371, r = Math.PI / 180, dl = (b[1] - a[1]) * r, dp = (b[0] - a[0]) * r;
      var h = Math.sin(dp / 2) * Math.sin(dp / 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dl / 2) * Math.sin(dl / 2);
      return 2 * R * Math.asin(Math.sqrt(h));
    }
    var b = new maplibregl.LngLatBounds([d.lng, d.lat], [d.lng, d.lat]);
    d.stations.forEach(function (s) { b.extend([s.lng, s.lat]); });
    // keep the site clear of the facts card on the left of wide screens
    var pad = wide ? { top: 90, bottom: 80, left: 420, right: 90 } : { top: 100, bottom: 70, left: 90, right: 90 };
    var map = new maplibregl.Map({ container: el, style: 'https://tiles.openfreemap.org/styles/positron', bounds: b,
      fitBoundsOptions: { padding: pad, maxZoom: 15.5 }, cooperativeGestures: true, attributionControl: { compact: true } });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

    var GREEN = ['grass', 'wood', 'forest', 'farmland', 'wetland', 'meadow', 'scrub', 'park', 'garden'];
    var groups = {
      green: ['an-green', 'an-park', 'an-water', 'an-waterway'],
      roads: ['an-road-major', 'an-road-mid', 'an-road-minor', 'an-path'],
      transit: ['an-rail', 'an-bus'],
      buildings: ['an-building']
    };

    map.on('load', function () {
      map.getStyle().layers.forEach(function (l) {
        if (l.type === 'symbol' && map.getLayoutProperty(l.id, 'text-field')) {
          map.setLayoutProperty(l.id, 'text-field', ko ? ['coalesce', ['get', 'name:ko'], ['get', 'name']] : ['coalesce', ['get', 'name:latin'], ['get', 'name_en'], ['get', 'name']]);
        }
        if (/shield|poi|airport/.test(l.id)) map.setLayoutProperty(l.id, 'visibility', 'none');
      });
      var src = 'openmaptiles';
      // analysis layers, below the labels
      var before = map.getStyle().layers.filter(function (l) { return l.type === 'symbol'; })[0].id;
      map.addLayer({ id: 'an-green', type: 'fill', source: src, 'source-layer': 'landcover', filter: ['in', ['get', 'class'], ['literal', GREEN]],
        paint: { 'fill-color': '#9DB38F', 'fill-opacity': 0.55 } }, before);
      map.addLayer({ id: 'an-park', type: 'fill', source: src, 'source-layer': 'park', paint: { 'fill-color': '#9DB38F', 'fill-opacity': 0.45 } }, before);
      map.addLayer({ id: 'an-water', type: 'fill', source: src, 'source-layer': 'water', paint: { 'fill-color': '#8FCAD8', 'fill-opacity': 0.9 } }, before);
      map.addLayer({ id: 'an-waterway', type: 'line', source: src, 'source-layer': 'waterway', paint: { 'line-color': '#5FA7B8', 'line-width': 2.5 } }, before);
      map.addLayer({ id: 'an-building', type: 'fill', source: src, 'source-layer': 'building', paint: { 'fill-color': '#000', 'fill-opacity': 0.85 } }, before);
      map.addLayer({ id: 'an-path', type: 'line', source: src, 'source-layer': 'transportation', filter: ['in', ['get', 'class'], ['literal', ['path', 'pedestrian', 'footway']]],
        paint: { 'line-color': '#6C6A71', 'line-width': 1.4, 'line-dasharray': [2, 2] } }, before);
      map.addLayer({ id: 'an-road-minor', type: 'line', source: src, 'source-layer': 'transportation', filter: ['in', ['get', 'class'], ['literal', ['minor', 'service']]],
        paint: { 'line-color': '#000', 'line-width': 0.8 } }, before);
      map.addLayer({ id: 'an-road-mid', type: 'line', source: src, 'source-layer': 'transportation', filter: ['in', ['get', 'class'], ['literal', ['secondary', 'tertiary']]],
        paint: { 'line-color': '#000', 'line-width': 2 } }, before);
      map.addLayer({ id: 'an-road-major', type: 'line', source: src, 'source-layer': 'transportation', filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary']]],
        paint: { 'line-color': '#000', 'line-width': 4 } }, before);
      map.addLayer({ id: 'an-rail', type: 'line', source: src, 'source-layer': 'transportation', filter: ['in', ['get', 'class'], ['literal', ['rail', 'transit']]],
        paint: { 'line-color': '#7D7889', 'line-width': 3, 'line-dasharray': [3, 2] } }, before);
      map.addLayer({ id: 'an-bus', type: 'circle', source: src, 'source-layer': 'poi', filter: ['==', ['get', 'class'], 'bus'], minzoom: 13,
        paint: { 'circle-radius': 3.5, 'circle-color': '#F0F0EE', 'circle-stroke-color': '#000', 'circle-stroke-width': 1.5 } });

      // site and stations
      var lines = d.stations.map(function (s) {
        return { type: 'Feature', geometry: { type: 'LineString', coordinates: [[d.lng, d.lat], [s.lng, s.lat]] },
          properties: { t: d.km.replace('{d}', km([d.lat, d.lng], [s.lat, s.lng]).toFixed(1)) } };
      });
      var pts = [{ type: 'Feature', geometry: { type: 'Point', coordinates: [d.lng, d.lat] }, properties: { k: 'site', t: d.label } }].concat(
        d.stations.map(function (s) { return { type: 'Feature', geometry: { type: 'Point', coordinates: [s.lng, s.lat] }, properties: { k: 'st', t: s.name } }; }));
      map.addSource('l', { type: 'geojson', data: { type: 'FeatureCollection', features: lines } });
      map.addSource('p', { type: 'geojson', data: { type: 'FeatureCollection', features: pts } });
      map.addLayer({ id: 'l', type: 'line', source: 'l', paint: { 'line-color': '#7D7889', 'line-width': 2, 'line-dasharray': [3, 2] } });
      map.addLayer({ id: 'l-t', type: 'symbol', source: 'l', layout: { 'symbol-placement': 'line-center', 'text-field': ['get', 't'], 'text-font': ['Noto Sans Bold'], 'text-size': 12, 'text-offset': [0, -0.9] },
        paint: { 'text-color': '#000', 'text-halo-color': '#F0F0EE', 'text-halo-width': 2 } });
      map.addLayer({ id: 'st', type: 'circle', source: 'p', filter: ['==', ['get', 'k'], 'st'], paint: { 'circle-radius': 7, 'circle-color': '#F0F0EE', 'circle-stroke-color': '#000', 'circle-stroke-width': 2.5 } });
      map.addLayer({ id: 'site-halo', type: 'circle', source: 'p', filter: ['==', ['get', 'k'], 'site'], paint: { 'circle-radius': 22, 'circle-color': '#7D7889', 'circle-opacity': 0.18, 'circle-stroke-color': '#7D7889', 'circle-stroke-width': 1.5 } });
      map.addLayer({ id: 'site', type: 'circle', source: 'p', filter: ['==', ['get', 'k'], 'site'], paint: { 'circle-radius': 8, 'circle-color': '#000', 'circle-stroke-color': '#F0F0EE', 'circle-stroke-width': 3 } });
      map.addLayer({ id: 'p-t', type: 'symbol', source: 'p', layout: { 'text-field': ['get', 't'], 'text-font': ['Noto Sans Bold'], 'text-size': 13, 'text-offset': [0, 1.6], 'text-anchor': 'top', 'text-max-width': 14 },
        paint: { 'text-color': '#000', 'text-halo-color': '#F0F0EE', 'text-halo-width': 2 } });

      // layer chips
      [].forEach.call(fig.querySelectorAll('[data-layer]'), function (btn) {
        function apply() {
          var on = btn.getAttribute('aria-pressed') === 'true';
          groups[btn.dataset.layer].forEach(function (id) { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none'); });
        }
        apply();
        btn.addEventListener('click', function () {
          btn.setAttribute('aria-pressed', btn.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
          apply();
          if (window.gtag) gtag('event', 'map_layer', { layer: btn.dataset.layer });
        });
      });
    });
  });
})();
