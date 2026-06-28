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

if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
else:
    # connect_timeout evita que la app/los scripts se queden colgados si el
    # pooler no responde (en vez de esperar indefinidamente).
    _connect_args = {"connect_timeout": 10}
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
        # Partidos de ELIMINATORIA (num >= 73). Los de fase de grupos (1-72)
        # viven estaticos en fixtures.py; estos se llenan solos desde la API
        # (fetch_partidos.py). api_id es el id estable del partido en la API.
        cx.execute(text("""CREATE TABLE IF NOT EXISTS partidos(
            num INTEGER PRIMARY KEY, api_id TEXT UNIQUE, etapa TEXT,
            local TEXT, visitante TEXT, ciudad TEXT, kickoff TEXT)"""))
        for n in nombres:
            cx.execute(text("INSERT INTO participantes(nombre) VALUES(:n) "
                            "ON CONFLICT(nombre) DO NOTHING"), {"n": n})


def lista_participantes():
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT nombre FROM participantes ORDER BY nombre")).all()
    return [r[0] for r in rows]


def es_admin(nombre):
    return nombre in ADMINS


def agregar_participante(nombre):
    """Agrega una persona a la polla. Devuelve (ok, mensaje)."""
    nombre = str(nombre).strip()
    if not nombre:
        return False, "Escribe un nombre."
    with engine.begin() as cx:
        existe = cx.execute(text("SELECT 1 FROM participantes WHERE nombre=:n"),
                            {"n": nombre}).first()
        if existe:
            return False, f"'{nombre}' ya está en la lista."
        cx.execute(text("INSERT INTO participantes(nombre) VALUES(:n)"), {"n": nombre})
    return True, f"'{nombre}' agregado. Creará su PIN en su primer ingreso."


def eliminar_participante(nombre):
    """Quita a una persona y todas sus apuestas. Devuelve (ok, mensaje)."""
    nombre = str(nombre).strip()
    if nombre in ADMINS:
        return False, "No puedes quitar a un administrador."
    with engine.begin() as cx:
        existe = cx.execute(text("SELECT 1 FROM participantes WHERE nombre=:n"),
                            {"n": nombre}).first()
        if not existe:
            return False, f"'{nombre}' no está en la lista."
        cx.execute(text("DELETE FROM apuestas WHERE nombre=:n"), {"n": nombre})
        cx.execute(text("DELETE FROM participantes WHERE nombre=:n"), {"n": nombre})
    return True, f"'{nombre}' eliminado junto con sus apuestas."


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


# ===== Partidos de eliminatoria (num >= 73, llenados desde la API) =====
def partidos_eliminatoria():
    """Filas crudas de los partidos de eliminatoria, ordenadas por num.
    Devuelve [{num, etapa, local, visitante, ciudad, kickoff}]. fixtures.py les
    da formato (kickoff -> datetime, dia_txt, hora_txt) y los une a los de grupos."""
    with engine.connect() as cx:
        rows = cx.execute(text("SELECT num, etapa, local, visitante, ciudad, kickoff "
                               "FROM partidos WHERE num >= 73 ORDER BY num")).all()
    return [{"num": r[0], "etapa": r[1], "local": r[2], "visitante": r[3],
             "ciudad": r[4], "kickoff": r[5]} for r in rows]


def num_de_api(api_id):
    """Devuelve el num asignado a un api_id, o None si es nuevo."""
    with engine.connect() as cx:
        row = cx.execute(text("SELECT num FROM partidos WHERE api_id=:a"),
                         {"a": str(api_id)}).first()
    return row[0] if row else None


def siguiente_num_partido():
    """Proximo num libre para un partido de eliminatoria (empieza en 73)."""
    with engine.connect() as cx:
        mx = cx.execute(text("SELECT MAX(num) FROM partidos")).scalar()
    return max(72, mx or 72) + 1


def upsert_partido(num, api_id, etapa, local, visitante, ciudad, kickoff):
    """Crea/actualiza un partido de eliminatoria (por num)."""
    with engine.begin() as cx:
        cx.execute(text("""INSERT INTO partidos(num, api_id, etapa, local, visitante, ciudad, kickoff)
            VALUES(:num,:api,:et,:loc,:vis,:ciu,:ko)
            ON CONFLICT(num) DO UPDATE SET
              api_id=:api, etapa=:et, local=:loc, visitante=:vis, ciudad=:ciu, kickoff=:ko"""),
            {"num": num, "api": str(api_id), "et": etapa, "loc": local,
             "vis": visitante, "ciu": ciudad, "ko": kickoff})
