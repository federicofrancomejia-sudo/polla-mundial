# -*- coding: utf-8 -*-
"""Polla Mundial 2026 - App web (Streamlit). Mobile-friendly."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import db
from fixtures import PARTIDOS, TZ

# ===== Configuración =====
PARTICIPANTES = [
    "Jaime Pinzon", "Angela Duran", "Federico Franco", "Yeison Garzon", "Martin Higuera",
    "Rodrigo Garcia", "Carlos Vargas", "Pedro Artunduaga", "Andres Toro", "Alejandro Garzon",
    "Armando Pineda", "Jhon Gomez", "Flavio Ortega", "Jairo Zambrano", "Felipe Carmona",
    "Omar Duarte", "Jesus Muñoz", "Custodio Roa", "Fernando Gomez", "Veronica Capera",
    "Oscar Muñoz", "Andres Torres", "Alejandra Rincon", "Wbeymar Torres", "Fredy Mogollon",
]
BOLSA_UNIT = 50000

st.set_page_config(page_title="Polla Mundial 2026", page_icon="🏆", layout="centered")
db.init_db(PARTICIPANTES)


def now_co():
    return datetime.now(TZ)


def puntos(pred, real):
    if not pred or not real:
        return None
    pgl, pgv = pred
    rgl, rgv = real
    if None in (pgl, pgv, rgl, rgv):
        return None
    if pgl == rgl and pgv == rgv:
        return 3
    sg = lambda x: (x > 0) - (x < 0)
    if sg(pgl - pgv) == sg(rgl - rgv):
        return 1 if pgl == pgv else 2
    return 0


def proximo_partido(now):
    fut = [p for p in PARTIDOS if p["kickoff"] > now]
    return min(fut, key=lambda p: p["kickoff"]) if fut else None


# ===== Login =====
def login_view():
    st.title("🏆 Polla Mundial 2026")
    st.caption("Ingresa para apostar y ver el ranking.")
    nombre = st.selectbox("Tu nombre", db.lista_participantes())
    pin = st.text_input("Tu PIN (créalo en tu primer ingreso)", type="password")
    if st.button("Entrar", type="primary", width="stretch"):
        ok, msg = db.login(nombre, pin)
        if ok:
            st.session_state.user = nombre
            st.rerun()
        else:
            st.error(msg)
    st.info("💡 La primera vez que entras, el PIN que escribas queda como tu clave.")


# ===== Contador (se actualiza solo cada segundo) =====
@st.fragment(run_every=1)
def contador():
    now = now_co()
    prox = proximo_partido(now)
    if prox is None:
        st.success("✅ Fase de grupos finalizada")
        return
    seg = int((prox["kickoff"] - now).total_seconds())
    d, r = divmod(seg, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    falta = (f"{d}d " if d else "") + f"{h:02d}:{m:02d}:{s:02d}"
    st.markdown(
        f"<div style='text-align:center;background:#C00000;color:#fff;padding:10px;border-radius:10px'>"
        f"<div style='font-size:13px'>⏱ PRÓXIMO PARTIDO — cierra en</div>"
        f"<div style='font-size:30px;font-weight:bold'>{falta}</div>"
        f"<div style='font-size:15px'>{prox['local']} vs {prox['visitante']}"
        f" · {prox['dia_txt']} {prox['hora_txt']}</div></div>",
        unsafe_allow_html=True)


# ===== Apuestas =====
def apuestas_view(user):
    now = now_co()
    mis = db.get_apuestas(user)
    res = db.get_resultados()

    contador()
    st.write("")

    # Pendientes de HOY
    hoy = now.date()
    pend_hoy = [p for p in PARTIDOS
                if p["kickoff"].date() == hoy and p["kickoff"] > now and p["num"] not in mis]
    if pend_hoy:
        nombres = ", ".join(f"{p['local']} vs {p['visitante']}" for p in pend_hoy)
        st.warning(f"⚠️ Te faltan por apostar HOY: {nombres}")

    st.subheader("⚽ Mis apuestas")
    st.caption("Escribe los goles. Cada partido se cierra a su hora de inicio (hora Colombia).")

    dias = sorted({p["kickoff"].date() for p in PARTIDOS})
    with st.form("form_apuestas"):
        for dia in dias:
            ps = [p for p in PARTIDOS if p["kickoff"].date() == dia]
            etiqueta = ps[0]["dia_txt"]
            abierto_hoy = (dia == hoy)
            with st.expander(f"📅 {etiqueta}  ({len(ps)} partidos)", expanded=abierto_hoy):
                for p in ps:
                    n = p["num"]
                    cerrado = p["kickoff"] <= now
                    pred = mis.get(n)
                    st.markdown(f"**{p['local']} vs {p['visitante']}**  ·  {p['hora_txt']}")
                    if cerrado:
                        ap = f"{pred[0]}-{pred[1]}" if pred else "sin apuesta"
                        rr = res.get(n)
                        extra = ""
                        if rr:
                            pt = puntos(pred, rr)
                            extra = f"  ·  resultado {rr[0]}-{rr[1]}  ·  **{pt if pt is not None else 0} pts**"
                        st.caption(f"🔒 CERRADO — tu apuesta: {ap}{extra}")
                    else:
                        c1, c2 = st.columns(2)
                        c1.number_input(p["local"], min_value=0, max_value=20, step=1,
                                        value=(pred[0] if pred else None),
                                        key=f"gl_{n}", placeholder="-")
                        c2.number_input(p["visitante"], min_value=0, max_value=20, step=1,
                                        value=(pred[1] if pred else None),
                                        key=f"gv_{n}", placeholder="-")
                    st.divider()
        guardar = st.form_submit_button("💾 Guardar mis apuestas", type="primary",
                                        width="stretch")

    if guardar:
        now2 = now_co()
        n_ok = 0
        for p in PARTIDOS:
            n = p["num"]
            if p["kickoff"] <= now2:
                continue
            gl = st.session_state.get(f"gl_{n}")
            gv = st.session_state.get(f"gv_{n}")
            if gl is not None and gv is not None:
                db.set_apuesta(user, n, int(gl), int(gv))
                n_ok += 1
        st.success(f"✅ Guardado. {n_ok} partidos con apuesta.")
        st.rerun()


# ===== Ranking =====
def calcular_ranking():
    todas = db.todas_apuestas()
    res = db.get_resultados()
    filas = []
    for nombre in db.lista_participantes():
        ap = todas.get(nombre, {})
        tot = ex = apu = 0
        for n, pred in ap.items():
            if pred[0] is not None and pred[1] is not None:
                apu += 1
            pt = puntos(pred, res.get(n))
            if pt is not None:
                tot += pt
                ex += (pt == 3)
        filas.append({"Participante": nombre, "Puntos": tot, "Exactos": ex, "Apostados": apu})
    filas.sort(key=lambda f: (-f["Puntos"], -f["Exactos"], f["Participante"]))
    for i, f in enumerate(filas, 1):
        f["Puesto"] = i
    return filas


def ranking_view(user):
    st.subheader("📊 Ranking general")
    filas = calcular_ranking()
    res = db.get_resultados()
    st.caption(f"Partidos con resultado cargado: {len(res)}")
    df = pd.DataFrame(filas)[["Puesto", "Participante", "Puntos", "Exactos", "Apostados"]]
    yo = df[df["Participante"] == user]
    if not yo.empty:
        r = yo.iloc[0]
        st.metric(f"Tu posición ({user})", f"#{int(r['Puesto'])}", f"{int(r['Puntos'])} pts")
    st.dataframe(df, hide_index=True, width="stretch")


# ===== Admin =====
def admin_view():
    st.subheader("🛠️ Panel de administrador")
    res = db.get_resultados()
    tab1, tab2 = st.tabs(["Cargar resultados", "Control"])

    with tab1:
        st.caption("Escribe los goles reales y guarda. El ranking se actualiza solo.")
        dias = sorted({p["kickoff"].date() for p in PARTIDOS})
        with st.form("form_res"):
            for dia in dias:
                ps = [p for p in PARTIDOS if p["kickoff"].date() == dia]
                with st.expander(f"📅 {ps[0]['dia_txt']}", expanded=(dia == now_co().date())):
                    for p in ps:
                        n = p["num"]
                        rr = res.get(n)
                        st.markdown(f"**{p['local']} vs {p['visitante']}**")
                        c1, c2 = st.columns(2)
                        c1.number_input(p["local"], min_value=0, max_value=20, step=1,
                                        value=(rr[0] if rr else None), key=f"rgl_{n}",
                                        placeholder="-")
                        c2.number_input(p["visitante"], min_value=0, max_value=20, step=1,
                                        value=(rr[1] if rr else None), key=f"rgv_{n}",
                                        placeholder="-")
            g = st.form_submit_button("💾 Guardar resultados", type="primary",
                                      use_container_width=True)
        if g:
            for p in PARTIDOS:
                n = p["num"]
                gl = st.session_state.get(f"rgl_{n}")
                gv = st.session_state.get(f"rgv_{n}")
                db.set_resultado(n, None if gl is None else int(gl),
                                 None if gv is None else int(gv))
            st.success("✅ Resultados guardados.")
            st.rerun()

    with tab2:
        pins = db.con_pin()
        todas = db.todas_apuestas()
        filas = []
        for nombre in db.lista_participantes():
            filas.append({"Participante": nombre,
                          "¿PIN?": "Sí" if pins.get(nombre) else "No",
                          "Apostados": len(todas.get(nombre, {}))})
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        st.caption("Resetear PIN de alguien que lo olvidó:")
        quien = st.selectbox("Participante", db.lista_participantes(), key="reset_sel")
        if st.button("Resetear su PIN"):
            db.reset_pin(quien)
            st.success(f"PIN de {quien} reseteado. Creará uno nuevo en su próximo ingreso.")


# ===== Main =====
def main():
    if "user" not in st.session_state:
        st.session_state.user = None
    if not st.session_state.user:
        login_view()
        return

    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"👤 **{user}**")
        bolsa = BOLSA_UNIT * len(PARTICIPANTES)
        st.caption(f"Bolsa: ${bolsa:,.0f}".replace(",", "."))
        st.caption(f"🥇 ${bolsa*.5:,.0f} · 🥈 ${bolsa*.3:,.0f} · 🥉 ${bolsa*.2:,.0f}".replace(",", "."))
        if st.button("Cerrar sesión"):
            st.session_state.user = None
            st.rerun()

    tabs = ["⚽ Apuestas", "📊 Ranking"]
    if db.es_admin(user):
        tabs.append("🛠️ Admin")
    sel = st.tabs(tabs)
    with sel[0]:
        apuestas_view(user)
    with sel[1]:
        ranking_view(user)
    if db.es_admin(user):
        with sel[2]:
            admin_view()


main()
