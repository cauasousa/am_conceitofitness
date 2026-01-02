# Verificação de Estoque no Carrinho

## Resumo da Implementação

Foi implementado um sistema automático de verificação de estoque que:

1. **Verifica o estoque em tempo real** quando o carrinho é carregado
2. **Remove produtos sem estoque** automaticamente
3. **Ajusta quantidades** se o estoque diminuir
4. **Notifica o cliente** quando um produto sai do estoque

## Arquivos Modificados

### 1. `static/js/cart.js` - Função `renderCartPage()`

A função agora:
- Extrai todos os `variant_ids` do carrinho
- Faz uma requisição POST para `/api/check-stock`
- Recebe um mapa com as quantidades atuais de estoque
- Remove itens com quantidade 0
- Ajusta quantidade se ela exceder o estoque
- Atualiza o campo `max` (quantidade máxima) com o estoque atual
- Mostra notificações toast para itens removidos

**Fluxo:**
```
renderCartPage()
  ↓
Extrai variant_ids do carrinho
  ↓
fetch('/api/check-stock', { variant_ids: [1, 2, 3] })
  ↓
Recebe: { success: true, stock: { 1: 10, 2: 0, 3: 5 } }
  ↓
Remove item 2 (stock = 0)
  ↓
Atualiza item 1 (max = 10)
  ↓
Atualiza item 3 (max = 5)
  ↓
Renderiza carrinho atualizado
```

### 2. `app.py` - Novo endpoint `/api/check-stock`

```python
POST /api/check-stock
Content-Type: application/json

{
  "variant_ids": [1, 2, 3, ...]
}

Resposta:
{
  "success": true,
  "stock": {
    "1": 10,
    "2": 0,
    "3": 5
  }
}
```

O endpoint:
- Recebe uma lista de `variant_ids`
- Consulta a tabela `ProductStock` no banco
- Retorna um mapa com: `{ variant_id: quantity }`
- Variantes não encontradas recebem quantidade 0

## Como Funciona

### Cenário 1: Produto Sai do Estoque
1. Usuário tem 2x "Camiseta P" no carrinho
2. Você remove o estoque do banco (quantity = 0)
3. Usuário acessa o carrinho
4. Sistema detecta que "Camiseta P" não tem estoque
5. Produto é removido do carrinho
6. Notificação é mostrada: "❌ Camiseta (P) foi removido - Fora de estoque"

### Cenário 2: Estoque Diminui
1. Usuário tem 10x "Camiseta M" no carrinho
2. Estoque diminui para 5 (outros clientes compraram)
3. Usuário acessa o carrinho
4. Sistema detecta que há apenas 5 em estoque
5. Quantidade é ajustada para 5
6. Campo `max` é atualizado para 5
7. Usuário não consegue aumentar a quantidade além de 5

## Testes Recomendados

### Teste 1: Remover do Banco
1. Adicione um produto ao carrinho
2. Abra o banco de dados
3. Defina `quantity = 0` para aquela variante
4. Recarregue o carrinho
5. ✅ Produto deve desaparecer com notificação

### Teste 2: Reduzir Estoque
1. Adicione produto com qty=10 ao carrinho
2. Defina `quantity = 3` no banco
3. Recarregue o carrinho
4. ✅ Quantidade deve ajustar para 3
5. ✅ Max input deve ser 3

### Teste 3: Produto Continua
1. Produto tem `quantity = 5` no banco
2. Carrinho tem qty=2
3. Recarregue
4. ✅ Produto deve permanecer
5. ✅ Max deve atualizar para 5

## Integração com Interface

### Toast Notifications
As notificações usam o sistema `window.showToast()` que já existe em `base.html`:

```javascript
window.showToast(message, type = 'info', duration = 4000)
// type: 'info', 'success', 'warning', 'error'
```

### Atualização do Carrinho
Quando há alterações (remoção/ajuste), o carrinho é:
1. Atualizado em localStorage
2. Renderizado novamente
3. Totais recalculados
4. UI sincronizada

## Verificação de Erro

Se a requisição falhar (erro de rede, servidor offline):
- O carrinho ainda é renderizado com os dados locais
- Uma mensagem é logada no console
- O usuário pode prosseguir (dados podem estar desatualizados)
- Próximo carregamento tentará sincronizar novamente

```javascript
.catch(err => {
    console.warn('Erro ao verificar estoque:', err);
    renderCartItems(cart);  // Renderiza mesmo com erro
});
```

## Estrutura Esperada do localStorage

```json
{
  "variant_id": 1,
  "name": "Camiseta",
  "size": "P",
  "price": 49.90,
  "qty": 2,
  "max": 5,
  "image": "camiseta.jpg"
}
```

O campo `max` agora é atualizado dinamicamente com o estoque do servidor.

## Notas Importantes

1. **O sistema só verifica quando:** Página de carrinho é carregada ou `renderCartPage()` é chamada
2. **Não impede adição:** Este sistema não bloqueia adicionar produtos sem estoque (isso é feito em `product_detail.html`)
3. **Sincronização:** Cada vez que o carrinho é acessado, os estoques são verificados
4. **Notificações:** Aparecem em tempo real quando produtos são removidos

## Próximos Passos (Opcional)

Se quiser melhorias futuras:
1. Verificar estoque ao **adicionar** produto (em `product_detail.html`)
2. Mostrar **"Últimas unidades"** quando estoque < 3
3. Verificar periodicamente estoque enquanto usuário está na página
4. Avisar quando estoque está prestes a acabar
