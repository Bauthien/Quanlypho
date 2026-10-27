/* A shared, explicit destination picker. GPS never stands in for an address. */
(() => {
  'use strict';
  let leafletPromise;
  function loadLeaflet() {
    if (window.L) return Promise.resolve(window.L);
    if (leafletPromise) return leafletPromise;
    const load = (tag, url, integrity) => new Promise((resolve, reject) => {
      const element = document.createElement(tag);
      if (tag === 'link') { element.rel = 'stylesheet'; element.href = url; } else element.src = url;
      element.integrity = integrity; element.crossOrigin = '';
      const timer = setTimeout(() => { element.remove(); reject(new Error('map-timeout')); }, 15000);
      element.onload = () => { clearTimeout(timer); resolve(); };
      element.onerror = () => { clearTimeout(timer); element.remove(); reject(new Error('map-unavailable')); };
      document.head.append(element);
    });
    leafletPromise = Promise.all([
      load('link', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='),
      load('script', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='),
    ]).then(() => window.L).catch(error => { leafletPromise = null; throw error; });
    return leafletPromise;
  }
  const number = value => value.trim() === '' ? NaN : Number(value.trim().replace(',', '.'));
  const valid = (lat, lng) => Number.isFinite(lat) && Number.isFinite(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
  const money = value => Number(value).toLocaleString('vi-VN') + 'đ';
  document.querySelectorAll('[data-location-picker]').forEach(root => {
    const $ = selector => root.querySelector(selector);
    const lat = $('[data-location-lat]'), lng = $('[data-location-lng]');
    const gps = $('[data-location-gps]'), toggle = $('[data-location-map-toggle]'), canvas = $('[data-location-map]');
    const status = $('[data-location-status]'), fee = $('[data-location-fee]'), preview = $('[data-location-preview]');
    const shop = [Number(root.dataset.shopLat), Number(root.dataset.shopLng)];
    let serial = 0, gpsSerial = 0, locked = false, timer, map, marker, controller;
    function coords() { const a = number(lat.value), b = number(lng.value); return valid(a, b) ? [a, b] : null; }
    function message(text, error = false) { status.textContent = text; status.classList.toggle('field-error', error); }
    function emit(detail) { root.dispatchEvent(new CustomEvent('locationchange', {bubbles: true, detail})); }
    function updateMarker() {
      if (!map) return;
      const point = coords();
      if (!point) { if (marker) { marker.remove(); marker = null; } return; }
      if (!marker) {
        marker = window.L.marker(point, {draggable: !locked, title: 'Vị trí nhận món',
          icon: window.L.divIcon({className: 'location-pin', iconSize: [20, 20], iconAnchor: [10, 10]})}).addTo(map);
        marker.on('dragend', () => { const point = marker.getLatLng().wrap(); setCoordinates(point.lat, point.lng); });
      } else marker.setLatLng(point);
      if (locked) marker.dragging.disable(); else marker.dragging.enable();
      map.setView(point, Math.max(15, map.getZoom()));
    }
    async function check() {
      clearTimeout(timer); controller?.abort();
      const current = ++serial, point = coords();
      fee.removeAttribute('aria-busy');
      const bothEmpty = !lat.value.trim() && !lng.value.trim();
      const error = point || bothEmpty ? '' : 'Nhập đủ vĩ độ từ −90 đến 90 và kinh độ từ −180 đến 180.';
      lat.setCustomValidity(error); lng.setCustomValidity(error);
      preview.hidden = !point;
      updateMarker();
      if (!point) {
        fee.textContent = 'Chưa thể tính phí: chọn điểm nhận món bằng GPS, bản đồ hoặc nhập tọa độ.';
        if (error) message(error, true); else message('Chưa chọn vị trí nhận món.');
        emit({coords: null, allowed: false, fee: 0}); return;
      }
      if (status.textContent.startsWith('Đang nhập tọa độ')) message('Đã chọn tọa độ nhận món. Kiểm tra đúng địa chỉ trước khi đặt.');
      preview.href = 'https://www.google.com/maps/search/?' + new URLSearchParams({api: '1', query: point.join(',')});
      fee.textContent = 'Đang kiểm tra khoảng cách và phí giao…';
      fee.setAttribute('aria-busy', 'true');
      emit({coords: point, allowed: false, pending: true});
      const requestController = new AbortController();
      controller = requestController;
      const timeout = setTimeout(() => requestController.abort(), 12000);
      try {
        const url = new URL(root.dataset.feeUrl, location.origin);
        url.searchParams.set('lat', point[0]); url.searchParams.set('lng', point[1]);
        const response = await fetch(url, {headers: {Accept: 'application/json'}, signal: requestController.signal, cache: 'no-store'});
        const data = await response.json();
        if (current !== serial) return;
        if (!response.ok || !data.ok) throw new Error(data.error || data.message || 'Chưa kiểm tra được vị trí.');
        fee.textContent = `Cách quán ${Number(data.distance_km).toLocaleString('vi-VN', {maximumFractionDigits: 3})} km (đường thẳng) · phí giao ${money(data.fee)}.`;
        emit({coords: point, allowed: true, fee: data.fee, distance: data.distance_km});
      } catch (error) {
        if (current !== serial) return;
        fee.textContent = error.name === 'AbortError' ? 'Kết nối kiểm tra phí giao bị gián đoạn. Chọn lại vị trí hoặc thử lại.' : (error.message || 'Chưa kiểm tra được phí giao. Vui lòng thử lại.');
        emit({coords: point, allowed: false, fee: 0});
      } finally { clearTimeout(timeout); if (current === serial) fee.removeAttribute('aria-busy'); }
    }
    function stopGPS() { ++gpsSerial; gps.disabled = locked; gps.removeAttribute('aria-busy'); }
    function setCoordinates(a, b, {notify = true} = {}) {
      stopGPS(); clearTimeout(timer);
      lat.value = valid(Number(a), Number(b)) && a !== '' && b !== '' && a != null && b != null ? Number(a).toFixed(7) : '';
      lng.value = lat.value ? Number(b).toFixed(7) : '';
      message(lat.value ? 'Đã chọn vị trí nhận món. Kiểm tra ghim và địa chỉ trước khi đặt.' : 'Chưa chọn vị trí nhận món.');
      if (notify) check(); else updateMarker();
    }
    [lat, lng].forEach(input => input.addEventListener('input', () => {
      stopGPS(); controller?.abort(); ++serial; clearTimeout(timer);
      message('Đang nhập tọa độ nhận món…'); emit({coords: null, allowed: false, pending: true});
      timer = setTimeout(check, 300);
    }));
    gps.addEventListener('click', () => {
      if (!window.isSecureContext) { message('GPS cần HTTPS hoặc localhost. Bạn vẫn có thể chọn bản đồ hoặc nhập tọa độ.', true); return; }
      if (!navigator.geolocation) { message('Trình duyệt không hỗ trợ GPS. Chọn trên bản đồ hoặc nhập tọa độ.', true); return; }
      const current = ++gpsSerial;
      gps.disabled = true; gps.setAttribute('aria-busy', 'true'); message('Đang lấy vị trí hiện tại…');
      navigator.geolocation.getCurrentPosition(position => {
        if (current !== gpsSerial || locked) return;
        setCoordinates(position.coords.latitude, position.coords.longitude);
        message(`Đã lấy GPS · sai số khoảng ${Math.round(position.coords.accuracy)} m. Kiểm tra đây là nơi nhận món.`);
      }, error => {
        if (current !== gpsSerial) return;
        stopGPS();
        const reason = {1: 'Bạn chưa cho phép truy cập vị trí. Bật quyền vị trí trong trình duyệt hoặc', 2: 'Thiết bị chưa xác định được vị trí. Hãy', 3: 'Lấy vị trí quá thời gian chờ. Thử lại hoặc'}[error.code] || 'Chưa lấy được vị trí. Hãy';
        message(`${reason} chọn trên bản đồ / nhập tọa độ bên dưới.`, true);
      }, {enableHighAccuracy: true, timeout: 12000, maximumAge: 0});
    });
    toggle.addEventListener('click', async () => {
      canvas.hidden = !canvas.hidden;
      toggle.setAttribute('aria-expanded', String(!canvas.hidden));
      $('[data-location-map-help]').hidden = canvas.hidden;
      if (canvas.hidden) return;
      toggle.disabled = true;
      try {
        const L = await loadLeaflet();
        if (!map) {
          map = L.map(canvas, {scrollWheelZoom: false}).setView(coords() || shop, coords() ? 15 : 13);
          L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(map);
          L.circle(shop, {radius: Number(root.dataset.maxKm) * 1000, color: '#287354', fillOpacity: 0.04, weight: 1, interactive: false}).addTo(map);
          L.circleMarker(shop, {radius: 6, color: '#287354', fillOpacity: 1}).addTo(map).bindTooltip('Phở Nhà');
          map.on('click', event => { if (!locked) { const point = event.latlng.wrap(); setCoordinates(point.lat, point.lng); } });
          canvas.addEventListener('keydown', event => {
            if (event.key === 'Enter' && !locked) { event.preventDefault(); const point = map.getCenter().wrap(); setCoordinates(point.lat, point.lng); }
          });
        }
        map.invalidateSize(); updateMarker();
      } catch (_) { canvas.hidden = true; $('[data-location-map-help]').hidden = true; toggle.setAttribute('aria-expanded', 'false'); message('Chưa tải được bản đồ. Bạn vẫn có thể dùng GPS hoặc nhập tọa độ.', true); }
      finally { toggle.disabled = false; }
    });
    root.locationPicker = {
      setCoordinates,
      clear(text) { setCoordinates(null, null); if (text) message(text); },
      setLocked(value) { locked = Boolean(value); stopGPS(); lat.readOnly = locked; lng.readOnly = locked; updateMarker(); },
      check,
    };
    $('[data-location-retry]').addEventListener('click', check);
    root.closest('form')?.addEventListener('submit', () => {
      const point = coords();
      if (point) { lat.value = point[0].toFixed(7); lng.value = point[1].toFixed(7); }
    });
    check();
  });
})();
