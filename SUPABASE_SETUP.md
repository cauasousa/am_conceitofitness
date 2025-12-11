# Configuração do Supabase Storage

## Passo 1: Criar Bucket no Supabase

1. Acesse o painel do Supabase: https://app.supabase.com
2. Vá em **Storage** no menu lateral
3. Clique em **New Bucket**
4. Configure:
   - **Name**: `product-images`
   - **Public bucket**: ✅ Marque como público
   - Clique em **Create bucket**

## Passo 2: Configurar Políticas de Acesso (RLS)

### Política para LEITURA (qualquer pessoa pode visualizar):
```sql
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'product-images' );
```

### Política para UPLOAD (qualquer pessoa autenticada pode fazer upload):
```sql
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'product-images' );
```

### Política para DELETE (qualquer pessoa autenticada pode deletar):
```sql
CREATE POLICY "Authenticated users can delete"
ON storage.objects FOR DELETE
USING ( bucket_id = 'product-images' );
```

## Passo 3: Obter as Credenciais

1. Vá em **Settings** > **API**
2. Copie:
   - **Project URL**: `https://seu-projeto.supabase.co`
   - **service_role key** (não a `anon` key!)

## Passo 4: Configurar Variáveis de Ambiente

Edite seu arquivo `.env`:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua_service_role_key_aqui
```

## Passo 5: Testar

Execute o app e tente adicionar um produto com imagem pela interface admin. A imagem será armazenada no Supabase e a URL será salva no PostgreSQL.

## Estrutura de Pastas no Supabase

```
product-images/
  └── products/
      ├── uuid-1.jpg
      ├── uuid-2.png
      └── uuid-3.webp
```

## Migração de Imagens Existentes (Opcional)

Se você já tem imagens em `/static/images/`, pode fazer upload manual:

1. Acesse o bucket no Supabase
2. Clique em **Upload file**
3. Selecione as imagens
4. Copie as URLs públicas
5. Atualize os registros no banco de dados PostgreSQL

Ou crie um script Python para migração automática.
