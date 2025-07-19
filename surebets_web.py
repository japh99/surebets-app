import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

API_KEY = "0901e36296eb76fd7b645f6676cd9f31"
SPORTS = [
    ("soccer", "⚽ Fútbol"),
    ("basketball", "🏀 Baloncesto"),
    ("tennis", "🎾 Tenis"),
    ("baseball_mlb", "⚾ Béisbol")
]
REGION = 'us,eu,uk'
MARKETS = ['h2h', 'spreads', 'totals']

def calcular_surebet(cuotas):
    inv = [1/q for q in cuotas if q > 0]
    if len(inv) >= 2 and sum(inv) < 1:
        return True, round((1 - sum(inv)) * 100, 2)
    return False, 0

def determinar_estado(commence):
    try:
        inicio = datetime.fromisoformat(commence.replace("Z", "+00:00"))
        ahora = datetime.now(timezone.utc)
        delta = (ahora - inicio).total_seconds() / 60
        if -2880 <= delta < -1:
            return "Pre-Partido"
        elif 0 <= delta <= 120:
            return "En Vivo"
        else:
            return "Finalizado"
    except:
        return "Desconocido"

def obtener_eventos(sport_key):
    surebets = []
    for market in MARKETS:
        r = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",
            params={"apiKey": API_KEY, "regions": REGION, "markets": market, "oddsFormat": "decimal"},
            timeout=10
        )
        if r.status_code != 200:
            st.error(f"Error {r.status_code} en {sport_key}/{market}: {r.text}")
            continue

        data = r.json()
        for e in data:
            estado = determinar_estado(e.get("commence_time", ""))
            if estado == "Finalizado" or not e.get("bookmakers"):
                continue

            for bm in e["bookmakers"]:
                for m in bm.get("markets", []):
                    if m.get("key") != market:
                        continue
                    outcomes = m.get("outcomes", [])
                    if len(outcomes) < 2:
                        continue

                    mejores = {}
                    for o in outcomes:
                        nombre = o["name"]
                        precio = o["price"]
                        prev = mejores.get(nombre, {"price": 0})
                        if precio > prev["price"]:
                            mejores[nombre] = {"price": precio, "bookmaker": bm["title"]}

                    if len(mejores) < 2:
                        continue

                    cuotas = [v["price"] for v in mejores.values()]
                    names = list(mejores.keys())
                    bkrs = [v["bookmaker"] for v in mejores.values()]
                    es, roi = calcular_surebet(cuotas)

                    if es:
                        registro = {
                            "Evento": f"{e.get('home_team')} vs {e.get('away_team')}",
                            "Estado": estado,
                            "Tipo de Apuesta": market.upper(),
                            "Selección 1": names[0],
                            "Cuota 1": cuotas[0],
                            "Casa 1": bkrs[0],
                            "Selección 2": names[1],
                            "Cuota 2": cuotas[1],
                            "Casa 2": bkrs[1],
                            "ROI (%)": roi
                        }
                        surebets.append(registro)
    return surebets

st.set_page_config(page_title="Surebets por Deporte", layout="wide")
st.title("🎯 Surebets Multimercado: Fútbol, Baloncesto, Tenis y Béisbol")
st.write("Busca oportunidades reales de arbitraje (surebets) por deporte y mercado.")

if st.button("🔍 Buscar Ahora"):
    for key, label in SPORTS:
        st.subheader(f"{label} - Surebets Detectados")
        surebets = obtener_eventos(key)
        df_sure = pd.DataFrame(surebets)
        if not df_sure.empty:
            st.dataframe(df_sure)
        else:
            st.info(f"No se encontraron surebets para {label}.")
