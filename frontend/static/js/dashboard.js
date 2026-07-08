document.addEventListener("DOMContentLoaded", function () {
    loadProducts();
    loadStats();
    loadSales();
    checkLowStock();
    loadRecentSales(); // ✅ NEW

    setInterval(() => { 
        loadProducts(); 
        loadStats(); 
        checkLowStock(); 
    }, 30000);
});

let currentEditId = null;
const CRITICAL_THRESHOLD = 5;

// ==================== PRODUCTS ====================

async function loadProducts() {
    const res = await fetch("/api/get_products");
    const data = await res.json();

    const searchEl = document.getElementById("searchInput");
    const categoryEl = document.getElementById("categoryFilter");

    const search = searchEl ? searchEl.value.toLowerCase() : "";
    const category = categoryEl ? categoryEl.value : "";

    const tbody = document.querySelector("#productTable tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const categories = new Set();
    let lowStockItems = [];
    let criticalItems = [];

    const path = window.location.pathname;
    const isDashboard = path.includes("dashboard");
    const isProductListPage = path.includes("product_list_page");

    const showActions = !(isDashboard || isProductListPage);

    let filtered = data.filter(p =>
        (p.name.toLowerCase().includes(search) || p.sku.toLowerCase().includes(search)) &&
        (!category || p.category === category)
    );

    let displayData = isDashboard ? filtered.slice(0, 12) : filtered;

    displayData.forEach(p => {
        const stock = Number(p.stock);

        categories.add(p.category);
        if (p.is_low && stock > 0) lowStockItems.push(p);
        if (stock <= CRITICAL_THRESHOLD) criticalItems.push(p);

        let stockBox = "";
        let statusBox = "";

        if (stock === 0) {
            stockBox = `<span style="padding:4px 10px;border-radius:8px;background:#ffd6d6;color:#8b0000;">${stock} units</span>`;
            statusBox = `<span style="padding:4px 10px;border-radius:8px;background:#ffd6d6;color:#8b0000;">Out of Stock</span>`;
        } 
        else if (stock <= CRITICAL_THRESHOLD) {
            stockBox = `<span style="padding:4px 10px;border-radius:8px;background:#ffe6c7;color:#cc5500;">${stock} units</span>`;
            statusBox = `<span style="padding:4px 10px;border-radius:8px;background:#ffe6c7;color:#cc5500;">Low Stock</span>`;
        } 
        else {
            stockBox = `<span style="padding:4px 10px;border-radius:8px;background:#d6f5d6;color:#0b6b0b;">${stock} units</span>`;
            statusBox = `<span style="padding:4px 10px;border-radius:8px;background:#d6f5d6;color:#0b6b0b;">In Stock</span>`;
        }

        tbody.innerHTML += `<tr>
           <td>${formatProductId(p.id)}</td>
            <td>${p.name}</td>
            <td>${p.sku}</td>
            <td>${p.category}</td>
            <td>${stockBox}</td>
            <td>${statusBox}</td>
            <td>${p.price}</td>
           ${showActions ? `
<td>
    <button class="sell" onclick="sellProduct(${p.id},${stock})">Sell</button>
    <button class="edit" onclick="openEditModal(${p.id})">Edit</button>
    <button class="delete" onclick="deleteProduct(${p.id})">Delete</button>
</td>
` : ``}
        </tr>`;
    });

    if (isDashboard) {
        tbody.innerHTML += `
        <tr>
            <td colspan="7" style="text-align:center; position:sticky; bottom:0; background:#2c2c2c; z-index:5;">
                <button onclick="window.location.href='/api/product_list_page'"
                    style="background:none; border:none; color:#4da6ff; cursor:pointer; font-size:14px;">
                    View All Products ▶
                </button>
            </td>
        </tr>`;
    }

    if (categoryEl) {
        categoryEl.innerHTML = '<option value="">All</option>';
        categories.forEach(cat => {
            if (cat) categoryEl.innerHTML += `<option value="${cat}">${cat}</option>`;
        });
    }

    updateLowStockModal(lowStockItems, criticalItems);
}

// ==================== STATS ====================

async function loadStats() {
    const res = await fetch("/api/stats");
    const data = await res.json();

    const totalProducts = document.getElementById("totalProducts");
    const totalSales = document.getElementById("totalSales");
    const lowStock = document.getElementById("lowStock");
    const outOfStock = document.getElementById("outOfStock");

    if(totalProducts) totalProducts.innerText = data.total_products;
    if(totalSales) totalSales.innerText = data.total_sales;
    if(lowStock) lowStock.innerText = data.low_stock;

    const res2 = await fetch("/api/get_products");
    const products = await res2.json();

    const outCount = products.filter(p => Number(p.stock) === 0).length;

    if(outOfStock) outOfStock.innerText = outCount;
}

// ==================== SALES ====================

async function loadSales() {
    const table = document.querySelector("#salesTable tbody");
    if (!table) return;

    const res = await fetch("/api/get_sales");
    const data = await res.json();

    table.innerHTML = "";

    data.forEach(s => {
        table.innerHTML += `<tr>
            <td>${s.id}</td>
            <td>${s.product_name}</td>
            <td>${s.quantity}</td>
            <td>${s.total_price}</td>
            <td>${s.date}</td>
        </tr>`;
    });
}

// ==================== SELL ====================

async function sellProduct(productId, currentStock){
    let qty = prompt(`Enter quantity to sell (max ${currentStock}):`);
    if(qty === null) return;

    qty = parseInt(qty);

    if(isNaN(qty) || qty <= 0){
        alert("Invalid quantity");
        return;
    }

    if(qty > currentStock){
        alert("Quantity exceeds stock");
        return;
    }

    const res = await fetch("/api/add_sale", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({product_id: productId, quantity: qty})
    });

    const data = await res.json();

    if(data.error){
        alert(data.error);
        return;
    }

    loadProducts();
    loadStats();
    loadSales();
    loadRecentSales(); // ✅ NEW
}

