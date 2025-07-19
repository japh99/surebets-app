# surebets_streamlit_app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import time

# --- Configuración de la Página y Título ---
st.set_page_config(
    page_title="Buscador de Surebets",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Buscador de Surebets Deportivo")
st.markdown("""
Esta aplicación detecta oportunidades de **surebets (arbitraje deportivo)** en tiempo real.
Utiliza datos de **The Odds API** para el mercado *Head-to-Head (H2H)* y rota entre 50 claves API para optimizar el uso de créditos.
- **Deportes Analizados:** Fútbol, Baloncesto, Tenis y Béisbol.
- **Filtros:** Muestra solo surebets con utilidad positiva y diferencia entre eventos en vivo y pre-partido.
""")

# --- Lista de API Keys y Variables Globales ---
API_KEYS = [
    "734f30d0866696cf90d5029ac106cfba", "10fb6d9d7b3240906d0acea646068535",
    "a9ff72549c4910f1fa9659e175a35cc0", "25e9d8872877f5110254ff6ef42056c6",
    "6205cdb2cfd889e6fc44518f950f7dad", "d39a6f31abf6412d46b2c7185a5dfffe",
    "fbd5dece2a99c992cfd783aedfcd2ef3", "687ba857bcae9c7f33545dcbe59aeb2b",
    "f9ff83040b9d2afc1862094694f53da2", "f730fa9137a7cd927554df334af916dc",
    "9091ec0ea25e0cdfc161b91603e31a9a", "c0f7d526dd778654dfee7c0686124a77",
    "61a015bc1506aac11ec62901a6189dc6", "d585a73190a117c1041ccc78b92b23d9",
    "4056628d07b0b900175cb332c191cda0", "ac4d3eb2d6df42030568eadeee906770",
    "3cebba62ff5330d1a409160e6870bfd6", "358644d442444f95bd0b0278e4d3ea22",
    "45dff0519cde0396df06fc4bc1f9bce1", "a4f585765036f57be0966b39125f87a0",
    "349f8eff303fa0963424c54ba181535b", "f54405559ba5aaa27a9687992a84ae2f",
    "24772de60f0ebe37a554b179e0dd819f", "b7bdefecc83235f7923868a0f2e3e114",
    "3a9d3110045fd7373875bdbc7459c82c", "d2aa9011f39bfcb309b3ee1da6328573",
    "107ad40390a24eb61ee02ff976f3d3ac", "8f6358efeec75d6099147764963ae0f8",
    "672962843293d4985d0bed1814d3b716", "4b1867baf919f992554c77f493d258c5",
    "b3fd66af803adc62f00122d51da7a0e6", "53ded39e2281f16a243627673ad2ac8c",
    "bf785b4e9fba3b9cd1adb99b9905880b", "60e3b2a9a7324923d78bfc6dd6f3e5d3",
    "cc16776a60e3eee3e1053577216b7a29", "a0cc233165bc0ed04ee42feeaf2c9d30",
    "d2afc749fc6b64adb4d8361b0fe58b4b", "b351eb6fb3f5e95b019c18117e93db1b",
    "74dbc42e50dd64687dc1fad8af59c490", "7b4a5639cbe63ddf37b64d7e327d3e71",
    "20cec1e2b8c3fd9bb86d9e4fad7e6081", "1352436d9a0e223478ec83aec230b4aa",
    "29257226d1c9b6a15c141d989193ef72", "24677adc5f5ff8401c6d98ea033e0f0b",
    "54e84a82251def9696ba767d6e2ca76c", "ff3e9e3a12c2728c6c4ddea087bc51a9",
    "f3ff0fb5d7a7a683f88b8adec904e7b8", "1e0ab1ff51d111c88aebe4723020946a",
    "6f74a75a76f42fabaa815c4461c59980", "86de2f86b0b628024ef6d5546b479c0f"
]

# Diccionario de deportes para la API
SPORTS = {
    "Fútbol": "soccer_usa_mls", # Ejemplo, puedes agregar más ligas
    "Baloncesto": "basketball_nba",
    "Béisbol": "baseball_mlb",
    "Tenis": "tennis_atp_french_open" # Cambiar según el Grand Slam actual
}

# --- Lógica de Rotación de API Keys ---
if 'api_key_index' not in st.session_state:
    st.session_state.api_key_index = 0

def get_next_api_key():
    """Obtiene la siguiente API key de la lista y actualiza el índice."""
    index = st.session_state.api_key_index
    key = API_KEYS[index]
    st.session_state.api_key_index = (index + 1) % len(API_KEYS)
    return key

# --- Funciones Principales ---
def get_event_status(commence_time_str):
    """Clasifica un evento como 'En Vivo' o 'Pre-Partido'."""
    commence_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
    now_utc = datetime.now(timezone.utc)
    
    if commence_time < now_utc:
        return "🔴 En Vivo"
    elif commence_time < now_utc + timedelta(hours=48):
        return "🟢 Pre-Partido"
    else:
        # Si el evento es más allá de 48 horas, no lo consideramos.
        return None

def find_surebets_for_sport(sport_key, sport_name, api_key):
    """Busca surebets para un deporte específico usando una API key."""
    surebets_found = []
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        "apiKey": api_key,
        "regions": "us,eu,uk", # Ampliamos regiones para más casas de apuestas
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status() # Lanza un error si la petición falla
        data = response.json()
        
        remaining_requests = response.headers.get('x-requests-remaining', 'N/A')
        st.sidebar.info(f"Consumiendo API Key #{st.session_state.api_key_index}. Créditos restantes: {remaining_requests}")

        for event in data:
            status = get_event_status(event['commence_time'])
            if not status:
                continue # Ignora eventos que no son en vivo ni en las próximas 48h

            home_team = event['home_team']
            away_team = event['away_team']
            
            best_odds = {home_team: {'price': 0, 'bookmaker': ''}, away_team: {'price': 0, 'bookmaker': ''}}

            # Filtrar solo eventos con al menos 2 casas de apuestas
            if len(event['bookmakers']) < 2:
                continue

            for bookmaker in event['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            team_name = outcome['name']
                            price = outcome['price']
                            if team_name in best_odds and price > best_odds[team_name]['price']:
                                best_odds[team_name]['price'] = price
                                best_odds[team_name]['bookmaker'] = bookmaker['title']
            
            odds1 = best_odds[home_team]['price']
            odds2 = best_odds[away_team]['price']

            if odds1 > 0 and odds2 > 0:
                # Fórmula de utilidad
                utilidad = (1 - (1/odds1 + 1/odds2)) * 100
                
                if utilidad > 0:
                    surebets_found.append({
                        "Deporte": sport_name,
                        "Estado": status,
                        "Evento": f"{home_team} vs {away_team}",
                        "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                        "Equipo 1": home_team,
                        "Mejor Cuota 1": odds1,
                        "Casa de Apuestas 1": best_odds[home_team]['bookmaker'],
                        "Equipo 2": away_team,
                        "Mejor Cuota 2": odds2,
                        "Casa de Apuestas 2": best_odds[away_team]['bookmaker'],
                        "Utilidad (%)": f"{utilidad:.2f}%"
                    })
        
        return surebets_found

    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión o API para {sport_name}: {e}")
        return []
    except Exception as e:
        st.warning(f"No se encontraron datos o ocurrió un error para {sport_name}: {e}")
        return []

# --- Interfaz de Usuario ---
st.sidebar.header("Panel de Control")

if st.sidebar.button("🚀 Iniciar Búsqueda de Surebets"):
    # Placeholder para los resultados
    results_placeholder = st.empty()
    
    # Barra de progreso y estado
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_surebets = []
    total_sports = len(SPORTS)

    for i, (sport_name, sport_key) in enumerate(SPORTS.items()):
        status_text.text(f"Buscando en: {sport_name}...")
        
        # Obtiene una nueva API key para cada deporte
        api_key = get_next_api_key()
        
        # Realiza la búsqueda
        sport_surebets = find_surebets_for_sport(sport_key, sport_name, api_key)
        
        if sport_surebets:
            all_surebets.extend(sport_surebets)
        
        # Actualiza la barra de progreso
        progress_bar.progress((i + 1) / total_sports)
        time.sleep(1) # Pequeña pausa para no saturar la API

    status_text.success("¡Búsqueda completada!")
    progress_bar.empty()

    # --- Visualización de Resultados ---
    with results_placeholder.container():
        if not all_surebets:
            st.warning("No se encontraron surebets en esta búsqueda.")
        else:
            st.success(f"¡Se encontraron {len(all_surebets)} oportunidades de surebet!")
            
            df = pd.DataFrame(all_surebets)
            
            # Reordenar columnas para mejor visualización
            column_order = [
                "Deporte", "Estado", "Evento", "Fecha (UTC)", 
                "Utilidad (%)", "Equipo 1", "Mejor Cuota 1", "Casa de Apuestas 1",
                "Equipo 2", "Mejor Cuota 2", "Casa de Apuestas 2"
            ]
            df = df[column_order]

            # Agrupar por deporte para una visualización ordenada
            for sport in df['Deporte'].unique():
                with st.expander(f"Surebets para {sport}", expanded=True):
                    sport_df = df[df['Deporte'] == sport].drop(columns=['Deporte'])
                    
                    # Estilizar el DataFrame
                    st.dataframe(sport_df.style.apply(
                        lambda x: ['background-color: #28a745' if col == 'Utilidad (%)' else '' for col in x.index],
                        axis=1
                    ), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("Información de API")
st.sidebar.write(f"Total de API Keys disponibles: {len(API_KEYS)}")
st.sidebar.info(f"Próxima API Key a usar: #{ (st.session_state.api_key_index + 1) % len(API_KEYS) }")
st.sidebar.markdown("---")
st.sidebar.markdown("Autor: **JAPH99** 🇨🇴")

