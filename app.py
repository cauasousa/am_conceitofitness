import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Boolean # Importações necessárias

# Carrega variáveis de ambiente
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET = os.environ.get("FLASK_SECRET") or os.environ.get("SECRET_KEY") or "troque_ja"

if not DATABASE_URL:
  raise SystemExit("Configure DATABASE_URL no .env")

engine = create_engine(DATABASE_URL, future=True)
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
  color = Column(String(50), nullable=False)
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

# chamada de inicialização
ensure_admin()

app = Flask(__name__)
app.secret_key = SECRET

# UPLOAD CONFIG
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# host/port configuráveis (use .env: FLASK_HOST, FLASK_PORT, FLASK_DEBUG)
HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
PORT = int(os.environ.get("FLASK_PORT", "5000"))
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

# rota simples para checagem de saúde (útil para debug rápido)
@app.route("/health")
def health():
    return "ok", 200

# =========================================================================
# ROTAS PÚBLICAS
# =========================================================================

@app.route("/")
def index():
  q = (request.args.get('q') or "").strip()
  with SessionLocal() as db:
    # Eager load de imagens e variações para uso direto nos templates
    base_stmt = select(Product).options(joinedload(Product.images), joinedload(Product.stock_variants))
    if q:
      stmt = base_stmt.filter(Product.name.ilike(f"%{q}%"))
    else:
      stmt = base_stmt
    products = db.scalars(stmt).unique().all()
  brand = "Conforto, autocuidado e amor próprio!🌷🤍"
  insta = "@am_conceitofitness"
  return render_template("index.html", products=products, brand=brand, insta=insta, q=q)

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
      {"id": v.id, "size": v.size, "color": v.color, "quantity": int(v.quantity or 0), "is_available": bool(v.is_available), "price": v.price}
      for v in variant_objs
    ]
    # Filtra apenas tamanhos e cores únicos que TÊM ALGUM ESTOQUE
    available_variants = [v for v in variants if v["quantity"] > 0]
    
    sizes = sorted(list({v["size"] for v in available_variants}))
    colors = sorted(list({v["color"] for v in available_variants}))
    
    # NOTE: Para o Jinja, agora você só verá tamanhos/cores que TÊM ESTOQUE inicial.

    preco_original = product.price
    preco_promocional = product.discount_price if product.discount_price is not None else product.price

    return render_template(
      "product_detail.html",
      product=product,
      preco_original=preco_original,
      preco_promocional=preco_promocional,
      variants=variants, # Envia TODAS as variantes para o JS
      sizes=sizes,
      colors=colors
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
    classifications = db.scalars(select(Classification)).all()
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
    c = Classification(name=name)
    db.add(c)
    db.commit()
  flash("Classificação criada")
  return redirect(url_for("admin_dashboard"))

def save_uploaded_images(files):
  saved = []
  for f in files:
    if not f:
      continue
    filename = secure_filename(f.filename)
    if filename == "":
      continue
    target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    # evita sobrescrever: se existir, prefixa timestamp
    if os.path.exists(target):
      base, ext = os.path.splitext(filename)
      filename = f"{base}_{int(os.times()[4])}{ext}"
      target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(target)
    saved.append(filename)
  return saved

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
    # salvar imagens e criar ProductImage
    saved_files = save_uploaded_images(uploaded)
    for fname in saved_files:
      db.add(ProductImage(product_id=p.id, image_url=fname))
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
    saved_files = save_uploaded_images(uploaded)
    for fname in saved_files:
      db.add(ProductImage(product_id=p.id, image_url=fname))
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
  color = (request.form.get("color") or "").strip()
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

  if not size or not color:
    flash("Tamanho e Cor são obrigatórios para nova variação.")
    return redirect(url_for("admin_dashboard"))

  with SessionLocal() as db:
    exists = db.scalar(select(ProductStock).filter_by(product_id=pid, size=size, color=color))
    if exists:
      flash("Variação (Tamanho/Cor) já existe!")
      return redirect(url_for("admin_dashboard"))

    new_variant = ProductStock(
      product_id=pid,
      size=size,
      color=color,
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
  flash(f"Variação {size}/{color} adicionada com sucesso.")
  return redirect(url_for("admin_dashboard"))

# Remover imagem específica (arquivo + registro DB)
@app.route("/admin/remove_image/<int:image_id>", methods=["POST"])
@admin_required
def admin_remove_image(image_id):
    with SessionLocal() as db:
        img = db.get(ProductImage, image_id)
        if not img:
            flash("Imagem não encontrada")
            return redirect(url_for("admin_dashboard"))
        # tenta remover arquivo físico (se existir)
        try:
            path = os.path.join(app.config["UPLOAD_FOLDER"], img.image_url)
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            # não bloquear remoção no DB se falhar ao remover arquivo
            print(f"[warn] não foi possível apagar arquivo de imagem: {e}")
        # remove registro
        db.delete(img)
        db.commit()
    flash("Imagem removida com sucesso.")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
  session.pop("admin_logged", None)
  return redirect(url_for("index"))

if __name__ == "__main__":
  print(f"[startup] Iniciando app em http://{HOST}:{PORT}  (DEBUG={DEBUG})")
  app.run(host=HOST, port=PORT, debug=DEBUG)