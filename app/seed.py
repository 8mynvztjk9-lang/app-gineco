"""
seed.py
-------
"Sembrar" (seed) la base de datos: crear las tablas y rellenarlas con datos
de PRUEBA FICTICIOS para poder probar la aplicación.

⚠️  IMPORTANTE: todos los datos de este archivo son inventados.
    Nunca se deben usar datos reales de pacientes.

Cómo ejecutarlo (desde la carpeta del proyecto):
    python -m app.seed
"""

from app.database import Base, engine, SessionLocal
from app.models import Profesional
from app.security import hash_password


def crear_datos_de_prueba():
    # 1) Crea todas las tablas en la base de datos (si no existen ya).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 2) Si ya hay profesionales, no volvemos a insertar (evita duplicados).
        if db.query(Profesional).first() is not None:
            print("La base de datos ya tiene datos. No se ha modificado nada.")
            return

        # 3) Creamos un profesional de prueba.
        #    Usuario: medico    Contraseña: clave1234
        profesional = Profesional(
            username="medico",
            nombre="Dra. Ana Ejemplo (ficticia)",
            hashed_password=hash_password("clave1234"),
        )
        db.add(profesional)
        db.commit()

        print("✅ Datos de prueba creados correctamente.")
        print("   Usuario: medico")
        print("   Contraseña: clave1234")
    finally:
        db.close()


if __name__ == "__main__":
    crear_datos_de_prueba()
