# surebets_web.py
import streamlit as st
import requests
import time
from itertools import cycle

# ----- CONFIGURACIÓN -----
st.set_page_config(page_title="Surebets Japh", layout="wide")
st.title("🔎 Buscador de Surebets - Japh")

# Deportes permitidos (según The Odds API)
DEPORTES = {
    "soccer": "Fútbol",
    "basketball": "Baloncesto",
    "tennis": "Tenis",
    "baseball": "Béisbol"
}

# Lista de 50 claves API proporcionadas por el usuario
API_KEYS = [
    "734f30d0866696cf90d5029ac106cfba",
    "10fb6d9d7b3240906d0acea646068535",
    "a9ff72549c4910f1fa9659e175a35cc0",
    "1e3d9c9f72505821cf9d50649fc2aa55",
    "cd07d4dcaf1f6fd9e5a4536f865b1004",
    "8c08c68248fa3b8001523f6671cbb6e3",
    "eb5d9e0d9f9b49e0a6a8806ff8bb83b6",
    "4ac3a2ad45f1a04225fcd4602f7d0062",
    "50f7fd9b14c5984d66f70522d7e59703",
    "b537b23b8464f155fd78012e4fa3e9ef",
    "9aa5b8ad39b28e4e19cb3a1c37c13a24",
    "15de2a8c5e002c37e1c1a3ed037d6c87",
    "36882b22bc92c3645b7c38a27c5e8439",
    "a4b1f1df79846cb5e19d7c5a021ae769",
    "82b1e287a1e12d77d77aa5d2e234aabf",
    "b1aa84912b35f6ddbcbe9cb3e2a2d087",
    "09a1d7acff37b7e2a7169cfaf0a17b58",
    "82d5a916473bfa0ee3cde5f9db2f263e",
    "6d5e6a56cb7fa6e38e0e9d590b0dc460",
    "3df6d6cc97e9bb740d83f3e4cb8505e9",
    "c7e229fa642457fb47de8e5e8edbb776",
    "04575dc6332a5485fc166b0a0c8acfea",
    "fce92f8d4a682c3f5a0e7815ea3dcf27",
    "4d1ea5b6c5ff03d40de23d7297b76b8f",
    "3bc5a94fd42e4a98b02aeac76b5a4d69",
    "7ef18d4f49c2eb4e50ebd47da4fdf50d",
    "28ef2c5a92c88a04889199b40296cf14",
    "9d96a10edb62d7cdb4e0d7a5f9d798b2",
    "e5e29a1e19f3c97f55bd3f37d6f991cc",
    "315cae388d83615431c71d3373883c40",
    "d6713a4d530ca99e21a5ee2bb77489c7",
    "19a1d48bd2c3726fe5e886bf0e9585d2",
    "9135d2ae0640135bb8781b4e4d67e0e3",
    "36c6c1b0935eb7516b44a9a8bb0dfd59",
    "6f7c6c6a2a23a5d0a17d3e4c9c3fa16c",
    "0fc4a920a0c2120e6a79a416bdca1f84",
    "9c85c671f2d10a3023b0e4bb3cde3f0e",
    "e49f36a84f46907f5a30ff10c901ea5b",
    "b264ddcc6ac2b5bffb9dfacfa2082b3a",
    "90ff542547f60313f4e13e8e34f727d3",
    "e053a059d7efafbf25f4a253d5abfb9c",
    "a743871028b9b4a0e39fcffb4bce1b19",
    "b24bb9ecaa39f16d7159a3f09375a9be",
    "ca9020f826eab3bc1715ea920a1eb2e6",
    "71ad64b6e99c65e72d6b87647f2580f4",
    "4094a8f2bfb0dd4890cf1ab7f5397a5d",
    "dd94bb8b5bca3d91d9a17219f1bd3ecf",
    "7fa9497e887a72c217ab4e1e5b9e88c9",
    "8a1a16fa321108edc5dc6a9d0bd8a7a7",
    "09bc64c229f3fa0e6e5f4933e123f0c0",
]

api_cycle = cycle(API_KEYS)
api_usage = {key: 0 for key in API_KEYS}
bad_keys = set()

# ----------- FUNCIONES -----------
def obtener_cuotas(deporte):
    for _ in range(len(API_KEYS)):
        api_key = next(api_cycle)
        if api_key in bad_keys:
            continue
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{deporte}/odds"
            params = {
                "regions": "us",
                "markets": "h2h",
                "apiKey": api_key,
            }
            response = requests.get(url, params=params)
            api_usage[api_key] += 1
            if response.status_code == 429:
                bad_keys.add(api_key)
                continue
            return response.json()
        except Exception as e:
            continue
    return []

def calcular_surebets(eventos):
    surebets = []
    for event in eventos:
        try:
            if "bookmakers" not in event or len(event["bookmakers"]) < 2:
                continue
            team1, team2 = event.get("teams", ["", ""])
            mejores = sorted([
                (b["markets"][0]["outcomes"], b["title"])
                for b in event["bookmakers"]
                if b["markets"]
            ], key=lambda x: -max(o["price"] for o in x[0]))

            if len(mejores) < 2:
                continue

            cuota1, casa1 = mejores[0][0][0]["price"], mejores[0][1]
            cuota2, casa2 = mejores[1][0][1]["price"], mejores[1][1]

            inv = 1 / cuota1 + 1 / cuota2
            if inv < 1:
                roi = round((1 - inv) * 100, 2)
                surebets.append({
                    "Evento": f"{team1} vs {team2}",
                    "Casa 1": casa1,
                    "Cuota 1": cuota1,
                    "Casa 2": casa2,
                    "Cuota 2": cuota2,
                    "ROI %": roi
                })
        except:
            continue
    return surebets

# ----------- INTERFAZ -----------
st.sidebar.title("⚙️ Configuración")
selected_deportes = st.sidebar.multiselect("Selecciona deportes", list(DEPORTES.keys()), default=list(DEPORTES.keys()))

if st.button("🔍 Buscar Surebets"):
    resultados = {}
    with st.spinner("Buscando oportunidades de surebets..."):
        for deporte in selected_deportes:
            data = obtener_cuotas(deporte)
            surebets = calcular_surebets(data)
            if surebets:
                resultados[deporte] = surebets
            time.sleep(0.3)

    st.success("¡Búsqueda completada!")

    for dep in resultados:
        st.subheader(f"{DEPORTES[dep]} 🏆")
        st.dataframe(resultados[dep])

# Mostrar estado de las APIs
with st.expander("🔑 Estado de las API Keys"):
    st.write("**API Keys activas/inactivas:**")
    for key in API_KEYS:
        estado = "✅ Activa" if key not in bad_keys else "❌ Agotada"
        st.write(f"{key[:6]}... → {estado} (usos: {api_usage[key]})")
