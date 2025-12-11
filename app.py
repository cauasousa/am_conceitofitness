import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Boolean, DateTime
import math
import requests
from datetime import datetime
from supabase_service import upload_file_to_supabase, delete_file_from_supabase

# Carrega variáveis de ambiente
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET = os.environ.get("FLASK_SECRET") or os.environ.get("SECRET_KEY") or "troque_ja"

if not DATABASE_URL:
  raise SystemExit("Configure DATABASE_URL no .env")

engine = create_engine(DATABASE_URL, future=True, pool_recycle=3600, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# =========================================================================
# MODELOS DE DADOS
# =========================================================================
class Product(Base):
  __tablename__ = "products"
  id = Column(Integer, primary_key=True)
  name = Column(String(200), nullable=False)
  description = Column(Text)
  price = Column(Float, nullable=False)
  discount_price = Column(Float, nullable=True) # NOVO
  category = Column(String(100))
  total_stock = Column(Integer, default=0) # NOVO
  # note: campo 'image' removido (usamos product.images para todas as imagens)
  images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
  stock_variants = relationship("ProductStock", back_populates="product", cascade="all, delete-orphan")
  # relação com Classification
  classification_id = Column(Integer, ForeignKey("classifications.id"), nullable=True)
  classification = relationship("Classification", back_populates="products")

class ProductImage(Base):
  __tablename__ = "product_images"
  id = Column(Integer, primary_key=True)
  product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
  image_url = Column(String(300), nullable=False)
  product = relationship("Product", back_populates="images")

class ProductStock(Base):
  __tablename__ = "product_stock"
  id = Column(Integer, primary_key=True)
  product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
  size = Column(String(50), nullable=False)
  quantity = Column(Integer, default=0)
  # preço específico para essa variação (opcional)
  price = Column(Float, nullable=True)
  is_available = Column(Boolean, default=True) 
  product = relationship("Product", back_populates="stock_variants")

class Admin(Base):
  __tablename__ = "admin"
  id = Column(Integer, primary_key=True)
  username = Column(String(100), unique=True, nullable=False)
  password_hash = Column(String(300), nullable=False)

class Classification(Base):
  __tablename__ = "classifications"
  id = Column(Integer, primary_key=True)
  name = Column(String(150), nullable=False, unique=True)
  display_order = Column(Integer, default=0)
  products = relationship("Product", back_populates="classification", cascade="all")


# =========================================================================
# FUNÇÕES E INICIALIZAÇÃO
# =========================================================================

Base.metadata.create_all(engine) # Garante que as tabelas existem

def ensure_admin():
  admin_user = os.environ.get("ADMIN_USER", "admin")
  admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
  with SessionLocal() as db:
    # CORREÇÃO: Usando a sintaxe moderna do SQLAlchemy 2.0 (select/scalar)
    exists = db.scalar(select(Admin).limit(1)) 
    if not exists:
      db.add(Admin(username=admin_user, password_hash=generate_password_hash(admin_pw)))
      db.commit()
      print(f"[setup] Admin criado: {admin_user} (senha a partir de ADMIN_PASSWORD)")

def ensure_classification_order_column():
  """Adds display_order column to classifications if missing (SQLite/Postgres safe)."""
  insp = inspect(engine)
  cols = [c['name'] for c in insp.get_columns('classifications')]
  if 'display_order' in cols:
    return
  try:
    with engine.begin() as conn:
      conn.exec_driver_sql("ALTER TABLE classifications ADD COLUMN display_order INTEGER DEFAULT 0")
    print("[setup] Column display_order added to classifications")
  except Exception as e:
    print(f"[setup] Could not add display_order column: {e}")

# chamada de inicialização
ensure_admin()
ensure_classification_order_column()

app = Flask(__name__)
app.secret_key = SECRET

# UPLOAD CONFIG (Desativado - agora usa Supabase Storage)
# UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# host/port configuráveis (use .env: FLASK_HOST, FLASK_PORT, FLASK_DEBUG)
HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
PORT = int(os.environ.get("FLASK_PORT", "5000"))
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

# rota simples para checagem de saúde (útil para debug rápido)
@app.route("/health")
def health():
    return "ok", 200

# CONSTANTES DE FRETE
PICKUP_POINT_CEP = "65606-530"  # Caxias
COST_PER_KM = 0.1724  # R$ por km

def get_cep_coordinates(cep):
    """
    Obtém latitude/longitude de um CEP usando a API ViaCEP + Nominatim.
    Retorna tuple (lat, lon) ou None se não encontrar.
    """
    try:
        cep_clean = cep.replace('-', '').replace(' ', '').strip()
        if len(cep_clean) != 8 or not cep_clean.isdigit():
            print(f"[warn] CEP inválido: {cep_clean}")
            return None
            
        # Busca dados do CEP na ViaCEP
        url = f"https://viacep.com.br/ws/{cep_clean}/json/"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if not data.get('erro'):
                # ViaCEP retorna logradouro, localidade, uf
                logradouro = data.get('logradouro', '')
                localidade = data.get('localidade', '')
                uf = data.get('uf', '')
                
                # Usa Nominatim para converter endereço em coordenadas
                return get_coordinates_nominatim(logradouro, localidade, uf)
            else:
                print(f"[warn] CEP não encontrado: {cep_clean}")
                return None
        else:
            print(f"[warn] ViaCEP retornou status {resp.status_code}")
            return None
    except Exception as e:
        print(f"[warn] Erro ao buscar CEP {cep}: {e}")
        return None

def get_coordinates_nominatim(street, city, state):
    """
    Usa Nominatim (OpenStreetMap) para obter coordenadas a partir do endereço.
    Retorna tuple (lat, lon) ou None se não encontrar.
    """
    try:
        if not city:
            print("[warn] Cidade não fornecida")
            return None
            
        # Monta query para nominatim
        addr = f"{city}, {state}, Brasil"
        if street:
            addr = f"{street}, {addr}"
            
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': addr,
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'AM-Conceito-Fitness-Shop'}
        
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                print(f"[info] Coordenadas encontradas: ({lat}, {lon}) para {addr}")
                return (lat, lon)
            else:
                print(f"[warn] Nominatim não encontrou coordenadas para: {addr}")
                return None
        else:
            print(f"[warn] Nominatim retornou status {resp.status_code}")
            return None
    except Exception as e:
        print(f"[warn] Erro ao buscar coordenadas nominatim: {e}")
        return None

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula distância em km entre dois pontos (lat/lon) usando fórmula de Haversine.
    """
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

@app.route("/api/calculate-shipping", methods=["POST"])
def calculate_shipping():
    """
    Calcula o custo do frete baseado no CEP do cliente.
    Recebe JSON: { "cep": "xxxxx-xxx", "method": "delivery" ou "pickup" }
    Retorna JSON: { "success": bool, "shipping_cost": float, "distance_km": float, "message": str }
    """
    try:
        data = request.get_json() or {}
        cep = (data.get('cep') or '').strip()
        method = (data.get('method') or 'delivery').strip()
        
        print(f"[info] calculate_shipping chamado: CEP={cep}, method={method}")
        
        # Se for retirar no ponto, frete é grátis
        if method == 'pickup':
            return jsonify({
                'success': True,
                'shipping_cost': 0.0,
                'distance_km': 0.0,
                'message': 'Retirada no ponto: Frete grátis'
            })
        
        # Validação básica do CEP
        if not cep or len(cep.replace('-', '')) != 8:
            return jsonify({
                'success': False,
                'shipping_cost': 0.0,
                'distance_km': 0.0,
                'message': 'CEP inválido. Use formato: xxxxx-xxx'
            }), 400
        
        # Obter coordenadas do CEP do cliente
        print(f"[info] Buscando coordenadas do cliente para CEP {cep}...")
        client_coords = get_cep_coordinates(cep)
        if not client_coords:
            return jsonify({
                'success': False,
                'shipping_cost': 0.0,
                'distance_km': 0.0,
                'message': 'CEP não encontrado. Tente outro.'
            }), 404
        
        # Obter coordenadas do ponto de retirada
        print(f"[info] Buscando coordenadas do ponto de retirada...")
        pickup_coords = get_cep_coordinates(PICKUP_POINT_CEP)
        if not pickup_coords:
            return jsonify({
                'success': False,
                'shipping_cost': 0.0,
                'distance_km': 0.0,
                'message': 'Erro ao calcular frete. Tente novamente.'
            }), 500
        
        # Calcular distância
        distance_km = haversine_distance(
            pickup_coords[0], pickup_coords[1],
            client_coords[0], client_coords[1]
        )
        
        # Calcular custo
        shipping_cost = (distance_km * COST_PER_KM) + 2
        
        print(f"[info] Frete calculado: {distance_km:.2f}km = R$ {shipping_cost:.2f}")
        
        return jsonify({
            'success': True,
            'shipping_cost': round(shipping_cost, 2),
            'distance_km': round(distance_km, 2),
            # 'message': f'Frete para {distance_km:.1f} km: R$ {shipping_cost:.2f}'
            'message': f'Chega entre entre 1 a 7 dias úteis.'
        })
    
    except Exception as e:
        print(f"[error] Erro em calculate_shipping: {e}")
        return jsonify({
            'success': False,
            'shipping_cost': 0.0,
            'distance_km': 0.0,
            'message': f'Erro ao calcular frete: {str(e)}'
        }), 500

# =========================================================================
# ROTAS PÚBLICAS
# =========================================================================

@app.route("/")
def index():
  q = (request.args.get('q') or "").strip()
  with SessionLocal() as db:
    # Eager load de imagens e variações para uso direto nos templates
    base_stmt = select(Product).options(
      joinedload(Product.images),
      joinedload(Product.stock_variants),
      joinedload(Product.classification)
    )
    if q:
      stmt = base_stmt.filter(Product.name.ilike(f"%{q}%"))
    else:
      stmt = base_stmt
    products = db.scalars(stmt).unique().all()
    classifications = db.scalars(select(Classification).order_by(Classification.display_order, Classification.name)).all()

  # Agrupa produtos por classificação para exibição na home
  grouped_products = []
  for c in classifications:
    classified = [p for p in products if p.classification and p.classification.id == c.id]
    if classified:
      grouped_products.append({"id": c.id, "name": c.name, "products": classified})

  # Inclui produtos sem classificação explícita
  uncategorized = [p for p in products if not p.classification]
  if uncategorized:
    grouped_products.append({"id": None, "name": "Outros", "products": uncategorized})
  brand = "Conforto, autocuidado e amor próprio!🌷🤍"
  insta = "@am_conceitofitness"
  return render_template(
    "index.html",
    products=products,
    grouped_products=grouped_products,
    brand=brand,
    insta=insta,
    q=q
  )

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    with SessionLocal() as db:
      # CORREÇÃO: Usando select moderno
      admin = db.scalar(select(Admin).filter_by(username=username)) 
      if not admin or not check_password_hash(admin.password_hash, password):
        flash("Credenciais inválidas")
        return redirect(url_for("login"))
      
      # sucesso: set session and redirect to admin dashboard
      session["admin_logged"] = True
      session.permanent = True
      session.modified = True
      return redirect(url_for("admin_dashboard"))
  return render_template("login.html")

@app.route("/produto/<int:product_id>")
def product_detail(product_id):
  with SessionLocal() as db:
    # Carrega o produto, as imagens E AS VARIAÇÕES DE ESTOQUE
    stmt = select(Product).options(joinedload(Product.images), joinedload(Product.stock_variants)).filter_by(id=product_id)
    product = db.scalar(stmt)
    if not product:
      return redirect(url_for('index'))

    # Converte variações para estrutura simples para o JS/Template
    variant_objs = product.stock_variants
    variants = [
      {"id": v.id, "size": v.size, "quantity": int(v.quantity or 0), "is_available": bool(v.is_available), "price": v.price}
      for v in variant_objs
    ]
    # Filtra apenas tamanhos únicos que TÊM ALGUM ESTOQUE
    available_variants = [v for v in variants if v["quantity"] > 0]
    
    sizes = sorted(list({v["size"] for v in available_variants}))
    
    # NOTE: Para o Jinja, agora você só verá tamanhos/cores que TÊM ESTOQUE inicial.

    preco_original = product.price
    preco_promocional = product.discount_price if product.discount_price is not None else product.price

    return render_template(
      "product_detail.html",
      product=product,
      preco_original=preco_original,
      preco_promocional=preco_promocional,
      variants=variants, # Envia TODAS as variantes para o JS
      sizes=sizes
    )
# =========================================================================
# ROTAS ADMIN (adições)
# =========================================================================

def admin_required(f):
  from functools import wraps
  @wraps(f)
  def wrapped(*args, **kwargs):
    if not session.get("admin_logged"):
      return redirect(url_for("login"))
    return f(*args, **kwargs)
  return wrapped

@app.route("/admin")
@admin_required
def admin_dashboard():
  q = (request.args.get('q') or "").strip()
  with SessionLocal() as db:
    # BUSCA: Carrega produtos e suas variações e imagens (eager load)
    base_stmt = select(Product).options(joinedload(Product.stock_variants), joinedload(Product.images), joinedload(Product.classification))
    if q:
      stmt = base_stmt.filter(Product.name.ilike(f"%{q}%"))
    else:
      stmt = base_stmt
    products = db.scalars(stmt).unique().all()
    classifications = db.scalars(select(Classification).order_by(Classification.display_order, Classification.name)).all()
  return render_template("admin.html", products=products, classifications=classifications, q=q)
  # note: template admin.html agora recebe 'classifications' — abaixo ajustaremos template

@app.route("/admin/home")
@admin_required
def admin_home():
  # rota administrativa principal após login — reaproveita o template admin
  return redirect(url_for('admin_dashboard')) # Redireciona para o painel principal

@app.route("/admin/classification/add", methods=["POST"])
@admin_required
def admin_add_classification():
  name = request.form.get("name")
  if not name:
    flash("Nome da classificação é obrigatório")
    return redirect(url_for("admin_dashboard"))
  with SessionLocal() as db:
    # evita duplicados simples
    exists = db.scalar(select(Classification).filter_by(name=name))
    if exists:
      flash("Classificação já existe")
      return redirect(url_for("admin_dashboard"))
    # define ordem como último + 1
    max_order = db.scalar(select(Classification.display_order).order_by(Classification.display_order.desc()).limit(1)) or 0
    c = Classification(name=name, display_order=max_order + 1)
    db.add(c)
    db.commit()
  flash("Classificação criada")
  return redirect(url_for("admin_dashboard"))

def save_uploaded_images(files, product_name="produto", existing_count=0):
  """
  Faz upload de múltiplas imagens para o Supabase Storage.
  Renomeia as imagens com base no nome do produto + timestamp único.
  
  Args:
    files: Lista de arquivos de imagem
    product_name: Nome do produto (usado para renomear)
    existing_count: Número de imagens já existentes (não usado, mantido por compatibilidade)
  
  Retorna lista de URLs públicas das imagens.
  """
  import re
  import uuid
  from pathlib import Path
  from datetime import datetime
  
  saved_urls = []
  
  # Normaliza o nome do produto (remove caracteres especiais, espaços -> underscores)
  normalized_name = re.sub(r'[^\w\s-]', '', product_name.lower())
  normalized_name = re.sub(r'[-\s]+', '_', normalized_name)
  normalized_name = normalized_name[:30]  # Limita tamanho
  
  # Gera timestamp único para este batch de uploads
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  
  for idx, f in enumerate(files, start=1):
    if not f or not f.filename:
      continue
    
    # Pega extensão original
    original_ext = Path(f.filename).suffix.lower()
    if not original_ext:
      original_ext = '.jpg'
    
    # Gera novo nome com timestamp: produto_20251211_143022_01.jpg
    # Isso garante unicidade mesmo após exclusões
    new_filename = f"{normalized_name}_{timestamp}_{idx:02d}{original_ext}"
    
    # Upload para Supabase Storage com nome customizado
    public_url = upload_file_to_supabase(f, folder_path="products", custom_filename=new_filename)
    
    if public_url:
      saved_urls.append(public_url)
    else:
      print(f"[warning] Falha ao fazer upload de {f.filename}")
  
  return saved_urls

@app.route("/admin/add", methods=["POST"])
@admin_required
def admin_add():
  name = request.form.get("name")
  description = request.form.get("description")
  
  # NOVO CAMPO: Desconto
  price_str = request.form.get("price") or '0'
  discount_price_str = request.form.get("discount_price")
  
  price = float(price_str)
  discount_price = float(discount_price_str) if discount_price_str else None
  
  classification_id = request.form.get("classification") or None
  uploaded = request.files.getlist("images")
  
  with SessionLocal() as db:
    p = Product(
      name=name, 
      description=description, 
      price=price, 
      discount_price=discount_price,
      classification_id=int(classification_id) if classification_id else None
    )
    db.add(p)
    db.commit()
    # salvar imagens no Supabase e criar ProductImage com URLs
    # Passa o nome do produto para renomeação inteligente
    saved_urls = save_uploaded_images(uploaded, product_name=name, existing_count=0)
    for url in saved_urls:
      db.add(ProductImage(product_id=p.id, image_url=url))
    db.commit()
    flash(f"Produto '{name}' adicionado com sucesso. Adicione variações de estoque.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit/<int:pid>", methods=["POST"])
@admin_required
def admin_edit(pid):
  with SessionLocal() as db:
    p = db.get(Product, pid)
    if not p:
      flash("Produto não encontrado")
      return redirect(url_for("admin_dashboard"))
    # atualização campos básicos
    p.name = request.form.get("name")
    p.description = request.form.get("description")
    
    # NOVO CAMPO: Desconto
    price_str = request.form.get("price")
    discount_price_str = request.form.get("discount_price")

    p.price = float(price_str) if price_str else p.price
    p.discount_price = float(discount_price_str) if discount_price_str else None
    
    # classificação
    classification_id = request.form.get("classification") or None
    p.classification_id = int(classification_id) if classification_id else None
    # imagens novas (não removemos as antigas aqui — apenas adicionamos)
    uploaded = request.files.getlist("images")
    # Conta quantas imagens já existem para incrementar corretamente
    existing_images_count = len(p.images)
    saved_urls = save_uploaded_images(uploaded, product_name=p.name, existing_count=existing_images_count)
    for url in saved_urls:
      db.add(ProductImage(product_id=p.id, image_url=url))
    db.commit()
  flash("Produto atualizado")
  return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit_stock/<int:pid>", methods=["POST"])
@admin_required
def admin_edit_stock(pid):
  with SessionLocal() as db:
    # Carrega variantes do produto
    variants = db.scalars(select(ProductStock).filter_by(product_id=pid)).all()
    for variant in variants:
      qty_field = f"qty_{variant.id}"
      price_field = f"price_{variant.id}"
      avail_field = f"available_{variant.id}"
      new_quantity_str = request.form.get(qty_field)
      new_price_str = request.form.get(price_field)
      is_available_checked = request.form.get(avail_field) == 'on'
      if new_quantity_str is not None:
        try:
          new_quantity = int(new_quantity_str)
        except ValueError:
          new_quantity = variant.quantity or 0
        variant.quantity = new_quantity
        # força disponibilidade baseada na quantidade
        variant.is_available = False if new_quantity == 0 else bool(is_available_checked)
      if new_price_str is not None:
        try:
          new_price = float(new_price_str.replace(',', '.'))
          variant.price = new_price
        except ValueError:
          pass

    # Atualiza total_stock do produto
    product = db.get(Product, pid)
    if product:
      total = sum((v.quantity or 0) for v in product.stock_variants)
      product.total_stock = total

    db.commit()
  flash("Estoque atualizado com sucesso!")
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/add_variant/<int:pid>", methods=["POST"])
@admin_required
def admin_add_variant(pid):
  size = (request.form.get("size") or "").strip()
  try:
    quantity = int(request.form.get("quantity") or 0)
  except ValueError:
    quantity = 0

  # preço opcional por variação
  price_raw = request.form.get("price") or ""
  try:
    price_val = float(price_raw.replace(',', '.')) if price_raw.strip() != "" else None
  except ValueError:
    price_val = None

  if not size:
    flash("Tamanho é obrigatório para nova variação.")
    return redirect(url_for("admin_dashboard"))

  with SessionLocal() as db:
    exists = db.scalar(select(ProductStock).filter_by(product_id=pid, size=size))
    if exists:
      flash("Variação de tamanho já existe!")
      return redirect(url_for("admin_dashboard"))

    new_variant = ProductStock(
      product_id=pid,
      size=size,
      quantity=quantity,
      is_available=(quantity > 0),
      price=price_val
    )
    db.add(new_variant)

    # Atualiza total_stock do produto pai
    product = db.get(Product, pid)
    if product:
      product.total_stock = (product.total_stock or 0) + quantity

    db.commit()
  flash(f"Variação tamanho {size} adicionada com sucesso.")
  return redirect(url_for("admin_dashboard"))

# Remover imagem específica (Supabase Storage + registro DB)
@app.route("/admin/remove_image/<int:image_id>", methods=["POST"])
@admin_required
def admin_remove_image(image_id):
    with SessionLocal() as db:
        img = db.get(ProductImage, image_id)
        if not img:
            flash("Imagem não encontrada")
            return redirect(url_for("admin_dashboard"))
        
        # Remove do Supabase Storage usando a URL pública
        delete_success = delete_file_from_supabase(img.image_url)
        
        if not delete_success:
            print(f"[warn] Falha ao deletar imagem do Supabase: {img.image_url}")
        
        # Remove registro do banco de dados
        db.delete(img)
        db.commit()
    
    flash("Imagem removida com sucesso.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<int:pid>", methods=["POST"])
@admin_required
def admin_delete(pid):
    """Deleta um produto completamente (imagens do Supabase, variações e dados)"""
    with SessionLocal() as db:
        product = db.get(Product, pid)
        if not product:
            flash("Produto não encontrado")
            return redirect(url_for("admin_dashboard"))
        
        # Remove imagens do Supabase Storage
        for img in product.images:
            delete_success = delete_file_from_supabase(img.image_url)
            if not delete_success:
                print(f"[warn] Falha ao deletar imagem do Supabase: {img.image_url}")
        
        # Remove produto (cascata remove imagens e variações do DB)
        db.delete(product)
        db.commit()
    
    flash(f"Produto '{product.name}' deletado com sucesso!")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_variant/<int:variant_id>", methods=["POST"])
@admin_required
def admin_delete_variant(variant_id):
    """Deleta uma variação de um produto"""
    with SessionLocal() as db:
        variant = db.get(ProductStock, variant_id)
        if not variant:
            flash("Variação não encontrada")
            return redirect(url_for("admin_dashboard"))
        
        product_id = variant.product_id
        db.delete(variant)
        db.commit()
    
    flash("Variação deletada com sucesso!")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_classification/<int:class_id>", methods=["POST"])
@admin_required
def admin_delete_classification(class_id):
    """Deleta uma classificação (se não tiver produtos)"""
    with SessionLocal() as db:
        classification = db.get(Classification, class_id)
        if not classification:
            flash("Classificação não encontrada")
            return redirect(url_for("admin_dashboard"))
        
        # Verifica se há produtos nesta classificação
        product_count = db.query(Product).filter_by(classification_id=class_id).count()
        if product_count > 0:
            flash(f"Não é possível deletar a classificação '{classification.name}' porque há {product_count} produto(s) associado(s)")
            return redirect(url_for("admin_dashboard"))
        
        class_name = classification.name
        db.delete(classification)
        db.commit()
    
    flash(f"Classificação '{class_name}' deletada com sucesso!")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reorder_classifications", methods=["POST"])
@admin_required
def admin_reorder_classifications():
  """Atualiza display_order das classificações a partir do formulário."""
  with SessionLocal() as db:
    classifications = db.scalars(select(Classification)).all()
    for c in classifications:
      field = f"order_{c.id}"
      val = request.form.get(field)
      if val is None:
        continue
      try:
        c.display_order = int(val)
      except ValueError:
        continue
    db.commit()
  flash("Ordem das classificações atualizada")
  return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
  session.pop("admin_logged", None)
  return redirect(url_for("index"))

# ======== NOVAS ROTAS PARA CARRINHO E CHECKOUT ========
@app.route("/cart")
def cart():
  # Página do carrinho — conteúdo gerenciado via JS (localStorage)
  return render_template("cart.html")

@app.route("/checkout")
def checkout():
  # Página de checkout/entrega/pagamento
  return render_template("checkout.html")


if __name__ == "__main__":
  print(f"[startup] Iniciando app em http://{HOST}:{PORT}  (DEBUG={DEBUG})")
  app.run(host=HOST, port=PORT, debug=DEBUG)