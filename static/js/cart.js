// Funções para manipular o carrinho (localStorage key: cart_v1)
(function () {
    // --- VARIÁVEIS ÚTEIS ---
    const formatBRL = (value) => 'R$ ' + (typeof value === 'number' ? value.toFixed(2) : '0.00').replace('.', ',');
    const getCart = () => { try { return JSON.parse(localStorage.getItem('cart_v1') || '[]'); } catch (e) { return []; } };
    const setCart = (c) => { localStorage.setItem('cart_v1', JSON.stringify(c)); window.dispatchEvent(new Event('storage')); };

    window.updateCartCount = function () { /* ... */ };
    function setQty(variantId, qty) { /* ... */ };
    function changeQty(variantId, delta) { /* ... */ };
    function removeItem(variantId) { /* ... */ };

    // --- FUNÇÃO DE ESTILO PARA SELEÇÃO DE FRETE (FEEDBACK VISUAL) ---
    function updateShippingOptionStyles() {
        document.querySelectorAll('.js-shipping-radio').forEach(label => {
            label.classList.remove('ring-2', 'ring-green-500', 'ring-primary-pink', 'bg-green-100', 'bg-primary-pink/10', 'border-green-500', 'border-primary-pink', 'shadow-md');

            if (label.querySelector('input[value="pickup"]')) {
                label.classList.add('bg-gray-50', 'border-gray-300');
            } else {
                label.classList.add('bg-white', 'border-gray-300');
            }
        });

        const selectedRadio = document.querySelector('input[name="shipping_option"]:checked');
        if (selectedRadio) {
            const label = selectedRadio.closest('.js-shipping-radio');
            if (label) {
                const isPickup = selectedRadio.value === 'pickup';
                const ringColor = isPickup ? 'ring-green-500' : 'ring-primary-pink';
                const bgColor = isPickup ? 'bg-green-100' : 'bg-primary-pink/10';
                const borderColor = isPickup ? 'border-green-500' : 'border-primary-pink';

                label.classList.remove('bg-gray-50', 'bg-white', 'border-gray-300');
                label.classList.add('ring-2', ringColor, bgColor, borderColor, 'shadow-md');
            }
        }
    }


    // --- FUNÇÃO DE CÁLCULO DE FRETE ---

    window.calculateShipping = function () {
        const cepInput = document.getElementById('cep-input');
        const cepErrorMessage = document.getElementById('cep-error-message');
        const cepInputArea = document.getElementById('cep-input-area');
        const cepCalculatedSummary = document.getElementById('cep-calculated-summary');
        const currentCepDisplay = document.getElementById('current-cep-display');
        const shippingOptionsResponse = document.getElementById('shipping-options-response');
        const deliveryOptionsContainer = document.getElementById('delivery-options-container');
        const errorDiv = document.getElementById('shipping-error');
        const calcBtn = document.getElementById('calc-shipping');

        if (!cepInput) return;
        const cep = cepInput.value.trim().replace(/\D/g, '');
        const originalText = calcBtn ? calcBtn.textContent : 'Calcular';

        if (cep.length !== 8 || cep === '00000000') {
            cepErrorMessage && cepErrorMessage.classList.remove('hidden');
            return;
        }
        cepErrorMessage && cepErrorMessage.classList.add('hidden');

        // Mostrar loading
        if (calcBtn) {
            calcBtn.disabled = true;
            calcBtn.textContent = 'Calculando...';
        }
        deliveryOptionsContainer && (deliveryOptionsContainer.innerHTML = '<div class="p-3 text-center text-gray-600">Buscando opções de envio...</div>');
        errorDiv && errorDiv.classList.add('hidden');
        localStorage.setItem('user_cep', cep);

        // CHAMADA REAL À API DO BACKEND
        fetch('/api/calculate-shipping', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cep: cep, method: 'delivery' })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const shippingCostWithFee = (data.shipping_cost || 0);
                    const cart = getCart();
                    const subtotalAmount = cart.reduce((s, i) => s + (i.price || 0) * i.qty, 0);
                    const totalAmount = subtotalAmount + shippingCostWithFee;

                    // 1. Exibir CEP calculado
                    currentCepDisplay && (currentCepDisplay.textContent = cep.substring(0, 5) + '-' + cep.substring(5));
                    cepInputArea && cepInputArea.classList.add('hidden');
                    cepCalculatedSummary && cepCalculatedSummary.classList.remove('hidden');
                    shippingOptionsResponse && shippingOptionsResponse.classList.remove('hidden');

                    // 2. Renderizar a opção de Entrega Calculada
                    let deliveryHTML = `
                    <div class="js-shipping-list-item radio-button-item w-full">
                        <label for="option_delivery" class="js-shipping-radio list-item block p-5 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:border-primary-pink/50 bg-white border-gray-300">
                            <div class="flex items-start gap-4 w-full">
                                <input id="option_delivery" class="shipping-method js-shipping-radio-input" 
                                       data-price="${shippingCostWithFee.toFixed(2)}" data-code="delivery" data-name="Entrega para seu Endereço" 
                                       type="radio" value="delivery" name="shipping_option" required>
                                <div class="flex-1">
                                    <div class="flex items-center justify-between mb-2">
                                        <h3 class="font-bold text-gray-900 text-base">📦 Entrega para seu Endereço</h3>
                                        <span class="text-2xl font-extrabold text-primary-pink">${formatBRL(shippingCostWithFee)}</span>
                                    </div>
                                    <div class="text-xs text-gray-500">Distância: ${(data.distance_km || 0).toFixed(1)} km</div>
                                    <div class="text-xs text-gray-500">${data.message || 'Prazo padrão.'}</div>
                                </div>
                            </div>
                        </label>
                    </div>`;
                    deliveryOptionsContainer && (deliveryOptionsContainer.innerHTML = deliveryHTML);

                    // 3. Selecionar a Entrega Calculada (como padrão após o cálculo)
                    const deliveryRadio = document.getElementById('option_delivery');
                    if (deliveryRadio) {
                        deliveryRadio.checked = true;
                        deliveryRadio.dispatchEvent(new Event('change', { bubbles: true }));
                    }

                    // 4. Atualiza totais (Resumo Lateral)
                    document.getElementById('summary-shipping-cost') && (document.getElementById('summary-shipping-cost').textContent = formatBRL(shippingCostWithFee));
                    document.getElementById('summary-total') && (document.getElementById('summary-total').textContent = formatBRL(totalAmount));
                    updateShippingOptionStyles();

                } else {
                    console.error('Erro da API:', data.message);
                    errorDiv && (errorDiv.textContent = 'Erro: ' + (data.message || 'Erro desconhecido'));
                    errorDiv && errorDiv.classList.remove('hidden');
                    deliveryOptionsContainer && (deliveryOptionsContainer.innerHTML = '');
                    shippingOptionsResponse && shippingOptionsResponse.classList.add('hidden');

                    // Falha no cálculo: garante que a Retirada seja selecionada
                    document.getElementById('option_pickup').checked = true;
                    updateShippingOptionStyles();
                }
            })
            .catch(err => {
                console.error('Erro na requisição:', err);
                errorDiv && (errorDiv.textContent = 'Erro ao conectar com o servidor. Tente novamente.');
                errorDiv && errorDiv.classList.remove('hidden');
                deliveryOptionsContainer && (deliveryOptionsContainer.innerHTML = '');
                shippingOptionsResponse && shippingOptionsResponse.classList.add('hidden');

                // Falha total: garante que a Retirada seja selecionada
                document.getElementById('option_pickup').checked = true;
                updateShippingOptionStyles();
            })
            .finally(() => {
                if (calcBtn) {
                    calcBtn.disabled = false;
                    calcBtn.textContent = originalText;
                }
            });
    }

    // --- FUNÇÃO DE RENDERIZAÇÃO PRINCIPAL ---

    window.renderCartPage = function () {
        // ... Lógica de renderização do carrinho (itens e totais) ...
        updateCartCount();
        const list = document.getElementById('cart-items-list');
        const summaryList = document.getElementById('summary-list');
        const summarySubtotal = document.getElementById('summary-subtotal');
        const summaryTotal = document.getElementById('summary-total');
        const summaryShipping = document.getElementById('summary-shipping-cost');
        if (!list) return;

        const cart = getCart();
        list.innerHTML = '';
        summaryList && (summaryList.innerHTML = '');
        let subtotal = 0;

        if (cart.length === 0) {
            list.innerHTML = '<div class="p-4 bg-white border rounded text-center text-gray-600">Seu carrinho está vazio.</div>';
        }

        cart.forEach(item => {
            const itemTotal = (item.price || 0) * item.qty;
            subtotal += itemTotal;
            const div = document.createElement('div');
            div.className = 'flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 bg-white border rounded';

            const imgFile = item.image || 'placeholder.jpg';
            const imgSrc = '/static/images/' + imgFile;

            // Renderização do Item
            div.innerHTML = `
                <div class="flex items-start gap-3 flex-1">
                    <img src="${imgSrc}" alt="${(item.name || '')}" class="w-20 h-20 object-cover rounded border flex-shrink-0" onerror="this.src='/static/images/placeholder.jpg'">
                    <div class="flex-1 min-w-0">
                        <div class="font-bold text-gray-900">${item.name}</div>
                        <div class="text-sm text-gray-600 mt-1">${item.size} / ${item.color}</div>
                        <div class="text-sm font-semibold text-primary-pink mt-2">${formatBRL(item.price || 0)} × ${item.qty} = ${formatBRL(itemTotal)}</div>
                    </div>
                </div>
                <div class="flex items-center gap-2 flex-wrap justify-end w-full sm:w-auto">
                    <div class="flex items-center gap-1 border rounded-lg p-1 bg-gray-50">
                        <button class="qty-decr px-3 py-1 hover:bg-gray-200 rounded transition font-bold" data-id="${item.variant_id}">−</button>
                        <input type="number" class="w-12 text-center border-0 bg-white px-1 py-1 qty-input" data-id="${item.variant_id}" value="${item.qty}" min="1" max="${item.max}">
                        <button class="qty-incr px-3 py-1 hover:bg-gray-200 rounded transition font-bold" data-id="${item.variant_id}">+</button>
                    </div>
                    <button class="remove-item text-red-500 hover:text-red-700 transition p-2" title="Remover" data-id="${item.variant_id}">
                        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M5 6l1 14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-14" /></svg>
                    </button>
                </div>
            `;
            list.appendChild(div);

            // Resumo lateral
            if (summaryList) {
                const sdiv = document.createElement('div');
                sdiv.className = 'py-2 flex items-center justify-between';
                sdiv.innerHTML = `<div class="text-sm">${item.name} <span class="text-xs text-gray-500">(${item.size}/${item.color}) × ${item.qty}</span></div><div class="text-sm">${formatBRL(itemTotal)}</div>`;
                summaryList.appendChild(sdiv);
            }
        });

        // Atualiza totais (Reseta frete para zero, ou mantém o valor se já calculado)
        const currentShippingCost = summaryShipping ? parseFloat(summaryShipping.textContent.replace('R$', '').replace(',', '.').trim() || 0) : 0;
        const totalWithShipping = subtotal + currentShippingCost;

        summarySubtotal && (summarySubtotal.textContent = formatBRL(subtotal));
        summaryShipping && (summaryShipping.textContent = formatBRL(currentShippingCost));
        summaryTotal && (summaryTotal.textContent = formatBRL(totalWithShipping));

        // Atualização de elementos de checkout
        const checkoutTotal = document.getElementById('checkout-total');
        const checkoutSubtotal = document.getElementById('checkout-subtotal');
        if (checkoutSubtotal) checkoutSubtotal.textContent = formatBRL(subtotal);
        if (checkoutTotal) checkoutTotal.textContent = formatBRL(totalWithShipping);
    };


    // --- SETUP GLOBAL (DOM READY) ---

    document.addEventListener('DOMContentLoaded', () => {
        const list = document.getElementById('cart-items-list');
        const calcBtn = document.getElementById('calc-shipping');
        const checkoutBtn = document.getElementById('checkout-btn');
        const changeCepBtn = document.querySelector('.js-shipping-calculator-change-zipcode');
        const cepInput = document.getElementById('cep-input');
        const pickupRadio = document.getElementById('option_pickup');

        // 1. VINCULAÇÃO ÚNICA DE EVENTOS DO CARRINHO (Delegation)
        if (list) {
            list.addEventListener('click', (e) => {
                const decBtn = e.target.closest('.qty-decr');
                const incBtn = e.target.closest('.qty-incr');
                const removeBtn = e.target.closest('.remove-item');

                if (decBtn) {
                    const id = parseInt(decBtn.dataset.id);
                    changeQty(id, -1);
                }

                if (incBtn) {
                    const id = parseInt(incBtn.dataset.id);
                    changeQty(id, +1);
                }

                if (removeBtn) {
                    const id = parseInt(removeBtn.dataset.id);
                    removeItem(id);
                }
            });

            list.addEventListener('change', (e) => {
                if (e.target.classList.contains('qty-input')) {
                    const id = parseInt(e.target.dataset.id);
                    const val = Math.max(1, Math.min(parseInt(e.target.value || '1'), parseInt(e.target.max || '1')));
                    setQty(id, val);
                }
            });
        }

        // 2. LISTENERS DE FRETE/CEP
        if (calcBtn) {
            calcBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.calculateShipping();
            });
        }

        if (changeCepBtn) {
            changeCepBtn.addEventListener('click', (e) => {
                e.preventDefault();
                document.getElementById('cep-input-area') && document.getElementById('cep-input-area').classList.remove('hidden');
                document.getElementById('cep-calculated-summary') && document.getElementById('cep-calculated-summary').classList.add('hidden');
                document.getElementById('shipping-options-response') && document.getElementById('shipping-options-response').classList.add('hidden');
                cepInput && cepInput.focus();
            });
        }

        // 3. LISTENERS DE SELEÇÃO DE OPÇÃO DE FRETE
        if (pickupRadio) {
            pickupRadio.addEventListener('change', updateShippingOptionStyles);
            pickupRadio.checked = true;
        }

        document.getElementById('shipping-options-response') && document.getElementById('shipping-options-response').addEventListener('change', (e) => {
            if (e.target.name === 'shipping_option') {
                updateShippingOptionStyles();

                const selectedRadio = document.querySelector('input[name="shipping_option"]:checked');
                if (selectedRadio) {
                    const shippingCost = parseFloat(selectedRadio.dataset.price) || 0;
                    const cart = getCart();
                    const subtotal = cart.reduce((s, i) => s + (i.price || 0) * i.qty, 0);
                    const total = subtotal + shippingCost;

                    const summaryShipping = document.getElementById('summary-shipping-cost');
                    const summaryTotal = document.getElementById('summary-total');

                    if (summaryShipping) summaryShipping.textContent = formatBRL(shippingCost);
                    if (summaryTotal) summaryTotal.textContent = formatBRL(total);
                }
            }
        });


        // 4. INICIALIZAÇÃO
        window.renderCartPage();
        updateShippingOptionStyles();
        updateCartCount();
        window.addEventListener('storage', updateCartCount);

        // Restaura CEP salvo e recalcula automaticamente se for válido
        const savedCep = localStorage.getItem('user_cep');
        if (cepInput && savedCep && savedCep.length === 8) {
            cepInput.value = savedCep;
            window.calculateShipping();
        }
    });
})();