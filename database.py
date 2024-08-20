# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuración de la URL de la base de datos para MySQL
DATABASE_URL = "mysql+pymysql://root:root1234@mysql_container/machine"

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear una base declarativa
Base = declarative_base()

# Función para crear las tablas en la base de datos
def create_db():
    Base.metadata.create_all(bind=engine)

# Función para obtener una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ejecutar la creación de tablas si el archivo es ejecutado directamente
if __name__ == "__main__":
    create_db()