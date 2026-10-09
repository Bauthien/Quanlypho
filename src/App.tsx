import { useState, type ReactNode } from "react"

type IconName = "grid" | "orders" | "menu" | "users" | "chef" | "chart" | "settings" | "help" | "arrow" | "chevron" | "bell" | "search" | "plus" | "down" | "wallet" | "bag" | "clock" | "check" | "truck" | "table" | "close" | "logout" | "calendar" | "leaf" | "qr" | "print" | "edit" | "trash" | "phone" | "message" | "facebook" | "location" | "star"
function Icon({
  name,
  size = 20,
  className = "",
}: {
  name: IconName
  size?: number
  className?: string
}) {
  const paths: Record<IconName, ReactNode> = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    orders: (
      <>
        <path d="M8 4H5v17h14V4h-3" />
        <rect x="8" y="2" width="8" height="4" rx="1" />
        <path d="M8 10h8M8 14h8M8 18h5" />
      </>
    ),
    menu: (
      <>
        <path d="M4 3v7a3 3 0 006 0V3M7 3v19M19 3c-4 3-4 9 0 10V3Zm0 10v9" />
      </>
    ),
    users: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 21v-3a6 6 0 0112 0v3M16 5a3 3 0 010 6M18 15a5 5 0 013 5" />
      </>
    ),
    chef: (
      <>
        <path d="M7 15a5 5 0 01-2-9 5 5 0 019-2 5 5 0 015 9v7H7v-5ZM7 17h12M10 11v3m6-3v3" />
      </>
    ),
    chart: (
      <>
        <path d="M4 3v18h17M8 16v-5m5 5V7m5 9V4" />
      </>
    ),
    settings: (
      <>
        <path d="m9 3-1 3-3 1v4l-2 2 2 3 3 1 1 3h4l1-3 3-1 2-3-2-2V7l-3-1-1-3Z" />
        <circle cx="11" cy="12" r="3" />
      </>
    ),
    help: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M9 9a3 3 0 116 0c0 2-3 2-3 4m0 3h.01" />
      </>
    ),
    arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
    chevron: <path d="m9 5 7 7-7 7" />,
    down: <path d="m6 9 6 6 6-6" />,
    bell: (
      <>
        <path d="M5 17h14l-2-3V9a5 5 0 00-10 0v5l-2 3ZM10 21h4" />
      </>
    ),
    search: (
      <>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m16 16 5 5" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    wallet: (
      <>
        <rect x="3" y="5" width="18" height="15" rx="3" />
        <path d="M3 8V5l14-3v3m4 6h-6v5h6m-3-2h.01" />
      </>
    ),
    bag: (
      <>
        <path d="M5 7h14l2 14H3L5 7Z" />
        <path d="M8 8V6a4 4 0 018 0v2" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 6v6l4 2" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    truck: (
      <>
        <path d="M3 5h11v12H3V5Zm11 5h4l3 4v3h-7" />
        <circle cx="7" cy="18" r="2" />
        <circle cx="17" cy="18" r="2" />
      </>
    ),
    table: (
      <>
        <rect x="3" y="5" width="18" height="6" rx="1" />
        <path d="M5 11v9m14-9v9M9 5V3m6 2V3" />
      </>
    ),
    close: <path d="m6 6 12 12M6 18 18 6" />,
    logout: (
      <>
        <path d="M10 4H4v16h6m4-12 4 4-4 4m-6-4h12" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M7 3v4m10-4v4M3 11h18M7 15h2m4 0h2" />
      </>
    ),
    leaf: (
      <>
        <path d="M20 3C4 2 2 9 7 15s14 2 13-12ZM5 20 16 9" />
      </>
    ),
    qr: (
      <>
        <path d="M3 3h6v6H3V3Zm12 0h6v6h-6V3ZM3 15h6v6H3v-6Zm12-1v4h6v3h-6m6-9v3M12 3v3m0 5v3H8m-5-2h2m7 6v4" />
      </>
    ),
    print: (
      <>
        <path d="M7 7V3h10v4M7 17H3V8h18v9h-4M7 14h10v7H7v-7Zm10-3h1" />
      </>
    ),
    edit: (
      <>
        <path d="m4 16-1 5 5-1L20 8l-4-4L4 16Zm10-10 4 4" />
      </>
    ),
    trash: (
      <>
        <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7" />
      </>
    ),
    phone: (
      <path d="M7 3H4a1 1 0 00-1 1c0 9.4 7.6 17 17 17a1 1 0 001-1v-3l-5-2-2 2c-3.2-1.4-5.6-3.8-7-7l2-2-2-5Z" />
    ),
    message: (
      <>
        <path d="M4 5h16v12H8l-4 4V5Z" />
        <path d="M8 9h8m-8 4h5" />
      </>
    ),
    facebook: (
      <path d="M14 21v-8h3l.5-4H14V7c0-1.2.4-2 2-2h2V2.4c-.6-.1-1.7-.2-3-.2-3 0-5 1.8-5 5.2V9H7v4h3v8" />
    ),
    location: (
      <>
        <path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1116 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),
    star: (
      <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z" />
    ),
  }
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  )
}
const money = (v: number) => v.toLocaleString("vi-VN") + " ₫"
const photos = [
  "/images/pho-tai.jpg",
  "/images/pho-nam.jpg",
  "/images/pho-dac-biet.jpg",
  "/images/nuoc-uong.jpg",
]
type Dish = {
  id: number
  name: string
  desc: string
  price: number
  image: string
  category: string
  available: boolean
}
const initialDishes: Dish[] = [
  {
    id: 1,
    name: "Phở bò tái",
    desc: "Thịt bò tái mềm, nước dùng thanh ngọt",
    price: 55000,
    image: photos[0],
    category: "Phở bò",
    available: true,
  },
  {
    id: 2,
    name: "Phở bò đặc biệt",
    desc: "Tái, nạm, gầu, gân và bò viên",
    price: 75000,
    image: photos[2],
    category: "Phở bò",
    available: true,
  },
  {
    id: 3,
    name: "Phở bò tái nạm",
    desc: "Bò tái mềm cùng nạm bò đậm vị",
    price: 65000,
    image: photos[1],
    category: "Phở bò",
    available: true,
  },
  {
    id: 4,
    name: "Phở gà ta",
    desc: "Gà ta thả vườn, nước dùng thơm dịu",
    price: 55000,
    image: photos[1],
    category: "Phở gà",
    available: true,
  },
  {
    id: 5,
    name: "Phở nạm viên",
    desc: "Nạm bò mềm đậm vị cùng bò viên giòn dai",
    price: 65000,
    image: photos[1],
    category: "Phở bò",
    available: true,
  },
  {
    id: 6,
    name: "Phở nạm gân",
    desc: "Nạm bò mềm và gân bò trong, giòn vừa",
    price: 68000,
    image: photos[1],
    category: "Phở bò",
    available: true,
  },
  {
    id: 7,
    name: "Phở tái gân",
    desc: "Bò tái mềm hồng kết hợp gân bò sần sật",
    price: 68000,
    image: photos[0],
    category: "Phở bò",
    available: true,
  },
  {
    id: 8,
    name: "Phở viên gân",
    desc: "Bò viên thơm tiêu cùng gân bò ninh mềm",
    price: 65000,
    image: photos[2],
    category: "Phở bò",
    available: true,
  },
  {
    id: 9,
    name: "Phở tái bò viên",
    desc: "Thịt bò tái ngọt mềm và bò viên nhà làm",
    price: 65000,
    image: photos[0],
    category: "Phở bò",
    available: true,
  },
  {
    id: 10,
    name: "Phở thập cẩm",
    desc: "Tái, nạm, gân, bò viên và gầu bò đầy đặn",
    price: 79000,
    image: photos[2],
    category: "Phở bò",
    available: true,
  },
  {
    id: 11,
    name: "Phở bò viên",
    desc: "Bò viên dai giòn, thơm tiêu và nước dùng thanh",
    price: 58000,
    image: photos[2],
    category: "Phở bò",
    available: true,
  },
  {
    id: 12,
    name: "Phở nhỏ cho bé",
    desc: "Khẩu phần nhỏ, thịt bò mềm, không hành và ít tiêu",
    price: 39000,
    image: photos[0],
    category: "Phở trẻ em",
    available: true,
  },
  {
    id: 13,
    name: "Cà phê đá",
    desc: "Cà phê pha phin đậm đà, dùng cùng đá lạnh",
    price: 25000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 14,
    name: "Cà phê sữa",
    desc: "Cà phê phin hòa cùng sữa đặc béo thơm",
    price: 30000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 15,
    name: "Sữa bắp",
    desc: "Sữa bắp ngọt dịu, thơm tự nhiên",
    price: 15000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 16,
    name: "Sữa chua",
    desc: "Sữa chua mát lạnh, vị chua ngọt cân bằng",
    price: 18000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 17,
    name: "Chanh dây tươi",
    desc: "Chanh dây tươi chua ngọt, giải khát",
    price: 20000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 18,
    name: "Tắc ép tươi",
    desc: "Tắc tươi ép cùng đường phèn và đá",
    price: 20000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 19,
    name: "Trà ô long",
    desc: "Trà ô long thanh nhẹ, hậu vị thơm",
    price: 15000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 20,
    name: "Ô long trà chanh",
    desc: "Trà ô long kết hợp chanh tươi mát",
    price: 15000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 21,
    name: "Sâm bông cúc",
    desc: "Nước sâm bông cúc thanh mát, ít ngọt",
    price: 15000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 22,
    name: "Sâm rong biển nhãn nhục",
    desc: "Rong biển, nhãn nhục và đường phèn",
    price: 15000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 23,
    name: "Nước suối",
    desc: "Nước suối đóng chai ướp lạnh",
    price: 12000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
  {
    id: 24,
    name: "Nước ngọt các loại",
    desc: "Pepsi, 7Up, Sting, xá xị",
    price: 15000,
    image: photos[3],
    category: "Nước uống",
    available: true,
  },
]
type Order = {
  id: string
  table: string
  type: "Tại bàn" | "Giao hàng"
  items: string
  itemDetails?: {
    name: string
    extras: string[]
  }[]
  total: number
  payment: "VietQR" | "Tiền mặt"
  status: string
  time: string
  note?: string
  address?: string
}
const initialOrders: Order[] = [
  {
    id: "PH-0248",
    table: "Bàn 05",
    type: "Tại bàn",
    items: "2 Phở bò tái, 1 Trứng chần",
    total: 115000,
    payment: "VietQR",
    status: "Đang chế biến",
    time: "10:42",
    note: "KHÔNG HÀNH",
  },
  {
    id: "PH-0247",
    table: "Nguyễn Minh Anh",
    type: "Giao hàng",
    items: "2 Phở bò đặc biệt",
    total: 150000,
    payment: "VietQR",
    status: "Chờ lấy hàng",
    time: "10:38",
    address: "28 Nguyễn Du, Quận 1, TP. HCM",
  },
  {
    id: "PH-0246",
    table: "Bàn 03",
    type: "Tại bàn",
    items: "1 Phở bò tái nạm",
    total: 65000,
    payment: "Tiền mặt",
    status: "Chờ thanh toán",
    time: "10:35",
  },
  {
    id: "PH-0245",
    table: "Bàn 08",
    type: "Tại bàn",
    items: "2 Phở gà ta, 2 Trứng chần",
    total: 120000,
    payment: "VietQR",
    status: "Hoàn tất",
    time: "10:30",
  },
  {
    id: "PH-0244",
    table: "Trần Quốc Bảo",
    type: "Giao hàng",
    items: "1 Phở bò đặc biệt, 1 Phở bò tái",
    total: 130000,
    payment: "VietQR",
    status: "Đang chế biến",
    time: "10:26",
    note: "KHÔNG GIÁ · NƯỚC BÉO",
  },
]
const navItems: {
  id: string
  label: string
  icon: IconName
  count?: string
}[] = [
  { id: "dashboard", label: "Tổng quan", icon: "grid" },
  { id: "orders", label: "Đơn hàng", icon: "orders", count: "12" },
  { id: "menu", label: "Thực đơn", icon: "menu" },
  { id: "queue", label: "Hàng đợi & bàn", icon: "users", count: "8" },
  { id: "kitchen", label: "Màn hình bếp", icon: "chef" },
  { id: "reports", label: "Báo cáo doanh thu", icon: "chart" },
]
function Badge({
  children,
  tone = "green",
}: {
  children: ReactNode
  tone?: string
}) {
  return (
    <span className={`badge ${tone}`}>
      <span className="badge-dot" />
      {children}
    </span>
  )
}
function Status({ status }: { status: string }) {
  return (
    <Badge
      tone={
        status === "Hoàn tất" || status === "Đã thanh toán"
          ? "green"
          : status === "Đang chế biến"
            ? "orange"
            : status === "Chờ thanh toán"
              ? "red"
              : "blue"
      }
    >
      {status}
    </Badge>
  )
}
function Modal({
  title,
  children,
  onClose,
}: {
  title: string
  children: ReactNode
  onClose: () => void
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-heading">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Đóng">
            <Icon name="close" />
          </button>
        </div>
        {children}
      </section>
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState("login")
  const [role, setRole] = useState("Khách hàng")
  const [orders, setOrders] = useState(initialOrders)
  const [dishes, setDishes] = useState(initialDishes)
  const [toppings, setToppings] = useState([
    { name: "Thêm thịt bò", amount: "50 g", price: 15000 },
    { name: "Trứng chần", amount: "1 quả", price: 5000 },
    { name: "Thêm bánh phở", amount: "100 g", price: 10000 },
  ])
  const [period, setPeriod] = useState("Hôm nay")
  const [chartTab, setChartTab] = useState("Tất cả")
  const [orderFilter, setOrderFilter] = useState("Tất cả")
  const [search, setSearch] = useState("")
  const [toast, setToast] = useState("")
  const [notification, setNotification] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [dishEditor, setDishEditor] = useState<Partial<Dish> | null>(null)
  const [queue, setQueue] = useState([
    { number: "A018", name: "Nguyễn Hoàng", people: 3, time: "12 phút" },
    { number: "A019", name: "Lê Minh Anh", people: 2, time: "8 phút" },
    { number: "A020", name: "Trần Gia Huy", people: 4, time: "5 phút" },
  ])
  const [called, setCalled] = useState("A017")
  const [customerMode, setCustomerMode] = useState("Tại bàn")
  const [customDish, setCustomDish] = useState<Dish | null>(null)
  const [extras, setExtras] = useState<string[]>([])
  const [cart, setCart] = useState<{
    dish: Dish
    extras: string[]
    price: number
  }[]>([])
  const [checkout, setCheckout] = useState(false)
  const [payment, setPayment] = useState("VietQR")
  const [address, setAddress] = useState("")
  const [customerName, setCustomerName] = useState("")
  const [customerOrder, setCustomerOrder] = useState<string | null>(null)
  const [queueTicket, setQueueTicket] = useState<string | null>(null)
  const [menuCategory, setMenuCategory] = useState("Tất cả")
  const [customerCategory, setCustomerCategory] = useState("Tất cả")
  const [settingsSaved, setSettingsSaved] = useState(false)
  const extrasPrice = toppings
    .filter((t) => extras.includes(t.name))
    .reduce((sum, t) => sum + t.price, 0)
  const notify = (message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(""), 3500)
  }
  const go = (id: string) => {
    setPage(id)
    setSearch("")
  }
  const changeRole = (value: string) => {
    setRole(value)
    go(
      value === "Bếp"
        ? "kitchen"
        : value === "Thu ngân"
          ? "orders"
          : value === "Khách hàng"
            ? "customer"
            : "dashboard",
    )
  }
  const startOrdering = (mode = "Tại bàn") => {
    setRole("Khách hàng")
    setCustomerMode(mode)
    go("customer")
  }
  const updateOrder = (id: string, status: string) => {
    setOrders((prev) => prev.map((o) => (o.id === id ? { ...o, status } : o)))
    setSelectedOrder(null)
    notify(
      status === "Đang chế biến"
        ? "Đã xác nhận thanh toán. Đơn hàng đã chuyển tới bếp."
        : `Đơn ${id}: ${status}`,
    )
  }
  const callNext = () => {
    if (!queue.length) return notify("Không còn khách trong hàng đợi")
    setCalled(queue[0].number)
    setQueue(queue.slice(1))
    notify(`Đã gọi số ${queue[0].number}. Mời khách vào bàn!`)
  }
  const saveDish = () => {
    if (!dishEditor?.name?.trim() || !dishEditor.price || dishEditor.price <= 0)
      return notify("Vui lòng nhập tên món và giá bán hợp lệ")
    const dish = {
      id: dishEditor.id || Date.now(),
      name: dishEditor.name,
      desc: dishEditor.desc || "Món ngon từ bếp Phở Nhà",
      price: dishEditor.price,
      image: dishEditor.image || photos[0],
      category: dishEditor.category || "Phở bò",
      available: true,
    }
    setDishes((prev) =>
      dishEditor.id
        ? prev.map((d) => (d.id === dishEditor.id ? dish : d))
        : [...prev, dish],
    )
    setDishEditor(null)
    notify("Đã lưu món ăn vào thực đơn")
  }
  const totalCart = cart.reduce((s, c) => s + c.price, 0)
  const placeOrder = () => {
    if (
      customerMode === "Giao hàng" &&
      (!address.trim() || !customerName.trim())
    )
      return notify("Vui lòng nhập tên người nhận và địa chỉ giao hàng")
    const id = `PH-${String(249 + orders.length - initialOrders.length).padStart(4, "0")}`
    setOrders((prev) => [
      {
        id,
        table: customerMode === "Giao hàng" ? customerName : "Bàn 05",
        type: customerMode === "Giao hàng" ? "Giao hàng" : "Tại bàn",
        items: cart.map((c) => c.dish.name).join(", "),
        itemDetails: cart.map((c) => ({
          name: c.dish.name,
          extras: c.extras,
        })),
        total: totalCart,
        payment: payment as Order["payment"],
        status: payment === "Tiền mặt" ? "Chờ thanh toán" : "Chờ xác nhận QR",
        time: new Date().toLocaleTimeString("vi-VN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        note: cart
          .flatMap((c) =>
            c.extras.filter((e) => e.startsWith("Không") || e === "Nước béo"),
          )
          .join(" · ")
          .toUpperCase(),
        address,
      },
      ...prev,
    ])
    setCustomerOrder(id)
    setCart([])
    setCheckout(false)
    
    if (payment === "VietQR") {
      notify("Đang chờ thanh toán VietQR...")
      setTimeout(() => {
        setOrders((prev) => prev.map((o) => (o.id === id ? { ...o, status: "Đang chế biến" } : o)))
        notify(`[Webhook] VietQR báo thành công! Đơn ${id} đã tự động chuyển sang Bếp.`)
      }, 5000)
    } else {
      notify("Đặt món thành công. Vui lòng thanh toán tiền mặt tại quầy.")
    }
  }
  const activeCustomerOrder = orders.find((o) => o.id === customerOrder)
  const activeCustomerOrderItemCount = activeCustomerOrder
    ? activeCustomerOrder.itemDetails?.length ||
      activeCustomerOrder.items.split(", ").length
    : 0
  const visibleOrders = orders.filter(
    (o) =>
      (orderFilter === "Tất cả" ||
        o.type === orderFilter ||
        o.status === orderFilter) &&
      `${o.id} ${o.table} ${o.items}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  )
  const title =
    page === "home"
      ? "Phở Nhà"
      : page === "customer"
      ? "Thực đơn Phở Nhà"
      : page === "settings"
        ? "Cài đặt cửa hàng"
        : navItems.find((n) => n.id === page)?.label || "Trung tâm trợ giúp"

  const orderTable = (compact = false) => (
    <div className="table-scroll">
      <table className="order-table">
        <thead>
          <tr>
            <th>MÃ ĐƠN HÀNG</th>
            <th>KHÁCH HÀNG / BÀN</th>
            <th>LOẠI ĐƠN</th>
            <th>TỔNG TIỀN</th>
            <th>TRẠNG THÁI</th>
            <th>THỜI GIAN</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {(compact ? orders.slice(0, 5) : visibleOrders).map((o) => (
            <tr
              key={o.id}
              onClick={() => setSelectedOrder(o)}
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && setSelectedOrder(o)}
            >
              <td>
                <strong>#{o.id}</strong>
              </td>
              <td>
                <span className="table-person">
                  <span
                    className={`mini-icon ${
                      o.type === "Tại bàn" ? "neutral" : "blue"
                    }`}
                  >
                    <Icon
                      name={o.type === "Tại bàn" ? "table" : "users"}
                      size={15}
                    />
                  </span>
                  {o.table}
                </span>
              </td>
              <td>
                <span className="type-cell">
                  <Icon
                    name={o.type === "Tại bàn" ? "table" : "truck"}
                    size={15}
                  />
                  {o.type}
                </span>
              </td>
              <td className="money-cell">{money(o.total)}</td>
              <td>
                <Status status={o.status} />
              </td>
              <td className="muted">{o.time}</td>
              <td>
                <Icon name="chevron" size={16} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!visibleOrders.length && !compact && (
        <div className="empty-state">
          <Icon name="orders" size={36} />
          <h3>Không tìm thấy đơn hàng</h3>
          <p>Thử tìm kiếm hoặc chọn một trạng thái khác.</p>
        </div>
      )}
    </div>
  )

  const revenueChart = (
    <section className="panel revenue-panel">
      <div className="panel-heading">
        <div>
          <h2>Biểu đồ doanh thu</h2>
          <p>Doanh thu theo khung giờ trong ngày</p>
        </div>
        <div className="segmented small">
          {["Tất cả", "Tại bàn", "Giao hàng"].map((t) => (
            <button
              className={chartTab === t ? "active" : ""}
              onClick={() => setChartTab(t)}
              key={t}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-summary">
        <strong>
          {money(
            period === "Hôm nay"
              ? chartTab === "Tại bàn"
                ? 8540000
                : chartTab === "Giao hàng"
                  ? 3910000
                  : 12450000
              : period === "7 ngày qua"
                ? 87350000
                : 352450000,
          )}
        </strong>
        <span className="growth">
          <Icon name="chart" size={14} /> 18,6%
        </span>
        <span className="muted">
          so với {period === "Hôm nay" ? "hôm qua" : "kỳ trước"}
        </span>
      </div>
      <div className="chart">
        <div className="chart-y">
          <span>4.000k</span>
          <span>3.000k</span>
          <span>2.000k</span>
          <span>1.000k</span>
          <span>0</span>
        </div>
        <div className="chart-plot">
          <svg
            viewBox="0 0 760 180"
            preserveAspectRatio="none"
            role="img"
            aria-label="Biểu đồ doanh thu tăng mạnh từ 6 giờ đến 12 giờ"
          >
            <defs>
              <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--brand)" stopOpacity=".14" />
                <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {[5, 47, 89, 131, 173].map((y) => (
              <line
                key={y}
                x1="0"
                x2="760"
                y1={y}
                y2={y}
                stroke="var(--border)"
                strokeDasharray="4 5"
              />
            ))}
            <path
              d="M0 159C32 157 46 143 69 133S114 152 138 105S182 64 207 88S253 145 277 121S322 126 345 114S392 15 415 10S461 62 484 66S528 30 553 31S598 17 623 27S669 62 691 62S738 45 760 40V180H0Z"
              fill="url(#chartFill)"
            />
            <path
              d={
                chartTab === "Giao hàng"
                  ? "M0 168C50 167 80 142 138 155S220 100 277 135S350 70 415 95S500 125 553 81S660 100 760 70"
                  : chartTab === "Tại bàn"
                    ? "M0 163C45 159 70 119 138 138S200 81 277 119S350 118 415 36S500 97 553 65S660 52 760 49"
                    : "M0 159C32 157 46 143 69 133S114 152 138 105S182 64 207 88S253 145 277 121S322 126 345 114S392 15 415 10S461 62 484 66S528 30 553 31S598 17 623 27S669 62 691 62S738 45 760 40"
              }
              fill="none"
              stroke="var(--brand)"
              strokeWidth="3"
              strokeLinecap="round"
            />
            <circle
              cx="415"
              cy={chartTab === "Tất cả" ? 10 : chartTab === "Tại bàn" ? 36 : 95}
              r="5"
              fill="var(--brand)"
              stroke="white"
              strokeWidth="3"
            />
          </svg>
          <div className="chart-x">
            {[
              "06:00",
              "08:00",
              "10:00",
              "12:00",
              "14:00",
              "16:00",
              "18:00",
              "20:00",
              "22:00",
            ].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </div>
      </div>
      <div className="chart-footer">
        <span>
          <i className="legend-dot" /> Doanh thu
        </span>
        <span>
          <Icon name="clock" size={13} /> Cập nhật lúc 10:45
        </span>
      </div>
    </section>
  )

  if (page === "login") {
    return (
      <div className="min-h-screen bg-[#f5efe5] flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-[#9b3b2f] flex justify-center mb-4">
              <svg width="60" height="60" viewBox="0 0 40 40" fill="none">
                <path d="M7 21h26c-1 10-7 13-13 13S8 31 7 21Z" fill="currentColor" />
                <path d="M5 21h30M12 36h16M15 6c-4 4 4 5 0 9m6-12c-4 4 4 5 0 10m6-8c-4 4 4 5 0 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-[#9b3b2f] tracking-tight">phở nhà.</h1>
            <p className="text-xs text-[#a0917d] mt-2 tracking-widest font-semibold uppercase">Đăng nhập hệ thống</p>
          </div>
          
          <div className="space-y-4">
            <button 
              onClick={() => { setRole("Khách hàng"); setPage("home"); }}
              className="w-full flex items-center justify-between p-4 border-2 border-[#f0eee9] hover:border-[#9b3b2f] hover:bg-[#f7eae6] rounded-xl transition-colors text-left"
            >
              <div>
                <strong className="block text-[#595447] font-semibold">Khách hàng</strong>
                <span className="text-xs text-[#929089]">Quét QR, Đặt món, Xếp hàng</span>
              </div>
              <Icon name="arrow" size={20} className="text-[#9b3b2f]" />
            </button>
            
            <button 
              onClick={() => { setRole("Thu ngân"); setPage("orders"); }}
              className="w-full flex items-center justify-between p-4 border-2 border-[#f0eee9] hover:border-[#9b3b2f] hover:bg-[#f7eae6] rounded-xl transition-colors text-left"
            >
              <div>
                <strong className="block text-[#595447] font-semibold">Thu ngân / Điều phối</strong>
                <span className="text-xs text-[#929089]">Xác nhận thanh toán, Gọi số, Giao hàng</span>
              </div>
              <Icon name="arrow" size={20} className="text-[#9b3b2f]" />
            </button>

            <button 
              onClick={() => { setRole("Bếp"); setPage("kitchen"); }}
              className="w-full flex items-center justify-between p-4 border-2 border-[#f0eee9] hover:border-[#9b3b2f] hover:bg-[#f7eae6] rounded-xl transition-colors text-left"
            >
              <div>
                <strong className="block text-[#595447] font-semibold">Bếp / Trạm trụng phở</strong>
                <span className="text-xs text-[#929089]">Xem ghi chú, Trả món, In tem</span>
              </div>
              <Icon name="arrow" size={20} className="text-[#9b3b2f]" />
            </button>

            <button 
              onClick={() => { setRole("Admin"); setPage("dashboard"); }}
              className="w-full flex items-center justify-between p-4 border-2 border-[#f0eee9] hover:border-[#9b3b2f] hover:bg-[#f7eae6] rounded-xl transition-colors text-left"
            >
              <div>
                <strong className="block text-[#595447] font-semibold">Quản lý (Admin)</strong>
                <span className="text-xs text-[#929089]">Dashboard, Menu, Cấu hình</span>
              </div>
              <Icon name="arrow" size={20} className="text-[#9b3b2f]" />
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`app-shell ${role === "Khách hàng" ? "customer-shell" : ""} ${
        page === "home" ? "public-home" : ""
      }`}
    >
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <svg viewBox="0 0 40 40" fill="none">
              <path
                d="M7 21h26c-1 10-7 13-13 13S8 31 7 21Z"
                fill="currentColor"
              />
              <path
                d="M5 21h30M12 36h16M15 6c-4 4 4 5 0 9m6-12c-4 4 4 5 0 10m6-8c-4 4 4 5 0 9"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <span className="brand-name">
              phở nhà<span>.</span>
            </span>
            <small>ĐẬM VỊ VIỆT · TRỌN YÊU THƯƠNG</small>
          </div>
        </div>
        <div className="location">
          <span className="store-icon">
            <Icon name="table" size={19} />
          </span>
          <div>
            <strong>Phở Nhà · Quận 1</strong>
            <span>Chi nhánh chính</span>
          </div>
          <Icon name="down" size={15} />
        </div>
        <div className="nav-label">QUẢN LÝ CỬA HÀNG</div>
        <nav>
          {navItems
            .filter(
              (item) =>
                role === "Admin" ||
                (role === "Thu ngân" &&
                  ["orders", "queue"].includes(item.id)) ||
                (role === "Bếp" && item.id === "kitchen"),
            )
            .map((item) => (
              <button
                key={item.id}
                className={`nav-item ${page === item.id ? "active" : ""}`}
                onClick={() => go(item.id)}
              >
                <Icon name={item.icon} />
                <span>{item.label}</span>
                {item.count && (
                  <span className="nav-count">
                    {item.id === "queue"
                      ? queue.length
                      : orders.filter((o) => o.status !== "Hoàn tất").length}
                  </span>
                )}
              </button>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="help-card">
            <span className="help-symbol">
              <Icon name="leaf" size={23} />
            </span>
            <h3>Vận hành nhẹ nhàng hơn</h3>
            <p>
              Để Phở Nhà lo việc quản lý,
              <br />
              bạn tập trung vào hương vị.
            </p>
            <button onClick={() => go("help")}>
              Khám phá hướng dẫn <Icon name="arrow" size={16} />
            </button>
          </div>
          {role === "Admin" && (
            <button
              className={`nav-item ${page === "settings" ? "active" : ""}`}
              onClick={() => go("settings")}
            >
              <Icon name="settings" />
              <span>Cài đặt</span>
            </button>
          )}
          <button
            className={`nav-item ${page === "help" ? "active" : ""}`}
            onClick={() => go("help")}
          >
            <Icon name="help" />
            <span>Trợ giúp & hỗ trợ</span>
            <Icon name="arrow" size={15} />
          </button>
          <div className="sidebar-profile">
            <div className="avatar">HN</div>
            <div>
              <strong>Hoàng Nam</strong>
              <span>Quản lý cửa hàng</span>
            </div>
            <button
              className="icon-btn"
              aria-label="Đăng xuất"
              onClick={() => {
                setPage("login")
                notify("Đã đăng xuất thành công.")
              }}
            >
              <Icon name="logout" size={18} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        {page === "home" ? (
          <header className="home-header">
            <button
              className="home-brand"
              onClick={() => go("home")}
              aria-label="Về trang chủ Phở Nhà"
            >
              <span className="home-brand-mark">
                <svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
                  <path
                    d="M7 21h26c-1 10-7 13-13 13S8 31 7 21Z"
                    fill="currentColor"
                  />
                  <path
                    d="M5 21h30M12 36h16M15 6c-4 4 4 5 0 9m6-12c-4 4 4 5 0 10m6-8c-4 4 4 5 0 9"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
              <span>
                <strong>phở nhà.</strong>
                <small>ĐẬM VỊ VIỆT · TRỌN YÊU THƯƠNG</small>
              </span>
            </button>
            <nav className="home-nav" aria-label="Điều hướng trang chủ">
              <button
                onClick={() =>
                  document
                    .getElementById("home-menu")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                Thực đơn
              </button>
              <button
                onClick={() =>
                  document
                    .getElementById("home-story")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                Câu chuyện
              </button>
              <button
                onClick={() =>
                  document
                    .getElementById("home-contact")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                Ghé quán
              </button>
            </nav>
            <div className="home-header-actions">
              <button
                className="home-admin-link"
                onClick={() => changeRole("Admin")}
              >
                Quản lý cửa hàng
              </button>
              <button
                className="home-order-button"
                onClick={() => startOrdering()}
              >
                Đặt món ngay
                <Icon name="arrow" size={17} />
              </button>
            </div>
          </header>
        ) : (
        <header className="topbar">
          <div className="breadcrumb">
            Cửa hàng <Icon name="chevron" size={13} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-right">
            <span className="live-status">
              <i />
              Cửa hàng đang mở
            </span>
            <div className="top-divider" />
            <div className="role-picker">
              <span>Vai trò:</span>
              <select
                value={role}
                onChange={(e) => changeRole(e.target.value)}
                aria-label="Chọn vai trò"
              >
                {["Admin", "Thu ngân", "Bếp", "Khách hàng"].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </div>
            <button
              className="notification-button icon-btn"
              onClick={() => setNotification(!notification)}
              aria-label="Thông báo"
            >
              <Icon name="bell" />
              <i />
            </button>
            <div className="avatar small-avatar">HN</div>
          </div>
          {notification && (
            <div className="notification-popover">
              <h3>Thông báo mới</h3>
              <p>
                <span className="notice-dot" />
                Bàn 08 đã hoàn tất đơn hàng<small>5 phút trước</small>
              </p>
              <p>
                <span className="notice-dot orange-dot" />
                Bàn 03 đang chờ thanh toán tiền mặt<small>10 phút trước</small>
              </p>
              <button
                className="text-button"
                onClick={() => {
                  go("orders")
                  setNotification(false)
                }}
              >
                Xem tất cả đơn hàng <Icon name="arrow" size={15} />
              </button>
            </div>
          )}
        </header>
        )}
        <main>
          {page === "home" && (
            <div className="home-page">
              <section className="home-hero">
                <div className="home-hero-copy">
                  <span className="home-kicker">
                    <i />
                    PHỞ NGON MỖI NGÀY · TỪ 06:00
                  </span>
                  <h1>
                    Gói trọn vị nhà
                    <br />
                    trong từng <em>tô phở.</em>
                  </h1>
                  <p>
                    Nước dùng trong, ngọt thanh từ xương hầm 12 giờ. Thịt tươi
                    thái mỗi sáng. Một hương vị thân quen, được nấu bằng tất cả
                    sự tử tế.
                  </p>
                  <div className="home-hero-actions">
                    <button
                      className="home-primary-action"
                      onClick={() => startOrdering()}
                    >
                      Thưởng thức ngay
                      <Icon name="arrow" size={19} />
                    </button>
                    <button
                      className="home-secondary-action"
                      onClick={() => startOrdering("Giao hàng")}
                    >
                      <Icon name="truck" size={18} />
                      Giao phở tận nhà
                    </button>
                  </div>
                  <div className="home-proof">
                    <div>
                      <strong>12 giờ</strong>
                      <span>hầm nước dùng</span>
                    </div>
                    <div>
                      <strong>100%</strong>
                      <span>nguyên liệu tươi</span>
                    </div>
                    <div>
                      <strong>4,9/5</strong>
                      <span>từ thực khách</span>
                    </div>
                  </div>
                </div>
                <div className="home-hero-visual">
                  <div className="hero-image-frame">
                    <img
                      src={photos[2]}
                      alt="Tô phở bò đặc biệt nóng hổi của Phở Nhà"
                    />
                    <span className="hero-image-label">
                      <small>MÓN ĐƯỢC YÊU THÍCH</small>
                      <strong>Phở bò đặc biệt</strong>
                    </span>
                  </div>
                  <div className="hero-note hero-note-top">
                    <Icon name="leaf" size={20} />
                    <span>
                      <strong>Tươi mỗi sáng</strong>
                      Rau thơm chọn tại chợ sớm
                    </span>
                  </div>
                  <div className="hero-note hero-note-bottom">
                    <Icon name="clock" size={20} />
                    <span>
                      <strong>Nóng hổi trong 8 phút</strong>
                      Gọi món nhanh qua QR
                    </span>
                  </div>
                </div>
              </section>

              <section className="home-signature" id="home-menu">
                <div className="home-section-heading">
                  <div>
                    <span className="home-kicker">MÓN NHÀ NẤU</span>
                    <h2>Những tô phở được gọi nhiều nhất</h2>
                  </div>
                  <p>
                    Giữ vị truyền thống trong từng nguyên liệu, thêm chút chỉn
                    chu để mỗi bữa ăn đều thật trọn vẹn.
                  </p>
                </div>
                <div className="home-dish-grid">
                  {dishes.slice(0, 3).map((dish, index) => (
                    <article
                      className={`home-dish-card ${index === 1 ? "featured" : ""}`}
                      key={dish.id}
                    >
                      <div className="home-dish-image">
                        <img src={dish.image} alt={dish.name} />
                        {index === 1 && <span>BÁN CHẠY NHẤT</span>}
                      </div>
                      <div className="home-dish-content">
                        <span className="home-dish-number">
                          0{index + 1} · {dish.category}
                        </span>
                        <h3>{dish.name}</h3>
                        <p>{dish.desc}</p>
                        <div>
                          <strong>{money(dish.price)}</strong>
                          <button
                            onClick={() => {
                              startOrdering()
                              setCustomDish(dish)
                              setExtras([])
                            }}
                            aria-label={`Chọn ${dish.name}`}
                          >
                            <Icon name="plus" size={18} />
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
                <button
                  className="home-menu-link"
                  onClick={() => startOrdering()}
                >
                  Xem toàn bộ thực đơn
                  <Icon name="arrow" size={17} />
                </button>
              </section>

              <section className="home-story" id="home-story">
                <div className="home-story-images">
                  <img src={photos[0]} alt="Phở bò tái với thịt bò tươi" />
                  <div>
                    <strong>12</strong>
                    <span>giờ chắt chiu vị ngọt thanh</span>
                  </div>
                </div>
                <div className="home-story-copy">
                  <span className="home-kicker">VỀ PHỞ NHÀ</span>
                  <h2>Một quán phở nhỏ, gìn giữ hương vị Việt thân quen.</h2>
                  <p>
                    Phở Nhà phục vụ phở bò và phở gà nấu mới mỗi ngày tại trung
                    tâm Quận 1. Mỗi nồi nước dùng bắt đầu từ xương tuyển chọn,
                    hầm liu riu cùng quế, hồi và gừng nướng trong 12 giờ để giữ
                    vị ngọt trong, thơm dịu như căn bếp nhà.
                  </p>
                  <div className="home-about-facts">
                    <div>
                      <strong>Từ 2018</strong>
                      <span>Gìn giữ công thức gia đình</span>
                    </div>
                    <div>
                      <strong>06:00 – 22:00</strong>
                      <span>Phục vụ mỗi ngày</span>
                    </div>
                    <div>
                      <strong>Quận 1</strong>
                      <span>Ăn tại quán và giao tận nơi</span>
                    </div>
                  </div>
                  <ul>
                    <li>
                      <Icon name="check" size={16} /> Không chất bảo quản
                    </li>
                    <li>
                      <Icon name="check" size={16} /> Thịt tươi thái trong ngày
                    </li>
                    <li>
                      <Icon name="check" size={16} /> Rau thơm rửa mới mỗi ca
                    </li>
                  </ul>
                  <button onClick={() => startOrdering()}>
                    Chọn tô phở của bạn
                    <Icon name="arrow" size={17} />
                  </button>
                </div>
              </section>

              <section className="home-contact-section">
                <div className="home-section-heading">
                  <div>
                    <span className="home-kicker">KẾT NỐI VỚI PHỞ NHÀ</span>
                    <h2>Liên hệ nhanh theo cách tiện nhất</h2>
                  </div>
                  <p>
                    Đặt bàn, hỏi món hoặc tìm đường đến quán. Phở Nhà luôn sẵn
                    sàng hỗ trợ bạn trong giờ mở cửa.
                  </p>
                </div>
                <div className="home-contact-grid">
                  <button
                    onClick={() => {
                      window.location.href = "tel:02838225566"
                    }}
                  >
                    <i>
                      <Icon name="phone" size={22} />
                    </i>
                    <span>
                      <small>HOTLINE</small>
                      <strong>028 3822 5566</strong>
                    </span>
                    <Icon name="arrow" size={17} />
                  </button>
                  <button
                    onClick={() =>
                      window.open(
                        "https://zalo.me/02838225566",
                        "_blank",
                        "noopener,noreferrer",
                      )
                    }
                  >
                    <i>
                      <Icon name="message" size={22} />
                    </i>
                    <span>
                      <small>ZALO</small>
                      <strong>Phở Nhà Quận 1</strong>
                    </span>
                    <Icon name="arrow" size={17} />
                  </button>
                  <button
                    onClick={() =>
                      window.open(
                        "https://www.facebook.com/",
                        "_blank",
                        "noopener,noreferrer",
                      )
                    }
                  >
                    <i>
                      <Icon name="facebook" size={22} />
                    </i>
                    <span>
                      <small>FACEBOOK</small>
                      <strong>Phở Nhà</strong>
                    </span>
                    <Icon name="arrow" size={17} />
                  </button>
                  <button
                    onClick={() =>
                      window.open(
                        "https://www.google.com/maps/search/?api=1&query=28+Nguyễn+Du,+Bến+Nghé,+Quận+1,+TP.HCM",
                        "_blank",
                        "noopener,noreferrer",
                      )
                    }
                  >
                    <i>
                      <Icon name="location" size={22} />
                    </i>
                    <span>
                      <small>VỊ TRÍ</small>
                      <strong>28 Nguyễn Du, Quận 1</strong>
                    </span>
                    <Icon name="arrow" size={17} />
                  </button>
                </div>
              </section>

              <section className="home-how">
                <span className="home-kicker">NHANH HƠN · NHẸ NHÀNG HƠN</span>
                <h2>Từ lúc gọi món đến khi phở lên bàn</h2>
                <div>
                  {[
                    {
                      icon: "qr" as IconName,
                      number: "01",
                      title: "Quét QR",
                      text: "Nhận diện bàn và mở thực đơn ngay trên điện thoại.",
                    },
                    {
                      icon: "menu" as IconName,
                      number: "02",
                      title: "Chọn vị bạn thích",
                      text: "Tùy chỉnh hành, giá, nước béo và topping thật dễ dàng.",
                    },
                    {
                      icon: "chef" as IconName,
                      number: "03",
                      title: "Bếp nấu tức thì",
                      text: "Đơn đã thanh toán được chuyển thẳng đến bếp.",
                    },
                  ].map((step) => (
                    <article key={step.number}>
                      <span>{step.number}</span>
                      <i>
                        <Icon name={step.icon} size={23} />
                      </i>
                      <h3>{step.title}</h3>
                      <p>{step.text}</p>
                    </article>
                  ))}
                </div>
              </section>

              <section className="home-reviews">
                <div className="home-section-heading">
                  <div>
                    <span className="home-kicker">THỰC KHÁCH NÓI GÌ</span>
                    <h2>Vị ngon được kể lại bằng những lần quay lại</h2>
                  </div>
                  <div className="review-summary">
                    <strong>4,9</strong>
                    <span>
                      <i>
                        {Array.from({ length: 5 }, (_, index) => (
                          <Icon name="star" size={14} key={index} />
                        ))}
                      </i>
                      Hơn 1.200 lượt đánh giá
                    </span>
                  </div>
                </div>
                <div className="home-review-grid">
                  {[
                    {
                      initials: "MA",
                      name: "Minh Anh",
                      meta: "Khách quen · Quận 3",
                      text: "Nước dùng thanh, thơm mùi quế hồi nhưng không bị gắt. Phở tái gân là món mình gọi gần như mỗi tuần.",
                    },
                    {
                      initials: "HP",
                      name: "Hoàng Phúc",
                      meta: "Đặt giao hàng",
                      text: "Đóng gói rất cẩn thận, nước lèo và bánh phở để riêng nên khi nhận vẫn ngon. Bò viên dai vừa, trẻ con rất thích.",
                    },
                    {
                      initials: "TL",
                      name: "Thu Lan",
                      meta: "Khách tại quán",
                      text: "Quán sạch, nhân viên dễ thương. Có phần phở nhỏ cho bé và sữa bắp nên cả gia đình ăn sáng rất tiện.",
                    },
                  ].map((review) => (
                    <article key={review.name}>
                      <div className="review-stars">
                        {Array.from({ length: 5 }, (_, index) => (
                          <Icon name="star" size={14} key={index} />
                        ))}
                      </div>
                      <p>“{review.text}”</p>
                      <div className="review-person">
                        <span>{review.initials}</span>
                        <div>
                          <strong>{review.name}</strong>
                          <small>{review.meta}</small>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </section>

              <div className="home-contact-float" aria-label="Liên hệ nhanh">
                {[
                  {
                    icon: "phone" as IconName,
                    label: "Gọi hotline",
                    action: () => {
                      window.location.href = "tel:02838225566"
                    },
                  },
                  {
                    icon: "message" as IconName,
                    label: "Liên hệ Zalo",
                    action: () =>
                      window.open(
                        "https://zalo.me/02838225566",
                        "_blank",
                        "noopener,noreferrer",
                      ),
                  },
                  {
                    icon: "facebook" as IconName,
                    label: "Xem Facebook",
                    action: () =>
                      window.open(
                        "https://www.facebook.com/",
                        "_blank",
                        "noopener,noreferrer",
                      ),
                  },
                  {
                    icon: "location" as IconName,
                    label: "Xem vị trí",
                    action: () =>
                      window.open(
                        "https://www.google.com/maps/search/?api=1&query=28+Nguyễn+Du,+Bến+Nghé,+Quận+1,+TP.HCM",
                        "_blank",
                        "noopener,noreferrer",
                      ),
                  },
                ].map((contact) => (
                  <button
                    key={contact.label}
                    onClick={contact.action}
                    aria-label={contact.label}
                    title={contact.label}
                  >
                    <Icon name={contact.icon} size={19} />
                  </button>
                ))}
              </div>

              <section className="home-visit" id="home-contact">
                <div>
                  <span className="home-kicker">GHÉ PHỞ NHÀ HÔM NAY</span>
                  <h2>Một góc nhỏ ấm cúng giữa lòng Sài Gòn.</h2>
                  <p>
                    28 Nguyễn Du, Bến Nghé, Quận 1, TP. HCM
                    <br />
                    Mở cửa mỗi ngày · 06:00 – 22:00
                  </p>
                </div>
                <div className="home-visit-actions">
                  <button onClick={() => startOrdering("Chờ bàn")}>
                    <Icon name="clock" size={18} />
                    Lấy số chờ bàn
                  </button>
                  <button onClick={() => startOrdering()}>
                    Đặt món ngay
                    <Icon name="arrow" size={18} />
                  </button>
                </div>
              </section>

              <footer className="home-footer">
                <div className="home-brand footer-brand">
                  <span className="home-brand-mark">
                    <Icon name="leaf" size={24} />
                  </span>
                  <span>
                    <strong>phở nhà.</strong>
                    <small>ẤM LÒNG MỖI NGÀY</small>
                  </span>
                </div>
                <p>© 2025 Phở Nhà · Đậm vị Việt, trọn yêu thương.</p>
                <span>
                  <i />
                  Đang mở cửa
                </span>
              </footer>
            </div>
          )}
          {page !== "home" && (
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {page === "dashboard"
                  ? "MỘT NGÀY MỚI, MỘT KHỞI ĐẦU NGON"
                  : page === "customer"
                    ? "NÓNG HỔI TỪ BẾP · ĐẬM ĐÀ TỪ TÂM"
                    : "PHỞ NHÀ · QUẢN LÝ THÔNG MINH"}
              </div>
              <h1>
                {page === "dashboard" ? "Tổng quan cửa hàng" : title}
                {page === "dashboard" && (
                  <svg
                    className="heading-sun"
                    width="26"
                    height="26"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="4" />
                    <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2" />
                  </svg>
                )}
              </h1>
              <p>
                {page === "dashboard"
                  ? "Chào Nam, cùng xem cửa hàng của bạn đang hoạt động thế nào nhé."
                  : page === "orders"
                    ? "Mọi đơn hàng, từ thanh toán đến phục vụ, ở cùng một nơi."
                    : page === "kitchen"
                      ? "Chỉ nhận đơn đã thanh toán. Chế biến đúng món, đúng yêu cầu."
                      : page === "menu"
                        ? "Chăm chút từng món ngon, cập nhật thực đơn của cửa hàng."
                        : page === "queue"
                          ? "Đón khách đúng lượt, sắp xếp bàn thật dễ dàng."
                          : page === "customer"
                            ? "Một tô phở ngon, một ngày trọn vẹn."
                            : "Thông tin rõ ràng, vận hành hiệu quả hơn mỗi ngày."}
              </p>
            </div>
            <div className="heading-actions">
              {page === "dashboard" || page === "reports" ? (
                <>
                  <label className="date-select">
                    <Icon name="calendar" size={17} />
                    <select
                      value={period}
                      onChange={(e) => setPeriod(e.target.value)}
                      aria-label="Khoảng thời gian"
                    >
                      <option>Hôm nay</option>
                      <option>7 ngày qua</option>
                      <option>Tháng này</option>
                    </select>
                  </label>
                  <button className="primary-btn" onClick={() => go("reports")}>
                    <Icon name="chart" size={17} />
                    Xem báo cáo
                  </button>
                </>
              ) : page === "menu" ? (
                <button
                  className="primary-btn"
                  onClick={() => setDishEditor({})}
                >
                  <Icon name="plus" size={18} />
                  Thêm món mới
                </button>
              ) : page === "queue" ? (
                <button className="primary-btn" onClick={callNext}>
                  <Icon name="users" size={18} />
                  Gọi số tiếp theo
                </button>
              ) : page === "customer" ? (
                <>
                  <button
                    className="secondary-btn customer-home-button"
                    onClick={() => go("home")}
                  >
                    <Icon name="arrow" size={17} className="back-arrow" />
                    Trang chủ
                  </button>
                  <button
                    className="primary-btn customer-cart-button"
                    onClick={() => {
                      if (cart.length) return setCheckout(true)
                      if (activeCustomerOrder) {
                        document
                          .getElementById("customer-active-order")
                          ?.scrollIntoView({
                            behavior: "smooth",
                            block: "center",
                          })
                        return
                      }
                      notify("Hãy chọn món ngon trước nhé!")
                    }}
                  >
                    <Icon
                      name={activeCustomerOrder ? "orders" : "bag"}
                      size={18}
                    />
                    {cart.length
                      ? `Giỏ hàng (${cart.length})`
                      : activeCustomerOrder
                        ? `Đơn của tôi (${activeCustomerOrderItemCount})`
                        : "Giỏ hàng (0)"}
                  </button>
                </>
              ) : (
                <span className="realtime">
                  <i />
                  Đồng bộ theo thời gian thực
                </span>
              )}
            </div>
          </div>
          )}

          {(page === "dashboard" || page === "reports") && (
            <>
              <div className="stats-grid">
                {[
                  {
                    label: "Doanh thu hôm nay",
                    value: money(
                      period === "Hôm nay"
                        ? 12450000
                        : period === "7 ngày qua"
                          ? 87350000
                          : 352450000,
                    ),
                    icon: "wallet" as IconName,
                    color: "red",
                    growth: "+18,6%",
                    detail: "so với hôm qua",
                    graph: "M1 27 12 21 23 24 34 12 45 16 56 8 67 10 78 2",
                  },
                  {
                    label: "Tổng đơn hàng",
                    value:
                      period === "Hôm nay"
                        ? "186"
                        : period === "7 ngày qua"
                          ? "1.302"
                          : "5.280",
                    icon: "bag" as IconName,
                    color: "blue",
                    growth: "+12,8%",
                    detail: "so với hôm qua",
                    graph: "M1 27 12 20 23 23 34 15 45 19 56 7 67 12 78 3",
                  },
                  {
                    label: "Đơn đang xử lý",
                    value: String(
                      orders.filter((o) => o.status !== "Hoàn tất").length,
                    ).padStart(2, "0"),
                    icon: "chef" as IconName,
                    color: "orange",
                    growth: "",
                    detail: `${orders.filter((o) => o.status !== "Hoàn tất" && o.type === "Tại bàn").length} tại bàn · ${orders.filter((o) => o.status !== "Hoàn tất" && o.type === "Giao hàng").length} giao hàng`,
                    graph: "",
                  },
                  {
                    label: "Khách đang chờ",
                    value: String(
                      queue.reduce((sum, q) => sum + q.people, 0),
                    ).padStart(2, "0"),
                    icon: "users" as IconName,
                    color: "purple",
                    growth: "",
                    detail: "Thời gian chờ TB: 12 phút",
                    graph: "",
                  },
                ].map((s, i) => (
                  <section className="stat-card" key={s.label}>
                    <div className="stat-top">
                      <span>{s.label}</span>
                      <span className={`stat-icon ${s.color}`}>
                        <Icon name={s.icon} size={21} />
                      </span>
                    </div>
                    <div className="stat-value">
                      {s.value}
                      {i === 0 && <span className="currency-label">VND</span>}
                    </div>
                    <div className="stat-bottom">
                      {s.growth ? (
                        <>
                          <span className="growth">↗ {s.growth}</span>
                          <span>{s.detail}</span>
                          <svg className="sparkline" viewBox="0 0 80 32">
                            <path
                              d={s.graph}
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            />
                          </svg>
                        </>
                      ) : (
                        <>
                          <span className={`small-dot ${s.color}`} />
                          <span>{s.detail}</span>
                          <button
                            onClick={() => go(i === 2 ? "orders" : "queue")}
                            aria-label={
                              i === 2 ? "Xem đơn hàng" : "Xem hàng đợi"
                            }
                          >
                            <Icon name="arrow" size={17} />
                          </button>
                        </>
                      )}
                    </div>
                  </section>
                ))}
              </div>
              <div className="analytics-grid">
                {revenueChart}
                <section className="panel channel-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Doanh thu theo kênh</h2>
                      <p>Mỗi kênh, một cơ hội tăng trưởng</p>
                    </div>
                    <button
                      className="icon-btn"
                      onClick={() => go("reports")}
                      aria-label="Xem chi tiết doanh thu"
                    >
                      <Icon name="chevron" size={17} />
                    </button>
                  </div>
                  <div className="donut-wrap">
                    <div className="donut">
                      <div>
                        <span>Tổng doanh thu</span>
                        <strong>
                          12,45<span> triệu</span>
                        </strong>
                      </div>
                    </div>
                  </div>
                  <div className="channel-row">
                    <span className="channel-icon dine">
                      <Icon name="table" size={18} />
                    </span>
                    <div>
                      <strong>Tại bàn</strong>
                      <span>128 đơn hàng</span>
                    </div>
                    <div>
                      <strong>8.540.000 ₫</strong>
                      <span>68,6%</span>
                    </div>
                  </div>
                  <div className="channel-row">
                    <span className="channel-icon delivery">
                      <Icon name="truck" size={18} />
                    </span>
                    <div>
                      <strong>Giao hàng</strong>
                      <span>58 đơn hàng</span>
                    </div>
                    <div>
                      <strong>3.910.000 ₫</strong>
                      <span>31,4%</span>
                    </div>
                  </div>
                </section>
              </div>
              {page === "dashboard" ? (
                <>
                  <div className="operational-grid">
                    <section className="panel recent-panel">
                      <div className="panel-heading">
                        <div className="title-with-count">
                          <h2>Đơn hàng gần đây</h2>
                          <span className="count-pill">
                            {
                              orders.filter((o) => o.status !== "Hoàn tất")
                                .length
                            }{" "}
                            đơn đang hoạt động
                          </span>
                        </div>
                        <button
                          className="text-button"
                          onClick={() => go("orders")}
                        >
                          Xem tất cả
                          <Icon name="arrow" size={16} />
                        </button>
                      </div>
                      {orderTable(true)}
                    </section>
                    <section className="panel queue-summary">
                      <div className="panel-heading">
                        <h2>Hàng đợi hiện tại</h2>
                        <span className="mini-icon orange">
                          <Icon name="users" size={17} />
                        </span>
                      </div>
                      <div className="current-call">
                        <span>ĐANG GỌI SỐ</span>
                        <strong>{called}</strong>
                        <span>
                          <i />
                          Mời khách vào bàn
                        </span>
                      </div>
                      <div className="queue-meta">
                        <span>
                          <Icon name="users" size={15} />
                          {queue.reduce((sum, q) => sum + q.people, 0)} khách
                          đang chờ
                        </span>
                        <span>~ 12 phút</span>
                      </div>
                      <button className="primary-btn full" onClick={callNext}>
                        Gọi số tiếp theo
                        <Icon name="arrow" size={17} />
                      </button>
                      <button
                        className="text-button queue-link"
                        onClick={() => go("queue")}
                      >
                        Quản lý hàng đợi
                        <Icon name="chevron" size={14} />
                      </button>
                    </section>
                  </div>
                  <div className="bottom-grid">
                    <section className="panel bestselling">
                      <div className="panel-heading">
                        <div>
                          <h2>Món bán chạy</h2>
                          <p>Những hương vị được yêu thích hôm nay</p>
                        </div>
                        <button
                          className="text-button"
                          onClick={() => go("menu")}
                        >
                          Xem thực đơn
                          <Icon name="arrow" size={16} />
                        </button>
                      </div>
                      <div className="bestseller-list">
                        {dishes.slice(0, 3).map((d, i) => (
                          <button
                            className="bestseller"
                            key={d.id}
                            onClick={() => setDishEditor(d)}
                          >
                            <div className="dish-photo">
                              <img src={d.image} alt={d.name} />
                              <span>{i + 1}</span>
                            </div>
                            <div>
                              <strong>{d.name}</strong>
                              <span>{[68, 52, 36][i]} phần đã bán</span>
                            </div>
                            <div className="bestseller-price">
                              <strong>
                                {money(d.price * [68, 52, 36][i])}
                              </strong>
                              <span>{money(d.price)} / phần</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </section>
                    <section className="insight-card">
                      <div className="insight-icon">
                        <Icon name="leaf" size={22} />
                      </div>
                      <div className="eyebrow">GÓC NHÌN KINH DOANH</div>
                      <h2>
                        Một tô phở ngon.
                        <br />
                        Nhiều khách quay lại.
                      </h2>
                      <p>
                        Doanh thu hôm nay tăng <strong>18,6%</strong>.<br />
                        Phở bò tái vẫn là món được yêu thích nhất!
                      </p>
                      <button onClick={() => go("reports")}>
                        Khám phá báo cáo
                        <Icon name="arrow" size={17} />
                      </button>
                      <svg
                        className="bowl-decoration"
                        viewBox="0 0 150 120"
                        fill="none"
                      >
                        <path
                          d="M15 57h120c-5 43-29 50-60 50S20 100 15 57ZM45 115h60M9 57h132M57 11c-14 13 11 14 0 28m20-35c-14 13 11 14 0 28m20-20c-14 13 11 14 0 28"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeLinecap="round"
                        />
                      </svg>
                    </section>
                  </div>
                </>
              ) : (
                <section className="panel report-breakdown">
                  <div className="panel-heading">
                    <h2>Phân tích hiệu quả kinh doanh</h2>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        const data =
                          "Kênh,Đơn hàng,Doanh thu\nTại bàn,128,8540000\nGiao hàng,58,3910000"
                        const a = document.createElement("a")
                        a.href = URL.createObjectURL(
                          new Blob(["\uFEFF" + data], {
                            type: "text/csv;charset=utf-8;",
                          }),
                        )
                        a.download = "bao-cao-pho-nha.csv"
                        a.click()
                        URL.revokeObjectURL(a.href)
                        notify("Đã xuất báo cáo CSV")
                      }}
                    >
                      Xuất báo cáo CSV
                    </button>
                  </div>
                  <div className="report-cards">
                    <div>
                      <span>Giá trị đơn trung bình</span>
                      <strong>66.935 ₫</strong>
                      <p>+5,2% so với kỳ trước</p>
                    </div>
                    <div>
                      <span>Tỷ lệ thanh toán VietQR</span>
                      <strong>82,3%</strong>
                      <p>153 trên 186 đơn hàng</p>
                    </div>
                    <div>
                      <span>Thời gian phục vụ trung bình</span>
                      <strong>8,5 phút</strong>
                      <p>Nhanh hơn 2 phút so với hôm qua</p>
                    </div>
                  </div>
                  <p className="demo-note">
                    Số liệu tổng hợp minh họa cho giao diện báo cáo.
                  </p>
                </section>
              )}
            </>
          )}

          {page === "orders" && (
            <section className="panel">
              <div className="list-toolbar">
                <div className="filter-tabs">
                  {["Tất cả", "Tại bàn", "Giao hàng", "Chờ thanh toán"].map(
                    (f) => (
                      <button
                        key={f}
                        className={orderFilter === f ? "active" : ""}
                        onClick={() => setOrderFilter(f)}
                      >
                        {f}
                        {f === "Tất cả" && <span>{orders.length}</span>}
                      </button>
                    ),
                  )}
                </div>
                <label className="search-field">
                  <Icon name="search" size={17} />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Tìm mã đơn, khách hàng..."
                  />
                </label>
              </div>
              {orderTable()}
              <div className="table-footer">
                Hiển thị {visibleOrders.length} đơn hàng
                <span>
                  Nhấn vào đơn để xem chi tiết và xử lý{" "}
                  <Icon name="arrow" size={14} />
                </span>
              </div>
            </section>
          )}

          {page === "menu" && (
            <>
              <div className="list-toolbar menu-toolbar">
                <div className="filter-tabs">
                  {[
                    "Tất cả",
                    "Phở bò",
                    "Phở gà",
                    "Phở trẻ em",
                    "Nước uống",
                    "Topping",
                  ].map((c) => (
                    <button
                      key={c}
                      className={menuCategory === c ? "active" : ""}
                      onClick={() => setMenuCategory(c)}
                    >
                      {c}
                    </button>
                  ))}
                </div>
                <label className="search-field">
                  <Icon name="search" size={17} />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Tìm món ăn..."
                  />
                </label>
              </div>
              {menuCategory !== "Topping" ? (
                <div className="menu-grid">
                  {dishes
                    .filter(
                      (d) =>
                        (menuCategory === "Tất cả" ||
                          d.category === menuCategory) &&
                        d.name.toLowerCase().includes(search.toLowerCase()),
                    )
                    .map((d) => (
                      <article className="panel menu-card" key={d.id}>
                        <div className="menu-image">
                          <img src={d.image} alt={d.name} />
                          <Badge tone={d.available ? "green" : "red"}>
                            {d.available ? "Đang bán" : "Tạm hết"}
                          </Badge>
                        </div>
                        <div className="menu-card-content">
                          <span className="eyebrow">{d.category}</span>
                          <h2>{d.name}</h2>
                          <p>{d.desc}</p>
                          <div className="menu-card-price">
                            <strong>{money(d.price)}</strong>
                            <button
                              className="icon-btn"
                              aria-label={`Sửa ${d.name}`}
                              onClick={() => setDishEditor(d)}
                            >
                              <Icon name="edit" size={18} />
                            </button>
                            <button
                              className="icon-btn"
                              aria-label={`Xóa ${d.name}`}
                              onClick={() => {
                                if (
                                  window.confirm(`Xóa ${d.name} khỏi thực đơn?`)
                                ) {
                                  setDishes(
                                    dishes.filter((item) => item.id !== d.id),
                                  )
                                  notify("Đã xóa món khỏi thực đơn")
                                }
                              }}
                            >
                              <Icon name="trash" size={18} />
                            </button>
                          </div>
                          <button
                            className="availability-btn"
                            onClick={() => {
                              setDishes(
                                dishes.map((item) =>
                                  item.id === d.id
                                    ? { ...item, available: !item.available }
                                    : item,
                                ),
                              )
                              notify("Đã cập nhật trạng thái món")
                            }}
                          >
                            {d.available
                              ? "Đánh dấu tạm hết món"
                              : "Mở bán trở lại"}
                          </button>
                        </div>
                      </article>
                    ))}
                </div>
              ) : (
                <section className="panel topping-panel">
                  <h2>Định lượng & giá topping</h2>
                  <p>Topping được hiển thị khi khách tùy biến món.</p>
                  {toppings.map((t) => (
                    <form
                      key={t.name}
                      className="topping-row"
                      onSubmit={(e) => {
                        e.preventDefault()
                        const form = new FormData(e.currentTarget)
                        setToppings((prev) =>
                          prev.map((item) =>
                            item.name === t.name
                              ? {
                                  ...item,
                                  amount: String(form.get("amount")),
                                  price: Number(form.get("price")),
                                }
                              : item,
                          ),
                        )
                        notify(`Đã lưu định lượng và giá ${t.name}`)
                      }}
                    >
                      <strong>{t.name}</strong>
                      <label>
                        Định lượng
                        <input name="amount" defaultValue={t.amount} required />
                      </label>
                      <label>
                        Giá bán (₫)
                        <input
                          name="price"
                          type="number"
                          min="0"
                          defaultValue={t.price}
                          required
                        />
                      </label>
                      <button className="secondary-btn">Lưu</button>
                    </form>
                  ))}
                  <p className="demo-note">
                    Cấu hình topping trong phiên demo; chưa kết nối dữ liệu
                    thực.
                  </p>
                </section>
              )}
            </>
          )}

          {page === "queue" && (
            <div className="queue-page-grid">
              <section className="panel">
                <div className="panel-heading">
                  <h2>Khách đang chờ</h2>
                  <Badge tone="orange">{queue.length} nhóm khách</Badge>
                </div>
                <div className="queue-big-call">
                  <span>Đang gọi</span>
                  <strong>{called}</strong>
                  <button className="primary-btn" onClick={callNext}>
                    Gọi số tiếp theo <Icon name="arrow" size={18} />
                  </button>
                </div>
                {queue.map((q) => (
                  <div className="waiting-row" key={q.number}>
                    <span className="ticket-number">{q.number}</span>
                    <div>
                      <strong>{q.name}</strong>
                      <span>
                        {q.people} khách · Đã chờ {q.time}
                      </span>
                    </div>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setCalled(q.number)
                        setQueue(
                          queue.filter((item) => item.number !== q.number),
                        )
                        notify(`Đã gọi số ${q.number}`)
                      }}
                    >
                      Gọi khách
                    </button>
                  </div>
                ))}
                {!queue.length && (
                  <div className="empty-state">
                    <Icon name="check" size={32} />
                    <h3>Tất cả khách đã được gọi</h3>
                    <p>Hàng đợi hiện đang trống.</p>
                  </div>
                )}
              </section>
              <section className="panel table-map">
                <div className="panel-heading">
                  <div>
                    <h2>Sơ đồ bàn</h2>
                    <p>12 bàn · 4 bàn đang trống</p>
                  </div>
                  <Icon name="table" />
                </div>
                <div className="tables-grid">
                  {Array.from({ length: 12 }, (_, i) => (
                    <button
                      key={i}
                      className={`table-tile ${
                        [1, 5, 9, 11].includes(i) ? "free" : "occupied"
                      }`}
                      onClick={() =>
                        notify(
                          [1, 5, 9, 11].includes(i)
                            ? `Bàn ${String(i + 1).padStart(2, "0")} đang trống, có thể đón khách.`
                            : `Bàn ${String(i + 1).padStart(2, "0")} đang phục vụ khách.`,
                        )
                      }
                    >
                      <Icon name="table" size={27} />
                      <strong>Bàn {String(i + 1).padStart(2, "0")}</strong>
                      <span>
                        {[1, 5, 9, 11].includes(i) ? "Trống" : "Đang phục vụ"}
                      </span>
                    </button>
                  ))}
                </div>
                <p className="demo-note">
                  Sơ đồ bàn minh họa · Mỗi bàn có mã QR riêng.
                </p>
              </section>
            </div>
          )}

          {page === "kitchen" && (
            <>
              <div className="kitchen-banner">
                <Icon name="chef" size={23} />
                <span>
                  <strong>Bếp sẵn sàng</strong> · Đơn đã thanh toán được chuyển
                  tự động đến đây.
                </span>
                <Badge tone="green">Đang kết nối</Badge>
              </div>
              <div className="kitchen-grid">
                {orders
                  .filter((o) =>
                    ["Đang chế biến", "Chờ lấy hàng"].includes(o.status),
                  )
                  .map((o) => (
                    <article
                      className={`panel kitchen-card ${
                        o.status === "Chờ lấy hàng" ? "ready" : ""
                      }`}
                      key={o.id}
                    >
                      <div className="kitchen-card-top">
                        <div>
                          <span className="eyebrow">#{o.id}</span>
                          <h2>{o.table}</h2>
                        </div>
                        <Badge tone={o.type === "Tại bàn" ? "neutral" : "blue"}>
                          {o.type}
                        </Badge>
                      </div>
                      <div className="kitchen-time">
                        <Icon name="clock" size={16} />
                        Nhận lúc {o.time}
                        <Status status={o.status} />
                      </div>
                      <div className="kitchen-items">
                        {(o.itemDetails ||
                          o.items.split(", ").map((name) => ({
                            name,
                            extras: [],
                          }))
                        ).map((item, index) => (
                          <div key={`${item.name}-${index}`}>
                            <Icon name="menu" size={18} />
                            <span>
                              <strong>{item.name}</strong>
                              {item.extras.length > 0 && (
                                <small>
                                  {item.extras
                                    .filter(
                                      (extra) =>
                                        !extra.startsWith("Không") &&
                                        extra !== "Nước béo",
                                    )
                                    .join(" · ")}
                                </small>
                              )}
                            </span>
                          </div>
                        ))}
                      </div>
                      {o.note && (
                        <div className="border-2 border-red-500 bg-red-50 rounded-lg p-4 my-4">
                          <span className="block text-xs font-bold tracking-widest text-red-800 mb-2">LƯU Ý ĐẶC BIẾT</span>
                          <strong className="block text-3xl md:text-4xl leading-tight font-black text-red-600 uppercase">{o.note}</strong>
                        </div>
                      )}
                      {o.type === "Giao hàng" && (
                        <div className="delivery-labels">
                          <Icon name="print" size={18} />
                          <div>
                            <strong>2 tem đóng gói</strong>
                            <span>
                              01 · Hộp khô: bánh phở + thịt
                              <br />
                              02 · Bịch nước lèo
                            </span>
                          </div>
                          <Badge
                            tone={
                              o.status === "Chờ lấy hàng" ? "green" : "neutral"
                            }
                          >
                            {o.status === "Chờ lấy hàng"
                              ? "Đã tạo tem"
                              : "Chờ hoàn tất"}
                          </Badge>
                        </div>
                      )}
                      <button
                        className={
                          o.status === "Chờ lấy hàng"
                            ? "secondary-btn full"
                            : "primary-btn full"
                        }
                        onClick={() =>
                          o.status === "Chờ lấy hàng"
                            ? notify(
                                `Mô phỏng in 2 tem cho đơn ${o.id}: hộp khô và nước lèo`,
                              )
                            : updateOrder(
                                o.id,
                                o.type === "Giao hàng"
                                  ? "Chờ lấy hàng"
                                  : "Hoàn tất",
                              )
                        }
                      >
                        <Icon
                          name={o.status === "Chờ lấy hàng" ? "print" : "check"}
                          size={18}
                        />
                        {o.status === "Chờ lấy hàng"
                          ? "In lại 2 tem (demo)"
                          : "Hoàn tất chế biến"}
                      </button>
                    </article>
                  ))}
              </div>
              {!orders.some((o) =>
                ["Đang chế biến", "Chờ lấy hàng"].includes(o.status),
              ) && (
                <div className="panel empty-state">
                  <Icon name="chef" size={42} />
                  <h2>Bếp đã hoàn tất mọi đơn</h2>
                  <p>Đơn mới đã thanh toán sẽ xuất hiện tại đây.</p>
                </div>
              )}
            </>
          )}

          {page === "customer" && (
            <div className="customer-content">
              <div className="customer-welcome">
                <div>
                  <span className="eyebrow">CHÀO MỪNG ĐẾN PHỞ NHÀ</span>
                  <h2>
                    Hương vị thân quen,
                    <br />
                    ấm lòng mỗi ngày.
                  </h2>
                  <p>Nước dùng hầm 12 giờ · Nguyên liệu tươi mỗi sáng</p>
                  <Badge>Đang mở cửa · 06:00 – 22:00</Badge>
                </div>
                <img src={photos[2]} alt="Tô phở nóng hổi tại Phở Nhà" />
              </div>
              <div className="customer-mode segmented">
                {["Tại bàn", "Giao hàng", "Chờ bàn"].map((m) => (
                  <button
                    key={m}
                    className={customerMode === m ? "active" : ""}
                    onClick={() => {
                      setCustomerMode(m)
                      setPayment("VietQR")
                    }}
                  >
                    <Icon
                      name={
                        m === "Tại bàn"
                          ? "table"
                          : m === "Giao hàng"
                            ? "truck"
                            : "clock"
                      }
                      size={18}
                    />
                    {m}
                  </button>
                ))}
              </div>
              {customerMode === "Tại bàn" && (
                <div className="customer-info">
                  <Icon name="qr" size={22} />
                  <div>
                    <strong>Bạn đang gọi món tại Bàn 05</strong>
                    <span>QR bàn đã được nhận diện trong bản demo.</span>
                  </div>
                </div>
              )}
              {customerMode === "Giao hàng" && (
                <div className="customer-info">
                  <Icon name="truck" size={22} />
                  <div>
                    <strong>Phở ngon giao tận nhà</strong>
                    <span>Thanh toán 100% qua VietQR trước khi chế biến.</span>
                  </div>
                </div>
              )}
              {customerMode === "Chờ bàn" && (
                <div className="waiting-customer panel">
                  {queueTicket ? (
                    <>
                      <span>SỐ THỨ TỰ CỦA BẠN</span>
                      <strong className="ticket-large">{queueTicket}</strong>
                      <p>
                        {called === queueTicket
                          ? "Đã đến lượt! Mời bạn vào quán và quét QR tại bàn."
                          : "Bạn có thể chọn món trước trong lúc chờ. Chưa cần thanh toán."}
                      </p>
                      <button
                        className="primary-btn"
                        onClick={() => {
                          setCustomerMode("Tại bàn")
                          notify(
                            "Mô phỏng quét QR Bàn 05. Giỏ hàng của bạn được giữ nguyên.",
                          )
                        }}
                      >
                        <Icon name="qr" size={18} />
                        Quét QR bàn (demo)
                      </button>
                    </>
                  ) : (
                    <>
                      <h2>Giữ chỗ, không cần đứng chờ</h2>
                      <p>
                        {queue.length} nhóm khách đang chờ · Dự kiến khoảng 12
                        phút
                      </p>
                      <button
                        className="primary-btn"
                        onClick={() => {
                          const number =
                            "A" + String(21 + queue.length).padStart(3, "0")
                          setQueueTicket(number)
                          setQueue([
                            ...queue,
                            {
                              number,
                              name: "Khách QR",
                              people: 2,
                              time: "0 phút",
                            },
                          ])
                          notify(`Số xếp hàng của bạn: ${number}`)
                        }}
                      >
                        Lấy số xếp hàng
                        <Icon name="arrow" size={18} />
                      </button>
                    </>
                  )}
                </div>
              )}
              {activeCustomerOrder && (
                <div
                  className="panel customer-order"
                  id="customer-active-order"
                >
                  <div>
                    <strong>Đơn của bạn · #{activeCustomerOrder.id}</strong>
                    <Status status={activeCustomerOrder.status} />
                  </div>
                  <p>
                    {activeCustomerOrder.items} ·{" "}
                    {money(activeCustomerOrder.total)}
                  </p>
                  {activeCustomerOrder.status === "Chờ xác nhận QR" && (
                    <div className="qr-payment">
                      <div
                        className="demo-qr"
                        aria-label="Mã QR minh họa, không dùng để thanh toán"
                      >
                        {Array.from({ length: 121 }, (_, i) => (
                          <i
                            key={i}
                            className={
                              (i * 7 + Math.floor(i / 11) * 3) % 5 < 3
                                ? "filled"
                                : ""
                            }
                          />
                        ))}
                      </div>
                      <div>
                        <h3>Thanh toán VietQR</h3>
                        <strong>{money(activeCustomerOrder.total)}</strong>
                        <p>
                          Nội dung: {activeCustomerOrder.id}
                          <br />
                          QR minh họa, không chuyển tiền thật.
                        </p>
                        <button
                          className="primary-btn"
                          onClick={() =>
                            updateOrder(activeCustomerOrder.id, "Đang chế biến")
                          }
                        >
                          <Icon name="check" size={17} />
                          Mô phỏng nhận thanh toán
                        </button>
                      </div>
                    </div>
                  )}
                  {activeCustomerOrder.status === "Chờ thanh toán" && (
                    <p className="cash-notice">
                      Vui lòng thanh toán tiền mặt tại quầy. Bếp sẽ nhận đơn sau
                      khi thu ngân xác nhận.
                    </p>
                  )}
                </div>
              )}
              <div className="customer-menu-title">
                <h2>Chọn món bạn yêu thích</h2>
                <span>
                  {
                    dishes.filter(
                      (d) =>
                        d.available &&
                        (customerCategory === "Tất cả" ||
                          d.category === customerCategory),
                    ).length
                  }{" "}
                  món sẵn sàng
                </span>
              </div>
              <div className="customer-category-tabs">
                {[
                  "Tất cả",
                  "Phở bò",
                  "Phở gà",
                  "Phở trẻ em",
                  "Nước uống",
                ].map((category) => (
                  <button
                    key={category}
                    className={customerCategory === category ? "active" : ""}
                    onClick={() => setCustomerCategory(category)}
                  >
                    {category}
                  </button>
                ))}
              </div>
              <div className="customer-dish-grid">
                {dishes
                  .filter(
                    (d) =>
                      d.available &&
                      (customerCategory === "Tất cả" ||
                        d.category === customerCategory),
                  )
                  .map((d) => (
                    <article
                      className={`panel customer-dish ${
                        d.category === "Nước uống" ? "drink-dish" : ""
                      }`}
                      key={d.id}
                    >
                      <img src={d.image} alt={d.name} />
                      <div>
                        <h3>{d.name}</h3>
                        <p>{d.desc}</p>
                        <div>
                          <strong>{money(d.price)}</strong>
                          <button
                            className="add-dish-btn"
                            onClick={() => {
                              if (d.category === "Nước uống") {
                                setCart([
                                  ...cart,
                                  { dish: d, extras: [], price: d.price },
                                ])
                                notify(`Đã thêm ${d.name} vào giỏ hàng`)
                              } else {
                                setCustomDish(d)
                                setExtras([])
                              }
                            }}
                            aria-label={`Thêm ${d.name}`}
                          >
                            <Icon name="plus" size={19} />
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
              </div>
              {cart.length > 0 && (
                <div className="cart-bar">
                  <span>
                    <strong>{cart.length} món</strong> · {money(totalCart)}
                  </span>
                  <button
                    className="primary-btn"
                    onClick={() =>
                      customerMode === "Chờ bàn"
                        ? notify(
                            "Giỏ hàng đã được giữ. Quét QR tại bàn để đặt món khi đến lượt.",
                          )
                        : setCheckout(true)
                    }
                  >
                    {customerMode === "Chờ bàn" ? "Giữ giỏ hàng" : "Đặt món"}
                    <Icon name="arrow" size={17} />
                  </button>
                </div>
              )}
            </div>
          )}

          {page === "settings" && (
            <section className="panel settings-panel">
              <h2>Thông tin cửa hàng</h2>
              <p>Cập nhật thông tin hiển thị với khách hàng.</p>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  setSettingsSaved(true)
                  notify("Đã lưu cài đặt trong phiên demo")
                }}
              >
                <label>
                  Tên cửa hàng
                  <input defaultValue="Phở Nhà · Quận 1" required />
                </label>
                <label>
                  Địa chỉ
                  <input
                    defaultValue="28 Nguyễn Du, Bến Nghé, Quận 1, TP. HCM"
                    required
                  />
                </label>
                <div className="form-columns">
                  <label>
                    Giờ mở cửa
                    <input type="time" defaultValue="06:00" required />
                  </label>
                  <label>
                    Giờ đóng cửa
                    <input type="time" defaultValue="22:00" required />
                  </label>
                </div>
                <label>
                  Số điện thoại
                  <input type="tel" defaultValue="028 3822 5566" required />
                </label>
                <label className="checkbox-label">
                  <input type="checkbox" defaultChecked />
                  Tự động chuyển đơn đã thanh toán đến bếp
                </label>
                <button className="primary-btn">
                  <Icon name="check" size={18} />
                  Lưu thay đổi
                </button>
                {settingsSaved && (
                  <p className="success-text">
                    Thông tin đã được lưu trong phiên trải nghiệm.
                  </p>
                )}
              </form>
            </section>
          )}
          {page === "help" && (
            <section className="panel help-panel">
              <span className="stat-icon red">
                <Icon name="help" size={26} />
              </span>
              <h2>Vận hành Phở Nhà thật dễ dàng</h2>
              <p>Khám phá luồng làm việc tự động giữa các bộ phận.</p>
              {[
                {
                  title: "1. Khách chọn món & thanh toán",
                  text: "Khách quét QR tại bàn, tùy biến phở, đặt món và thanh toán VietQR hoặc tiền mặt. Đơn giao hàng chỉ thanh toán VietQR.",
                },
                {
                  title: "2. Thu ngân xác nhận & điều phối",
                  text: "Xác nhận đơn tiền mặt, gọi số tiếp theo và bàn giao đơn cho đơn vị giao hàng.",
                },
                {
                  title: "3. Bếp chế biến & hoàn tất",
                  text: "Bếp chỉ nhận đơn thanh toán hợp lệ. Lưu ý tùy biến được làm nổi bật. Đơn giao hàng cần 2 tem đóng gói.",
                },
                {
                  title: "4. Quản lý theo dõi kinh doanh",
                  text: "Cập nhật món ăn, giá bán, định lượng topping và theo dõi doanh thu tại bàn / giao hàng.",
                },
              ].map((item) => (
                <details key={item.title}>
                  <summary>
                    {item.title}
                    <Icon name="down" size={17} />
                  </summary>
                  <p>{item.text}</p>
                </details>
              ))}
              <p className="demo-note">
                Đây là bản demo tương tác. Thanh toán, máy in và giao vận cần
                tích hợp dịch vụ thật trước khi vận hành.
              </p>
            </section>
          )}
          {page !== "home" && <footer className="page-footer">
            <span>
              <span className="footer-logo">phở nhà.</span> Tinh gọn vận hành,
              trọn vẹn hương vị.
            </span>
            <span>
              <i />
              Hệ thống hoạt động ổn định{" "}
              <span className="footer-separator">·</span> Phiên bản 1.0
            </span>
          </footer>}
        </main>
      </div>

      {selectedOrder && (
        <Modal
          title={`Chi tiết đơn #${selectedOrder.id}`}
          onClose={() => setSelectedOrder(null)}
        >
          <div className="order-detail-header">
            <div>
              <strong>{selectedOrder.table}</strong>
              <p>
                {selectedOrder.type} · {selectedOrder.time}
              </p>
            </div>
            <Status status={selectedOrder.status} />
          </div>
          <div className="detail-items">
            {(selectedOrder.itemDetails ||
              selectedOrder.items.split(", ").map((name) => ({
                name,
                extras: [],
              }))
            ).map((item, index) => (
              <p key={`${item.name}-${index}`}>
                <Icon name="menu" size={18} />
                <span>
                  {item.name}
                  {item.extras.length > 0 && (
                    <small>{item.extras.join(" · ")}</small>
                  )}
                </span>
              </p>
            ))}
          </div>
          {selectedOrder.note && (
            <div className="kitchen-note">
              <span>YÊU CẦU CỦA KHÁCH</span>
              <strong>{selectedOrder.note}</strong>
            </div>
          )}
          {selectedOrder.address && (
            <p className="delivery-address">
              <Icon name="truck" size={18} />
              {selectedOrder.address}
            </p>
          )}
          <div className="detail-total">
            <span>
              Tổng thanh toán <small>{selectedOrder.payment}</small>
            </span>
            <strong>{money(selectedOrder.total)}</strong>
          </div>
          {selectedOrder.type === "Giao hàng" && (
            <div className="tracking-info">
              <span>Mã vận đơn (demo)</span>
              <strong>GHN-{selectedOrder.id.replace("PH-", "")}-VN</strong>
            </div>
          )}
          {selectedOrder.status === "Chờ thanh toán" ? (
            <button
              className="primary-btn full"
              onClick={() => updateOrder(selectedOrder.id, "Đang chế biến")}
            >
              <Icon name="check" size={18} />
              Xác nhận đã nhận tiền mặt
            </button>
          ) : selectedOrder.status === "Chờ lấy hàng" ? (
            <button
              className="primary-btn full"
              onClick={() => updateOrder(selectedOrder.id, "Hoàn tất")}
            >
              <Icon name="truck" size={18} />
              Đã bàn giao cho đơn vị giao hàng
            </button>
          ) : selectedOrder.status === "Chờ xác nhận QR" ? (
            <p className="cash-notice">
              Đang chờ thông báo thanh toán từ VietQR. Mô phỏng xác nhận ở giao
              diện khách hàng.
            </p>
          ) : (
            <button
              className="secondary-btn full"
              onClick={() => {
                setSelectedOrder(null)
                go("kitchen")
              }}
            >
              Xem màn hình bếp
              <Icon name="arrow" size={18} />
            </button>
          )}
        </Modal>
      )}
      {dishEditor && (
        <Modal
          title={dishEditor.id ? "Chỉnh sửa món ăn" : "Thêm món mới"}
          onClose={() => setDishEditor(null)}
        >
          <form
            className="dish-form"
            onSubmit={(e) => {
              e.preventDefault()
              saveDish()
            }}
          >
            <label>
              Tên món
              <input
                required
                value={dishEditor.name || ""}
                onChange={(e) =>
                  setDishEditor({ ...dishEditor, name: e.target.value })
                }
                placeholder="Ví dụ: Phở bò tái"
              />
            </label>
            <label>
              Mô tả
              <textarea
                value={dishEditor.desc || ""}
                onChange={(e) =>
                  setDishEditor({ ...dishEditor, desc: e.target.value })
                }
                placeholder="Hương vị và nguyên liệu nổi bật..."
                rows={3}
              />
            </label>
            <div className="form-columns">
              <label>
                Giá bán (₫)
                <input
                  required
                  type="number"
                  min="1000"
                  step="1000"
                  value={dishEditor.price || ""}
                  onChange={(e) =>
                    setDishEditor({
                      ...dishEditor,
                      price: Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                Danh mục
                <select
                  value={dishEditor.category || "Phở bò"}
                  onChange={(e) =>
                    setDishEditor({ ...dishEditor, category: e.target.value })
                  }
                >
                  <option>Phở bò</option>
                  <option>Phở gà</option>
                  <option>Phở trẻ em</option>
                  <option>Nước uống</option>
                </select>
              </label>
            </div>
            <button className="primary-btn full">
              <Icon name="check" size={18} />
              Lưu món ăn
            </button>
          </form>
        </Modal>
      )}
      {customDish && (
        <Modal title={customDish.name} onClose={() => setCustomDish(null)}>
          <img
            className="custom-dish-image"
            src={customDish.image}
            alt={customDish.name}
          />
          <p className="muted">
            {customDish.category === "Nước uống"
              ? "Thức uống mát lạnh dùng cùng món ngon."
              : "Một tô phở theo đúng sở thích của bạn."}
          </p>
          {customDish.category !== "Nước uống" && (
            <>
              <h3>Tùy chỉnh bắt buộc</h3>
              <div className="custom-options mb-4">
                <label className="checkbox-label">
                  <input type="radio" name="nuoc-dung" checked={!extras.includes("Nước béo")} onChange={() => setExtras(extras.filter(x => x !== "Nước béo"))} />
                  Nước trong (Thanh vị)
                </label>
                <label className="checkbox-label">
                  <input type="radio" name="nuoc-dung" checked={extras.includes("Nước béo")} onChange={() => setExtras([...extras.filter(x => x !== "Nước béo"), "Nước béo"])} />
                  Nước béo (Đậm đà)
                </label>
              </div>

              <h3>Rau & Topping thêm</h3>
              <div className="custom-options">
                {[
                  "Không hành",
                  "Không giá",
                  ...toppings.map((t) => t.name),
                ].map((e) => (
                  <label className="checkbox-label" key={e}>
                    <input
                      type="checkbox"
                      checked={extras.includes(e)}
                      onChange={() =>
                        setExtras(
                          extras.includes(e)
                            ? extras.filter((x) => x !== e)
                            : [...extras, e],
                        )
                      }
                    />
                    {e}
                    {toppings.find((t) => t.name === e) &&
                      ` +${money(toppings.find((t) => t.name === e)!.price)}`}
                  </label>
                ))}
              </div>
            </>
          )}
          <button
            className="primary-btn full"
            onClick={() => {
              setCart([
                ...cart,
                {
                  dish: customDish,
                  extras,
                  price: customDish.price + extrasPrice,
                },
              ])
              setCustomDish(null)
              notify("Đã thêm món vào giỏ hàng")
            }}
          >
            <Icon name="plus" size={18} />
            Thêm vào giỏ · {money(customDish.price + extrasPrice)}
          </button>
        </Modal>
      )}
      {checkout && (
        <Modal title="Giỏ hàng của bạn" onClose={() => setCheckout(false)}>
          <div className="cart-items">
            {cart.map((c, i) => (
              <div key={i}>
                <img src={c.dish.image} alt={c.dish.name} />
                <div>
                  <strong>{c.dish.name}</strong>
                  <span>{c.extras.join(", ") || "Vị nguyên bản"}</span>
                  <b>{money(c.price)}</b>
                </div>
                <button
                  className="icon-btn"
                  aria-label="Bỏ món"
                  onClick={() =>
                    setCart(cart.filter((_, index) => index !== i))
                  }
                >
                  <Icon name="trash" size={17} />
                </button>
              </div>
            ))}
          </div>
          {customerMode === "Giao hàng" && (
            <div className="dish-form">
              <label>
                Tên người nhận
                <input
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Họ và tên"
                />
              </label>
              <label>
                Địa chỉ giao hàng
                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Số nhà, đường, phường, quận"
                />
              </label>
            </div>
          )}
          <h3>Phương thức thanh toán</h3>
          <div className="payment-options">
            {(customerMode === "Giao hàng"
              ? ["VietQR"]
              : ["VietQR", "Tiền mặt"]
            ).map((p) => (
              <label key={p}>
                <input
                  type="radio"
                  name="payment"
                  checked={payment === p}
                  onChange={() => setPayment(p)}
                />
                <Icon name={p === "VietQR" ? "qr" : "wallet"} size={20} />
                <strong>{p}</strong>
              </label>
            ))}
          </div>
          <div className="detail-total">
            <span>Tổng cộng</span>
            <strong>{money(totalCart)}</strong>
          </div>
          <button
            className="primary-btn full"
            disabled={!cart.length || customerMode === "Chờ bàn"}
            onClick={placeOrder}
          >
            Xác nhận đặt món
            <Icon name="arrow" size={18} />
          </button>
          <p className="demo-note">
            Đơn chỉ chuyển đến bếp sau khi xác nhận thanh toán.
          </p>
        </Modal>
      )}
      {toast && (
        <div className="toast" role="status">
          <span>
            <Icon name="check" size={19} />
          </span>
          {toast}
          <button
            className="icon-btn"
            onClick={() => setToast("")}
            aria-label="Đóng thông báo"
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
