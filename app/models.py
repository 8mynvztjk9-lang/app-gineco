"""
models.py
---------
Define las "tablas" de la base de datos como clases de Python.
Cada clase = una tabla. Cada atributo = una columna.

Tablas:
  - Profesional               -> los usuarios que pueden iniciar sesión.
  - CuestionarioPOP           -> cuestionario POP que rellena la paciente.
  - CuestionarioIncontinencia -> cuestionario CACV + ICIQ-IU-SF.
  - DiarioMiccional           -> diario que la paciente envía a su profesional.

NHC = Número de Historia Clínica. Aquí usamos SIEMPRE datos ficticios.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database import Base


class Profesional(Base):
    """Un profesional sanitario que puede acceder a la zona privada."""
    __tablename__ = "profesionales"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    # Guardamos SOLO la contraseña cifrada, nunca la contraseña en claro.
    hashed_password = Column(String, nullable=False)
    nombre = Column(String, nullable=False)


class CuestionarioPOP(Base):
    """Un cuestionario POP (PFDI-20 + PFIQ-7 + PISQ-IR) que rellena la PACIENTE
    desde la zona pública. Se guarda asociado a un NHC para que el profesional
    pueda consultarlo después buscando por ese número.

    Solo datos ficticios de prueba.
    """
    __tablename__ = "cuestionarios_pop"

    id = Column(Integer, primary_key=True, index=True)
    nhc = Column(String, index=True, nullable=False)          # Nº Historia Clínica (ficticio)
    nombre = Column(String, nullable=False, default="")
    apellidos = Column(String, nullable=False, default="")
    # Fecha que indica la paciente en el cuestionario (texto del formulario).
    fecha = Column(String, nullable=False, default="")
    # Momento exacto en que se guardó (lo pone el servidor).
    creado_en = Column(DateTime, default=datetime.utcnow)

    # Informe completo ya redactado (texto listo para la historia clínica).
    informe = Column(Text, nullable=False, default="")
    # Respuestas en bruto (JSON) por si se quieren reprocesar.
    respuestas_json = Column(Text, nullable=False, default="{}")

    # Puntuaciones totales (0-300) para mostrarlas de un vistazo en la lista.
    pfdi_total = Column(String, nullable=True)
    pfiq_total = Column(String, nullable=True)


class CuestionarioIncontinencia(Base):
    """Cuestionario combinado de incontinencia / vejiga que rellena la PACIENTE:
      · CACV  — Cuestionario de Autoevaluación del Control de la Vejiga (cribado de
                vejiga hiperactiva): puntuación de síntomas (0-12) y de molestia (0-12).
      · ICIQ-IU-SF — gravedad e impacto de la incontinencia urinaria (0-21) + tipo.

    Solo datos ficticios de prueba.
    """
    __tablename__ = "cuestionarios_incontinencia"

    id = Column(Integer, primary_key=True, index=True)
    nhc = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False, default="")
    apellidos = Column(String, nullable=False, default="")
    fecha = Column(String, nullable=False, default="")
    creado_en = Column(DateTime, default=datetime.utcnow)

    informe = Column(Text, nullable=False, default="")
    respuestas_json = Column(Text, nullable=False, default="{}")

    # Puntuaciones para mostrarlas de un vistazo.
    cacv_sintomas = Column(String, nullable=True)   # 0-12
    cacv_molestia = Column(String, nullable=True)   # 0-12
    iciq_total = Column(String, nullable=True)       # 0-21
    iciq_tipo = Column(String, nullable=True)        # esfuerzo / urgencia / mixta…


class DiarioMiccional(Base):
    """Diario miccional que la PACIENTE decide ENVIAR a su profesional.
    Guarda los datos en bruto, las métricas calculadas y una interpretación
    orientativa basada en valores de referencia de la literatura (ICS, etc.).

    Solo datos ficticios de prueba.
    """
    __tablename__ = "diarios_miccionales"

    id = Column(Integer, primary_key=True, index=True)
    nhc = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False, default="")
    creado_en = Column(DateTime, default=datetime.utcnow)

    datos_json = Column(Text, nullable=False, default="{}")     # campos en bruto
    metricas_json = Column(Text, nullable=False, default="{}")  # métricas calculadas
    informe = Column(Text, nullable=False, default="")          # interpretación redactada


class ValoracionPOPQ(Base):
    """Valoración POP-Q (cuantificación del prolapso de órganos pélvicos) que
    registra el PROFESIONAL. Guarda las 9 medidas, el estadio calculado y el
    momento de la valoración, para seguir la evolución del prolapso en el tiempo
    (primera valoración → tras ejercicios/conservador → tras cirugía).

    Solo datos ficticios de prueba.
    """
    __tablename__ = "valoraciones_popq"

    id = Column(Integer, primary_key=True, index=True)
    nhc = Column(String, index=True, nullable=False)
    nombre = Column(String, nullable=False, default="")
    fecha = Column(String, nullable=False, default="")
    creado_en = Column(DateTime, default=datetime.utcnow)

    # Momento clínico: Primera valoración / Tras ejercicios (conservador) / Tras cirugía / Seguimiento
    momento = Column(String, nullable=False, default="Primera valoración")
    con_utero = Column(String, nullable=True)   # "si" / "no"

    # Las 9 medidas POP-Q (en cm; negativo = por encima del himen, positivo = por debajo).
    aa = Column(String, nullable=True)
    ba = Column(String, nullable=True)
    c = Column(String, nullable=True)
    d = Column(String, nullable=True)
    ap = Column(String, nullable=True)
    bp = Column(String, nullable=True)
    gh = Column(String, nullable=True)
    pb = Column(String, nullable=True)
    tvl = Column(String, nullable=True)

    estadio = Column(String, nullable=True)     # 0, I, II, III, IV
    borde = Column(String, nullable=True)        # punto más distal (cm)
    informe = Column(Text, nullable=False, default="")