// ==================== LOW STOCK ====================

function updateLowStockModal(lowStockItems, criticalItems){
    const ul = document.getElementById("lowStockList");
    if(!ul) return;

    ul.innerHTML = "";

    const allItems = [...criticalItems, ...lowStockItems.filter(i => !criticalItems.includes(i))];

    allItems.forEach(p=>{
        ul.innerHTML += `<li>${p.name} (Stock: ${p.stock})</li>`;
    });
}

function checkLowStock(){
    const ul = document.getElementById("lowStockList");

    if(ul && ul.children.length > 0){
        document.getElementById("lowStockModal").style.display="block";
    }
}

function closeLowStockModal(){
    document.getElementById("lowStockModal").style.display="none";
}

// ================= QUICK SALE =================

async function quickSale(){
    const productId = document.getElementById("quickProduct").value;
    const qty = parseInt(document.getElementById("quickQty").value);

    if(!productId || !qty){
        alert("Select product and quantity");
        return;
    }

    const res = await fetch("/api/add_sale", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({product_id: productId, quantity: qty})
    });

    const data = await res.json();

    if(data.error){
        alert(data.error);
        return;
    }

    loadProducts();
    loadStats();
    loadSales();
    loadRecentSales(); // ✅ NEW
}

// ================= RECENT SALES =================
async function loadRecentSales(){
    const res = await fetch("/api/get_sales");
    const data = await res.json();

    const list = document.getElementById("recentSalesList");
    if(!list) return;

    list.innerHTML = "";

    const recent = data.slice(0, 3);

    recent.forEach(s => {
       list.innerHTML += `
    <li>
        <div>
            <strong>${s.product_name}</strong>
            <span class="qty">×${s.quantity}</span>
        </div>

        <span class="price">+ ₹${s.total_price}</span>
    </li>
`;
    });
}

