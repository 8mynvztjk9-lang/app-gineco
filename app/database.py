"""
database.py
-----------
Configura la conexión con la base de datos SQLite.

SQLite es una base de datos que se guarda en un único archivo (clinica.db).
No necesitas instalar ningún servidor de base de datos aparte: es perfecta
para aprender y para proyectos pequeños.

Usamos SQLAlchemy, una librería que nos deja trabajar con la base de datos
usando objetos de Python en lugar de escribir SQL a mano.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ruta del archivo de la base de datos. Se creará junto al proyecto.
SQLALCHEMY_DATABASE_URL = "sqlite:///./clinica.db"

# El "engine" (motor) es el objeto que abre la conexión con SQLite.
# check_same_thread=False es necesario para que funcione bien con FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal crea "sesiones": cada vez que queramos leer o escribir en la
# base de datos, abriremos una sesión, haremos la operación y la cerraremos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase de la que heredarán nuestras tablas (ver models.py).
Base = declarative_base()


def get_db():
    """
    Función auxiliar que entrega una sesión de base de datos a cada página
    que la necesite y se asegura de cerrarla al terminar.
    FastAPI la usa automáticamente con "Depends(get_db)".
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
