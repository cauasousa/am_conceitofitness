import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, Session, relationship
from werkzeug.security import generate_password_hash

# Carrega variáveis de ambiente
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
  raise SystemExit("Set DATABASE_URL in environment")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# --- MODELOS DE DADOS OTIMIZADOS ---

class Classification(Base):
  __tablename__ = "classifications"
  id = Column(Integer, primary_key=True)
  name = Column(String(150), nullable=False, unique=True)
  # Relacionamento Um-para-Muitos: Uma classificação tem vários produtos
  products = relationship("Product", backref="classification") # Corrigido: backref é mais simples

class Product(Base):
  __tablename__ = "products"
  id = Column(Integer, primary_key=True)
  name = Column(String(200), nullable=False)
  description = Column(Text)
  price = Column(Float, nullable=False)
  discount_price = Column(Float, nullable=True) 
  category = Column(String(100))
  total_stock = Column(Integer, default=0) 
  
  # CORREÇÃO: Chave estrangeira para a tabela Classification
  classification_id = Column(Integer, ForeignKey("classifications.id"), nullable=True)
  
  # RELACIONAMENTOS:
  images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
  stock_variants = relationship("ProductStock", back_populates="product", cascade="all, delete-orphan")

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


# --- FUNÇÃO DE INICIALIZAÇÃO E POPULAÇÃO ---

def init():
  Base.metadata.drop_all(engine)
  Base.metadata.create_all(engine)
  admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
  with Session(engine) as session:
    admin = Admin(username="admin", password_hash=generate_password_hash(admin_pw))
    session.add(admin)

    # CRIAÇÃO DAS CLASSIFICAÇÕES
    c_leggings = Classification(name="Leggings")
    c_tops = Classification(name="Tops")
    c_camisetas = Classification(name="Camisetas")
    session.add_all([c_leggings, c_tops, c_camisetas])
    session.flush() # Garante que os IDs das classificações sejam gerados antes de usar

    # 1. PRODUTO 1: LEGGING CONFORTO
    p1 = Product(
      name="Legging Conforto",
      description="Legging de alta compressão, tecido respirável e cintura alta para máximo conforto durante seus treinos. Ideal para atividades físicas e uso diário.",
      price=129.90,
      discount_price=109.90,
      category="Leggings",
      total_stock=15,
      classification=c_leggings # ASSOCIAÇÃO CORRETA: usa o objeto
    )
    p1.stock_variants.extend([
      ProductStock(size="P", color="Preto", quantity=5, is_available=True, price=129.90),
      ProductStock(size="M", color="Branco", quantity=0, is_available=False, price=129.90),
      ProductStock(size="G", color="Rosa", quantity=10, is_available=True, price=119.90),
    ])
    p1.images.extend([
      ProductImage(image_url="legging_conforto_main.jpeg"),
      ProductImage(image_url="legging_conforto_main_2.png"),
      ProductImage(image_url="legging_conforto_main_3.png"),
    ])
    
    # 2. PRODUTO 2: TOP AUTOCUIDADO
    p2 = Product(
      name="Top Autocuidado", 
      description="Top esportivo com sustentação leve, costas nadador e tecido macio, ideal para ioga e treinos de baixo impacto.",
      price=79.90, 
      discount_price=None,
      category="Tops", 
      total_stock=25,
      classification=c_tops # ASSOCIAÇÃO CORRETA
    )
    p2.stock_variants.extend([
      ProductStock(size="P", color="Rosa", quantity=8, is_available=True, price=79.90),
      ProductStock(size="M", color="Bege", quantity=0, is_available=False, price=79.90),
      ProductStock(size="G", color="Preto", quantity=17, is_available=True, price=84.90),
    ])
    p2.images.extend([
      ProductImage(image_url="top_autocuidado_main.png"),
    ])
    
    # 3. PRODUTO 3: CAMISETA AMOR PRÓPRIO
    p3 = Product(
      name="Camiseta Amor Próprio", 
      description="Camiseta oversized leve e confortável, ideal para aquecimento e uso casual. Tecido de alta respirabilidade.",
      price=59.90, 
      discount_price=49.90,
      category="Camisetas", 
      total_stock=30,
      classification=c_camisetas # ASSOCIAÇÃO CORRETA
    )
    p3.stock_variants.extend([
      ProductStock(size="P", color="Branco", quantity=10, is_available=True, price=59.90),
      ProductStock(size="M", color="Branco", quantity=0, is_available=False, price=59.90),
      ProductStock(size="G", color="Preto", quantity=15, is_available=True, price=64.90),
      ProductStock(size="GG", color="Preto", quantity=5, is_available=True, price=64.90),
    ])
    p3.images.extend([
      ProductImage(image_url="camiseta_amor_proprio_main.png"),
      ProductImage(image_url="camiseta_amor_proprio_main_2.png"),
      ProductImage(image_url="camiseta_amor_proprio_main_3.png"),
    ])

    # Adiciona todos os produtos e variações à sessão
    session.add_all([p1, p2, p3])
    session.commit()
    print("DB inicializada e dados inseridos. Admin usuario=admin (senha do .env ou admin123)")

if __name__ == "__main__":
  init()