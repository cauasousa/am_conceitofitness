# 🔧 Troubleshooting: Invalid Compact JWS

## Erro encontrado:
```
[error] Erro ao fazer upload para Supabase: {'statusCode': 403, 'error': Unauthorized, 'message': Invalid Compact JWS}
```

## ❌ Causa do problema:
O erro `Invalid Compact JWS` significa que a **service_role key** do Supabase está:
- Incorreta
- Mal formatada (espaços extras, quebras de linha)
- Usando a chave errada (anon ao invés de service_role)
- Não configurada no arquivo `.env`

## ✅ Solução:

### 1. Verificar o arquivo `.env`

Abra o arquivo `.env` e verifique:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Obter a chave correta no Supabase

1. Acesse: https://app.supabase.com
2. Selecione seu projeto
3. Vá em **Settings** → **API**
4. **NÃO USE** a `anon public` key
5. **USE** a `service_role` key (mais longa, começa com `eyJ...`)
6. Clique no ícone de copiar 📋

### 3. Colar no `.env` corretamente

⚠️ **IMPORTANTE:**
- Cole em UMA linha só (sem quebras)
- Sem espaços antes ou depois
- Sem aspas extras

**❌ ERRADO:**
```env
SUPABASE_SERVICE_KEY = " eyJhbGciOiJIUzI... "
```

**✅ CERTO:**
```env
SUPABASE_SERVICE_KEY=eyJhbIkpXVCJ9...longo...
```

### 4. Verificar se está usando a key correta

A `service_role` key é MUITO maior que a `anon` key.

- **anon key**: ~200-300 caracteres
- **service_role key**: ~500-800 caracteres

Se sua key é curta, você está usando a errada!

### 5. Reiniciar o servidor Flask

Após editar o `.env`:

```bash
# Pare o servidor (Ctrl+C)
# Inicie novamente
python app.py
```

### 6. Testar novamente

Execute o upload de uma imagem e verifique os logs no terminal.

## 🔍 Debug adicional

Execute este comando no terminal Python para testar:

```python
from dotenv import load_dotenv
import os

load_dotenv()
key = os.environ.get("SUPABASE_SERVICE_KEY")
url = os.environ.get("SUPABASE_URL")

print(f"URL: {url}")
print(f"Key length: {len(key) if key else 0}")
print(f"Key starts with: {key[:20] if key else 'NOT FOUND'}")
print(f"Key ends with: {key[-20:] if key else 'NOT FOUND'}")
```

**Resultado esperado:**
```
URL: https://xxxxx.supabase.co
Key length: 500-800
Key starts with: eyJhbGciOiJIUzI1NiIs...
Key ends with: ...randomstring
```

## 🔐 Segurança

⚠️ **NUNCA commit a service_role key no Git!**

Verifique se `.env` está no `.gitignore`:

```bash
# .gitignore deve conter:
.env
```

## 📞 Ainda com problemas?

Se o erro persistir:

1. Regenere a `service_role` key no Supabase:
   - Settings → API → Regenerate service_role key
   - Copie a nova key
   - Cole no `.env`
   - Reinicie o servidor

2. Verifique as permissões do bucket:
   - Storage → product-images → Policies
   - Certifique-se que as políticas de INSERT e DELETE existem

3. Teste a autenticação diretamente:
   ```python
   from supabase import create_client
   
   url = "https://seu-projeto.supabase.co"
   key = "sua_service_role_key"
   
   supabase = create_client(url, key)
   print("✅ Conexão OK!")
   ```

## ✅ Checklist final

- [ ] `.env` existe na raiz do projeto
- [ ] `SUPABASE_URL` está correto (https://...)
- [ ] `SUPABASE_SERVICE_KEY` é a key service_role (não anon)
- [ ] Key está em uma linha só, sem espaços extras
- [ ] Servidor Flask foi reiniciado
- [ ] `.env` está no `.gitignore`
