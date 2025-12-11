"""
Script de Migração de Imagens Locais para Supabase Storage

Este script migra todas as imagens existentes em /static/images/ para o Supabase Storage
e atualiza as URLs no banco de dados PostgreSQL.

ATENÇÃO: Execute este script APENAS UMA VEZ após configurar o Supabase.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app import Base, Product, ProductImage
from supabase_service import upload_file_to_supabase
from werkzeug.datastructures import FileStorage
import io

# Carrega variáveis de ambiente
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise SystemExit("Configure DATABASE_URL no .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

STATIC_IMAGES_PATH = os.path.join(os.path.dirname(__file__), "static", "images")

def migrate_images():
    """
    Migra todas as imagens locais para o Supabase e atualiza as URLs no banco.
    """
    print("[info] Iniciando migração de imagens para Supabase...")
    
    if not os.path.exists(STATIC_IMAGES_PATH):
        print(f"[error] Pasta não encontrada: {STATIC_IMAGES_PATH}")
        return
    
    with SessionLocal() as db:
        # Busca todas as imagens do banco
        images = db.scalars(select(ProductImage)).all()
        
        migrated_count = 0
        failed_count = 0
        
        for img in images:
            # Verifica se a URL já é do Supabase
            if img.image_url.startswith("http"):
                print(f"[skip] Imagem já migrada: {img.image_url}")
                continue
            
            # Caminho local da imagem
            local_path = os.path.join(STATIC_IMAGES_PATH, img.image_url)
            
            if not os.path.exists(local_path):
                print(f"[warn] Arquivo não encontrado: {local_path}")
                failed_count += 1
                continue
            
            try:
                # Lê o arquivo local
                with open(local_path, 'rb') as f:
                    file_data = f.read()
                
                # Determina o content_type
                ext = os.path.splitext(img.image_url)[1].lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.webp': 'image/webp',
                    '.gif': 'image/gif'
                }
                content_type = content_type_map.get(ext, 'image/jpeg')
                
                # Cria um objeto FileStorage simulado
                file_storage = FileStorage(
                    stream=io.BytesIO(file_data),
                    filename=img.image_url,
                    content_type=content_type
                )
                
                # Faz upload para o Supabase
                print(f"[info] Fazendo upload: {img.image_url}...")
                public_url = upload_file_to_supabase(file_storage, folder_path="products")
                
                if public_url:
                    # Atualiza a URL no banco
                    img.image_url = public_url
                    print(f"[success] Migrado: {img.image_url} -> {public_url}")
                    migrated_count += 1
                else:
                    print(f"[error] Falha no upload: {img.image_url}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"[error] Erro ao migrar {img.image_url}: {e}")
                failed_count += 1
        
        # Salva todas as alterações
        db.commit()
        
        print("\n" + "="*60)
        print(f"[info] Migração concluída!")
        print(f"[info] Imagens migradas com sucesso: {migrated_count}")
        print(f"[info] Falhas: {failed_count}")
        print("="*60)

if __name__ == "__main__":
    confirm = input("⚠️  Este script irá migrar TODAS as imagens para o Supabase. Continuar? (s/n): ")
    
    if confirm.lower() == 's':
        migrate_images()
    else:
        print("[info] Migração cancelada.")
