/* Update the kitchen without interrupting a focused form or overlapping requests. */
(() => {
  async function poll() {
    try {
      if (document.hidden) return;
      const response = await fetch(location.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!response.ok || response.redirected) throw new Error('Session or connection changed');
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const incoming = page.getElementById('kitchenOrders');
      const current = document.getElementById('kitchenOrders');
      if (!incoming || !current) throw new Error('Kitchen content unavailable');
      // CSRF form tokens rotate on each render; compare order text and actions instead.
      const signature = (root) => root.textContent.replace(/\s+/g, ' ').trim() + [...root.querySelectorAll('form')].map((form) => form.getAttribute('action')).join('|');
      if (signature(incoming) !== signature(current) && !current.contains(document.activeElement)) {
        current.replaceChildren(...incoming.childNodes);
        current.querySelector('.kitchen-card')?.classList.add('is-new');
        setTimeout(() => current.querySelector('.is-new')?.classList.remove('is-new'), 2000);
        window.phoToast?.('Danh sách đơn bếp vừa được cập nhật.');
        navigator.vibrate?.([200, 100, 200]);
      }
      document.getElementById('kitchenConnection').textContent = 'Cập nhật mỗi 5 giây';
    } catch (_) {
      document.getElementById('kitchenConnection').textContent = 'Chưa kết nối · đang thử lại';
    } finally { setTimeout(poll, 5000); }
  }
  setTimeout(poll, 5000);
})();
