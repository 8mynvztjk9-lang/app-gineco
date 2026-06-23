"""
security.py
-----------
Funciones para manejar contraseñas de forma segura.

REGLA DE ORO: nunca se guarda la contraseña tal cual en la base de datos.
Se guarda un "hash" (una huella cifrada). Al iniciar sesión, ciframos lo que
escribe el usuario y lo comparamos con la huella guardada.

Usamos hashlib.pbkdf2_hmac, que viene incluido en Python (no hace falta
instalar nada extra) y es un método seguro y estándar.
"""

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """
    Convierte una contraseña en una huella cifrada.
    Genera un 'salt' (texto aleatorio) distinto cada vez para que dos
    contraseñas iguales no produzcan la misma huella.
    Devuelve un texto con el formato:  salt$hash
    """
    salt = os.urandom(16)  # 16 bytes aleatorios
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex() + "$" + hashed.hex()


def verify_password(password: str, stored: str) -> bool:
    """
    Comprueba si una contraseña coincide con la huella guardada.
    Devuelve True si coincide, False si no.
    """
    try:
        salt_hex, hash_hex = stored.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    # hmac.compare_digest evita comparaciones inseguras (ataques de tiempo).
    return hmac.compare_digest(hashed.hex(), hash_hex)
