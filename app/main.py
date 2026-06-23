"""
main.py
-------
Punto de entrada de la aplicación. Aquí se "monta" todo:
  - se crea la app de FastAPI,
  - se activa el sistema de sesiones (para el login),
  - se conectan los archivos estáticos (CSS) y las rutas (públicas y privadas).

Cómo arrancar el servidor (desde la carpeta del proyecto):
    uvicorn app.main:app --reload

Luego abre en el navegador:  http://127.0.0.1:8000
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine
from app import models  # noqa: F401  (importa los modelos para que se registren)
from app.routers import public, private

app = FastAPI(title="App Clínica (demo)")

# Crea las tablas que aún no existan (idempotente). Así, al añadir una tabla
# nueva como "cuestionarios_pop", se crea sola sin tener que re-sembrar la BD.
Base.metadata.create_all(bind=engine)

# Siembra el profesional de prueba (medico/clave1234) si la BD está vacía.
# Es idempotente: si ya existe un profesional, no hace nada. Imprescindible
# para que el login funcione en un despliegue nuevo (p. ej. Render) con BD vacía.
try:
    from app.seed import crear_datos_de_prueba
    crear_datos_de_prueba()
except Exception as _e:  # nunca debe impedir que arranque la app
    print("Aviso: no se pudo sembrar el profesional de prueba:", _e)

# SessionMiddleware permite guardar el login en una cookie firmada.
# ⚠️ En un proyecto real, esta clave debe ser secreta y venir de una variable
#    de entorno, no escrita aquí. Para aprender, la dejamos visible.
app.add_middleware(SessionMiddleware, secret_key="cambia-esta-clave-secreta-en-produccion")

# Hace accesibles los archivos de la carpeta "static" (por ejemplo el CSS)
# desde la URL /static/...
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Conectamos las dos secciones de la web.
app.include_router(public.router)
app.include_router(private.router)
