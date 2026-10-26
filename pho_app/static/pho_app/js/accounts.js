(() => {
  const meta = document.querySelector('meta[name="account-generation"]');
  if (!meta) return;
  const generation = meta.content;
  const bind = form => {
    if ((form.method || '').toLowerCase() !== 'post') return;
    let input = form.querySelector('[name="account_generation"]');
    if (!input) { input = document.createElement('input'); input.type = 'hidden'; input.name = 'account_generation'; form.append(input); }
    input.value = generation;
  };
  document.querySelectorAll('form').forEach(bind);
  document.addEventListener('submit', event => bind(event.target), true);
  const channel = 'BroadcastChannel' in window ? new BroadcastChannel('pho-account-context') : null;
  const announce = { generation, at: Date.now() };
  channel?.postMessage(announce);
  let warned = false;
  function changed(value) {
    if (!value || String(value.generation) === generation || warned) return;
    warned = true;
    document.querySelectorAll('form button[type="submit"]').forEach(button => button.disabled = true);
    const banner = document.createElement('div'); banner.className = 'flash flash-warning account-stale';
    banner.setAttribute('role', 'alert'); banner.append('Tài khoản đã thay đổi ở tab khác. ');
    const link = document.createElement('a'); link.href = location.pathname; link.textContent = 'Tải lại trang'; banner.append(link);
    document.body.prepend(banner);
  }
  if (channel) channel.onmessage = event => changed(event.data);
  document.addEventListener('visibilitychange', async () => {
    if (document.hidden || !generation) return;
    try { const response = await fetch(meta.dataset.contextUrl, { cache: 'no-store' }); if (response.ok) changed(await response.json()); else if (response.status === 409) changed({ generation: 'stale' }); } catch (_) { /* Server still checks generation on every mutation. */ }
  });
  document.querySelectorAll('[data-avatar-input]').forEach(input => input.addEventListener('change', () => {
    const file = input.files[0], preview = document.querySelector('[data-avatar-preview]');
    input.setCustomValidity('');
    if (!preview) return;
    if (!('originalSrc' in preview.dataset)) preview.dataset.originalSrc = preview.getAttribute('src') || '';
    if (!file) {
      if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
      if (preview.dataset.originalSrc) preview.src = preview.dataset.originalSrc; else preview.removeAttribute('src');
      preview.hidden = !preview.dataset.originalSrc;
      const fallback = preview.parentElement.querySelector('.avatar'); if (fallback) fallback.hidden = !preview.hidden;
      return;
    }
    if (file.size > 5000000 || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      input.setCustomValidity('Chọn ảnh JPG, PNG, WEBP tối đa 5 MB.'); input.reportValidity(); return;
    }
    input.setCustomValidity('');
    if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
    const url = URL.createObjectURL(file); preview.src = url; preview.hidden = false; preview.dataset.objectUrl = url;
    const fallback = preview.parentElement.querySelector('.avatar'); if (fallback) fallback.hidden = true;
  }));
  document.querySelector('[data-address-locate]')?.addEventListener('click', event => {
    const button = event.currentTarget;
    if (!navigator.geolocation) return;
    button.disabled = true;
    navigator.geolocation.getCurrentPosition(position => {
      document.querySelector('[name="latitude"]').value = position.coords.latitude.toFixed(7);
      document.querySelector('[name="longitude"]').value = position.coords.longitude.toFixed(7); button.disabled = false;
    }, () => { button.disabled = false; window.phoToast?.('Chưa lấy được tọa độ. Bạn có thể nhập tọa độ địa chỉ nhận món.'); }, { timeout: 15000 });
  });
})();
