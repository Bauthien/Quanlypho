/* Customer menu, customization dialog, persistent cart and existing Django endpoints. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const readJSON = (id) => JSON.parse(document.getElementById(id).textContent);
  const config = readJSON('menu-config');
  const menuItems = readJSON('menu-data');
  const customizationOptions = readJSON('customization-data');
  const toppings = readJSON('topping-data');
  const CART_KEY = `pho-order-cart-v1-${config.userId || 'guest'}`;
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const money = (value) => new Intl.NumberFormat('vi-VN').format(Number(value)) + 'đ';
  const icon = (name) => `<svg class="icon" width="20" height="20" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
  const normalize = (value) => String(value).toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  const category = (item) => item.category === 'drink' ? 'drink' : 'pho';
  const fallbackImage = (item) => {
    const name = normalize(item.name);
    const filename = category(item) === 'drink' ? 'nuoc-uong.jpg' : name.includes('dac biet') ? 'pho-dac-biet.jpg' : name.includes('nam') ? 'pho-nam.jpg' : 'pho-tai.jpg';
    return config.imageBase + filename;
  };
  const image = (item) => item.image || fallbackImage(item);
  const grid = $('#menuGrid'), cartDialog = $('#cartSidebar'), customDialog = $('#customizeDialog');
  const form = $('#checkoutForm'), orderType = $('#orderType'), payment = $('#paymentMethod');
  const tableSelect = $('#tableSelect'), address = $('#deliveryAddress');
  let cart = [], activeCategory = 'all', customItem = null, customQuantity = 1;
  let remainingCapacity = config.remainingCapacity, queueStatus = config.queueStatus;
  let deliveryAllowed = true, feeRequest = 0;
  try {
    const saved = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    if (Array.isArray(saved)) cart = saved.filter((entry) => entry && menuItems.some((item) => item.id === entry.id) && Number.isInteger(entry.qty) && entry.qty > 0 && Array.isArray(entry.customizations) && Array.isArray(entry.toppings)).map((entry) => ({ ...entry, qty: Math.min(99, entry.qty) }));
  } catch (_) { cart = []; }
  function save() { try { localStorage.setItem(CART_KEY, JSON.stringify(cart)); } catch (_) { window.phoToast?.('Giỏ hàng được giữ trong phiên này; trình duyệt đang tắt lưu trữ.'); } }
  const product = (entry) => menuItems.find((item) => item.id === entry.id);
  const linePrice = (entry) => Number(product(entry)?.price || 0) + entry.toppings.reduce((total, id) => total + Number(toppings.find((topping) => topping.id === id)?.price || 0), 0);

  function renderMenu() {
    const query = normalize($('#searchInput').value.trim());
    const items = menuItems.filter((item) => (activeCategory === 'all' || category(item) === activeCategory) && normalize(item.name).includes(query));
    $('#menuResultCount').textContent = `${items.length} món dành cho bạn`;
    grid.innerHTML = items.map((item) => `<article class="food-card" data-menu-id="${item.id}">
      <div class="food-img-wrapper"><img src="${escape(image(item))}" data-image-fallback="${escape(fallbackImage(item))}" width="360" height="240" alt="${escape(item.name)}" loading="lazy"></div>
      <div class="food-info"><span class="eyebrow">${category(item) === 'drink' ? 'MÁT LÀNH, THẢNH THƠI' : 'PHỞ NHÀ · ĐẬM VỊ VIỆT'}</span><h2 class="food-title">${escape(item.name)}</h2><p class="food-desc">${category(item) === 'drink' ? 'Một chút mát lành cho bữa ăn thêm trọn vị.' : 'Nước dùng đậm đà, thịt tươi và rau thơm. Chọn khẩu vị theo cách của bạn.'}</p><div class="food-footer"><span class="food-price">${money(item.price)}</span><button class="add-btn" type="button" data-customize="${item.id}" ${item.is_available === false ? 'disabled' : ''} aria-label="${item.is_available === false ? 'Tạm hết món' : 'Chọn'} ${escape(item.name)}">${icon('plus')} ${item.is_available === false ? 'Tạm hết món' : 'Chọn món'}</button></div></div></article>`).join('') || `<div class="panel empty-state">${icon('search')}<strong>Chưa tìm thấy món phù hợp</strong>Thử tên món khác hoặc chọn tất cả món nhé.</div>`;
  }

  function customPrice() {
    if (!customItem || customItem.is_available === false) return;
    const extra = [...$('#customOptions').querySelectorAll('[data-topping-id]:checked')].reduce((total, input) => total + Number(toppings.find((item) => item.id === Number(input.dataset.toppingId))?.price || 0), 0);
    $('#customTotal').textContent = money((Number(customItem.price) + extra) * customQuantity);
    $('#customQty').textContent = customQuantity;
  }
  function customize(id) {
    customItem = menuItems.find((item) => item.id === id);
    if (!customItem || customItem.is_available === false) return;
    customQuantity = 1;
    $('#customizeTitle').textContent = customItem.name;
    $('#customNote').value = '';
    $('#customError').hidden = true;
    $('#customDishIntro').innerHTML = `<img src="${escape(image(customItem))}" data-image-fallback="${escape(fallbackImage(customItem))}" alt="${escape(customItem.name)}"><div><span class="muted">Một món ngon, đúng khẩu vị</span><strong>${money(customItem.price)}</strong></div>`;
    const isDrink = category(customItem) === 'drink';
    if (isDrink) {
      $('#customOptions').innerHTML = `<div style="padding: 14px 12px; background: var(--blue-soft, #edf3f9); border-radius: 8px; color: var(--blue, #3f6c8e); font-size: 12.5px; margin-bottom: 8px;">🥤 Đồ uống ướp lạnh mát giải khát. Bạn có thể ghi chú thêm yêu cầu phục vụ (ví dụ: dùng kèm ly đá, ít đá...) ở ô bên dưới.</div>`;
    } else {
      const groups = { BROTH: 'Nước dùng', VEGGIE: 'Hành / giá', NOODLE: 'Bánh phở' };
      $('#customOptions').innerHTML = Object.entries(groups).map(([key, label]) => {
        const options = customizationOptions.filter((option) => option.category === key);
        return options.length ? `<fieldset class="choice-group"><legend>${label} <small>· chọn 1</small></legend>${options.map((option, index) => `<label><input type="radio" name="custom-${key}" value="${option.id}" data-category="${key}" ${index === 0 ? 'checked' : ''} required>${escape(option.name)}</label>`).join('')}</fieldset>` : '';
      }).join('') + (toppings.length ? `<fieldset class="choice-group"><legend>Thêm chút topping <small>· không bắt buộc</small></legend>${toppings.map((topping) => `<label><input type="checkbox" data-topping-id="${topping.id}">${escape(topping.name)}<span>+${money(topping.price)}</span></label>`).join('')}</fieldset>` : '');
    }
    customPrice();
    customDialog.showModal();
  }
  grid.addEventListener('click', (event) => { const button = event.target.closest('[data-customize]'); if (button) customize(Number(button.dataset.customize)); });
  $('#customOptions').addEventListener('change', customPrice);
  document.querySelectorAll('[data-custom-qty]').forEach((button) => button.addEventListener('click', () => { customQuantity = Math.min(customItem?.max_quantity ?? 99, Math.max(1, customQuantity + Number(button.dataset.customQty))); customPrice(); }));
  $('[data-close-customize]').addEventListener('click', () => customDialog.close());
  $('#customizeForm').addEventListener('submit', (event) => {
    event.preventDefault();
    if (!customItem) return;
    const alreadyInCart = cart.filter((entry) => entry.id === customItem.id).reduce((total, entry) => total + entry.qty, 0);
    if (customItem.is_available === false || alreadyInCart + customQuantity > (customItem.max_quantity ?? 99)) {
      $('#customError').textContent = 'Món này không còn đủ số lượng. Vui lòng giảm số lượng hoặc chọn món khác.';
      $('#customError').hidden = false;
      return;
    }
    const choices = [...$('#customOptions').querySelectorAll('input[type="radio"]:checked')].map((input) => Number(input.value)).sort((a, b) => a - b);
    const extras = [...$('#customOptions').querySelectorAll('[data-topping-id]:checked')].map((input) => Number(input.dataset.toppingId)).sort((a, b) => a - b);
    const note = $('#customNote').value.trim();
    const variantKey = JSON.stringify([customItem.id, choices, extras, note]);
    const entry = cart.find((item) => item.variantKey === variantKey);
    if (entry) entry.qty = Math.min(99, entry.qty + customQuantity);
    else cart.push({ id: customItem.id, qty: customQuantity, customizations: choices, toppings: extras, note, variantKey });
    save(); renderCart(); customDialog.close();
    window.phoToast?.(`Đã thêm ${customItem.name} vào giỏ hàng.`);
  });

  let quoteTimer, quoteRequest = 0, quoteReady = false;
  const quoteFields = ['checkoutAddressId', 'checkoutWalletId', 'voucherCode', 'checkoutPoints', 'recipientName', 'recipientPhone', 'deliveryAddress', 'orderType', 'paymentMethod'];
  const walletSelect = $('#checkoutWalletId'), codeInput = $('#voucherCode');
  walletSelect?.addEventListener('change', () => { if (walletSelect.value && codeInput) codeInput.value = ''; });
  codeInput?.addEventListener('input', () => { if (codeInput.value && walletSelect) walletSelect.value = ''; });
  $('#checkoutAddressId')?.addEventListener('change', () => {
    const option = $('#checkoutAddressId').selectedOptions[0];
    $('#checkoutAddressVersion').value = option.dataset.version || '';
    if (option.value) {
      $('#recipientName').value = option.dataset.name;
      $('#recipientPhone').value = option.dataset.phone;
      address.value = option.dataset.address;
      $('#customerLat').value = (option.dataset.lat || '').replace(',', '.');
      $('#customerLng').value = (option.dataset.lng || '').replace(',', '.');
      quoteFee($('#customerLat').value, $('#customerLng').value);
    } else {
      address.value = ''; $('#customerLat').value = ''; $('#customerLng').value = '';
      quoteFee();
    }
    [address, $('#recipientName'), $('#recipientPhone')].forEach(input => { input.readOnly = Boolean(option.value); });
    $('#locateBtn').disabled = Boolean(option.value);
  });
  quoteFields.forEach(id => $('#' + id)?.addEventListener('input', scheduleQuote));
  function scheduleQuote() {
    quoteReady = false;
    $('#quoteToken').value = '';
    $('#checkoutBtn').disabled = true;
    const number = ++quoteRequest;
    clearTimeout(quoteTimer);
    quoteTimer = setTimeout(() => refreshQuote(number), 250);
  }
  async function refreshQuote(number) {
      if (!cart.length) { $('#serverQuote').textContent = 'Chọn món để xem tổng tiền.'; $('#serverQuote').classList.remove('is-error', 'is-loading'); return; }
    const body = new FormData(form);
    body.set('cart', JSON.stringify(cart.map(({ id, qty, customizations, toppings, note }) => ({ id, qty, customizations, toppings, note }))));
    body.set('account_generation', document.querySelector('meta[name="account-generation"]').content);
    if (orderType.value !== 'DELIVERY') body.delete('address_id');
    try {
        $('#serverQuote').classList.remove('is-error'); $('#serverQuote').classList.add('is-loading');
        $('#serverQuote').setAttribute('aria-busy', 'true');
        $('#serverQuote').textContent = 'Đang tính ưu đãi…';
      const response = await fetch(config.quoteUrl, { method: 'POST', body, headers: { Accept: 'application/json' } });
      const data = await response.json();
      if (number !== quoteRequest) return;
      if (!response.ok || !data.ok) throw new Error(data.error || 'Chưa thể tính báo giá.');
      $('#quoteToken').value = data.token;
      $('#cartTotalAmount').textContent = money(data.payable);
      $('#serverQuote').replaceChildren();
        [['Tiền món', data.subtotal], ['Giảm hạng', -data.tier_discount], ['Voucher món', -data.voucher_discount], ['Phí giao', data.delivery_fee], ['Miễn giao theo hạng', -data.auto_shipping_discount], ['Voucher giao hàng', -data.voucher_shipping_discount], ['Đổi điểm', -data.point_discount]].filter(([, value], index) => index === 0 || Number(value) !== 0).forEach(([label, value]) => {
        const row = document.createElement('p'), span = document.createElement('span'), strong = document.createElement('strong');
          if (value < 0) row.classList.add('is-saving');
        span.textContent = label; strong.textContent = money(value); row.append(span, strong); $('#serverQuote').append(row);
      });
      if ($('#pointLimitHint')) $('#pointLimitHint').textContent = `Đơn này dùng tối đa ${data.max_points} điểm khả dụng.`;
      quoteReady = true;
      const blocked = orderType.value === 'QUEUE_CART' && queueStatus !== 'CALLED';
      const phoCount = cart.reduce((sum, entry) => sum + (category(product(entry)) === 'pho' ? entry.qty : 0), 0);
      $('#checkoutBtn').disabled = blocked || (orderType.value === 'DINE_IN' && phoCount > remainingCapacity);
      $('#checkoutBtn').textContent = blocked ? 'Chờ gọi số để thanh toán' : 'Đặt món ngay';
    } catch (error) {
      if (number !== quoteRequest) return;
      $('#serverQuote').textContent = error.message || 'Mất kết nối. Hãy thử lại.';
        $('#serverQuote').classList.add('is-error');
      $('#checkoutBtn').disabled = true;
      } finally {
        if (number === quoteRequest) { $('#serverQuote').classList.remove('is-loading'); $('#serverQuote').removeAttribute('aria-busy'); }
    }
  }
  function renderCart() {
    const count = cart.reduce((total, entry) => total + entry.qty, 0);
    const phoCount = cart.reduce((total, entry) => {
      const item = product(entry);
      return (item && category(item) === 'pho') ? total + entry.qty : total;
    }, 0);
    const subtotal = cart.reduce((total, entry) => total + linePrice(entry) * entry.qty, 0);
    const fee = orderType.value === 'DELIVERY' ? Number($('#cartTotalAmount').dataset.deliveryFee || 0) : 0;
    const badge = $('#cartBadge');
    if (badge) { badge.textContent = count; badge.setAttribute('aria-label', `${count} món trong giỏ`); }
    $('#cartTotalAmount').textContent = money(subtotal + (count ? fee : 0));
    $('#cartItemsList').innerHTML = cart.map((entry, index) => {
      const item = product(entry);
      const details = [...entry.customizations.map((id) => customizationOptions.find((option) => option.id === id)?.name), ...entry.toppings.map((id) => toppings.find((option) => option.id === id)?.name), entry.note].filter(Boolean).join(' · ');
      return `<div class="cart-item"><img src="${escape(image(item))}" data-image-fallback="${escape(fallbackImage(item))}" alt=""><div><div class="cart-item-name">${escape(item.name)}</div><small>${escape(details)}</small><div class="cart-item-price">${money(linePrice(entry) * entry.qty)}</div></div><div class="qty-controls"><button class="qty-btn" type="button" data-cart-index="${index}" data-delta="-1" aria-label="Giảm số lượng ${escape(item.name)}">−</button><span>${entry.qty}</span><button class="qty-btn" type="button" data-cart-index="${index}" data-delta="1" aria-label="Tăng số lượng ${escape(item.name)}">+</button></div></div>`;
    }).join('') || `<div class="empty-state">${icon('bag')}<strong>Giỏ hàng đang chờ món ngon</strong>Chọn một tô phở yêu thích để bắt đầu nhé.</div>`;
    const waiting = orderType.value === 'QUEUE_CART' && queueStatus !== 'CALLED';
    const full = orderType.value === 'DINE_IN' && remainingCapacity < 999 && phoCount > remainingCapacity;
    const blocked = orderType.value === 'DELIVERY' && !deliveryAllowed;
    const quantities = new Map();
    cart.forEach(entry => quantities.set(entry.id, (quantities.get(entry.id) || 0) + entry.qty));
    const unavailable = cart.find(entry => {
      const item = product(entry);
      return item?.is_available === false || quantities.get(entry.id) > (item?.max_quantity ?? 99);
    });
    $('#checkoutError').hidden = !unavailable;
    $('#checkoutError').textContent = unavailable ? `${product(unavailable).name} không còn đủ số lượng. Vui lòng giảm số lượng hoặc chọn món khác.` : '';
    $('#checkoutBtn').disabled = !count || waiting || full || blocked || Boolean(unavailable);
    $('#checkoutBtn').textContent = unavailable ? 'Món trong giỏ không còn đủ' : waiting ? 'Chờ gọi số để thanh toán' : full ? `Bàn chỉ còn ${remainingCapacity} tô phở` : blocked ? 'Ngoài phạm vi giao hàng' : 'Đặt món ngay';
    scheduleQuote();
  }
  $('#cartItemsList').addEventListener('click', (event) => {
    const button = event.target.closest('[data-cart-index]');
    if (!button) return;
    const entry = cart[Number(button.dataset.cartIndex)];
    entry.qty = Math.min(99, entry.qty + Number(button.dataset.delta));
    cart = cart.filter((item) => item.qty > 0);
    save(); renderCart();
  });
  function openCart() { if (!cartDialog.open) cartDialog.showModal(); }
  $('#openCartBtn')?.addEventListener('click', openCart);
  $('#closeCartBtn').addEventListener('click', () => cartDialog.close());
  [cartDialog, customDialog].forEach((dialog) => dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  }));
  $('#searchInput').addEventListener('input', renderMenu);
  document.querySelectorAll('[data-category]').forEach((button) => {
    if (!button.matches('button')) return;
    button.addEventListener('click', () => {
      activeCategory = button.dataset.category;
      document.querySelectorAll('.filter-btn').forEach((item) => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', String(item === button)); });
      renderMenu();
    });
  });
  function updateMode() {
    const delivery = orderType.value === 'DELIVERY', queue = orderType.value === 'QUEUE_CART';
    $('#addressField').hidden = !delivery;
    $('#deliveryRecipientFields').hidden = !delivery;
    if ($('#tableField')) $('#tableField').hidden = delivery || queue;
    if (tableSelect) tableSelect.required = false;
    address.required = delivery;
    $('#recipientName').required = delivery;
    $('#recipientPhone').required = delivery;
    if (delivery) payment.value = 'VIETQR';
    payment.disabled = delivery;
    document.querySelectorAll('[data-order-mode]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.orderMode === orderType.value)));
    renderCart();
  }
  document.querySelectorAll('[data-order-mode]').forEach((button) => button.addEventListener('click', () => { orderType.value = button.dataset.orderMode; updateMode(); if (orderType.value === 'DELIVERY') window.phoToast?.('Chọn món trước, sau đó nhập địa chỉ trong giỏ hàng nhé.'); }));
  orderType.addEventListener('change', updateMode);
  if (tableSelect) { tableSelect.addEventListener('change', () => { remainingCapacity = Number(tableSelect.selectedOptions[0]?.dataset.remaining || 999); renderCart(); }); }

  async function quoteFee(lat, lng) {
    const request = ++feeRequest;
    const params = new URLSearchParams();
    if (lat != null && lng != null) { params.set('lat', lat); params.set('lng', lng); }
    try {
      const response = await fetch(`${config.deliveryUrl}?${params}`, { headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('Delivery quote failed');
      const data = await response.json();
      if (request !== feeRequest) return;
      deliveryAllowed = data.ok;
      $('#cartTotalAmount').dataset.deliveryFee = String(data.ok ? data.fee : 0);
      const distanceLabel = Number(data.distance_km) < 1 ? 'dưới 1' : data.distance_km;
      $('#deliveryFeeHint').textContent = !data.ok ? `Ngoài phạm vi giao hàng: ${data.distance_km || '?'} km.` : data.fallback ? `Chưa có GPS · phí tạm tính ${money(data.fee)}.` : `Cách quán ${distanceLabel} km · phí giao ${money(data.fee)}.`;
      renderCart();
    } catch (_) { window.phoToast?.('Chưa lấy được phí giao hàng. Vui lòng thử lại.'); }
  }
  $('#locateBtn').addEventListener('click', () => {
    if (!navigator.geolocation) { quoteFee(); return; }
    $('#locateBtn').disabled = true;
    navigator.geolocation.getCurrentPosition((position) => {
      $('#locateBtn').disabled = false;
      $('#customerLat').value = position.coords.latitude;
      $('#customerLng').value = position.coords.longitude;
      updateMode();
      quoteFee(position.coords.latitude, position.coords.longitude);
    }, () => {
      $('#locateBtn').disabled = false;
      $('#customerLat').value = ''; $('#customerLng').value = '';
      updateMode();
      quoteFee();
    }, { enableHighAccuracy: true, timeout: 8000 });
  });

  async function pollQueue() {
    try {
      const response = await fetch(config.queueUrl, { headers: { Accept: 'application/json' } });
      if (!response.ok) return;
      const data = await response.json();
      if (!data.active) return;
      const calledNow = queueStatus !== 'CALLED' && data.status === 'CALLED';
      queueStatus = data.status;
      if ($('#queueStatusText')) $('#queueStatusText').textContent = `Số ${data.ticket} · ${data.status === 'CALLED' ? 'Đã gọi số' : 'Đang chờ'}`;
      if (data.status === 'CALLED' && data.table) {
        if ($('#queueStatusHelp')) $('#queueStatusHelp').textContent = `Đến lượt bạn! Mời bạn vào Bàn ${data.table} và thanh toán giỏ hàng.`;
        let option = $('option[value="QUEUE_CART"]', orderType);
        if (!option) { option = new Option('Chờ vào bàn', 'QUEUE_CART'); orderType.add(option); }
        option.textContent = `Chờ vào bàn · Bàn ${data.table}`;
        if (calledNow) {
          window.phoToast?.(`Đến lượt bạn! Mời vào Bàn ${data.table}.`);
          navigator.vibrate?.([200, 100, 200]);
        }
      }
      renderCart();
    } catch (_) { /* Preserve the current state during temporary network failures. */ }
  }
  if (config.queueStatus) { pollQueue(); setInterval(() => { if (!document.hidden) pollQueue(); }, 8000); }
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  form.addEventListener('submit', (event) => {
    if (!quoteReady || $('#checkoutBtn').disabled || !cart.length) { event.preventDefault(); return; }
    $('#cartPayload').value = JSON.stringify(cart.map(({ id, qty, customizations, toppings, note }) => ({ id, qty, customizations, toppings, note })));
    payment.disabled = false;
    if (orderType.value !== 'DELIVERY') $('#checkoutAddressId').disabled = true;
    const csrfToken = getCookie('csrftoken');
    const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken && csrfInput) {
      csrfInput.value = csrfToken;
    }
  });
  const incoming = new URLSearchParams(location.search);
  if (incoming.get('mode') === 'delivery') orderType.value = 'DELIVERY';
  const addressId = incoming.get('address');
  if (addressId && [...$('#checkoutAddressId').options].some(option => option.value === addressId)) $('#checkoutAddressId').value = addressId;
  const walletId = incoming.get('wallet');
  if (walletId && walletSelect && [...walletSelect.options].some(option => option.value === walletId)) { walletSelect.value = walletId; if (codeInput) codeInput.value = ''; }
  else if (incoming.get('promo') && codeInput) { codeInput.value = incoming.get('promo').slice(0, 50); if (walletSelect) walletSelect.value = ''; }
  if ($('#checkoutAddressId').value) $('#checkoutAddressId').dispatchEvent(new Event('change'));
  renderMenu(); updateMode();
  document.addEventListener('pho:choose-dish', event => { if (Number.isInteger(event.detail?.id)) { customize(event.detail.id); customQuantity = Math.max(1, Math.min(99, Number(event.detail.quantity) || 1)); customPrice(); } });
  document.addEventListener('pho:open-cart', openCart);
  if (incoming.get('dish')) customize(Number(incoming.get('dish')));
})();
