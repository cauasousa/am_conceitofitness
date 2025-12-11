(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const CART_KEY = "cart_v1"; // Mesma chave usada em cart.js
        let inMemoryCart = null;

        function safeLocalStorage() {
            try {
                return window.localStorage;
            } catch (err) {
                return null;
            }
        }

        function loadCart() {
            try {
                const ls = safeLocalStorage();
                if (!ls) return inMemoryCart ? Array.from(inMemoryCart) : [];
                const raw = ls.getItem(CART_KEY);
                return JSON.parse(raw || "[]");
            } catch (e) {
                console.warn("localStorage inacessível, usando fallback em memória:", e);
                return inMemoryCart ? Array.from(inMemoryCart) : [];
            }
        }

        function saveCart(c) {
            try {
                const ls = safeLocalStorage();
                if (ls) {
                    ls.setItem(CART_KEY, JSON.stringify(c));
                } else {
                    inMemoryCart = Array.from(c);
                }
            } catch (e) {
                console.warn("Falha ao salvar no localStorage, usando fallback em memória:", e);
                inMemoryCart = Array.from(c);
            }
            updateCartUI();
        }

        function updateCartUI() {
            try {
                const cart = Array.isArray(loadCart()) ? loadCart() : [];
                const cartCountEl = document.getElementById("cart-count");
                if (cartCountEl) cartCountEl.innerText = cart.reduce((s, i) => s + (i.qty || 0), 0);
                const itemsEl = document.getElementById("cart-items");
                const totalEl = document.getElementById("cart-total");
                if (itemsEl) {
                    itemsEl.innerHTML = "";
                    let total = 0;
                    if (cart.length === 0) itemsEl.innerHTML = "<div class='text-sm text-gray-500'>Carrinho vazio</div>";
                    cart.forEach((it, idx) => {
                        total += (it.price || 0) * (it.qty || 0);
                        const div = document.createElement("div");
                        div.className = "flex items-center justify-between";
                        div.innerHTML = `<div><div class="font-semibold">${it.name}</div><div class="text-sm text-gray-600">Tamanho: ${it.size || ''}</div></div><div class="text-sm">R$ ${((it.price || 0) * (it.qty || 0)).toFixed(2)} <button data-idx="${idx}" class="remove text-red-500 ml-2">x</button></div>`;
                        itemsEl.appendChild(div);
                    });
                    if (totalEl) totalEl.innerText = total.toFixed(2);
                    itemsEl.querySelectorAll(".remove").forEach(btn => {
                        btn.addEventListener("click", e => {
                            const idx = parseInt(e.target.dataset.idx, 10);
                            const c = loadCart(); c.splice(idx, 1); saveCart(c);
                        });
                    });
                }
            } catch (err) {
                console.warn("updateCartUI falhou:", err);
            }
        }

        function addItemToCart(item) {
            try {
                const cart = loadCart();
                const existing = cart.find(i => i.id === item.id && i.size === item.size);
                if (existing) {
                    existing.qty += item.qty;
                } else {
                    cart.push(item);
                }
                saveCart(cart);
            } catch (err) {
                console.warn("Erro ao adicionar ao carrinho:", err);
            }
        }

        // Cart button
        const cartBtn = document.getElementById("cart-btn");
        if (cartBtn) {
            cartBtn.addEventListener("click", () => {
                try {
                    const panel = document.getElementById("cart-panel");
                    if (panel) {
                        panel.classList.toggle("hidden");
                        updateCartUI();
                    }
                } catch (err) {
                    console.warn("Erro ao abrir painel do carrinho:", err);
                }
            });
        }

        // Close cart panel
        const closeCartBtn = document.getElementById("close-cart");
        if (closeCartBtn) {
            closeCartBtn.addEventListener("click", () => {
                const panel = document.getElementById("cart-panel");
                if (panel) panel.classList.add("hidden");
            });
        }

        // Inicializar UI do carrinho
        updateCartUI();

        // Expor funções globalmente se necessário
        window.addItemToCart = addItemToCart;
        window.loadCart = loadCart;
        window.saveCart = saveCart;
        window.updateCartUI = updateCartUI;
    });
})();
