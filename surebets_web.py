import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import random
import time

st.set_page_config(page_title="Buscador de Surebets por Deporte", layout="wide")

# Lista de 50 APIs que rotan automáticamente
API_KEYS = [
    "734f30d0866696cf90d5029ac106cfba",
    "10fb6d9d7b3240906d0acea646068535",
    "a9ff72549c4910f1fa9659e175a35cc0",
    "25e9d8872877f5110254ff6ef42056c6",
    "6205cdb2cfd889e6fc44518f950f7dad",
    "d39a6f31abf6412d46b2c7185a5dfffe",
    "fbd5dece2a99c992cfd783aedfcd2ef3",
    "687ba857bcae9c7f33545dcbe59aeb2b",
    "f9ff83040b9d2afc1862094694f53da2",
    "f730fa9137a7cd927554df334af916dc",
    "9091ec0ea25e0cdfc161b91603e31a9a",
    "c0f7d526dd778654dfee7c0686124a77",
    "61a015bc1506aac11ec62901a6189dc6",
    "d585a73190a117c1041ccc78b92b23d9",
    "4056628d07b0b900175cb332c191cda0",
    "ac4d3eb2d6df42030568eadeee906770",
    "3cebba62ff5330d1a409160e6870bfd6",
    "358644d442444f95bd0b0278e4d3ea22",
    "45dff0519cde0396df06fc4bc1f9bce1",
    "a4f585765036f57be0966b39125f87a0",
    "349f8eff303fa0963424c54ba181535b",
    "f54405559ba5aaa27a9687992a84ae2f",
    "24772de60f0ebe37a554b179e0dd819f",
    "b7bdefecc83235f7923868a0f2e3e114",
    "3a9d3110045fd7373875bdbc7459c82c",
    "d2aa9011f39bfcb309b3ee1da6328573",
    "107ad40390a24eb61ee02ff976f3d3ac",
    "8f6358efeec75d6099147764963ae0f8",
    "672962843293d4985d0bed1814d3b716",
    "4b1867baf919f992554c77f493d258c5",
    "b3fd66af803adc62f00122d51da7a0e6",
    "53ded39e2281f16a243627673ad2ac8c",
    "bf785b4e9fba3b9cd1adb99b9905880b",
    "60e3b2a9a7324923d78bfc6dd6f3e5d3",
    "cc16776a60e3eee3e1053577216b7a29",
    "a0cc233165bc0ed04ee42feeaf2c9d30",
    "d2afc749fc6b64adb4d8361b0fe58b4b",
    "b351eb6fb3f5e95b019c18117e93db1b",
    "74dbc42e50dd64687dc1fad8af59c490",
    "7b4a5639cbe63ddf37b64d7e327d3e71",
    "20cec1e2b8c3fd9bb86d9e4fad7e6081",
    "1352436d9a0e223478ec83aec230b4aa",
    "29257226d1c9b6a15c141d989193ef72",
    "24677adc5f5ff8401c6d98ea033e0f0b",
    "54e84a82251def9696ba767d6e2ca76c",
    "ff3e9e3a12c2728c6c4ddea087bc51a9",
    "f3ff0fb5d7a7a683f88b8adec904e7b8",
    "1e0ab1ff51d111c88aebe4723020946a",
    "6f74a75a76f42fabaa815c4461c59980",
    "86de2f86b0b628024ef6d5546b479c0f",
]

SPORTS = {
    "soccer": "Fútbol",
    "basketball": "Baloncesto",
    "tennis": "Tenis",
    "baseball": "Béisbol"
}

def fetch_odds(api_key, sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key}&regions=us&markets=h2h&oddsFormat=decimal"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def buscar_surebets():
    resultados = {nombre: [] for nombre in SPORTS.values()}
    for sport_key, sport_name in SPORTS.items():
        for api_key in API_KEYS:
            data = fetch_odds(api_key, sport_key)
            for event in data:
                try:
                    teams = event.get("teams", ["Equipo A", "Equipo B"])
                    sites = event.get("bookmakers", [])
                    if len(sites) < 2:
                        continue
                    mejores_cuotas = sorted(
                        [site["markets"][0]["outcomes"] for site in sites if site["markets"]],
                        key=lambda x: -1 * min([out["price"] for out in x])
                    )
                    if len(mejores_cuotas) >= 2:
                        cuota1 = mejores_cuotas[0][0]["price"]
                        cuota2 = mejores_cuotas[1][1]["price"]
                        prob_total = (1 / cuota1) + (1 / cuota2)
                        if prob_total < 1:
                            utilidad = round((1 - prob_total) * 100, 2)
                            resultados[sport_name].append({
                                "Evento": f"{teams[0]} vs {teams[1]}",
                                "Deporte": sport_name,
                                "Utilidad (%)": utilidad,
                                "Cuota 1": cuota1,
                                "Cuota 2": cuota2
                            })
                except:
                    continue
            time.sleep(0.5)
    return resultados

st.title("🎯 Buscador de Surebets por Deporte")
if st.button("🔍 Buscar Surebets"):
    with st.status("Buscando...", expanded=True) as status:
        resultados = buscar_surebets()
        for deporte, apuestas in resultados.items():
            if apuestas:
                st.subheader(f"🟢 Surebets en {deporte}")
                df = pd.DataFrame(apuestas)
                st.dataframe(df)
        status.update(label="✅ Búsqueda completada", state="complete")

