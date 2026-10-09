const CART_KEY = 'pho-order-cart-v1';
let cart = [];
try {
    cart = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    if (!Array.isArray(cart)) cart = [];
} catch (_error) {
    cart = [];
}

const menuGrid = document.getElementById('menuGrid');
const cartSidebar = document.getElementById('cartSidebar');
const cartOverlay = document.getElementById('cartOverlay');
const openCartBtn = document.getElementById('openCartBtn');
const closeCartBtn = document.getElementById('closeCartBtn');
const cartItemsList = document.getElementById('cartItemsList');
const cartBadge = document.getElementById('cartBadge');
const cartTotalAmount = document.getElementById('cartTotalAmount');
const checkoutBtn = document.getElementById('checkoutBtn');
const searchInput = document.getElementById('searchInput');
const checkoutForm = document.getElementById('checkoutForm');
const cartPayload = document.getElementById('cartPayload');
const orderType = document.getElementById('orderType');
const paymentMethod = document.getElementById('paymentMethod');
const addressField = document.getElementById('addressField');
const tableField = document.getElementById('tableField');

const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]));
const formatMoney = (value) => `${Number(value).toLocaleString('vi-VN')}đ`;
const categoryLabels = { BROTH: 'Nước dùng', VEGGIE: 'Hành / giá', NOODLE: 'Bánh phở' };

function optionsMarkup(item) {
    const optionGroups = ['BROTH', 'VEGGIE', 'NOODLE'].map((category) => {
        const choices = customizationOptions.filter((option) => option.category === category);
        return `<fieldset class="choice-group"><legend>${categoryLabels[category]} <span>*</span></legend>${choices.map((option) => `
            <label><input type="checkbox" data-customization-id="${option.id}" data-category="${category}"> ${escapeHtml(option.name)}</label>
        `).join('')}</fieldset>`;
    }).join('');
    const toppingChoices = toppings.map((topping) => `
        <label><input type="checkbox" data-topping-id="${topping.id}"> ${escapeHtml(topping.name)} (+${formatMoney(topping.price)})</label>
    `).join('');
    return `<details class="food-options"><summary>Tùy chỉnh món <small>(bắt buộc chọn 1 mục mỗi nhóm)</small></summary>
        ${optionGroups}
        ${toppingChoices ? `<fieldset class="choice-group"><legend>Topping thêm</legend>${toppingChoices}</fieldset>` : ''}
        <label class="note-label">Ghi chú <input class="form-input item-note" maxlength="500" placeholder="VD: ít cay"></label>
    </details>`;
}

function renderMenu(items) {
    if (!items.length) {
        menuGrid.innerHTML = '<p class="empty-state">Chưa có món trên thực đơn. Quản lý hãy thêm món trong trang Quản lý.</p>';
        return;
    }
    menuGrid.innerHTML = items.map((item) => `
        <article class="food-card" data-menu-id="${item.id}">
            <div class="food-img-wrapper"><img src="${escapeHtml(item.image || 'https://placehold.co/300x200?text=Pho+Viet')}" alt="${escapeHtml(item.name)}"></div>
            <div class="food-info">
                <h3 class="food-title">${escapeHtml(item.name)}</h3>
                <p class="food-desc">${escapeHtml(item.desc)}</p>
                ${optionsMarkup(item)}
                <div class="food-footer">
                    <span class="food-price">${formatMoney(item.price)}</span>
                    <button class="add-btn" type="button" data-add-item="${item.id}"><i class="fa-solid fa-plus"></i> Thêm</button>
                </div>
            </div>
        </article>
    `).join('');
}

