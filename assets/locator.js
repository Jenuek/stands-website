/* Case study location diagram: a quiet, fixed map with the site (black), the nearest station(s) (hollow) and a dashed straight line with its length */
(function () {
  if (!window.maplibregl) return;
  [].forEach.call(document.querySelectorAll('.locator'), function (fig) {
    var el = fig.querySelector('.locator-map');
    var d = JSON.parse(fig.querySelector('.locator-data').textContent);
    var ko = d.lang !== 'en';
    function km(a, b) {
      var R = 6371, r = Math.PI / 180, dl = (b[1] - a[1]) * r, dp = (b[0] - a[0]) * r;
      var h = Math.sin(dp / 2) * Math.sin(dp / 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dl / 2) * Math.sin(dl / 2);
      return 2 * R * Math.asin(Math.sqrt(h));
    }
    var b = new maplibregl.LngLatBounds([d.lng, d.lat], [d.lng, d.lat]);
    d.stations.forEach(function (s) { b.extend([s.lng, s.lat]); });
    var map = new maplibregl.Map({ container: el, style: 'https://tiles.openfreemap.org/styles/positron', bounds: b,
      fitBoundsOptions: { padding: { top: 70, bottom: 70, left: 90, right: 90 }, maxZoom: 15 }, interactive: false,
      attributionControl: { compact: true } });
    map.on('load', function () {
      map.getStyle().layers.forEach(function (l) {
        if (l.type === 'symbol' && map.getLayoutProperty(l.id, 'text-field')) {
          map.setLayoutProperty(l.id, 'text-field', ko ? ['coalesce', ['get', 'name:ko'], ['get', 'name']] : ['coalesce', ['get', 'name:latin'], ['get', 'name_en'], ['get', 'name']]);
        }
        if (/shield|poi|airport/.test(l.id)) map.setLayoutProperty(l.id, 'visibility', 'none');
      });
      var lines = d.stations.map(function (s) {
        return { type: 'Feature', geometry: { type: 'LineString', coordinates: [[d.lng, d.lat], [s.lng, s.lat]] },
          properties: { t: d.km.replace('{d}', km([d.lat, d.lng], [s.lat, s.lng]).toFixed(1)) } };
      });
      var pts = [{ type: 'Feature', geometry: { type: 'Point', coordinates: [d.lng, d.lat] }, properties: { k: 'site', t: d.label } }].concat(
        d.stations.map(function (s) { return { type: 'Feature', geometry: { type: 'Point', coordinates: [s.lng, s.lat] }, properties: { k: 'st', t: s.name } }; }));
      map.addSource('l', { type: 'geojson', data: { type: 'FeatureCollection', features: lines } });
      map.addSource('p', { type: 'geojson', data: { type: 'FeatureCollection', features: pts } });
      map.addLayer({ id: 'l', type: 'line', source: 'l', paint: { 'line-color': '#000', 'line-width': 1.4, 'line-dasharray': [3, 3] } });
      map.addLayer({ id: 'l-t', type: 'symbol', source: 'l', layout: { 'symbol-placement': 'line-center', 'text-field': ['get', 't'], 'text-font': ['Noto Sans Regular'], 'text-size': 12, 'text-offset': [0, -0.9] },
        paint: { 'text-color': '#000', 'text-halo-color': '#F0F0EE', 'text-halo-width': 2 } });
      map.addLayer({ id: 'st', type: 'circle', source: 'p', filter: ['==', ['get', 'k'], 'st'], paint: { 'circle-radius': 6, 'circle-color': '#F0F0EE', 'circle-stroke-color': '#000', 'circle-stroke-width': 2 } });
      map.addLayer({ id: 'site', type: 'circle', source: 'p', filter: ['==', ['get', 'k'], 'site'], paint: { 'circle-radius': 9, 'circle-color': '#000', 'circle-stroke-color': '#F0F0EE', 'circle-stroke-width': 3 } });
      map.addLayer({ id: 'p-t', type: 'symbol', source: 'p', layout: { 'text-field': ['get', 't'], 'text-font': ['Noto Sans Bold'], 'text-size': 13, 'text-offset': [0, 1.4], 'text-anchor': 'top', 'text-max-width': 14 },
        paint: { 'text-color': '#000', 'text-halo-color': '#F0F0EE', 'text-halo-width': 2 } });
    });
  });
})();
