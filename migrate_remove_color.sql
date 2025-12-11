-- Migração: Remover coluna 'color' da tabela product_stock
-- Data: 2025-12-11
-- Descrição: Simplificar variações para usar apenas tamanho (size)

-- BACKUP dos dados antes da migração (importante!)
-- Execute: pg_dump -U seu_usuario -d seu_banco -t product_stock > backup_product_stock.sql

BEGIN;

-- 1. Criar nova constraint de unicidade sem cor
ALTER TABLE product_stock DROP CONSTRAINT IF EXISTS product_stock_product_id_size_color_key;
ALTER TABLE product_stock DROP CONSTRAINT IF EXISTS uq_product_size_color;

-- 2. Remover a coluna 'color'
ALTER TABLE product_stock DROP COLUMN IF EXISTS color;

-- 3. Adicionar nova constraint de unicidade apenas com product_id e size
ALTER TABLE product_stock ADD CONSTRAINT uq_product_size UNIQUE (product_id, size);

-- 4. Verificar estrutura final
-- A tabela agora deve ter: id, product_id, size, quantity, price

COMMIT;

-- Para reverter esta migração (ROLLBACK):
-- BEGIN;
-- ALTER TABLE product_stock ADD COLUMN color VARCHAR(50);
-- ALTER TABLE product_stock DROP CONSTRAINT uq_product_size;
-- ALTER TABLE product_stock ADD CONSTRAINT uq_product_size_color UNIQUE (product_id, size, color);
-- COMMIT;
