"""
routers/private.py
------------------
La SECCIÓN PRIVADA, solo para profesionales.
Protegida con login (usuario + contraseña).

Cómo funciona el login aquí:
  - Cuando alguien inicia sesión correctamente, guardamos su id en la
    "sesión" (una cookie firmada en el navegador).
  - En cada página privada comprobamos que esa sesión exista.
  - Al cerrar sesión, borramos ese dato.
"""

import json

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Profesional,
    CuestionarioPOP,
    CuestionarioIncontinencia,
    DiarioMiccional,
    ValoracionPOPQ,
)
from app.security import verify_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Misma versión de CSS para las plantillas privadas (ver public.py).
from app.routers.public import css_v  # noqa: E402
templates.env.globals["css_v"] = css_v


def get_usuario_actual(request: Request, db: Session) -> Profesional | None:
    """Devuelve el profesional que ha iniciado sesión, o None si no hay nadie."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.query(Profesional).filter(Profesional.id == user_id).first()


# ----------------------- LOGIN -----------------------

@router.get("/login")
def mostrar_login(request: Request):
    """Muestra el formulario de inicio de sesión."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"titulo": "Acceso profesionales", "error": None},
    )


@router.post("/login")
def procesar_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Recibe usuario y contraseña, los comprueba y crea la sesión."""
    profesional = db.query(Profesional).filter(Profesional.username == username).first()

    # Si no existe el usuario o la contraseña no coincide, mostramos error.
    if profesional is None or not verify_password(password, profesional.hashed_password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "titulo": "Acceso profesionales",
                "error": "Usuario o contraseña incorrectos.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Login correcto: guardamos el id en la sesión y vamos al panel.
    request.session["user_id"] = profesional.id
    return RedirectResponse(url="/panel", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
def logout(request: Request):
    """Cierra la sesión y vuelve a la página pública."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# ----------------------- RESUMEN INTEGRADO -----------------------

