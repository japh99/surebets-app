import streamlit as st
import requests
from datetime import datetime, timedelta
import time

# Lista de 50 APIs
APIS = [
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
    "86de2f86b0b628024ef6d5546b479c0f"
]

st.set_page_config(page_title="Buscador de Surebets por Deporte", layout="centered")
st.title("🎯 Buscador de Surebets por Deporte")

if st.button("🔍 Buscar Surebets"):
    st.info("Buscando...")
    resultados = {"soccer": [], "basketball": [], "tennis": [], "baseball": []}
    creditos_restantes = {}

    for api_key in APIS:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/odds/?regions=us&markets=h2h,totals,spreads&apiKey={api_key}"
            response = requests.get(url)
            creditos_restantes[api_key] = int(response.headers.get("x-requests-remaining", 0))
            if response.status_code != 200:
                continue

            data = response.json()
            for event in data:
                if "teams" not in event or "bookmakers" not in event:
                    continue

                match_teams = event.get("teams", ["Equipo 1", "Equipo 2"])
                match = f"{match_teams[0]} vs {match_teams[1]}"
                sport = event.get("sport_key", "")
                sport_simple = sport.split(":")[0]  # soccer:premier_league -> soccer

                if sport_simple in resultados:
                    resultados[sport_simple].append({
                        "match": match,
                        "bookmakers": event["bookmakers"],
                        "commence_time": event.get("commence_time", "")
                    })
        except Exception as e:
            continue

    st.success("✅ Búsqueda completada")

    with st.expander("📊 Estado de las APIs"):
        for k, v in creditos_restantes.items():
            st.write(f"API {k[:8]}...: {v} créditos restantes")

    for deporte, eventos in resultados.items():
        with st.expander(f"⚽ Surebets en {deporte.capitalize()} ({len(eventos)} encontrados)"):
            for evento in eventos:
                st.write(f"📍 {evento['match']} — 🕒 {evento['commence_time']}")


