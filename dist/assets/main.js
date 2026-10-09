// Danh sách món ăn được trích xuất từ Figma
const menuItems = [
    {
        id: 1,
        name: "Phở Đặc Biệt",
        category: "pho",
        price: 65000,
        desc: "Đầy đủ Tái, Nạm, Gầu, Bò viên đậm vị truyền thống.",
        image: "images/pho-dac-biet.jpg"
    },
    {
        id: 2,
        name: "Phở Tái",
        category: "pho",
        price: 55000,
        desc: "Thịt bò tươi ngon chần tái mềm ngọt, nước dùng thanh vị.",
        image: "images/pho-tai.jpg"
    },
    {
        id: 3,
        name: "Phở Nạm",
        category: "pho",
        price: 55000,
        desc: "Thịt nạm bò mềm ngậy, giòn nhẹ, thơm nức gia vị.",
        image: "images/pho-nam.jpg"
    },
    {
        id: 4,
        name: "Nước Uống Các Loại",
        category: "drink",
        price: 15000,
        desc: "Trà đá, nước ngọt giải khát mát lạnh.",
        image: "images/nuoc-uong.jpg"
    }
];

// Giỏ hàng
let cart = [];

// Khai báo các thành phần DOM
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
const filterBtns = document.querySelectorAll('.filter-btn');
const successModal = document.getElementById('successModal');
const modalOkBtn = document.getElementById('modalOkBtn');

// Hiển thị danh sách món
function renderMenu(items) {
    menuGrid.innerHTML = items.map(item => `
        <div class="food-card">
            <div class="food-img-wrapper">
                <img src="${item.image}" alt="${item.name}" onerror="this.src='https://via.placeholder.com/300x200?text=Pho+Viet'">
            </div>
            <div class="food-info">
                <h3 class="food-title">${item.name}</h3>
                <p class="food-desc">${item.desc}</p>
                <div class="food-footer">
                    <span class="food-price">${item.price.toLocaleString('vi-VN')}đ</span>
                    <button class="add-btn" onclick="addToCart(${item.id})">
                        <i class="fa-solid fa-plus"></i> Thêm
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Thêm món vào giỏ
function addToCart(id) {
    const item = menuItems.find(p => p.id === id);
    const existing = cart.find(c => c.id === id);

    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ ...item, quantity: 1 });
    }

    updateCartUI();
}

// Tăng / giảm số lượng
function changeQuantity(id, change) {
    const index = cart.findIndex(c => c.id === id);
    if (index !== -1) {
        cart[index].quantity += change;
        if (cart[index].quantity <= 0) {
            cart.splice(index, 1);
        }
    }
    updateCartUI();
}

// Cập nhật giao diện giỏ hàng
function updateCartUI() {
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    cartBadge.textContent = totalItems;

    if (cart.length === 0) {
        cartItemsList.innerHTML = `<p style="text-align: center; color: #888; margin-top: 40px;">Giỏ hàng đang trống</p>`;
        checkoutBtn.disabled = true;
    } else {
        cartItemsList.innerHTML = cart.map(item => `
            <div class="cart-item">
                <div>
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">${(item.price * item.quantity).toLocaleString('vi-VN')}đ</div>
                </div>
                <div class="qty-controls">
                    <button class="qty-btn" onclick="changeQuantity(${item.id}, -1)">-</button>
                    <span>${item.quantity}</span>
                    <button class="qty-btn" onclick="changeQuantity(${item.id}, 1)">+</button>
                </div>
            </div>
        `).join('');
        checkoutBtn.disabled = false;
    }

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartTotalAmount.textContent = `${total.toLocaleString('vi-VN')}đ`;
}

// Lọc món ăn theo danh mục
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const cat = btn.getAttribute('data-category');
        if (cat === 'all') {
            renderMenu(menuItems);
        } else {
            renderMenu(menuItems.filter(i => i.category === cat));
        }
    });
});

// Tìm kiếm món ăn
searchInput.addEventListener('input', (e) => {
    const val = e.target.value.toLowerCase();
    const filtered = menuItems.filter(item => 
        item.name.toLowerCase().includes(val) || 
        item.desc.toLowerCase().includes(val)
    );
    renderMenu(filtered);
});

// Bật / Tắt Sidebar giỏ hàng
openCartBtn.addEventListener('click', () => {
    cartSidebar.classList.add('active');
    cartOverlay.classList.add('active');
});

function closeCart() {
    cartSidebar.classList.remove('active');
    cartOverlay.classList.remove('active');
}

closeCartBtn.addEventListener('click', closeCart);
cartOverlay.addEventListener('click', closeCart);

// Đặt hàng
checkoutBtn.addEventListener('click', () => {
    closeCart();
    successModal.classList.add('active');
    cart = [];
    updateCartUI();
});

modalOkBtn.addEventListener('click', () => {
    successModal.classList.remove('active');
});

// Khởi tạo hiển thị ban đầu
renderMenu(menuItems);