def _num(x):
    """Convierte a float de forma segura; None si no se puede."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def construir_resumen_integrado(nhc, pops, incos, diarios):
    """Sintetiza en un único texto, para la historia clínica, los resultados de
    TODOS los cuestionarios y el diario de una paciente (lo más reciente de cada
    uno), con una interpretación clínica orientativa.

    Devuelve None si no hay ningún dato para ese NHC.
    """
    if not pops and not incos and not diarios:
        return None

    # Identidad: la tomamos del registro más reciente disponible.
    nombre = ""
    for grupo in (incos, pops):
        if grupo:
            nombre = (grupo[0].nombre + " " + getattr(grupo[0], "apellidos", "")).strip()
            break
    if not nombre and diarios:
        nombre = diarios[0].nombre

    L = [
        "RESUMEN INTEGRADO PARA HISTORIA CLÍNICA",
        f"NHC: {nhc}    Paciente: {nombre or 'No consta'}",
        "",
    ]
    impresion = []  # frases para la impresión clínica global

    # --- POP (PFDI-20 / PFIQ-7) ---
    if pops:
        p = pops[0]
        L.append("• Prolapso / suelo pélvico (PFDI-20 · PFIQ-7):")
        L.append(f"    PFDI-20 {p.pfdi_total or '—'}/300 · PFIQ-7 {p.pfiq_total or '—'}/300")
        pfdi = _num(p.pfdi_total)
        if pfdi is not None:
            if pfdi > 100:
                impresion.append("sintomatología de suelo pélvico moderada-alta (PFDI-20)")
            elif pfdi > 50:
                impresion.append("sintomatología de suelo pélvico leve (PFDI-20)")
    else:
        L.append("• Prolapso / suelo pélvico: sin cuestionario POP registrado.")

    # --- Incontinencia (CACV + ICIQ) ---
    if incos:
        c = incos[0]
        L.append("• Vejiga e incontinencia (CACV · ICIQ-IU-SF):")
        L.append(
            f"    CACV síntomas {c.cacv_sintomas or '—'}/12 · molestia {c.cacv_molestia or '—'}/12"
            f" · ICIQ {c.iciq_total or '—'}/21 · tipo: {c.iciq_tipo or '—'}"
        )
        iciq = _num(c.iciq_total)
        if iciq is not None and iciq > 0:
            grav = (
                "muy grave" if iciq > 18 else
                "grave" if iciq > 12 else
                "moderada" if iciq > 5 else "leve"
            )
            tipo = (c.iciq_tipo or "").split(" (")[0]
            impresion.append(f"incontinencia urinaria {grav}{(' ' + tipo) if tipo else ''} (ICIQ {int(iciq)}/21)")
        sint = _num(c.cacv_sintomas)
        if sint is not None and sint >= 4:
            impresion.append(f"cribado positivo de vejiga hiperactiva (CACV {int(sint)}/12)")
    else:
        L.append("• Vejiga e incontinencia: sin cuestionario registrado.")

    # --- Diario miccional ---
    if diarios:
        d = diarios[0]
        L.append("• Diario miccional: registrado (" + d.creado_en.strftime("%d/%m/%Y") + ").")
        try:
            m = json.loads(d.metricas_json or "{}")
            if m:
                L.append(
                    f"    {m.get('micciones_dia','—')} micciones/día"
                    f" · nicturia {m.get('nicturia','—')}"
                    f" · capacidad funcional {m.get('capacidad_funcional','—')} ml"
                    f" · escapes/día {m.get('escapes_dia','—')}"
                )
                if isinstance(m.get("nicturia"), (int, float)) and m["nicturia"] >= 2:
                    impresion.append("nicturia significativa en el diario")
                if isinstance(m.get("capacidad_funcional"), (int, float)) and 0 < m["capacidad_funcional"] < 250:
                    impresion.append("capacidad vesical funcional reducida en el diario")
        except ValueError:
            pass
    else:
        L.append("• Diario miccional: no enviado.")

    L.append("")
    L.append("IMPRESIÓN CLÍNICA ORIENTATIVA:")
    if impresion:
        L.append("- " + "; ".join(impresion) + ".")
        L.append("- Correlacionar los cuestionarios con el diario miccional y la exploración (POP-Q, test de esfuerzo).")
    else:
        L.append("- Sin hallazgos relevantes en los instrumentos disponibles.")
    return "\n".join(L)


def _fecha_corta(reg):
    """Etiqueta de fecha breve (dd/mm/aaaa) para un registro: la fecha indicada
    por la paciente o, si no hay, la de recepción."""
    f = (getattr(reg, "fecha", "") or "").strip()
    if not f:
        return reg.creado_en.strftime("%d/%m/%Y")
    try:  # los <input type="date"> dan formato ISO AAAA-MM-DD
        y, m, d = f.split("-")
        return f"{d}/{m}/{y}"
    except ValueError:
        return f


def construir_evolucion(pops, incos, diarios, popqs=None):
    """Si la paciente ha rellenado un mismo cuestionario MÁS DE UNA VEZ, construye
    una tabla de evolución (valor por fecha) con la tendencia, para ver de un
    vistazo si los síntomas mejoran o empeoran en el tiempo.

    Devuelve una lista de bloques, o None si no hay nada repetido.
    """
    bloques = []

    def tendencia(valores, mejor="bajo"):
        """Compara el valor más antiguo con el más reciente.
        'mejor' indica si lo deseable es un valor bajo o alto.
        Devuelve (texto_con_flecha, clase_de_color)."""
        nums = [v for v in valores if v is not None]
        if len(nums) < 2:
            return ("—", "neutra")
        primero, ultimo = nums[0], nums[-1]
        if ultimo == primero:
            return ("→ estable", "neutra")
        subio = ultimo > primero
        flecha = "↑" if subio else "↓"
        # Mejora si baja (cuando lo bueno es bajo) o si sube (cuando lo bueno es alto)
        mejora = (not subio) if mejor == "bajo" else subio
        return (f"{flecha} {'mejora' if mejora else 'empeora'}", "buena" if mejora else "mala")

    def bloque(registros, indicadores, fecha_fn):
        """registros en orden cronológico (antiguo→reciente)."""
        filas = []
        for etiqueta, getter, mejor in indicadores:
            vals = [getter(r) for r in registros]
            t, clase = tendencia([_num(v) for v in vals], mejor)
            filas.append({
                "etiqueta": etiqueta,
                "puntos": [{"fecha": fecha_fn(r), "valor": (v if v not in (None, "") else "—")}
                           for r, v in zip(registros, vals)],
                "tendencia": t,
                "clase": clase,
            })
        return filas

    # --- POP-Q (cuantificación del prolapso por el profesional) ---
    # Lo primero, porque es lo que el profesional sigue tras ejercicios o cirugía.
    if popqs and len(popqs) >= 2:
        regs = list(reversed(popqs))  # cronológico (antiguo → reciente)
        romano = {"0": "0", "1": "I", "2": "II", "3": "III", "4": "IV"}
        abrev_mom = {
            "Primera valoración": "1ª valoración",
            "Tras ejercicios de suelo pélvico (conservador)": "Tras ejercicios",
            "Tras cirugía": "Tras cirugía",
            "Seguimiento": "Seguimiento",
        }

        def col_label(r):
            mom = (r.momento or "").strip()
            etiqueta = abrev_mom.get(mom, mom or "—")
            f = (r.fecha or "").strip() or _fecha_corta(r)
            return f"{etiqueta} · {f}"

        t_est, c_est = tendencia([_num(r.estadio) for r in regs], "bajo")
        fila_est = {
            "etiqueta": "Estadio POP-Q",
            "puntos": [{"fecha": col_label(r),
                        "valor": romano.get((r.estadio or "").strip(), r.estadio or "—")}
                       for r in regs],
            "tendencia": t_est, "clase": c_est,
        }
        t_b, c_b = tendencia([_num(r.borde) for r in regs], "bajo")
        fila_b = {
            "etiqueta": "Punto más distal (cm)",
            "puntos": [{"fecha": col_label(r),
                        "valor": (r.borde if r.borde not in (None, "") else "—")}
                       for r in regs],
            "tendencia": t_b, "clase": c_b,
        }
        bloques.append({
            "titulo": "Prolapso · POP-Q (evolución del estadio)",
            "filas": [fila_est, fila_b],
        })

    # --- Incontinencia (CACV + ICIQ) ---
    if len(incos) >= 2:
        regs = list(reversed(incos))  # cronológico
        filas = bloque(regs, [
            ("ICIQ-IU-SF (/21)", lambda r: r.iciq_total, "bajo"),
            ("CACV síntomas (/12)", lambda r: r.cacv_sintomas, "bajo"),
            ("CACV molestia (/12)", lambda r: r.cacv_molestia, "bajo"),
        ], _fecha_corta)
        bloques.append({"titulo": "Vejiga e incontinencia (CACV · ICIQ-IU-SF)", "filas": filas})

    # --- POP (PFDI / PFIQ) ---
    if len(pops) >= 2:
        regs = list(reversed(pops))
        filas = bloque(regs, [
            ("PFDI-20 (/300)", lambda r: r.pfdi_total, "bajo"),
            ("PFIQ-7 (/300)", lambda r: r.pfiq_total, "bajo"),
        ], _fecha_corta)
        bloques.append({"titulo": "Prolapso / suelo pélvico (PFDI-20 · PFIQ-7)", "filas": filas})

    # --- Diario miccional ---
    if len(diarios) >= 2:
        regs = list(reversed(diarios))

        def met(r, k):
            try:
                return json.loads(r.metricas_json or "{}").get(k)
            except ValueError:
                return None

        filas = bloque(regs, [
            ("Micciones/día", lambda r: met(r, "micciones_dia"), "bajo"),
            ("Nicturia", lambda r: met(r, "nicturia"), "bajo"),
            ("Escapes/día", lambda r: met(r, "escapes_dia"), "bajo"),
            ("Capacidad funcional (ml)", lambda r: met(r, "capacidad_funcional"), "alto"),
        ], lambda r: r.creado_en.strftime("%d/%m/%Y"))
        bloques.append({"titulo": "Diario miccional", "filas": filas})

    return bloques or None


# ----------------------- PANEL PRIVADO -----------------------

def _filtro_busqueda(consulta, columnas):
    """Filtro flexible: cada PALABRA de la consulta debe aparecer en alguna de
    las columnas indicadas (NHC, nombre…). El orden no importa, así que da igual
    escribir antes el apellido o el nombre, o solo parte de ellos."""
    condiciones = []
    for palabra in consulta.split():
        patron = f"%{palabra}%"
        condiciones.append(or_(*[col.ilike(patron) for col in columnas]))
    return and_(*condiciones)


@router.get("/panel")
def panel(request: Request, nhc: str = "", db: Session = Depends(get_db)):
    """Panel principal del profesional. Al buscar por NHC muestra los
    cuestionarios y el diario miccional que ha rellenado esa paciente."""
    usuario = get_usuario_actual(request, db)
    if usuario is None:
        # Si no ha iniciado sesión, lo mandamos al login.
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Búsqueda flexible por NHC o por nombre/apellidos (el orden no importa):
    # cada palabra debe aparecer en alguno de esos campos.
    nhc = (nhc or "").strip()
    cuestionarios = []
    incontinencias = []
    diarios = []
    valoraciones_popq = []
    resumen_integrado = None
    if nhc:
        cuestionarios = (
            db.query(CuestionarioPOP)
            .filter(_filtro_busqueda(nhc, [
                CuestionarioPOP.nhc, CuestionarioPOP.nombre, CuestionarioPOP.apellidos]))
            .order_by(CuestionarioPOP.creado_en.desc())
            .all()
        )
        incontinencias = (
            db.query(CuestionarioIncontinencia)
            .filter(_filtro_busqueda(nhc, [
                CuestionarioIncontinencia.nhc, CuestionarioIncontinencia.nombre,
                CuestionarioIncontinencia.apellidos]))
            .order_by(CuestionarioIncontinencia.creado_en.desc())
            .all()
        )
        diarios = (
            db.query(DiarioMiccional)
            .filter(_filtro_busqueda(nhc, [DiarioMiccional.nhc, DiarioMiccional.nombre]))
            .order_by(DiarioMiccional.creado_en.desc())
            .all()
        )
        valoraciones_popq = (
            db.query(ValoracionPOPQ)
            .filter(_filtro_busqueda(nhc, [ValoracionPOPQ.nhc, ValoracionPOPQ.nombre]))
            .order_by(ValoracionPOPQ.creado_en.desc())
            .all()
        )
        resumen_integrado = construir_resumen_integrado(
            nhc, cuestionarios, incontinencias, diarios
        )
        evolucion = construir_evolucion(
            cuestionarios, incontinencias, diarios, valoraciones_popq
        )
    else:
        evolucion = None

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "titulo": "Panel del profesional",
            "usuario": usuario,
            "nhc_buscado": nhc,
            "cuestionarios": cuestionarios,
            "incontinencias": incontinencias,
            "diarios": diarios,
            "valoraciones_popq": valoraciones_popq,
            "resumen_integrado": resumen_integrado,
            "evolucion": evolucion,
        },
    )


# ----------------------- CALCULADORA POP-Q -----------------------

@router.get("/panel/popq")
def popq(request: Request, db: Session = Depends(get_db)):
    """Calculadora POP-Q (cuantificación del prolapso) con registro por NHC."""
    usuario = get_usuario_actual(request, db)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request,
        "popq.html",
        {"titulo": "POP-Q · Cuantificación del prolapso"},
    )


@router.post("/panel/popq")
def guardar_popq(
    request: Request,
    nhc: str = Form(...),
    nombre: str = Form(""),
    fecha: str = Form(""),
    momento: str = Form("Primera valoración"),
    con_utero: str = Form(""),
    aa: str = Form(None), ba: str = Form(None), c: str = Form(None),
    d: str = Form(None), ap: str = Form(None), bp: str = Form(None),
    gh: str = Form(None), pb: str = Form(None), tvl: str = Form(None),
    estadio: str = Form(None), borde: str = Form(None),
    informe: str = Form(""),
    db: Session = Depends(get_db),
):
    """Guarda una valoración POP-Q asociada a un NHC."""
    usuario = get_usuario_actual(request, db)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    from fastapi.responses import JSONResponse
    nhc = (nhc or "").strip()
    if not nhc:
        return JSONResponse({"ok": False, "error": "Falta el NHC."}, status_code=400)

    registro = ValoracionPOPQ(
        nhc=nhc, nombre=(nombre or "").strip(), fecha=(fecha or "").strip(),
        momento=(momento or "Primera valoración"), con_utero=(con_utero or None),
        aa=aa, ba=ba, c=c, d=d, ap=ap, bp=bp, gh=gh, pb=pb, tvl=tvl,
        estadio=(estadio or None), borde=(borde or None), informe=informe or "",
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return JSONResponse({"ok": True, "id": registro.id})


# ----------------------- ALGORITMO DE INCONTINENCIA URINARIA -----------------------

@router.get("/panel/algoritmo-iu")
def algoritmo_iu(request: Request, db: Session = Depends(get_db)):
    """Algoritmo de manejo inicial de la incontinencia urinaria (esquema ICS),
    como ayuda diagnóstica en consulta de primaria o ginecología general."""
    usuario = get_usuario_actual(request, db)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request,
        "algoritmo_iu.html",
        {"titulo": "Algoritmo de incontinencia urinaria"},
    )


