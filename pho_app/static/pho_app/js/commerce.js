/* UI only: tabs, editors and previews. All totals and permissions stay on the server. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const money = value => new Intl.NumberFormat('vi-VN').format(Number(value || 0)) + 'đ';
  const normalize = value => String(value).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  $$('[data-tabs]').forEach(root => {
    const buttons = $$('[data-tab-target]', root).filter(button => button.closest('[data-tabs]') === root);
    const param = root.dataset.tabParam || 'view';
    const storageKey = `pho-ui-tabs:${location.pathname}:${param}`;
    function activate(button, updateUrl = true, focus = false) {
      if (!button) return;
      buttons.forEach(item => {
        const active = item === button;
        item.setAttribute('aria-selected', String(active)); item.tabIndex = active ? 0 : -1;
        item.classList.toggle('active', active);
        const panel = document.getElementById(item.dataset.tabTarget); if (panel) panel.hidden = !active;
      });
      if (updateUrl) {
        const url = new URL(location.href); url.searchParams.set(param, button.dataset.tabKey || button.dataset.tabTarget); url.hash = '';
        history.replaceState(null, '', url);
      }
      try { sessionStorage.setItem(storageKey, button.dataset.tabKey || button.dataset.tabTarget); } catch (_) {}
      if (focus) button.focus();
      const list = button.closest('[role="tablist"]');
      if (list && list.scrollWidth > list.clientWidth) {
        const itemRect = button.getBoundingClientRect(), listRect = list.getBoundingClientRect();
        if (itemRect.right > listRect.right) list.scrollLeft += itemRect.right - listRect.right + 8;
        else if (itemRect.left < listRect.left) list.scrollLeft -= listRect.left - itemRect.left + 8;
      }
    }
    const url = new URL(location.href);
    let saved = ''; try { saved = sessionStorage.getItem(storageKey); } catch (_) {}
    const legacyWallet = param === 'tab' && url.searchParams.get('member') === 'vouchers' ? 'wallet' : '';
    const key = root.dataset.forceTab || legacyWallet || url.hash.slice(1) || url.searchParams.get(param) || saved;
    activate(buttons.find(button => button.dataset.tabTarget === key || button.dataset.tabKey === key) || buttons.find(button => button.getAttribute('aria-selected') === 'true') || buttons[0], false);
    buttons.forEach((button, index) => {
      button.addEventListener('click', event => { event.preventDefault(); activate(button); });
      button.addEventListener('keydown', event => {
        let next = index;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % buttons.length;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + buttons.length) % buttons.length;
        else if (event.key === 'Home') next = 0; else if (event.key === 'End') next = buttons.length - 1; else return;
        event.preventDefault(); activate(buttons[next], true, true);
      });
    });
  });
  function openEditor(dialog) {
    if (!dialog || dialog.open) return;
    dialog.showModal(); document.body.classList.add('commerce-modal-open');
  }
  document.addEventListener('click', event => {
    const opener = event.target.closest('[data-dialog-open]');
    if (opener) {
      const dialog = document.getElementById(opener.dataset.dialogOpen);
      if (dialog && opener.dataset.importUrl) {
        $('form', dialog).action = opener.dataset.importUrl;
        $('[data-import-name]', dialog).textContent = opener.dataset.ingredientName;
        $('[data-import-unit]', dialog).textContent = opener.dataset.ingredientUnit;
        $('[name="input_unit"]', dialog).value = opener.dataset.ingredientUnit;
        $('[name="quantity"]', dialog).value = '';
      }
      openEditor(dialog);
    }
    const closer = event.target.closest('[data-dialog-close]'); if (closer) closer.closest('dialog').close();
    const copy = event.target.closest('[data-copy]');
    if (copy) navigator.clipboard?.writeText(copy.dataset.copy).then(() => window.phoToast?.('Đã sao chép.')).catch(() => window.phoToast?.('Bạn có thể chọn và sao chép nội dung trực tiếp.'));
  });
  $$('.commerce-dialog').forEach(dialog => {
    dialog.addEventListener('close', () => { if (!$('.commerce-dialog[open]')) document.body.classList.remove('commerce-modal-open'); });
    dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
    if (dialog.dataset.autoOpen === 'true') openEditor(dialog);
  });
  $$('[data-filter-list]').forEach(root => {
    const search = $('[data-list-search]', root), rows = $$('[data-list-record]', root);
    const filters = $$('[data-list-filter]', root), categories = $$('[data-list-category]', root), select = $('[data-list-state]', root);
    let state = select?.value || filters.find(button => button.getAttribute('aria-pressed') === 'true')?.dataset.listFilter || 'all', category = 'all';
    function filter() {
      const term = normalize(search?.value || ''); let count = 0;
      rows.forEach(row => { const visible = (!term || normalize(row.dataset.search || row.textContent).includes(term)) && (state === 'all' || (row.dataset.state || '').split(' ').includes(state)) && (category === 'all' || (row.dataset.category || '').split(' ').includes(category)); row.hidden = !visible; count += visible; });
      const empty = $('[data-list-empty]', root); if (empty) empty.hidden = count > 0;
      const number = $('[data-list-count]', root); if (number) number.textContent = count;
    }
    search?.addEventListener('input', filter);
    filters.forEach(button => button.addEventListener('click', () => { state = button.dataset.listFilter; filters.forEach(item => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', String(item === button)); }); filter(); }));
    categories.forEach(button => button.addEventListener('click', () => { category = button.dataset.listCategory; categories.forEach(item => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', String(item === button)); }); filter(); }));
    select?.addEventListener('change', () => { state = select.value; filter(); });
    filter();
  });
  const addressComparison = $('[data-address-comparison]');
  if (addressComparison) {
    let fee = null, serial = 0;
    $$('[data-preview-address]', addressComparison).forEach(button => button.addEventListener('click', async () => {
      const current = ++serial, error = $('[data-address-error]', addressComparison), use = $('[data-address-use]', addressComparison);
      error.hidden = true; use.hidden = true; button.disabled = true; button.setAttribute('aria-busy', 'true');
      try {
        const url = new URL(addressComparison.dataset.feeUrl, location.origin); url.searchParams.set('address_id', button.dataset.previewAddress);
        const response = await fetch(url, {headers:{Accept:'application/json'},cache:'no-store'}), data = await response.json();
        if (current !== serial) return;
        if (!response.ok || !data.ok) throw new Error(data.error || 'Chưa tính được phí giao. Hãy thử lại.');
        $('[data-address-before]', addressComparison).textContent = fee === null ? 'Chưa có địa chỉ trước' : money(fee);
        $('[data-address-preview-name]', addressComparison).textContent = button.dataset.addressLabel;
        $('[data-address-fee]', addressComparison).textContent = money(data.fee);
        $('[data-address-distance]', addressComparison).textContent = Number(data.distance).toLocaleString('vi-VN', {maximumFractionDigits:3}) + ' km';
        $('[data-address-benefit]', addressComparison).textContent = data.nearby_discount ? 'Miễn phí giao gần' : 'Kiểm tra voucher khi đặt';
        fee = data.fee; use.href = '/thuc-don/?mode=delivery&address=' + encodeURIComponent(button.dataset.previewAddress); use.hidden = false;
      } catch (err) { if (current === serial) { error.textContent = err.message; error.hidden = false; } }
      finally { button.disabled = false; button.removeAttribute('aria-busy'); }
    }));
  }
  const requestForm = $('[data-support-form]');
  if (requestForm) {
    const kind = $('[name="kind"]', requestForm), remedy = $('[name="remedy"]', requestForm), unitGroup = $('[data-support-units]', requestForm);
    function preview() {
      const cancel = kind.value === 'CANCEL';
      unitGroup.hidden = cancel; $('[data-support-cancel-note]', requestForm).hidden = !cancel;
      $('[data-support-remedy]', requestForm).hidden = cancel; if (cancel) remedy.value = 'REFUND';
      const all = $$('[data-unit-cash]', requestForm).filter(input => !input.disabled), checked = all.filter(input => input.checked);
      const selected = cancel || !checked.length ? all : checked;
      $('[data-support-cash]', requestForm).textContent = money(selected.reduce((sum, input) => sum + Number(input.dataset.unitCash), 0));
      $('[data-support-points]', requestForm).textContent = selected.reduce((sum, input) => sum + Number(input.dataset.unitPoints), 0);
      $('[data-support-caption]', requestForm).textContent = remedy.value === 'REPLACE' && !cancel ? 'Phần món được gửi để xét giao bù' : 'Giá trị phần món gửi để xét hoàn';
    }
    requestForm.addEventListener('change', preview); preview();
    requestForm.addEventListener('submit', () => {
      const freeUnits = $$('[data-unit-cash]', requestForm).filter(input => !input.disabled);
      if (kind.value === 'ISSUE' && !freeUnits.some(input => input.checked)) freeUnits.forEach(input => { input.checked = true; });
    });
  }
  $$('[data-recipe-target]').forEach(input => input.addEventListener('change', () => {
    const topping = input.value === 'TOPPING'; const menu = $('#menuItemSelect'), extra = $('#toppingSelect');
    menu.disabled = topping; extra.disabled = !topping; menu.required = !topping; extra.required = topping;
    $('#recipeMenuField').hidden = topping; $('#recipeToppingField').hidden = !topping;
  }));
  const stockForm = $('[data-stock-operation-form]');
  if (stockForm) {
    const mode = $('[name="action"]', stockForm), order = $('[name="order_id"]', stockForm);
    const ingredient = $('[name="ingredient_id"]', stockForm), payload = $('#stock-order-options');
    const data = payload ? JSON.parse(payload.textContent) : {};
    function updateStock() {
      const returning = mode.value === 'return'; order.required = returning;
      $$('option[data-order-state]', order).forEach(option => { option.disabled = returning && option.dataset.orderState !== 'CANCELLED'; option.hidden = option.disabled; });
      if (order.selectedOptions[0]?.disabled) order.value = '';
      const allowed = order.value && data[order.value];
      $$('option', ingredient).forEach(option => { option.disabled = Boolean(allowed) && !allowed.includes(Number(option.value)); option.hidden = option.disabled; });
      if (ingredient.selectedOptions[0]?.disabled) ingredient.value = $$('option', ingredient).find(option => !option.disabled)?.value || '';
      $('[data-stock-mode-help]', stockForm).textContent = returning ? 'Chọn đơn đã hủy và xác nhận với bếp rằng nguyên liệu chưa được sử dụng.' : 'Chọn đơn nếu món đã chế biến. Để trống đơn khi ghi hao hụt nguyên liệu còn trong kho.';
    }
    mode.addEventListener('change', updateStock); order.addEventListener('change', updateStock); updateStock();
  }
  const hashTarget = location.hash && document.getElementById(location.hash.slice(1)); if (hashTarget?.tagName === 'DETAILS') hashTarget.open = true;
  document.addEventListener('submit', event => {
    if (event.target.dataset.confirm && !window.confirm(event.target.dataset.confirm)) { event.preventDefault(); return; }
    const form = event.target; if (!form.matches('.commerce-form, [data-commerce-submit]') || event.defaultPrevented) return;
    if (form.dataset.submitting) { event.preventDefault(); return; }
    form.dataset.submitting = 'true'; form.setAttribute('aria-busy', 'true');
    const button = event.submitter; if (button) button.classList.add('is-submitting');
  });
  window.addEventListener('pageshow', () => $$('.commerce-form,[data-commerce-submit]').forEach(form => { delete form.dataset.submitting; form.removeAttribute('aria-busy'); $$('.is-submitting', form).forEach(button => button.classList.remove('is-submitting')); }));
})();
