/* Shared Phở Nhà interactions. No framework or build step is required. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  function fallbackImage(element) {
    if (!(element instanceof HTMLImageElement)) return;
    if (element.hasAttribute('data-qr-image')) {
      element.hidden = true;
      const warning = element.closest('[data-qr-state]')?.querySelector('[data-qr-error]');
      if (warning) warning.hidden = false;
      return;
    }
    if (!element.dataset.imageFallback) return;
    const fallback = element.dataset.imageFallback;
    delete element.dataset.imageFallback;
    element.src = fallback;
  }
  document.addEventListener('error', (event) => fallbackImage(event.target), true);
  document.querySelectorAll('img[data-image-fallback], img[data-qr-image]').forEach((element) => {
    if (element.complete && element.naturalWidth === 0) fallbackImage(element);
  });
  let toastTimer;
  window.phoToast = (message) => {
    const toast = $('#uiToast');
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 4000);
  };
  document.querySelectorAll('[data-copy-text]').forEach((button) => button.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(button.dataset.copyText); window.phoToast('Đã sao chép liên kết dành cho khách.'); }
    catch (_) { window.phoToast('Trình duyệt chưa cho phép sao chép. Vui lòng thử lại trên localhost hoặc HTTPS.'); }
  }));

  const sidebar = $('#workspace-sidebar');
  const opener = $('[data-open-sidebar]');
  const scrim = $('.sidebar-scrim');
  const mobile = matchMedia('(max-width: 1023px)');
  function setSidebar(open) {
    if (!sidebar) return;
    document.body.classList.toggle('sidebar-open', open);
    if (scrim) scrim.hidden = !open;
    opener?.setAttribute('aria-expanded', String(open));
    sidebar.inert = mobile.matches && !open;
    if (open) $('a,button', sidebar)?.focus();
    else if (mobile.matches && document.activeElement && sidebar.contains(document.activeElement)) opener?.focus();
  }
  opener?.addEventListener('click', () => setSidebar(true));
  document.querySelectorAll('[data-close-sidebar]').forEach((button) => button.addEventListener('click', () => setSidebar(false)));
  sidebar?.addEventListener('click', (event) => { if (event.target.closest('a') && mobile.matches) setSidebar(false); });
  mobile.addEventListener('change', () => setSidebar(false));
  setSidebar(false);
  document.addEventListener('keydown', (event) => {
    if (!document.body.classList.contains('sidebar-open')) return;
    if (event.key === 'Escape') setSidebar(false);
    if (event.key === 'Tab') {
      const controls = [...sidebar.querySelectorAll('a,button')].filter((el) => el.getClientRects().length && !el.disabled);
      const first = controls[0], last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });

  document.querySelectorAll('[data-dismiss-message]').forEach((button) => button.addEventListener('click', () => button.closest('.flash')?.remove()));
  document.querySelectorAll('[data-password-toggle]').forEach((button) => button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.passwordToggle);
    if (!input) return;
    const visible = input.type === 'password';
    input.type = visible ? 'text' : 'password';
    button.textContent = visible ? 'Ẩn' : 'Hiện';
    button.setAttribute('aria-pressed', String(visible));
  }));

  document.querySelectorAll('[data-money]').forEach((element) => {
    const value = Number(element.dataset.money);
    if (Number.isFinite(value)) element.textContent = new Intl.NumberFormat('vi-VN').format(value) + 'đ';
  });

  document.querySelectorAll('[data-filter-root]').forEach((root) => {
    const input = $('[data-filter-search]', root);
    const buttons = [...root.querySelectorAll('[data-filter-group]')];
    const cards = [...root.querySelectorAll('[data-filter-item]')];
    const requested = new URLSearchParams(location.search).get('category');
    let category = buttons.some(button => button.dataset.filterGroup === requested) ? requested : 'all';
    const normalize = (value) => value.toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
    function applyFilter() {
      const query = normalize(input?.value || '').trim().replace(/\s+/g, ' ');
      buttons.forEach(button => {
        const active = button.dataset.filterGroup === category;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      let count = 0;
      cards.forEach((card) => {
        const visible = (category === 'all' || card.dataset.filterCategory === category)
          && normalize(card.dataset.filterItem).includes(query);
        card.hidden = !visible;
        if (visible) count++;
      });
      const result = $('[data-filter-count]', root);
      if (result) result.textContent = `${count} món`;
      const empty = $('[data-filter-empty]', root);
      if (empty) empty.hidden = count !== 0;
      root.querySelectorAll('[data-catalog-delete] [name="category"]').forEach(field => { field.value = category; });
    }
    input?.addEventListener('input', applyFilter);
    buttons.forEach(button => button.addEventListener('click', () => {
      category = button.dataset.filterGroup;
      const url = new URL(location.href);
      if (category === 'all') url.searchParams.delete('category');
      else url.searchParams.set('category', category);
      history.replaceState(null, '', url);
      applyFilter();
    }));
    applyFilter();
  });

  document.querySelectorAll('[data-catalog-delete]').forEach(form => form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm)) {
      event.preventDefault();
      return;
    }
    form.querySelector('button[type="submit"]').disabled = true;
  }));
  window.addEventListener('pageshow', () => {
    document.querySelectorAll('[data-catalog-delete] button').forEach(button => { button.disabled = false; });
  });

  const chartData = $('#revenue-chart-data');
  if (chartData) {
    const data = JSON.parse(chartData.textContent);
    const chart = $('#revenueChart');
    const width = 600, height = 170, pad = 14;
    const max = Math.max(...data.map((day) => day.total), 1);
    const points = data.map((day, index) => [pad + index * (width - pad * 2) / Math.max(data.length - 1, 1), height - pad - (day.total / max) * (height - pad * 2)]);
    const path = points.map(([x, y], index) => `${index ? 'L' : 'M'} ${x} ${y}`).join(' ');
    const svgNS = 'http://www.w3.org/2000/svg';
    function add(tag, attributes) { const node = document.createElementNS(svgNS, tag); Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value)); chart.append(node); return node; }
    chart.setAttribute('viewBox', `0 0 ${width} ${height}`);
    [0, .25, .5, .75, 1].forEach((ratio) => add('line', { x1: pad, x2: width - pad, y1: pad + ratio * (height - 2 * pad), y2: pad + ratio * (height - 2 * pad), stroke: '#eeece7', 'stroke-dasharray': '4 5' }));
    if (points.length) {
      add('path', { d: `${path} L ${points.at(-1)[0]} ${height - pad} L ${pad} ${height - pad} Z`, fill: '#9b3b2f0c' });
      add('path', { d: path, fill: 'none', stroke: '#9b3b2f', 'stroke-width': 2.5, 'stroke-linejoin': 'round' });
      points.forEach(([x, y], index) => { const point = add('circle', { cx: x, cy: y, r: 4, fill: '#9b3b2f', stroke: '#fff', 'stroke-width': 2 }); const title = document.createElementNS(svgNS, 'title'); title.textContent = `${data[index].label}: ${new Intl.NumberFormat('vi-VN').format(data[index].total)}đ`; point.append(title); });
    }
  }
})();