// ================= DROPDOWN =================

async function loadQuickProducts(){
    const res = await fetch("/api/get_products");
    const data = await res.json();

    const select = document.getElementById("quickProduct");
    if(!select) return;

    select.innerHTML = "<option value=''>Select Product</option>";

    data.forEach(p=>{
        select.innerHTML += `<option value="${p.id}">${p.name}</option>`;
    });
}

document.addEventListener("DOMContentLoaded", loadQuickProducts);

function openEditModal(id){
    currentEditId = id;

    // product find karo
    fetch("/api/get_products")
    .then(res => res.json())
    .then(data => {
        const p = data.find(x => x.id === id);

        if(!p) return;

        document.getElementById("editName").value = p.name;
        document.getElementById("editSku").value = p.sku;
        document.getElementById("editCategory").value = p.category;
        document.getElementById("editStock").value = p.stock;
        document.getElementById("editPrice").value = p.price;

        document.getElementById("editModal").style.display = "block";
    });
}

async function deleteProduct(id){
    if(!confirm("Are you sure?")) return;

    const res = await fetch(`/api/delete_product/${id}`, {
        method: "DELETE"
    });

    const data = await res.json();

    if(data.error){
        alert(data.error);
        return;
    }

    loadProducts();
    loadStats();
}
async function saveEdit(){
    const updatedProduct = {
        name: document.getElementById("editName").value,
        sku: document.getElementById("editSku").value,
        category: document.getElementById("editCategory").value,
        stock: document.getElementById("editStock").value,
        price: document.getElementById("editPrice").value
    };

    const res = await fetch(`/api/update_product/${currentEditId}`, {
        method: "PUT",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(updatedProduct)
    });

    const data = await res.json();

    if(data.error){
        alert(data.error);
        return;
    }

    document.getElementById("editModal").style.display = "none";

    loadProducts();
    loadStats();
}
function closeModal(){
    document.getElementById("editModal").style.display = "none";
}
async function addProduct(){

    const name = document.getElementById("name")?.value?.trim();
    const sku = document.getElementById("sku")?.value?.trim();
    const category = document.getElementById("category")?.value?.trim();
    const stock = Number(document.getElementById("stock")?.value);
    const price = Number(document.getElementById("price")?.value);

    if(!name || !sku){
        alert("Name aur SKU required hai");
        return;
    }

    const res = await fetch("/api/add_product", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({name, sku, category, stock, price})
    });

    const data = await res.json();

    if(!res.ok || data.error){
        alert(data.error || "Product add nahi hua");
        return;
    }

    // reset form
    document.getElementById("name").value = "";
    document.getElementById("sku").value = "";
    document.getElementById("category").value = "";
    document.getElementById("stock").value = "";
    document.getElementById("price").value = "";

    document.getElementById("productForm").style.display = "none";

    loadProducts();
    loadStats();

    alert("Product added successfully");
}

function toggleForm(){
    const modal = document.getElementById("productForm");

    if(!modal) return;

    if(modal.style.display === "flex"){
        modal.style.display = "none";
    } else {
        modal.style.display = "flex";
    }
}

fetch('/api/stock-summary')
  .then(res => res.json())
  .then(data => {

    const ctx = document.getElementById('stockChart').getContext('2d');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['In Stock', 'Low Stock', 'Out of Stock'],
            datasets: [{
                data: [
                    data.in_stock,
                    data.low_stock,
                    data.out_of_stock
                ],
                backgroundColor: ['#4CAF50', '#FF9800', '#F44336']
            }]
        },
        options: {
            cutout: '65%',
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });

  });
  function loadSalesChart() {
    const ctx = document.getElementById("salesChart");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Product A", "Product B", "Product C", "Product D", "Product E"],
            datasets: [{
                label: "Sales",
                data: [2500, 1800, 1600, 1400, 1200],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

loadSalesChart();
function formatProductId(id) {
    return "PRD-" + String(id).padStart(3, '0');
}