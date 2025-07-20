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
- **Instrucciones:** Selecciona uno o más deportes y mercados en el panel de la izquierda.
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
SPORTS = {
    "Fútbol": "soccer",
    "Baloncesto": "basketball",
    "Tenis": "tennis",
    "Béisbol": "baseball_mlb", # **SOLUCIÓN 404: Asegurado 'baseball_mlb'**
}

# --- Diccionario de Mercados ---
MARKETS = {
    "12 (Ganador sin Empate)": "h2h",
    "1X2 (Resultado Final)": "full_time_result", # **SOLUCIÓN 422: Cambiado de 'h2h_moneyline' a 'full_time_result'**
}

# --- Lógica de Rotación de API Keys y Gestión de Créditos ---
if 'api_key_index' not in st.session_state:
    st.session_state.api_key_index = 0
if 'api_key_status' not in st.session_state:
    st.session_state.api_key_status = {key: True for key in API_KEYS}
if 'depleted_api_keys' not in st.session_state:
    st.session_state.depleted_api_keys = []

def get_next_available_api_key_info():
    """
    Obtiene la próxima API key disponible (que no haya agotado sus créditos)
    y su índice. Si todas están agotadas, devuelve None.
    """
    initial_index = st.session_state.api_key_index
    num_keys = len(API_KEYS)
    
    for _ in range(num_keys):
        current_key_index = st.session_state.api_key_index
        current_key = API_KEYS[current_key_index]
        
        if st.session_state.api_key_status.get(current_key, True):
            return current_key, current_key_index
        
        st.session_state.api_key_index = (current_key_index + 1) % num_keys
        
        if st.session_state.api_key_index == initial_index:
            break
            
    return None, None

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
        return None

