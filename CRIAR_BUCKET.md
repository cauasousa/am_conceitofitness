# 🪣 Erro: Bucket not found

## ❌ Erro:
```
Bucket not found: product-images
```

## ✅ Solução: Criar o bucket no Supabase

### Passo 1: Acessar o Dashboard
1. Vá para: https://app.supabase.com
2. Selecione seu projeto: `ifyfcxwzqqlsqacnzjhf`

### Passo 2: Criar o Bucket
1. No menu lateral, clique em **Storage**
2. Clique no botão **New Bucket** (ou **Create Bucket**)
3. Preencha:
   - **Name**: `product-images` (exatamente esse nome!)
   - **Public bucket**: ✅ **MARQUE ESTA OPÇÃO** (importante!)
   - **File size limit**: 50MB (padrão)
4. Clique em **Create bucket**

### Passo 3: Configurar Políticas de Acesso (RLS)

Após criar o bucket, você precisa configurar as políticas:

#### Opção A: Via Interface (Mais fácil)

1. Clique no bucket `product-images`
2. Vá na aba **Policies**
3. Clique em **New Policy**
4. Selecione um template:
   - **Public access (read only)** → Para SELECT
   - Depois crie outra para INSERT e DELETE

#### Opção B: Via SQL (Mais rápido)

1. No menu lateral, clique em **SQL Editor**
2. Clique em **New Query**
3. Cole este SQL:

```sql
-- Permite leitura pública (qualquer pessoa pode ver as imagens)
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'product-images' );

-- Permite upload (service_role pode fazer upload)
CREATE POLICY "Service Role Upload"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'product-images' );

-- Permite delete (service_role pode deletar)
CREATE POLICY "Service Role Delete"
ON storage.objects FOR DELETE
USING ( bucket_id = 'product-images' );
```

4. Clique em **Run** (ou pressione Ctrl+Enter)

### Passo 4: Verificar

1. Volte em **Storage** → **product-images**
2. Você deve ver o bucket vazio
3. Tente fazer upload manual de um arquivo de teste
4. Se funcionar, está configurado corretamente!

### Passo 5: Testar no app

1. Reinicie o servidor Flask (não é necessário, mas recomendado)
2. Vá no admin do site
3. Adicione/edite um produto
4. Faça upload de uma imagem
5. Verifique os logs no terminal

**Logs esperados:**
```
[info] Tentando upload: produto.jpg (123456 bytes)
[info] ✅ Upload bem-sucedido: products/uuid.jpg
[info] URL pública: https://ifyfcxwzqqlsqacnzjhf.supabase.co/storage/v1/object/public/product-images/products/uuid.jpg
```

### Passo 6: Verificar no Supabase

1. Vá em **Storage** → **product-images**
2. Entre na pasta **products/**
3. Você deve ver o arquivo enviado
4. Clique nele e copie a URL pública
5. Cole no navegador para verificar se abre a imagem

## 🎯 Checklist rápido

- [ ] Bucket `product-images` criado no Supabase
- [ ] Opção **Public bucket** marcada
- [ ] Políticas de SELECT, INSERT e DELETE configuradas
- [ ] Teste de upload manual funcionou
- [ ] Upload via admin do site funcionou
- [ ] Imagem aparece no site

## ⚠️ Importante

Se você quiser usar outro nome de bucket (não `product-images`), edite o arquivo:

**`supabase_service.py` - Linha 13:**
```python
BUCKET_NAME = "seu-nome-aqui"  # Mude aqui
```

## 🔄 Estrutura final no Supabase

```
Storage/
└── product-images/  ← Bucket público
    └── products/    ← Pasta (criada automaticamente)
        ├── uuid-1.jpg
        ├── uuid-2.png
        └── uuid-3.webp
```

## ✅ Pronto!

Após seguir esses passos, o upload funcionará corretamente! 🚀
