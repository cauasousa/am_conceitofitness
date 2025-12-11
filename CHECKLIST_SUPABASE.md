# ✅ Checklist de Migração para Supabase Storage

## Pré-requisitos

- [ ] Conta no Supabase criada (https://supabase.com)
- [ ] Projeto criado no Supabase
- [ ] PostgreSQL configurado no projeto (DATABASE_URL no .env)
- [ ] Dependências instaladas (`pip install -r requirements.txt`)

## Configuração do Supabase Storage

### 1. Criar o Bucket
- [ ] Acessar Dashboard do Supabase
- [ ] Ir em **Storage** → **New Bucket**
- [ ] Nome do bucket: `product-images`
- [ ] Marcar como **Public bucket** ✅
- [ ] Clicar em **Create bucket**

### 2. Configurar Políticas (RLS)
- [ ] Ir em **Storage** → **Policies**
- [ ] Adicionar política de **SELECT** (leitura pública)
- [ ] Adicionar política de **INSERT** (upload autenticado)
- [ ] Adicionar política de **DELETE** (delete autenticado)

**SQL das políticas:**
```sql
-- Leitura pública
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING ( bucket_id = 'product-images' );

-- Upload autenticado
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK ( bucket_id = 'product-images' );

-- Delete autenticado
CREATE POLICY "Authenticated users can delete"
ON storage.objects FOR DELETE
USING ( bucket_id = 'product-images' );
```

### 3. Obter Credenciais
- [ ] Ir em **Settings** → **API**
- [ ] Copiar **Project URL**
- [ ] Copiar **service_role key** (⚠️ NÃO a anon key!)

### 4. Configurar Variáveis de Ambiente
- [ ] Editar arquivo `.env`
- [ ] Adicionar `SUPABASE_URL=https://seu-projeto.supabase.co`
- [ ] Adicionar `SUPABASE_SERVICE_KEY=sua_service_role_key_aqui`
- [ ] Salvar arquivo

## Teste Básico

### 5. Testar Conexão
- [ ] Executar `python app.py`
- [ ] Verificar se não há erros de import
- [ ] App deve iniciar normalmente

### 6. Testar Upload de Imagem
- [ ] Acessar `http://localhost:5000/login`
- [ ] Fazer login como admin
- [ ] Clicar em "Adicionar Produto"
- [ ] Preencher dados do produto
- [ ] Selecionar uma imagem de teste
- [ ] Clicar em "Adicionar"
- [ ] Verificar se produto foi criado
- [ ] Verificar se imagem aparece no painel admin

### 7. Verificar no Supabase
- [ ] Ir em **Storage** → **product-images**
- [ ] Entrar na pasta **products/**
- [ ] Verificar se arquivo foi enviado (nome será uuid.extensão)
- [ ] Copiar URL pública da imagem
- [ ] Colar no navegador e verificar se abre

### 8. Verificar no PostgreSQL
- [ ] Acessar banco de dados PostgreSQL
- [ ] Executar: `SELECT * FROM product_images;`
- [ ] Verificar se `image_url` contém URL completa do Supabase
- [ ] URL deve começar com `https://`

## Migração de Imagens Antigas (Opcional)

### 9. Preparar Migração
- [ ] Verificar imagens em `/static/images/`
- [ ] Fazer backup das imagens locais
- [ ] Fazer backup do banco de dados

### 10. Executar Migração
- [ ] Executar `python migrate_images_to_supabase.py`
- [ ] Confirmar quando solicitado (digite `s`)
- [ ] Aguardar conclusão
- [ ] Verificar log de migração

### 11. Validar Migração
- [ ] Acessar site e verificar se produtos aparecem com imagens
- [ ] Verificar no Supabase se todas imagens foram enviadas
- [ ] Testar delete de imagem no admin
- [ ] Testar delete de produto com imagens

## Limpeza (Opcional)

### 12. Remover Imagens Locais
⚠️ **Só faça isso após confirmar que tudo funciona!**
- [ ] Fazer backup final de `/static/images/`
- [ ] Deletar imagens antigas de produtos (manter logo, banners, ícones)
- [ ] Manter apenas imagens estáticas do layout

## Troubleshooting

### Problema: "Bucket not found"
- [ ] Verificar nome do bucket em `supabase_service.py` (linha 9)
- [ ] Confirmar se bucket foi criado no Supabase
- [ ] Nome deve ser exatamente: `product-images`

### Problema: "Permission denied" ou "403"
- [ ] Verificar se políticas RLS foram criadas
- [ ] Confirmar que está usando `service_role` key (não `anon`)
- [ ] Verificar se bucket está marcado como público

### Problema: Imagens não aparecem
- [ ] Abrir DevTools (F12) e verificar erros no Console
- [ ] Verificar aba Network se requisição retorna 200
- [ ] Testar URL da imagem diretamente no navegador
- [ ] Verificar se URL foi salva corretamente no banco

### Problema: "Upload failed"
- [ ] Verificar tamanho do arquivo (Supabase tem limite de 50MB por padrão)
- [ ] Verificar formato da imagem (JPG, PNG, WEBP são suportados)
- [ ] Verificar logs no terminal do Flask
- [ ] Verificar logs no Dashboard do Supabase

## Documentação Adicional

📖 Para mais detalhes:
- `SUPABASE_SETUP.md` - Configuração completa passo a passo
- `MUDANCAS_SUPABASE.md` - Resumo técnico das alterações
- Documentação oficial: https://supabase.com/docs/guides/storage

## Status Final

- [ ] ✅ Todas as configurações concluídas
- [ ] ✅ Upload de imagens funcionando
- [ ] ✅ Delete de imagens funcionando
- [ ] ✅ Produtos aparecem corretamente no site
- [ ] ✅ Migração de imagens antigas (se aplicável)

---

**Data de conclusão:** ___/___/______

**Observações:**