def find_surebets_for_sport(sport_name, sport_key, api_key, api_key_idx, selected_market_key):
    """Busca surebets para TODAS las ligas de un deporte específico y un mercado."""
    surebets_found = []
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        "apiKey": api_key,
        "regions": "us,eu,uk,au",
        "markets": selected_market_key, # Usar el mercado seleccionado
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 401 or response.status_code == 402:
            st.session_state.api_key_status[api_key] = False
            if api_key not in st.session_state.depleted_api_keys:
                st.session_state.depleted_api_keys.append(api_key)
            st.error(f"⚠️ **Error: La API Key #{api_key_idx} (últimos 4 digitos: {api_key[-4:]}) ha agotado sus créditos.** Por favor, reemplázala.")
            return []
        
        if response.status_code == 404:
            st.error(f"⚠️ **Error 404 para {sport_name} en mercado '{selected_market_key}'**: La URL solicitada no se encontró. Esto podría indicar una 'sport_key' o 'market' incorrecta, o que no hay datos disponibles. URL: {response.url}")
            return []
        
        if response.status_code == 422: # Añadida gestión explícita para 422
            st.error(f"⚠️ **Error 422 (Entidad No Procesable) para {sport_name} en mercado '{selected_market_key}'**: Esto suele indicar un problema con los parámetros de la solicitud. Verifica que la combinación deporte/mercado sea válida. URL: {response.url}")
            return []

        response.raise_for_status()
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
            
            # Inicializar mejores cuotas según el tipo de mercado
            if selected_market_key == 'h2h': # Mercado 12 (2 vías)
                best_odds = {home_team: {'price': 0, 'bookmaker': ''}, away_team: {'price': 0, 'bookmaker': ''}}
                expected_outcomes = {home_team, away_team}
            elif selected_market_key == 'full_time_result': # Mercado 1X2 (3 vías)
                best_odds = {home_team: {'price': 0, 'bookmaker': ''}, 'Draw': {'price': 0, 'bookmaker': ''}, away_team: {'price': 0, 'bookmaker': ''}}
                expected_outcomes = {home_team, 'Draw', away_team}
            else:
                continue # No soportamos otros mercados por ahora

            if len(event['bookmakers']) < 2:
                continue

            for bookmaker in event['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == selected_market_key:
                        found_outcomes_for_bookmaker = set()
                        for outcome in market['outcomes']:
                            team_name = outcome['name']
                            price = outcome['price']
                            if team_name in best_odds and price > best_odds[team_name]['price']:
                                best_odds[team_name]['price'] = price
                                best_odds[team_name]['bookmaker'] = bookmaker['title']
                            found_outcomes_for_bookmaker.add(team_name)
                        
                        # Asegurarse de que el bookmaker ofrece todas las cuotas para el mercado seleccionado
                        # Ejemplo: si es 1X2, que tenga cuota para local, empate y visitante
                        if found_outcomes_for_bookmaker != expected_outcomes:
                            continue # No consideramos este bookmaker si no tiene todas las cuotas necesarias para el mercado

            # Verificar y calcular surebet
            if selected_market_key == 'h2h': # Mercado 12 (2 vías)
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
                            "Mercado": "12",
                            "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                            "Selección 1": home_team,
                            "Mejor Cuota 1": odds1,
                            "Casa de Apuestas 1": best_odds[home_team]['bookmaker'],
                            "Selección 2": away_team,
                            "Mejor Cuota 2": odds2,
                            "Casa de Apuestas 2": best_odds[away_team]['bookmaker'],
                            "Utilidad (%)": f"{utilidad:.2f}%"
                        })
            
            elif selected_market_key == 'full_time_result': # Mercado 1X2 (3 vías)
                odds1 = best_odds[home_team]['price']
                oddsX = best_odds['Draw']['price'] # Empate
                odds2 = best_odds[away_team]['price']

                if odds1 > 0 and oddsX > 0 and odds2 > 0:
                    utilidad = (1 - (1/odds1 + 1/oddsX + 1/odds2)) * 100
                    
                    if utilidad > 0:
                        surebets_found.append({
                            "Deporte": sport_name,
                            "Liga/Torneo": event['sport_title'],
                            "Estado": status,
                            "Evento": f"{home_team} vs {away_team}",
                            "Mercado": "1X2",
                            "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                            "Selección 1": home_team,
                            "Mejor Cuota 1": odds1,
                            "Casa de Apuestas 1": best_odds[home_team]['bookmaker'],
                            "Selección X": "Empate", # Nueva columna para el empate
                            "Mejor Cuota X": oddsX,
                            "Casa de Apuestas X": best_odds['Draw']['bookmaker'],
                            "Selección 2": away_team,
                            "Mejor Cuota 2": odds2,
                            "Casa de Apuestas 2": best_odds[away_team]['bookmaker'],
                            "Utilidad (%)": f"{utilidad:.2f}%"
                        })
        
        return surebets_found

    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión o API para {sport_name} en mercado '{selected_market_key}': {e}")
        return []
    except Exception as e:
        st.warning(f"No se encontraron datos o ocurrió un error inesperado para {sport_name} en mercado '{selected_market_key}': {e}")
        return []

# --- Interfaz de Usuario ---
st.sidebar.header("Panel de Control")

selected_sports = st.sidebar.multiselect(
    "Selecciona los deportes a escanear:",
    options=list(SPORTS.keys()),
    default=["Fútbol", "Baloncesto", "Tenis", "Béisbol"] 
)

selected_markets = st.sidebar.multiselect(
    "Selecciona los mercados a escanear:",
    options=list(MARKETS.keys()),
    default=["12 (Ganador sin Empate)", "1X2 (Resultado Final)"] # Seleccionar ambos por defecto
)

