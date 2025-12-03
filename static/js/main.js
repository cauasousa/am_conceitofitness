(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const CART_KEY = "am_cart_v1";
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
                // fallback para memória e evitar crash por SecurityError
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
                        div.innerHTML = `<div><div class="font-semibold">${it.name}</div><div class="text-sm text-gray-600">${it.size || ''} ${it.color || ''}</div></div><div class="text-sm">R$ ${((it.price || 0) * (it.qty || 0)).toFixed(2)} <button data-idx="${idx}" class="remove text-red-500 ml-2">x</button></div>`;
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

        // Add buttons (páginas admin podem não ter)
        document.querySelectorAll(".add-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                try {
                    const card = btn.closest(".bg-white");
                    if (!card) return;
                    const id = btn.dataset.id;
                    const name = btn.dataset.name;
                    const price = parseFloat(btn.dataset.price) || 0;
                    const sizeEl = card.querySelector(".size-select");
                    const colorEl = card.querySelector(".color-select");
                    const qtyEl = card.querySelector(".qty-input");
                    const size = sizeEl ? sizeEl.value : "";
                    const color = colorEl ? colorEl.value : "";
                    const qty = qtyEl ? (parseInt(qtyEl.value, 10) || 1) : 1;
                    if (!size) { alert("Escolha um tamanho"); return; }
                    if (!color) { alert("Escolha uma cor"); return; }
                    const cart = loadCart();
                    cart.push({ id, name, price, size, color, qty });
                    saveCart(cart);
                    const panel = document.getElementById("cart-panel");
                    if (panel) panel.classList.remove("hidden");
                } catch (e) {
                    console.warn("Erro ao adicionar ao carrinho:", e);
                    alert("Não foi possível adicionar ao carrinho neste ambiente.");
                }
            });
        });

        // Cart button
        const cartBtn = document.getElementById("cart-btn");
        if (cartBtn) {
            cartBtn.addEventListener("click", () => {
                try {
                    const panel = document.getElementById("cart-panel");
                    if (panel) panel.classList.toggle("hidden");
                    updateCartUI();
                } catch (e) {
                    console.warn("Erro ao abrir/fechar painel do carrinho:", e);
                }
            });
        }

        // Checkout -> abrir WhatsApp
        const checkoutBtn = document.getElementById("checkout-btn");
        if (checkoutBtn) {
            checkoutBtn.addEventListener("click", () => {
                try {
                    const cart = loadCart();
                    if (cart.length === 0) { alert("Carrinho vazio"); return; }
                    const lines = [];
                    lines.push("Olá! Gostaria de fazer um pedido da loja AM Conceito Fitness 🌷🤍");
                    lines.push("");
                    let total = 0;
                    cart.forEach((it, i) => {
                        lines.push(`${i + 1}. ${it.name} - ${it.size} - ${it.color} x${it.qty} - R$ ${((it.price || 0) * (it.qty || 0)).toFixed(2)}`);
                        total += (it.price || 0) * (it.qty || 0);
                    });
                    lines.push("");
                    lines.push(`Total: R$ ${total.toFixed(2)}`);
                    lines.push("");
                    lines.push("Meus dados: [Nome, Telefone, Endereço]");
                    lines.push("Instagram: @am_conceitofitness");
                    const text = encodeURIComponent(lines.join("\n"));
                    const url = `https://wa.me/?text=${text}`;
                    window.open(url, "_blank");
                } catch (e) {
                    console.warn("Erro no checkout:", e);
                    alert("Não foi possível iniciar o checkout neste ambiente.");
                }
            });
        }

        // init
        updateCartUI();

        // preencher modal
        document.querySelectorAll(".open-modal").forEach(btn => {
            btn.addEventListener("click", () => {
                const card = btn.closest(".bg-white");
                if (!card) return;
                const id = btn.dataset.id;
                const name = btn.dataset.name;
                const price = parseFloat(btn.dataset.price) || 0;
                const sizeEl = card.querySelector(".size-select");
                const colorEl = card.querySelector(".color-select");
                const qtyEl = card.querySelector(".qty-input");
                const size = sizeEl ? sizeEl.value : "";
                const color = colorEl ? colorEl.value : "";
                const qty = qtyEl ? (parseInt(qtyEl.value, 10) || 1) : 1;
                // preencher modal
                const modalName = document.getElementById('modal-produto-nome');
                const modalPrice = document.getElementById('modal-produto-preco');
                const modalSize = document.getElementById('modal-produto-tamanho');
                const modalColor = document.getElementById('modal-produto-cor');
                const modalQty = document.getElementById('modal-produto-quantidade');
                const modalImage = document.getElementById('modal-produto-imagem');
                if (modalName) modalName.textContent = name;
                if (modalPrice) modalPrice.textContent = `R$ ${price.toFixed(2)}`;
                if (modalSize) modalSize.textContent = size;
                if (modalColor) modalColor.textContent = color;
                if (modalQty) modalQty.textContent = qty;
                const imgEl = card.querySelector("img");
                if (modalImage && imgEl) modalImage.src = imgEl.src;
                // preencher link "Ver detalhes" dentro do modal, se existir
                const modalDetailLink = document.getElementById('modal-detail-link');
                if (modalDetailLink) {
                    modalDetailLink.href = `/produto/${encodeURIComponent(id)}`;
                }
            });
        });

        // --- CAROUSEL (index): setas prev/next que rolam a track horizontalmente ---
        document.querySelectorAll('.carousel-track').forEach(track => {
            const container = track;
            // o wrapper com posição relativa envolve o track e os botões
            const wrapper = container.closest('.relative') || container.parentElement;
            const prev = wrapper ? wrapper.querySelector('.carousel-prev') : null;
            const next = wrapper ? wrapper.querySelector('.carousel-next') : null;
            const scrollAmount = container.clientWidth || 300;
            // show arrows if overflow
            function updateArrows() {
                if (!prev || !next) return;
                const maxScroll = container.scrollWidth - container.clientWidth;
                if (maxScroll > 10) {
                    prev.classList.remove('hidden');
                    next.classList.remove('hidden');
                } else {
                    prev.classList.add('hidden');
                    next.classList.add('hidden');
                }
            }
            updateArrows();
            window.addEventListener('resize', updateArrows);
            if (prev) prev.addEventListener('click', () => {
                container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            });
            if (next) next.addEventListener('click', () => {
                container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            });
        });

        // --- DETAIL GALLERY: thumbnails change main image ---
        const detailMain = document.getElementById('detail-main-image');
        const thumbs = document.querySelectorAll('#detail-thumbs .thumb-btn');
        thumbs.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const src = btn.dataset.src;
                if (detailMain && src) {
                    detailMain.src = src;
                    // highlight selected thumbnail (basic)
                    thumbs.forEach(b => b.classList.remove('ring-2', 'ring-primary-pink'));
                    btn.classList.add('ring-2', 'ring-primary-pink');
                }
            });
        });

        // --- product_detail: controle de seleção size/color e quantidade ---
        (function setupDetailSelectors() {
            // só executa se existirem variantes desta página
            if (typeof PRODUCT_VARIANTS === 'undefined' || !Array.isArray(PRODUCT_VARIANTS)) return;

            const sizeRadios = Array.from(document.querySelectorAll('.size-radio'));
            const colorRadios = Array.from(document.querySelectorAll('.color-radio'));
            const qtyInput = document.getElementById('qty-input');
            const qtyInc = document.getElementById('qty-increment');
            const qtyDec = document.getElementById('qty-decrement');
            const qtyBlock = document.getElementById('quantity-block');
            const stockAvailable = document.getElementById('stock-available');
            const addBtn = document.getElementById('add-to-cart-btn');

            function findVariant(size, color) {
                return PRODUCT_VARIANTS.find(v => v.size === size && v.color === color);
            }

            // Marca visualmente disponibilidade sem desabilitar os inputs.
            function updateColorAvailability(selectedSize) {
                colorRadios.forEach(r => {
                    const color = r.value;
                    const variant = PRODUCT_VARIANTS.find(v => v.size === selectedSize && v.color === color && v.quantity > 0);
                    if (!variant) {
                        // r.dataset.available = "false";
                        r.closest('label')?.classList.add('opacity-40', 'cursor-not-allowed');
                    } else {
                        // r.dataset.available = "true";
                        r.closest('label')?.classList.remove('opacity-40', 'cursor-not-allowed');
                    }
                });
            }
            function updateSizeAvailability(selectedColor) {
                sizeRadios.forEach(r => {
                    const size = r.value;
                    const variant = PRODUCT_VARIANTS.find(v => v.color === selectedColor && v.size === size && v.quantity > 0);
                    if (!variant) {
                        r.dataset.available = "false";
                        r.closest('label')?.classList.add('opacity-40', 'cursor-not-allowed');
                    } else {
                        r.dataset.available = "true";
                        r.closest('label')?.classList.remove('opacity-40', 'cursor-not-allowed');
                    }
                });
            }

            function resetQtyBlock() {
                qtyInput.value = 1;
                qtyInput.min = 1;
                qtyInput.max = 1;
                qtyInput.disabled = true;
                qtyInc.disabled = true;
                qtyDec.disabled = true;
                if (qtyBlock) qtyBlock.setAttribute('aria-hidden', 'true');
                if (stockAvailable) stockAvailable.textContent = '-';
                if (addBtn) addBtn.disabled = true;
            }

            function enableQtyForVariant(variant) {
                const q = variant.quantity || 0;
                qtyInput.max = q;
                qtyInput.value = Math.min(Number(qtyInput.value) || 1, q) || 1;
                qtyInput.disabled = false;
                qtyInc.disabled = false;
                qtyDec.disabled = false;
                if (qtyBlock) qtyBlock.removeAttribute('aria-hidden');
                if (stockAvailable) stockAvailable.textContent = String(q);
                if (addBtn) addBtn.disabled = q === 0;
                // Atualiza preço exibido se houver elemento (usa price da variante quando disponível)
                const priceEl = document.getElementById('product-price');
                const origEl = document.getElementById('product-price-original');
                if (priceEl) {
                    if (variant.price !== null && variant.price !== undefined) {
                        priceEl.textContent = `R$ ${Number(variant.price).toFixed(2)}`;
                    } else {
                        // fallback: usa dataset do botão (preço do produto)
                        const base = parseFloat(addBtn?.dataset?.productPrice || '0') || 0;
                        priceEl.textContent = `R$ ${base.toFixed(2)}`;
                    }
                }
            }

            // handlers when size is changed
            sizeRadios.forEach(r => r.addEventListener('change', (e) => {
                const selectedSize = e.target.value;
                // atualiza visualmente quais cores existem para este tamanho (mas não bloqueia mudança de tamanho)
                updateColorAvailability(selectedSize);
                // se já havia uma cor selecionada e ela NÃO está disponível para o tamanho novo, desmarca a cor e reseta
                const selectedColorRadio = colorRadios.find(c => c.checked);
                if (selectedColorRadio) {
                    const variant = findVariant(selectedSize, selectedColorRadio.value);
                    if (!variant) {
                        // força o usuário a escolher cor novamente
                        selectedColorRadio.checked = false;
                        resetQtyBlock();
                        return;
                    }
                }
                // se existe cor selecionada e variante válida, habilita quantidade
                const selColor = (colorRadios.find(c => c.checked) || {}).value;
                if (selColor) {
                    const variant = findVariant(selectedSize, selColor);
                    if (variant) enableQtyForVariant(variant); else resetQtyBlock();
                } else {
                    resetQtyBlock();
                }
            }));

            // handlers when color is changed
            colorRadios.forEach(r => r.addEventListener('change', (e) => {
                const selectedColor = e.target.value;
                // enable only sizes that have stock for this color
                updateSizeAvailability(selectedColor);
                const selectedSizeRadio = sizeRadios.find(s => s.checked);
                if (selectedSizeRadio) {
                    const variant = findVariant(selectedSizeRadio.value, selectedColor);
                    if (variant) {
                        enableQtyForVariant(variant);
                    } else {
                        // se a combinação atual size+color ficou inválida, desmarca size para forçar reescolha do par
                        selectedSizeRadio.checked = false;
                        resetQtyBlock();
                    }
                } else {
                    resetQtyBlock();
                }
            }));

            // qty increment/decrement
            if (qtyInc) qtyInc.addEventListener('click', () => {
                const max = parseInt(qtyInput.max || '1', 10) || 1;
                let cur = parseInt(qtyInput.value || '1', 10) || 1;
                if (cur < max) cur += 1;
                qtyInput.value = cur;
            });
            if (qtyDec) qtyDec.addEventListener('click', () => {
                let cur = parseInt(qtyInput.value || '1', 10) || 1;
                if (cur > 1) cur -= 1;
                qtyInput.value = cur;
            });

            // validate qty typed
            if (qtyInput) qtyInput.addEventListener('input', () => {
                const max = parseInt(qtyInput.max || '1', 10) || 1;
                let cur = parseInt(qtyInput.value || '1', 10) || 1;
                if (cur < 1) cur = 1;
                if (cur > max) cur = max;
                qtyInput.value = cur;
            });

            // initial state
            resetQtyBlock();

            // when add-to-cart clicked, ensure we use qty and variant exists
            if (addBtn) {
                addBtn.addEventListener('click', (ev) => {
                    const selectedSize = (sizeRadios.find(r => r.checked) || {}).value;
                    const selectedColor = (colorRadios.find(r => r.checked) || {}).value;
                    if (!selectedSize || !selectedColor) {
                        alert('Escolha tamanho e cor antes de adicionar.');
                        return;
                    }
                    const variant = findVariant(selectedSize, selectedColor);
                    if (!variant) {
                        alert('Variação indisponível.');
                        return;
                    }
                    // prepare item consistent with addItemToCart
                    const qty = parseInt(qtyInput.value || '1', 10) || 1;
                    if (qty > variant.quantity) {
                        alert('Quantidade solicitada maior que o estoque disponível.');
                        return;
                    }
                    const productId = addBtn.dataset.productId || null;
                    const productName = addBtn.dataset.productName || '';
                    const productPrice = parseFloat(addBtn.dataset.productPrice) || 0;
                    addItemToCart({
                        id: productId,
                        name: productName,
                        // usa preço da variação se definido
                        price: (variant && variant.price !== null && variant.price !== undefined) ? variant.price : productPrice,
                        qty: qty,
                        size: selectedSize,
                        color: selectedColor,
                        shipping: 'A definir'
                    });
                });
            }
        })();
    });
})();
