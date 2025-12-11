from supabase import create_client, Client
import os
from werkzeug.utils import secure_filename # Para garantir nomes de arquivo seguros
import uuid

# Carrega as variáveis de ambiente (se estiver usando python-dotenv)
from dotenv import load_dotenv
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "product_images" # Use o nome que você definiu

# Validação das credenciais
if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] SUPABASE_URL ou SUPABASE_SERVICE_KEY não configurados no .env")
    print(f"[DEBUG] SUPABASE_URL: {SUPABASE_URL}")
    print(f"[DEBUG] SUPABASE_KEY: {'configurada' if SUPABASE_KEY else 'NÃO configurada'}")

# Inicializa o cliente Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"[ERROR] Falha ao criar cliente Supabase: {e}")

def upload_file_to_supabase(file_object, folder_path="products"):
    """
    Faz o upload de um objeto de arquivo (do formulário) para o Supabase Storage.
    
    Args:
        file_object: O objeto de arquivo recebido do formulário Flask (request.files).
        folder_path: A pasta dentro do bucket (ex: 'products').
        
    Returns:
        A URL pública do arquivo ou None em caso de falha.
    """
    if not file_object or not file_object.filename:
        return None

    # 1. Gera um nome de arquivo único para evitar colisões
    file_extension = file_object.filename.split('.')[-1] if '.' in file_object.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Caminho completo no storage: products/nome_unico.jpg
    path_on_storage = f"{folder_path}/{unique_filename}"
    
    try:
        # 2. Verifica credenciais
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("[error] Credenciais do Supabase não configuradas")
            return None
        
        # 3. Lê o conteúdo do arquivo
        file_object.seek(0)  # Garante que estamos no início do arquivo
        file_data = file_object.read()
        
        print(f"[info] Tentando upload: {file_object.filename} ({len(file_data)} bytes)")
        
        # 4. Faz o upload do arquivo
        response = supabase.storage.from_(BUCKET_NAME).upload(
            file=file_data,
            path=path_on_storage,
            file_options={"content-type": file_object.content_type or "image/jpeg"}
        )
        
        # 5. Obtém a URL pública para salvar no PostgreSQL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(path_on_storage)
        
        print(f"[info] ✅ Upload bem-sucedido: {path_on_storage}")
        print(f"[info] URL pública: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"[error] ❌ Erro ao fazer upload para Supabase: {e}")
        print(f"[debug] Arquivo: {file_object.filename}")
        print(f"[debug] Bucket: {BUCKET_NAME}")
        print(f"[debug] Path: {path_on_storage}")
        print(f"[debug] URL configurada: {SUPABASE_URL}")
        print(f"[debug] Key configurada: {'Sim' if SUPABASE_KEY else 'Não'}")
        return None
    

def delete_file_from_supabase(public_url):
    """
    Deleta um arquivo do Supabase Storage usando sua URL pública.
    
    Args:
        public_url: A URL completa do arquivo armazenada no seu PostgreSQL.
        
    Returns:
        True se a exclusão foi bem-sucedida, False caso contrário.
    """
    
    # 1. Extrai o caminho do arquivo (path) a partir da URL
    # Ex: 'https://[id].supabase.co/storage/v1/object/public/product-images/products/nome_unico.jpg'
    # Devemos extrair apenas: 'products/nome_unico.jpg'
    
    try:
        # Padrão da URL do Supabase Storage para extração do caminho
        path_segments = public_url.split(f"/{BUCKET_NAME}/")
        if len(path_segments) < 2:
            print("URL inválida ou não pertence a este bucket.")
            return False
            
        file_path_in_bucket = path_segments[1]
        
        # 2. Faz a remoção no Storage
        response = supabase.storage.from_(BUCKET_NAME).remove([file_path_in_bucket])
        
        # O Supabase retorna uma lista de objetos vazios em caso de sucesso
        if response and not response[0].get('error'):
             return True
        
        return False
        
    except Exception as e:
        print(f"Erro ao deletar arquivo do Supabase: {e}")
        return False