if st.sidebar.button("🚀 Iniciar Búsqueda Global de Surebets"):
    if not selected_sports or not selected_markets:
        st.warning("Por favor, selecciona al menos un deporte y un mercado para buscar.")
    else:
        results_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_surebets = []
        total_searches = len(selected_sports) * len(selected_markets)
        search_count = 0

        for sport_name in selected_sports:
            sport_key = SPORTS[sport_name]
            for market_display_name in selected_markets:
                market_key = MARKETS[market_display_name]

                # VALIDACIÓN IMPORTANTE: No todos los deportes tienen todos los mercados.
                # 'full_time_result' (1X2) es común en fútbol.
                # 'h2h' (12) es común en todos.
                # Considera añadir lógica para deshabilitar 1X2 para deportes donde no aplica naturalmente (ej. baloncesto, tenis, béisbol no tienen empate).
                if market_key == 'full_time_result' and sport_key in ["basketball", "tennis", "baseball_mlb"]:
                    st.warning(f"El mercado '{market_display_name}' no es común o aplicable para '{sport_name}'. Saltando esta combinación.")
                    search_count += 1
                    progress_bar.progress(search_count / total_searches)
                    continue

                api_key, api_key_idx = get_next_available_api_key_info()
                
                if api_key is None:
                    st.error("❌ Todas las API Keys disponibles han agotado sus créditos. Por favor, reemplaza las claves agotadas.")
                    break # Detener la búsqueda si no hay claves disponibles
                
                status_text.text(f"Buscando en: {sport_name} - Mercado: {market_display_name} (todas las ligas) usando API Key #{api_key_idx}...")
                
                sport_surebets = find_surebets_for_sport(sport_name, sport_key, api_key, api_key_idx, market_key)
                
                if sport_surebets:
                    all_surebets.extend(sport_surebets)
                
                search_count += 1
                progress_bar.progress(search_count / total_searches)
                time.sleep(1) # Pausa para evitar exceder límites de API

            if api_key is None: # Si se agotaron las claves durante el bucle de mercados
                break

        if api_key is not None:
            status_text.success("¡Búsqueda global completada!")
        progress_bar.empty()

        with results_placeholder.container():
            if not all_surebets:
                st.warning("No se encontraron surebets en los deportes/mercados seleccionados, o hubo problemas con la API.")
            else:
                st.success(f"¡Se encontraron {len(all_surebets)} oportunidades de surebet a nivel mundial!")
                
                df = pd.DataFrame(all_surebets)
                
                # Definir el orden de las columnas dinámicamente según si hay 'Selección X'
                if 'Selección X' in df.columns:
                    column_order = [
                        "Deporte", "Liga/Torneo", "Estado", "Evento", "Mercado", "Fecha (UTC)", 
                        "Utilidad (%)", "Selección 1", "Mejor Cuota 1", "Casa de Apuestas 1",
                        "Selección X", "Mejor Cuota X", "Casa de Apuestas X", # Columnas para 1X2
                        "Selección 2", "Mejor Cuota 2", "Casa de Apuestas 2"
                    ]
                else: # Para mercado 12 (H2H)
                    column_order = [
                        "Deporte", "Liga/Torneo", "Estado", "Evento", "Mercado", "Fecha (UTC)", 
                        "Utilidad (%)", "Selección 1", "Mejor Cuota 1", "Casa de Apuestas 1",
                        "Selección 2", "Mejor Cuota 2", "Casa de Apuestas 2"
                    ]
                
                # Asegurarse de que las columnas existan antes de reordenar
                df = df.reindex(columns=[col for col in column_order if col in df.columns])

                for sport in df['Deporte'].unique():
                    with st.expander(f"Surebets para {sport}", expanded=True):
                        # Filtrar por deporte y luego por mercado para expander
                        for market_type in df[df['Deporte'] == sport]['Mercado'].unique():
                            with st.expander(f"Mercado: {market_type}", expanded=True):
                                sport_market_df = df[(df['Deporte'] == sport) & (df['Mercado'] == market_type)].drop(columns=['Deporte', 'Mercado'])
                                
                                st.dataframe(sport_market_df.style.apply(
                                    lambda x: ['background-color: #28a745' if col == 'Utilidad (%)' else '' for col in x.index],
                                    axis=1
                                ), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("Información de API")
st.sidebar.write(f"Total de API Keys disponibles: {len(API_KEYS)}")

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
