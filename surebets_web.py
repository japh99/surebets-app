import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import time

# --- Configuración de la Página y Título ---
st.set_page_config(
    page_title="Buscador de Surebets Global",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Buscador de Surebets Global")
st.markdown("""
Esta aplicación detecta oportunidades de **surebets (arbitraje deportivo)** en tiempo real a través de **todas las ligas del mundo** para los deportes seleccionados.
- **Instrucciones:** Selecciona uno o más deportes en el panel de la izquierda. La aplicación escaneará todas las ligas activas para esos deportes.
- **API:** Rota automáticamente entre 50 claves de The Odds API para maximizar el uso de créditos.
""")

# --- Lista de API Keys ---
# NOTA IMPORTANTE: En un entorno de producción o si compartes este código públicamente,
# considera cargar estas claves desde variables de entorno o un archivo de secretos
# (.streamlit/secrets.toml) para mayor seguridad y evitar exponerlas.
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

# --- Diccionario de Deportes ---
# ¡ACTUALIZADO! Se asume 'baseball_mlb' como la clave correcta para Béisbol.
# Si el error persiste, usa el script 'check_sports.py' para verificar la clave exacta.
SPORTS = {
    "Fútbol": "soccer",
    "Baloncesto": "basketball",
    "Tenis": "tennis",
    "Béisbol": "baseball_mlb", # POSIBLE CORRECCIÓN: De 'baseball' a 'baseball_mlb'
}

# --- Lógica de Rotación de API Keys y Gestión de Créditos ---
if 'api_key_index' not in st.session_state:
    st.session_state.api_key_index = 0
if 'api_key_status' not in st.session_state:
    # Inicializar el estado de cada API key: True si está activa, False si agotó créditos
    st.session_state.api_key_status = {key: True for key in API_KEYS}
if 'depleted_api_keys' not in st.session_state:
    # Guardar las claves agotadas para mostrarlas
    st.session_state.depleted_api_keys = []

def get_next_available_api_key_info():
    """
    Obtiene la próxima API key disponible (que no haya agotado sus créditos)
    y su índice. Si todas están agotadas, devuelve None.
    """
    initial_index = st.session_state.api_key_index
    num_keys = len(API_KEYS)
    
    for _ in range(num_keys): # Iterar a través de todas las claves una vez
        current_key_index = st.session_state.api_key_index
        current_key = API_KEYS[current_key_index]
        
        # Si la clave actual está activa, la usamos
        if st.session_state.api_key_status.get(current_key, True):
            return current_key, current_key_index
        
        # Si la clave actual no está activa, pasar a la siguiente y continuar el bucle
        st.session_state.api_key_index = (current_key_index + 1) % num_keys
        
        # Si hemos dado la vuelta completa y ninguna está activa, salimos
        if st.session_state.api_key_index == initial_index:
            break
            
    return None, None # Todas las claves están agotadas

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
        return None # No mostrar eventos muy lejanos

def find_surebets_for_sport(sport_name, sport_key, api_key, api_key_idx):
    """Busca surebets para TODAS las ligas de un deporte específico."""
    surebets_found = []
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        "apiKey": api_key,
        "regions": "us,eu,uk,au",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        # Verificar si la clave ha agotado sus créditos (código 401 o 402)
        if response.status_code == 401 or response.status_code == 402:
            st.session_state.api_key_status[api_key] = False # Marcar la clave como agotada
            if api_key not in st.session_state.depleted_api_keys:
                st.session_state.depleted_api_keys.append(api_key)
            st.error(f"⚠️ **Error: La API Key #{api_key_idx} (últimos 4 digitos: {api_key[-4:]}) ha agotado sus créditos.** Por favor, reemplázala.")
            return [] # No procesar datos si la clave está agotada
        
        # Verificar si es un error 404 (Not Found) específicamente
        if response.status_code == 404:
            st.error(f"⚠️ **Error 404 para {sport_name}**: La URL solicitada no se encontró. Esto podría indicar una 'sport_key' incorrecta o que no hay datos disponibles para este deporte/liga en este momento. URL: {response.url}")
            return [] # No procesar datos si el recurso no se encontró

        response.raise_for_status() # Lanza una excepción para otros códigos de error HTTP
        data = response.json()
        
        remaining_requests = response.headers.get('x-requests-remaining', 'N/A')
        used_requests = response.headers.get('x-requests-used', 'N/A')
        st.sidebar.info(f"API Key #{api_key_idx} (usando {api_key[-4:]}..) | Usados: {used_requests} | Restantes: {remaining_requests}")

        for event in data:
            status = get_event_status(event['commence_time'])
            if not status:
                continue

            home_team = event['home_team']
            away_team = event['away_team']
            
            best_odds = {home_team: {'price': 0, 'bookmaker': ''}, away_team: {'price': 0, 'bookmaker': ''}}

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
                utilidad = (1 - (1/odds1 + 1/odds2)) * 100
                
                if utilidad > 0:
                    surebets_found.append({
                        "Deporte": sport_name,
                        "Liga/Torneo": event['sport_title'],
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
        # Otros errores de conexión o HTTP que no son 401/402/404
        st.error(f"Error de conexión o API para {sport_name}: {e}")
        return []
    except Exception as e:
        st.warning(f"No se encontraron datos o ocurrió un error inesperado para {sport_name}: {e}")
        return []

# --- Interfaz de Usuario ---
st.sidebar.header("Panel de Control")

selected_sports = st.sidebar.multiselect(
    "Selecciona los deportes a escanear:",
    options=list(SPORTS.keys()),
    default=["Fútbol", "Baloncesto", "Tenis", "Béisbol"] 
)

if st.sidebar.button("🚀 Iniciar Búsqueda Global de Surebets"):
    if not selected_sports:
        st.warning("Por favor, selecciona al menos un deporte para buscar.")
    else:
        results_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_surebets = []
        total_sports = len(selected_sports)

        for i, sport_name in enumerate(selected_sports):
            sport_key = SPORTS[sport_name]
            
            # Obtener la próxima clave API disponible
            api_key, api_key_idx = get_next_available_api_key_info()
            
            if api_key is None:
                st.error("❌ Todas las API Keys disponibles han agotado sus créditos. Por favor, reemplaza las claves agotadas.")
                break # Detener la búsqueda si no hay claves disponibles
            
            status_text.text(f"Buscando en: {sport_name} (todas las ligas) usando API Key #{api_key_idx}...")
            
            # Pasar el índice de la API key a la función para un mejor feedback
            sport_surebets = find_surebets_for_sport(sport_name, sport_key, api_key, api_key_idx)
            
            if sport_surebets:
                all_surebets.extend(sport_surebets)
            
            progress_bar.progress((i + 1) / total_sports)
            # Pequeña pausa para evitar exceder límites de API rápidamente y dar tiempo a Streamlit
            time.sleep(1) 

        # Mensaje final de búsqueda completada
        if api_key is not None:
            status_text.success("¡Búsqueda global completada!")
        progress_bar.empty() # Ocultar barra de progreso

        with results_placeholder.container():
            if not all_surebets:
                st.warning("No se encontraron surebets en los deportes seleccionados o hubo problemas con la API.")
            else:
                st.success(f"¡Se encontraron {len(all_surebets)} oportunidades de surebet a nivel mundial!")
                
                df = pd.DataFrame(all_surebets)
                
                column_order = [
                    "Deporte", "Liga/Torneo", "Estado", "Evento", "Fecha (UTC)", 
                    "Utilidad (%)", "Equipo 1", "Mejor Cuota 1", "Casa de Apuestas 1",
                    "Equipo 2", "Mejor Cuota 2", "Casa de Apuestas 2"
                ]
                df = df[column_order]

                for sport in df['Deporte'].unique():
                    with st.expander(f"Surebets para {sport}", expanded=True):
                        sport_df = df[df['Deporte'] == sport].drop(columns=['Deporte'])
                        
                        st.dataframe(sport_df.style.apply(
                            lambda x: ['background-color: #28a745' if col == 'Utilidad (%)' else '' for col in x.index],
                            axis=1
                        ), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("Información de API")
st.sidebar.write(f"Total de API Keys disponibles: {len(API_KEYS)}")

# Mostrar la próxima API Key a usar si hay alguna disponible
next_key_to_use, next_key_idx_to_use = get_next_available_api_key_info()
if next_key_to_use:
    st.sidebar.info(f"Próxima API Key a usar: #{next_key_idx_to_use} (termina en {next_key_to_use[-4:]})")
else:
    st.sidebar.warning("No quedan API Keys activas para usar.")

st.sidebar.markdown("---")
st.sidebar.subheader("Claves API Agotadas")
if st.session_state.depleted_api_keys:
    for depleted_key in st.session_state.depleted_api_keys:
        st.sidebar.error(f"❌ Agotada: {depleted_key} (últimos 4 digitos: {depleted_key[-4:]}) - Reemplazar")
else:
    st.sidebar.success("✅ Todas las API Keys están activas (o no se han detectado agotadas aún).")
st.sidebar.markdown("---")
st.sidebar.markdown("Autor: **JAPH99** 🇨🇴")