function persistCart() {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function addToCart(id, card) {
    const item = menuItems.find((product) => product.id === id);
    if (!item) return;
    const customizations = [...card.querySelectorAll('[data-customization-id]:checked')].map((input) => Number(input.dataset.customizationId)).sort();
    const selectedCategories = [...card.querySelectorAll('[data-customization-id]:checked')].map((input) => input.dataset.category);
    if (['BROTH', 'VEGGIE', 'NOODLE'].some((category) => selectedCategories.filter((value) => value === category).length !== 1)) {
        alert('Vui lòng chọn đúng một mục cho nước dùng, hành/giá và bánh phở.');
        return;
    }
    const selectedToppings = [...card.querySelectorAll('[data-topping-id]:checked')].map((input) => Number(input.dataset.toppingId)).sort();
    const note = card.querySelector('.item-note')?.value.trim() || '';
    const variantKey = JSON.stringify([item.id, customizations, selectedToppings, note]);
    const existing = cart.find((entry) => entry.variantKey === variantKey);
    if (existing) existing.qty = Math.min(existing.qty + 1, 99);
    else cart.push({
        id: item.id, name: item.name, basePrice: item.price, qty: 1,
        customizations, toppings: selectedToppings, note, variantKey,
    });
    persistCart();
    renderCart();
}

function changeQty(variantKey, delta) {
    const existing = cart.find((entry) => entry.variantKey === variantKey);
    if (!existing) return;
    existing.qty += delta;
    if (existing.qty <= 0) cart = cart.filter((entry) => entry.variantKey !== variantKey);
    persistCart();
    renderCart();
}

function getLinePrice(item) {
    const toppingTotal = item.toppings.reduce((sum, id) => sum + Number(toppings.find((topping) => topping.id === id)?.price || 0), 0);
    return Number(item.basePrice) + toppingTotal;
}

function renderCart() {
    const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
    const foodTotal = cart.reduce((sum, item) => sum + item.qty * getLinePrice(item), 0);
    const deliveryFee = orderType.value === 'DELIVERY' ? Number(cartTotalAmount.dataset.deliveryFee || 0) : 0;
    const total = foodTotal + deliveryFee;
    cartBadge.textContent = totalQty;
    cartTotalAmount.textContent = formatMoney(total);
    checkoutBtn.disabled = totalQty === 0;
    cartItemsList.innerHTML = cart.map((item) => {
        const selected = item.customizations.map((id) => customizationOptions.find((option) => option.id === id)?.name).filter(Boolean);
        const extras = item.toppings.map((id) => toppings.find((topping) => topping.id === id)?.name).filter(Boolean);
        const details = [...selected, ...extras, item.note].filter(Boolean).join(' · ');
        return `<div class="cart-item">
            <div><div class="cart-item-name">${escapeHtml(item.name)}</div>
                <small>${escapeHtml(details)}</small>
                <div class="cart-item-price">${formatMoney(getLinePrice(item) * item.qty)}</div></div>
            <div class="qty-controls"><button class="qty-btn" type="button" data-qty-key="${escapeHtml(item.variantKey)}" data-delta="-1">-</button>
                <span>${item.qty}</span><button class="qty-btn" type="button" data-qty-key="${escapeHtml(item.variantKey)}" data-delta="1">+</button></div>
        </div>`;
    }).join('') || '<p class="empty-state">Chưa có món trong giỏ.</p>';
}

function openCart() {
    cartSidebar.classList.add('active');
    cartOverlay.classList.add('active');
}

function closeCart() {
    cartSidebar.classList.remove('active');
    cartOverlay.classList.remove('active');
}

openCartBtn.addEventListener('click', openCart);
closeCartBtn.addEventListener('click', closeCart);
cartOverlay.addEventListener('click', closeCart);
menuGrid.addEventListener('click', (event) => {
    const addButton = event.target.closest('[data-add-item]');
    if (addButton) addToCart(Number(addButton.dataset.addItem), addButton.closest('.food-card'));
});
cartItemsList.addEventListener('click', (event) => {
    const button = event.target.closest('[data-qty-key]');
    if (button) changeQty(button.dataset.qtyKey, Number(button.dataset.delta));
});
menuGrid.addEventListener('change', (event) => {
    const input = event.target;
    if (!input.matches('[data-customization-id]') || !input.checked) return;
    menuGrid.querySelectorAll(`[data-menu-id="${input.closest('.food-card').dataset.menuId}"] [data-category="${input.dataset.category}"]`).forEach((other) => {
        if (other !== input) other.checked = false;
    });
});

searchInput.addEventListener('input', () => {
    const keyword = searchInput.value.toLowerCase().trim();
    renderMenu(menuItems.filter((item) => item.name.toLowerCase().includes(keyword)));
});

orderType.addEventListener('change', () => {
    const isDelivery = orderType.value === 'DELIVERY';
    const isQueue = orderType.value === 'QUEUE_CART';
    addressField.style.display = isDelivery ? 'block' : 'none';
    tableField.style.display = isDelivery || isQueue ? 'none' : 'block';
    paymentMethod.value = isDelivery ? 'VIETQR' : paymentMethod.value;
    paymentMethod.disabled = isDelivery;
    renderCart();
});

if (typeof queueStatusUrl !== 'undefined') {
    let previousQueueState = '';
    const pollQueueStatus = async () => {
        try {
            const response = await fetch(queueStatusUrl, { headers: { 'Accept': 'application/json' } });
            if (!response.ok) return;
            const data = await response.json();
            if (!data.active) return;
            const state = `${data.ticket}:${data.status}:${data.table || ''}`;
            const statusText = document.getElementById('queueStatusText');
            const statusHelp = document.getElementById('queueStatusHelp');
            if (statusText) statusText.textContent = `Số ${data.ticket} · ${data.status === 'CALLED' ? 'Đã gọi số' : 'Đang chờ'}`;
            if (data.status === 'CALLED' && data.table) {
                if (statusHelp) statusHelp.textContent = `Đến lượt bạn, vui lòng vào Bàn ${data.table}. Giỏ hàng đã chọn có thể thanh toán ngay.`;
                let queueOption = orderType.querySelector('option[value="QUEUE_CART"]');
                if (!queueOption) {
                    queueOption = new Option(`Giỏ xếp hàng · Bàn ${data.table}`, 'QUEUE_CART');
                    orderType.add(queueOption);
                }
                queueOption.textContent = `Giỏ xếp hàng · Bàn ${data.table}`;
                if (orderType.value !== 'QUEUE_CART') {
                    orderType.value = 'QUEUE_CART';
                    orderType.dispatchEvent(new Event('change'));
                }
                if (state !== previousQueueState) {
                    if (navigator.vibrate) navigator.vibrate([250, 100, 250]);
                    if ('Notification' in window && Notification.permission === 'granted') {
                        new Notification('Đến lượt bạn!', { body: `Vui lòng vào Bàn ${data.table}.` });
                    }
                }
            }
            previousQueueState = state;
        } catch (_error) {
            // Giữ nguyên giao diện hiện tại nếu mạng tạm thời không khả dụng.
        }
    };
    pollQueueStatus();
    window.setInterval(pollQueueStatus, 8000);
}

checkoutForm.addEventListener('submit', () => {
    cartPayload.value = JSON.stringify(cart.map(({ id, qty, customizations, toppings, note }) => ({ id, qty, customizations, toppings, note })));
    paymentMethod.disabled = false;
});

renderMenu(menuItems);
renderCart();
orderType.dispatchEvent(new Event('change'));
