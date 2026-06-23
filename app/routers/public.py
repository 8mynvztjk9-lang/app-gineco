"""
routers/public.py
-----------------
La SECCIÓN PÚBLICA, pensada para pacientes.
Aquí solo se muestra información general. NUNCA datos sensibles ni login.
"""

import json
import os

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CuestionarioPOP, CuestionarioIncontinencia, DiarioMiccional

# APIRouter agrupa varias páginas relacionadas.
router = APIRouter()

# Le decimos dónde están los archivos HTML.
templates = Jinja2Templates(directory="app/templates")


def css_v() -> int:
    """Devuelve la fecha de modificación del CSS (en segundos).

    Se usa en la plantilla como  ?v={{ css_v() }}  para que, cada vez que
    editamos style.css, el navegador descargue la versión nueva en lugar de
    una antigua guardada en su caché.
    """
    try:
        return int(os.path.getmtime("app/static/style.css"))
    except OSError:
        return 0


# La hacemos accesible desde TODAS las plantillas.
templates.env.globals["css_v"] = css_v


@router.get("/")
def pagina_inicio(request: Request):
    """Página de inicio pública. Cualquiera puede verla."""
    # En la versión actual de Starlette, el primer argumento es "request"
    # y el segundo el nombre de la plantilla. "request" se añade solo al
    # contexto, así que no hace falta repetirlo en el diccionario.
    return templates.TemplateResponse(
        request,
        "public_home.html",
        {"titulo": "Inicio - Clínica (demo)"},
    )


@router.get("/suelo-pelvico")
def pagina_suelo_pelvico(request: Request):
    """Página general: qué es el suelo pélvico y sus disfunciones."""
    return templates.TemplateResponse(
        request,
        "suelo_pelvico.html",
        {"titulo": "Suelo pélvico - Información para pacientes"},
    )


@router.get("/cuestionario-pop")
def pagina_cuestionario_pop(request: Request):
    """Cuestionario POP (PFDI-20 + PFIQ-7 + PISQ-IR) que rellena la paciente.
    Al terminar genera un informe y lo envía a guardar asociado a su NHC."""
    return templates.TemplateResponse(
        request,
        "cuestionario_pop.html",
        {"titulo": "Cuestionario de impacto del prolapso (POP)"},
    )


@router.post("/cuestionario-pop")
def guardar_cuestionario_pop(
    nhc: str = Form(...),
    nombre: str = Form(""),
    apellidos: str = Form(""),
    fecha: str = Form(""),
    informe: str = Form(...),
    respuestas_json: str = Form("{}"),
    pfdi_total: str = Form(None),
    pfiq_total: str = Form(None),
    db: Session = Depends(get_db),
):
    """Recibe el cuestionario completado por la paciente y lo guarda en la BD.

    Se llama por fetch() desde la página, así que devolvemos JSON.
    """
    nhc = (nhc or "").strip()
    if not nhc:
        return JSONResponse(
            {"ok": False, "error": "Falta el NHC."}, status_code=400
        )

    # Validación ligera: que el JSON de respuestas sea válido.
    try:
        json.loads(respuestas_json or "{}")
    except ValueError:
        respuestas_json = "{}"

    registro = CuestionarioPOP(
        nhc=nhc,
        nombre=(nombre or "").strip(),
        apellidos=(apellidos or "").strip(),
        fecha=(fecha or "").strip(),
        informe=informe or "",
        respuestas_json=respuestas_json or "{}",
        pfdi_total=(pfdi_total or None),
        pfiq_total=(pfiq_total or None),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)

    return JSONResponse({"ok": True, "id": registro.id})


@router.get("/cuestionario-incontinencia")
def pagina_cuestionario_incontinencia(request: Request):
    """Cuestionario combinado de vejiga e incontinencia (CACV + ICIQ-IU-SF)."""
    return templates.TemplateResponse(
        request,
        "cuestionario_incontinencia.html",
        {"titulo": "Cuestionario de vejiga e incontinencia"},
    )


