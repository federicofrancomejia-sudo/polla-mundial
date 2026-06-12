# -*- coding: utf-8 -*-
"""Capa de datos. Usa SQLite local por defecto; en la nube se conecta a Postgres
(Supabase) vía la variable DATABASE_URL (o st.secrets)."""
import hashlib
import os

from sqlalchemy import create_engine, text


def _cfg(key, default):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


DATABASE_URL = _cfg("DATABASE_URL", "sqlite:///polla.db")
SALT = _cfg("PIN_SALT", "polla-mundial-2026")
ADMINS = [a.strip() for a in str(_cfg("ADMINS", "Federico Franco")).split(";") if a.strip()]

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)


def hash_pin(pin):
    return hashlib.sha256((SALT + str(pin)).encode("utf-8")).hexdigest()


def init_db(nombres):
    with engine.begin() as cx:
        cx.execute(text("""CREATE TABLE IF NOT EXISTS participantes(
            nombre TEXT PRIMARY KEY, pin TEXT)"""))
        cx.execute(text("""CREATE TABLE IF NOT EXISTS apuestas(
            nombre TEXT, partido INTEGER, gl INTEGER, gv INTEGER,
            PRIMARY KEY(nombre, partido))"""))
        cx.execute(text("""CREATE TABLE IF NOT EXISTS resultados(
            partido INTEGER PRIMARY KEY, gl INTEGER, gv INTEGER)"""))
        for n in nombres:
            cx.execute(text("INSERT INTO participantes(nombre) VALUES(:n) "
                            "ON CONFLICT(nombre) DO NOTHING"), {"n": n})


def lista_participantes():
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT nombre FROM participantes ORDER BY nombre")).all()
    return [r[0] for r in rows]


def es_admin(nombre):
    return nombre in ADMINS


def login(nombre, pin):
    """Primer ingreso fija el PIN; luego lo valida. Devuelve (ok, mensaje)."""
    pin = str(pin).strip()
    if not pin:
        return False, "Escribe tu PIN."
    with engine.begin() as cx:
        row = cx.execute(text("SELECT pin FROM participantes WHERE nombre=:n"),
                         {"n": nombre}).first()
        if row is None:
            return False, "Ese nombre no está en la lista. Avísale al organizador."
        if row[0] in (None, ""):
            cx.execute(text("UPDATE participantes SET pin=:p WHERE nombre=:n"),
                       {"p": hash_pin(pin), "n": nombre})
            return True, "PIN creado. ¡Bienvenido!"
        if row[0] == hash_pin(pin):
            return True, "ok"
        return False, "PIN incorrecto."


def reset_pin(nombre):
    with engine.begin() as cx:
        cx.execute(text("UPDATE participantes SET pin=NULL WHERE nombre=:n"), {"n": nombre})


def get_apuestas(nombre):
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT partido, gl, gv FROM apuestas WHERE nombre=:n"),
                          {"n": nombre}).all()
    return {r[0]: (r[1], r[2]) for r in rows}


def set_apuesta(nombre, partido, gl, gv):
    with engine.begin() as cx:
        cx.execute(text("""INSERT INTO apuestas(nombre, partido, gl, gv)
            VALUES(:n,:p,:gl,:gv)
            ON CONFLICT(nombre, partido) DO UPDATE SET gl=:gl, gv=:gv"""),
            {"n": nombre, "p": partido, "gl": gl, "gv": gv})


def get_resultados():
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT partido, gl, gv FROM resultados")).all()
    return {r[0]: (r[1], r[2]) for r in rows}


def set_resultado(partido, gl, gv):
    with engine.begin() as cx:
        if gl is None or gv is None:
            cx.execute(text("DELETE FROM resultados WHERE partido=:p"), {"p": partido})
        else:
            cx.execute(text("""INSERT INTO resultados(partido, gl, gv)
                VALUES(:p,:gl,:gv)
                ON CONFLICT(partido) DO UPDATE SET gl=:gl, gv=:gv"""),
                {"p": partido, "gl": gl, "gv": gv})


def todas_apuestas():
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT nombre, partido, gl, gv FROM apuestas")).all()
    d = {}
    for nombre, p, gl, gv in rows:
        d.setdefault(nombre, {})[p] = (gl, gv)
    return d


def con_pin():
    """Participantes que ya crearon PIN (para control)."""
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT nombre, CASE WHEN pin IS NULL THEN 0 ELSE 1 END "
                               "FROM participantes")).all()
    return {r[0]: bool(r[1]) for r in rows}
