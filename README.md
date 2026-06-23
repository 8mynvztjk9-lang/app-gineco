# App Clínica (demo)

Aplicación web de **demostración** para uso médico, hecha con **Python + FastAPI**
y base de datos **SQLite**.

> ⚠️ Esta app usa **solo datos ficticios de prueba**. Nunca introduzcas datos
> reales de pacientes.

## ¿Qué hace?

- **Sección pública** (`/`): información general para pacientes, sin datos sensibles.
  - Páginas informativas sobre el suelo pélvico y sus diagnósticos.
  - **Guía de ejercicios con cronómetro guiado** (`/suelo-pelvico/ejercicios`).
- **Sección privada** (`/panel`): solo para profesionales, protegida con login.
  - Formulario para registrar **procesos clínicos** por **NHC**.

## Requisitos

- Python 3.10 o superior.

## Puesta en marcha (paso a paso)

Abre una terminal **dentro de la carpeta del proyecto** y ejecuta:

```bash
# 1) Crear un entorno virtual (una "caja" aislada para las librerías)
python3 -m venv .venv

# 2) Activarlo (en macOS / Linux)
source .venv/bin/activate

# 3) Instalar las librerías necesarias
pip install -r requirements.txt

# 4) Crear la base de datos con datos de prueba
python -m app.seed

# 5) Arrancar el servidor
uvicorn app.main:app --reload
```

Luego abre en el navegador: <http://127.0.0.1:8000>

## Datos de prueba para el login

- Usuario: `medico`
- Contraseña: `clave1234`

## Estructura del proyecto

```
app/
├── main.py        Punto de entrada (arranca el servidor)
├── database.py    Conexión con SQLite
├── models.py      Tablas: Profesional y ProcesoClinico
├── security.py    Cifrado y verificación de contraseñas
├── seed.py        Crea la base de datos con datos ficticios
├── routers/
│   ├── public.py  Páginas públicas (pacientes)
│   └── private.py Páginas privadas (profesionales, con login)
├── templates/     Páginas HTML
└── static/        Estilos CSS
```