@router.post("/cuestionario-incontinencia")
def guardar_cuestionario_incontinencia(
    nhc: str = Form(...),
    nombre: str = Form(""),
    apellidos: str = Form(""),
    fecha: str = Form(""),
    informe: str = Form(...),
    respuestas_json: str = Form("{}"),
    cacv_sintomas: str = Form(None),
    cacv_molestia: str = Form(None),
    iciq_total: str = Form(None),
    iciq_tipo: str = Form(None),
    db: Session = Depends(get_db),
):
    """Guarda el cuestionario de incontinencia rellenado por la paciente."""
    nhc = (nhc or "").strip()
    if not nhc:
        return JSONResponse({"ok": False, "error": "Falta el NHC."}, status_code=400)

    try:
        json.loads(respuestas_json or "{}")
    except ValueError:
        respuestas_json = "{}"

    registro = CuestionarioIncontinencia(
        nhc=nhc,
        nombre=(nombre or "").strip(),
        apellidos=(apellidos or "").strip(),
        fecha=(fecha or "").strip(),
        informe=informe or "",
        respuestas_json=respuestas_json or "{}",
        cacv_sintomas=(cacv_sintomas or None),
        cacv_molestia=(cacv_molestia or None),
        iciq_total=(iciq_total or None),
        iciq_tipo=(iciq_tipo or None),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return JSONResponse({"ok": True, "id": registro.id})


@router.post("/diario-miccional")
def guardar_diario_miccional(
    nhc: str = Form(...),
    nombre: str = Form(""),
    datos_json: str = Form("{}"),
    metricas_json: str = Form("{}"),
    informe: str = Form(""),
    db: Session = Depends(get_db),
):
    """Guarda el diario miccional que la paciente decide enviar a su profesional."""
    nhc = (nhc or "").strip()
    if not nhc:
        return JSONResponse({"ok": False, "error": "Falta el NHC."}, status_code=400)

    for campo in ("datos_json", "metricas_json"):
        try:
            json.loads(locals()[campo] or "{}")
        except ValueError:
            pass

    registro = DiarioMiccional(
        nhc=nhc,
        nombre=(nombre or "").strip(),
        datos_json=datos_json or "{}",
        metricas_json=metricas_json or "{}",
        informe=informe or "",
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return JSONResponse({"ok": True, "id": registro.id})


@router.get("/suelo-pelvico/diario")
def pagina_diario(request: Request):
    """Diario miccional rellenable: la paciente lo completa, se guarda en SU
    navegador (localStorage) y puede imprimirlo o guardarlo en PDF para el médico."""
    return templates.TemplateResponse(
        request,
        "diario_miccional.html",
        {"titulo": "Diario miccional - Para pacientes"},
    )


@router.get("/suelo-pelvico/ejercicios")
def pagina_ejercicios(request: Request):
    """Guía de ejercicios de suelo pélvico con un cronómetro guiado."""
    return templates.TemplateResponse(
        request,
        "ejercicios.html",
        {"titulo": "Ejercicios de suelo pélvico"},
    )


@router.get("/suelo-pelvico/prolapso")
def pagina_prolapso(request: Request):
    """Página de diagnóstico: prolapso de órganos pélvicos."""
    return templates.TemplateResponse(
        request,
        "diag_prolapso.html",
        {"titulo": "Prolapso de órganos pélvicos"},
    )


@router.get("/suelo-pelvico/incontinencia-esfuerzo")
def pagina_incontinencia_esfuerzo(request: Request):
    """Página de diagnóstico: incontinencia urinaria de esfuerzo."""
    return templates.TemplateResponse(
        request,
        "diag_incontinencia_esfuerzo.html",
        {"titulo": "Incontinencia urinaria de esfuerzo"},
    )


@router.get("/suelo-pelvico/incontinencia-urgencia")
def pagina_incontinencia_urgencia(request: Request):
    """Página de diagnóstico: incontinencia urinaria de urgencia."""
    return templates.TemplateResponse(
        request,
        "diag_incontinencia_urgencia.html",
        {"titulo": "Incontinencia urinaria de urgencia"},
    )


@router.get("/suelo-pelvico/incontinencia-mixta")
def pagina_incontinencia_mixta(request: Request):
    """Página de diagnóstico: incontinencia urinaria mixta."""
    return templates.TemplateResponse(
        request,
        "diag_incontinencia_mixta.html",
        {"titulo": "Incontinencia urinaria mixta"},
    )


@router.get("/suelo-pelvico/incontinencia-fecal")
def pagina_incontinencia_fecal(request: Request):
    """Página de diagnóstico: incontinencia fecal o a gases."""
    return templates.TemplateResponse(
        request,
        "diag_incontinencia_fecal.html",
        {"titulo": "Incontinencia fecal o a gases"},
    )


@router.get("/suelo-pelvico/urodinamia")
def pagina_urodinamia(request: Request):
    """Página informativa: preparación para la urodinamia."""
    return templates.TemplateResponse(
        request,
        "diag_urodinamia.html",
        {"titulo": "Preparación para urodinamia"},
    )
