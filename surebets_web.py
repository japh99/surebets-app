import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import time
import concurrent.futures # Importación necesaria para la paralelización

# --- Configuración de la Página y Título ---
st.set_page_config(
    page_title="Surebets: Buscador & Calculadora",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Buscador y Calculadora de Surebets")
st.markdown("""
Esta aplicación **detecta oportunidades de surebets (arbitraje deportivo)** en tiempo real para **varios mercados** y te permite **calcularlas** de forma sencilla.
""")

# --- Lista de API Keys (incluyendo las 50 proporcionadas) ---
# Es crucial mantener estas keys actualizadas y con créditos.
# Si tus keys se agotan, la aplicación no funcionará correctamente.
API_KEYS = [
    "734f30d0866696cf90d5029ac106cfba", "10fb6d9d7b3240906d0acea646068535",
    "a9ff72549c4910f1fa9659e175a35cc0", "25e9d8872877f5110254ff6ef42056c6",
    "6205cdb2cfd889e6fc44518f950f7dad", "d39a6f31abf6412d46b2c7185a5dfffe",
    "fbd5dece2a99c992cfd783aedfcd2ef3", "687ba857bcae9c7f33545dcbe59aeb2b",
    "f9ff83040b9d2afc1862094694f53da2", "f730fa9137a7cd927554df334af916dc",
    "9091ec0ea25e0cdfc161b91603e31a9a", "c0f7d526dd778654dfee7c0686124a77",
    "61a015bc1506aac11ec62901a6189dc6", "d585a73190a117c1041ccc778b92b23d9",
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

# --- Diccionario de Deportes de Interés (Solo los especificados) ---
SPORTS = {
    "Fútbol": "soccer",
    "Baloncesto": "basketball",
    "Tenis": "tennis",
    "Béisbol": "baseball_mlb",
}

# --- Diccionario de Mercados Disponibles (Ampliados) ---
MARKETS = {
    "Ganador (Moneyline/H2H)": "h2h",
    "Totales (Over/Under)": "totals",
    "Spreads (Hándicap)": "spreads",
}

# --- Inicialización del Estado de Sesión de Streamlit ---
# Se utilizan para mantener el estado de la aplicación entre recargas
if 'api_key_index' not in st.session_state:
    st.session_state.api_key_index = 0
if 'api_key_status' not in st.session_state:
    # Inicializa todas las keys como activas
    st.session_state.api_key_status = {key: True for key in API_KEYS}
if 'depleted_api_keys' not in st.session_state:
    st.session_state.depleted_api_keys = []

# Estado inicial para la calculadora, cargado con valores por defecto H2H
if 'calc_event_data' not in st.session_state:
    st.session_state.calc_event_data = {
        'Evento': 'Ej: Equipo A vs Equipo B',
        'Fecha (UTC)': 'N/A',
        'Mercado': 'Ganador (Moneyline/H2H)',
        'Cuota Local': 1.01,
        'Cuota Empate': 1.01, # Mantenido para flexibilidad si el usuario cambia el mercado en la calculadora
        'Cuota Visitante': 1.01,
        'Selección 1': 'Equipo Local',
        'Selección 2': 'Equipo Visitante',
        'Casa Local': 'Casa de Apuestas 1',
        'Casa Empate': 'N/A', # No aplica por defecto para H2H
        'Casa Visitante': 'Casa de Apuestas 2'
    }

# Estado para la calculadora manual: Nombres de casas y cuotas
if 'nombres_casas_manual' not in st.session_state:
    # Casas predeterminadas para COP, con facilidad de edición
    st.session_state.nombres_casas_manual = ["BetPlay", "Wplay", "Stake", "Bwin", "Betsson", "Luckia"] 
if 'cuotas_local_manual' not in st.session_state:
    st.session_state.cuotas_local_manual = [1.01] * 6
if 'cuotas_empate_manual' not in st.session_state:
    st.session_state.cuotas_empate_manual = [1.01] * 6 
if 'cuotas_visitante_manual' not in st.session_state:
    st.session_state.cuotas_visitante_manual = [1.01] * 6
if 'last_moneda_manual' not in st.session_state:
    st.session_state.last_moneda_manual = "COP" # Guarda la última moneda seleccionada

# --- Funciones Auxiliares para el Buscador ---

def get_next_available_api_key_info():
    """
    Obtiene la próxima API key disponible y su índice de forma segura para Streamlit.
    Esta función DEBE ser llamada SOLAMENTE desde el hilo principal de Streamlit
    para manipular st.session_state.
    """
    initial_index = st.session_state.api_key_index
    num_keys = len(API_KEYS)
    
    # Intentar encontrar una clave activa en el rango actual
    for _ in range(num_keys): # Iterar a través de todas las claves si es necesario
        current_key_index = st.session_state.api_key_index
        current_key = API_KEYS[current_key_index]
        
        # Verificar si la clave actual está activa
        if st.session_state.api_key_status.get(current_key, True):
            # Si está activa, avanzamos el índice para la próxima vez y la devolvemos
            st.session_state.api_key_index = (current_key_index + 1) % num_keys
            return current_key, current_key_index
        
        # Si la clave actual no está activa, simplemente avanzamos al siguiente índice
        st.session_state.api_key_index = (current_key_index + 1) % num_keys
        
        # Si hemos dado una vuelta completa y no encontramos ninguna clave activa, salimos
        if st.session_state.api_key_index == initial_index:
            break

    return None, None # No hay keys disponibles

def get_event_status(commence_time_str):
    """
    Clasifica un evento como 'En Vivo' (si ya empezó) o 'Pre-Partido' (en las próximas 48h).
    Ignora eventos que están muy lejos en el futuro.
    """
    # Manejar el formato Z para que datetime.fromisoformat funcione correctamente
    commence_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
    now_utc = datetime.now(timezone.utc)
    
    if commence_time < now_utc:
        return "🔴 En Vivo"
    elif commence_time < now_utc + timedelta(hours=48): # Considerar pre-partido hasta 48h antes
        return "🟢 Pre-Partido"
    else:
        return None # Eventos muy lejanos no son relevantes para surebets inmediatas

def find_surebets_task(sport_name, sport_key, market_key, api_key, api_key_idx):
    """
    Busca surebets para un deporte y mercado específicos.
    Esta función se ejecutará en un hilo secundario.
    Devuelve las surebets encontradas y el estado de la API key utilizada.
    NO DEBE ACCEDER DIRECTAMENTE A st.session_state.
    """
    surebets_found = []
    api_key_depleted = False # Bandera para indicar si esta API key se agotó
    error_message = None
    remaining_requests = None
    used_requests = None
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        "apiKey": api_key,
        "regions": "us,eu,uk,au", # Regiones de casas de apuestas a consultar
        "markets": market_key,
        "oddsFormat": "decimal",
        "bookmakers": "all" # Busca en todas las casas disponibles para el deporte
    }
    
    try:
        response = requests.get(url, params=params, timeout=30) # Timeout de 30 segundos
        
        # --- Lógica de Manejo de Errores de la API ---
        if response.status_code == 401: # Unauthorized - API Key inválida
            api_key_depleted = True
            error_message = "API Key inválida o no autorizada."
            return surebets_found, api_key_depleted, error_message, None, None
        
        if response.status_code == 402: # Payment Required - Límite de créditos alcanzado
            api_key_depleted = True
            error_message = "Créditos de API Key agotados."
            return surebets_found, api_key_depleted, error_message, None, None
        
        if response.status_code == 404: # Not Found - Deporte o mercado no encontrado
            error_message = f"Deporte o mercado '{sport_key}' no encontrado."
            return surebets_found, api_key_depleted, error_message, None, None
        
        if response.status_code == 422: # Unprocessable Entity - Parámetros inválidos
            error_message = f"Parámetros de solicitud inválidos para '{sport_key}'."
            return surebets_found, api_key_depleted, error_message, None, None
        
        if response.status_code >= 500: # Server Error
            error_message = f"Error del servidor API para '{sport_key}'. Código: {response.status_code}"
            return surebets_found, api_key_depleted, error_message, None, None

        response.raise_for_status() # Lanza una excepción para otros errores HTTP >= 400
        data = response.json()
        
        # Obtener información de uso de la API para devolverla
        remaining_requests = response.headers.get('x-requests-remaining', 'N/A')
        used_requests = response.headers.get('x-requests-used', 'N/A')

        # --- Lógica Principal de Búsqueda de Surebets por Mercado ---
        for event in data:
            status = get_event_status(event['commence_time'])
            if not status:
                continue # Saltar eventos no relevantes (muy lejanos en el futuro)

            home_team = event['home_team']
            away_team = event['away_team']
            
            # Lógica para H2H (Moneyline)
            if market_key == "h2h":
                best_odds = {
                    home_team: {'price': 0, 'bookmaker': ''}, 
                    away_team: {'price': 0, 'bookmaker': ''}
                }
                team_names = {home_team, away_team}

                for bookmaker in event['bookmakers']:
                    h2h_market = next((m for m in bookmaker['markets'] if m['key'] == market_key), None)
                    if not h2h_market:
                        continue

                    current_bookmaker_outcomes = {}
                    for outcome in h2h_market['outcomes']:
                        outcome_name = outcome['name']
                        price = outcome['price']
                        if outcome_name in team_names:
                            current_bookmaker_outcomes[outcome_name] = price
                    
                    if home_team in current_bookmaker_outcomes and away_team in current_bookmaker_outcomes:
                        if current_bookmaker_outcomes[home_team] > best_odds[home_team]['price']:
                            best_odds[home_team]['price'] = current_bookmaker_outcomes[home_team]
                            best_odds[home_team]['bookmaker'] = bookmaker['title']
                        
                        if current_bookmaker_outcomes[away_team] > best_odds[away_team]['price']:
                            best_odds[away_team]['price'] = current_bookmaker_outcomes[away_team]
                            best_odds[away_team]['bookmaker'] = bookmaker['title']
                
                odds1 = best_odds[home_team]['price']
                odds2 = best_odds[away_team]['price']

                if odds1 > 0 and odds2 > 0:
                    utilidad = (1 - (1/odds1 + 1/odds2)) * 100
                else:
                    continue

                if utilidad > 0.01: 
                    surebets_found.append({
                        "Deporte": sport_name,
                        "Liga/Torneo": event['sport_title'],
                        "Estado": status,
                        "Evento": f"{home_team} vs {away_team}",
                        "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                        "Mercado": "Ganador (Moneyline/H2H)",
                        "Utilidad (%)": f"{utilidad:.2f}%",
                        "Selección 1": home_team,
                        "Mejor Cuota 1": odds1,
                        "Casa de Apuestas 1": best_odds[home_team]['bookmaker'],
                        "Selección X": "N/A", 
                        "Mejor Cuota X": 1.01, 
                        "Casa de Apuestas X": "N/A",
                        "Selección 2": away_team,
                        "Mejor Cuota 2": odds2,
                        "Casa de Apuestas 2": best_odds[away_team]['bookmaker'],
                    })

            # Lógica para Totales (Over/Under)
            elif market_key == "totals":
                # Agrupar cuotas por 'point' (línea de total)
                best_totals_odds = {} # {point: {'over': {'price': X, 'bookmaker': Y}, 'under': {'price': A, 'bookmaker': B}}}

                for bookmaker in event['bookmakers']:
                    totals_market = next((m for m in bookmaker['markets'] if m['key'] == market_key), None)
                    if not totals_market:
                        continue
                    
                    for outcome in totals_market['outcomes']:
                        point = outcome['point']
                        name = outcome['name'] # 'Over' or 'Under'
                        price = outcome['price']

                        if point not in best_totals_odds:
                            best_totals_odds[point] = {'over': {'price': 0, 'bookmaker': ''}, 'under': {'price': 0, 'bookmaker': ''}}
                        
                        if name.lower() == 'over' and price > best_totals_odds[point]['over']['price']:
                            best_totals_odds[point]['over']['price'] = price
                            best_totals_odds[point]['over']['bookmaker'] = bookmaker['title']
                        elif name.lower() == 'under' and price > best_totals_odds[point]['under']['price']:
                            best_totals_odds[point]['under']['price'] = price
                            best_totals_odds[point]['under']['bookmaker'] = bookmaker['title']
                
                for point, odds_data in best_totals_odds.items():
                    over_odds = odds_data['over']['price']
                    under_odds = odds_data['under']['price']

                    if over_odds > 0 and under_odds > 0:
                        utilidad = (1 - (1/over_odds + 1/under_odds)) * 100
                    else:
                        continue

                    if utilidad > 0.01:
                        surebets_found.append({
                            "Deporte": sport_name,
                            "Liga/Torneo": event['sport_title'],
                            "Estado": status,
                            "Evento": f"{home_team} vs {away_team} (Total: {point})",
                            "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                            "Mercado": f"Totales (Over/Under {point})",
                            "Utilidad (%)": f"{utilidad:.2f}%",
                            "Selección 1": f"Over {point}",
                            "Mejor Cuota 1": over_odds,
                            "Casa de Apuestas 1": odds_data['over']['bookmaker'],
                            "Selección X": "N/A", 
                            "Mejor Cuota X": 1.01, 
                            "Casa de Apuestas X": "N/A",
                            "Selección 2": f"Under {point}",
                            "Mejor Cuota 2": under_odds,
                            "Casa de Apuestas 2": odds_data['under']['bookmaker'],
                        })

            # Lógica para Spreads (Hándicap)
            elif market_key == "spreads":
                # Agrupar cuotas por 'point' (línea de hándicap)
                best_spreads_odds = {} # {point: {'home_team_spread': {'price': X, 'bookmaker': Y}, 'away_team_spread': {'price': A, 'bookmaker': B}}}

                for bookmaker in event['bookmakers']:
                    spreads_market = next((m for m in bookmaker['markets'] if m['key'] == market_key), None)
                    if not spreads_market:
                        continue
                    
                    for outcome in spreads_market['outcomes']:
                        point = outcome['point']
                        name = outcome['name'] # Nombre del equipo
                        price = outcome['price']

                        # La API devuelve el hándicap para el equipo.
                        # Necesitamos encontrar la cuota opuesta para el mismo 'point'.
                        # Por ejemplo, si un equipo tiene +1.5, el otro tendrá -1.5.
                        # O si un equipo tiene -7.5, el otro tendrá +7.5.
                        # La clave para la surebet está en el 'point' y el 'name' (equipo).

                        # Normalizar el 'point' para que sea el mismo para ambos lados del spread
                        # Por ejemplo, si es -1.5 para el local, es +1.5 para el visitante.
                        # Usamos el valor absoluto del punto como clave para agrupar.
                        normalized_point = abs(point)

                        if normalized_point not in best_spreads_odds:
                            best_spreads_odds[normalized_point] = {
                                'home_spread': {'price': 0, 'bookmaker': '', 'point': None}, 
                                'away_spread': {'price': 0, 'bookmaker': '', 'point': None}
                            }
                        
                        if name == home_team:
                            if price > best_spreads_odds[normalized_point]['home_spread']['price']:
                                best_spreads_odds[normalized_point]['home_spread']['price'] = price
                                best_spreads_odds[normalized_point]['home_spread']['bookmaker'] = bookmaker['title']
                                best_spreads_odds[normalized_point]['home_spread']['point'] = point # Guardar el punto original
                        elif name == away_team:
                            if price > best_spreads_odds[normalized_point]['away_spread']['price']:
                                best_spreads_odds[normalized_point]['away_spread']['price'] = price
                                best_spreads_odds[normalized_point]['away_spread']['bookmaker'] = bookmaker['title']
                                best_spreads_odds[normalized_point]['away_spread']['point'] = point # Guardar el punto original
                
                for normalized_point, odds_data in best_spreads_odds.items():
                    home_spread_odds = odds_data['home_spread']['price']
                    away_spread_odds = odds_data['away_spread']['price']
                    home_point = odds_data['home_spread']['point']
                    away_point = odds_data['away_spread']['point']

                    # Asegurarse de que tenemos cuotas para ambos lados del spread y que los puntos son opuestos
                    if home_spread_odds > 0 and away_spread_odds > 0 and home_point is not None and away_point is not None and home_point == -away_point:
                        utilidad = (1 - (1/home_spread_odds + 1/away_spread_odds)) * 100
                    else:
                        continue

                    if utilidad > 0.01:
                        surebets_found.append({
                            "Deporte": sport_name,
                            "Liga/Torneo": event['sport_title'],
                            "Estado": status,
                            "Evento": f"{home_team} ({home_point}) vs {away_team} ({away_point})",
                            "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                            "Mercado": f"Spreads (Hándicap)",
                            "Utilidad (%)": f"{utilidad:.2f}%",
                            "Selección 1": f"{home_team} ({home_point})",
                            "Mejor Cuota 1": home_spread_odds,
                            "Casa de Apuestas 1": odds_data['home_spread']['bookmaker'],
                            "Selección X": "N/A", 
                            "Mejor Cuota X": 1.01, 
                            "Casa de Apuestas X": "N/A",
                            "Selección 2": f"{away_team} ({away_point})",
                            "Mejor Cuota 2": away_spread_odds,
                            "Casa de Apuestas 2": odds_data['away_spread']['bookmaker'],
                        })

        # Devolver las surebets, si la key se agotó, el mensaje de error y la info de requests
        return surebets_found, api_key_depleted, error_message, remaining_requests, used_requests

    except requests.exceptions.RequestException as e:
        error_message = f"Error de conexión o API para '{sport_name}': {e}"
        return [], api_key_depleted, error_message, None, None 
    except Exception as e:
        error_message = f"Error inesperado en la tarea para '{sport_name}': {e}"
        return [], api_key_depleted, error_message, None, None

# --- Funciones de Cálculo de Surebets Manuales ---

def calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto):
    """Calcula surebet para 2 resultados (Local/Visitante o Jugador1/Jugador2)."""
    if c1_local <= 1.01 or c2_visit <= 1.01: # Cuotas mínimas para evitar divisiones por cero o cuotas irreales
        return None, None, None, None, None, None
    
    inv1 = 1 / c1_local
    inv2 = 1 / c2_visit
    total_inv = inv1 + inv2

    if total_inv < 1: # Si la suma de las inversas de las cuotas es menor a 1, hay una surebet
        stake1 = round((inv1 / total_inv) * presupuesto)
        stake2 = round((inv2 / total_inv) * presupuesto)
        
        ganancia = round(min(stake1 * c1_local, stake2 * c2_visit) - presupuesto)
        roi = round((1 - total_inv) * 100, 2)
        return stake1, stake2, ganancia, roi, c1_local, c2_visit
    return None, None, None, None, None, None

def calcular_surebet_3_resultados(c_local, c_empate, c_visitante, presupuesto):
    """Calcula surebet para 3 resultados (Local/Empate/Visitante)."""
    if c_local <= 1.01 or c_empate <= 1.01 or c_visitante <= 1.01:
        return None, None, None, None, None, None, None, None
    
    inv_local = 1 / c_local
    inv_empate = 1 / c_empate
    inv_visitante = 1 / c_visitante
    total_inv = inv_local + inv_empate + inv_visitante

    if total_inv < 1:
        stake_local = round((inv_local / total_inv) * presupuesto)
        stake_empate = round((inv_empate / total_inv) * presupuesto)
        stake_visitante = round((inv_visitante / total_inv) * presupuesto)
        
        ganancia = round(min(stake_local * c_local, stake_empate * c_empate, stake_visitante * c_visitante) - presupuesto)
        roi = round((1 - total_inv) * 100, 2)
        return stake_local, stake_empate, stake_visitante, ganancia, roi, c_local, c_empate, c_visitante
    return None, None, None, None, None, None, None, None

# --- Definición de Casas de Apuestas Predeterminadas por Divisa ---
casas_predefinidas_manual = {
    "COP": ["BetPlay", "Wplay", "Stake", "Bwin", "Betsson", "Luckia"],
    "EUR": ["Bet365", "Unibet", "Bwin", "Pinnacle", "William Hill", "888sport"],
    "USD": ["DraftKings", "FanDuel", "BetMGM", "Caesars", "PointsBet", "Barstool"],
}


# --- Interfaz de Usuario con Streamlit (Tabs) ---
tab1, tab2 = st.tabs(["🔎 Buscador de Surebets", "🧮 Calculadora Manual"])

# --- TAB 1: Buscador de Surebets ---
with tab1:
    st.header("🔎 Buscador de Surebets (Múltiples Mercados)")
    st.markdown("""
    Aquí puedes buscar surebets en tiempo real para diferentes mercados
    entre una amplia gama de casas de apuestas y los deportes seleccionados.
    """)

    st.sidebar.header("Panel de Control del Buscador")

    selected_sports = st.sidebar.multiselect(
        "Selecciona los deportes a escanear:",
        options=list(SPORTS.keys()),
        default=["Fútbol", "Baloncesto", "Tenis", "Béisbol"] # Seleccionados por defecto
    )

    selected_market_name = st.sidebar.selectbox(
        "Selecciona el mercado a escanear:",
        options=list(MARKETS.keys()),
        default="Ganador (Moneyline/H2H)"
    )
    selected_market_key = MARKETS[selected_market_name]


    if st.sidebar.button("🚀 Iniciar Búsqueda de Surebets"):
        if not selected_sports:
            st.warning("Por favor, selecciona al menos un deporte para buscar.")
        else:
            results_placeholder = st.empty() # Placeholder para mostrar los resultados
            progress_bar = st.progress(0) # Barra de progreso de la búsqueda
            status_text = st.empty() # Texto de estado de la búsqueda
            
            all_surebets = []
            total_searches = len(selected_sports) 
            search_count = 0

            # Usar ThreadPoolExecutor para paralelizar las solicitudes API
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {}
                # PREPARACIÓN DE TAREAS: Asignar una API key a cada deporte antes de enviar la tarea
                for sport_name in selected_sports:
                    api_key, api_key_idx = get_next_available_api_key_info()
                    if api_key is None:
                        st.error("❌ Todas las API Keys disponibles han agotado sus créditos o están marcadas como agotadas. Por favor, actualiza tus API Keys o espera el reseteo diario.")
                        break # Salir del bucle si no hay más keys activas
                    
                    # Enviar la tarea al executor. La función find_surebets_task recibe la key y su índice.
                    futures[executor.submit(find_surebets_task, sport_name, SPORTS[sport_name], selected_market_key, api_key, api_key_idx)] = (sport_name, api_key, api_key_idx)
                
                # PROCESAR RESULTADOS: A medida que los futuros se completan, manejar los resultados en el hilo principal
                for future in concurrent.futures.as_completed(futures):
                    sport_name, used_api_key, used_api_key_idx = futures[future]
                    try:
                        # Los resultados de find_surebets_task son: surebets_found, api_key_depleted, error_message, remaining_requests, used_requests
                        surebets_for_sport, key_depleted_in_thread, task_error_message, remaining_reqs, used_reqs = future.result() 
                        
                        # AHORA, en el HILO PRINCIPAL, actualizamos st.session_state y mostramos mensajes
                        if key_depleted_in_thread:
                            st.session_state.api_key_status[used_api_key] = False
                            if used_api_key not in st.session_state.depleted_api_keys:
                                st.session_state.depleted_api_keys.append(used_api_key)
                            st.warning(f"⚠️ La API Key #{used_api_key_idx} (termina en {used_api_key[-4:]}) parece haber agotado sus créditos. Error: {task_error_message}")
                        elif task_error_message:
                            st.error(f"Error para '{sport_name}' con API Key {used_api_key_idx} ({used_api_key[-4:]}): {task_error_message}")
                        else:
                            # Mostrar información de uso de la API en la barra lateral para la key usada
                            st.sidebar.info(f"API Key #{used_api_key_idx} (usando {used_api_key[-4:]}..) | Usados: {used_reqs} | Restantes: {remaining_reqs}")

                        if surebets_for_sport:
                            all_surebets.extend(surebets_for_sport)
                        
                        search_count += 1
                        progress = search_count / total_searches if total_searches > 0 else 1
                        progress_bar.progress(progress)
                        status_text.text(f"Completado: **{sport_name}**. Procesando... {search_count}/{total_searches}")
                        
                    except Exception as exc:
                        # Captura cualquier otro error inesperado que pueda ocurrir al procesar el resultado del futuro
                        st.error(f"Error inesperado al procesar los resultados de '{sport_name}': {exc}. Por favor, revisa los logs.")
                        
            # --- FIN DE LA LÓGICA DE PARALELIZACIÓN ---

            # Mensaje final al terminar todas las búsquedas
            status_text.success("¡Búsqueda completada!")
            progress_bar.empty() # Ocultar barra de progreso al finalizar

            with results_placeholder.container():
                if not all_surebets:
                    # Mensaje más específico si no hay resultados debido a keys o no-surebets
                    if any(not status for status in st.session_state.api_key_status.values()):
                         st.warning("No se encontraron surebets. Es posible que algunas API Keys hayan agotado sus créditos o no haya surebets disponibles para los deportes y mercado seleccionados.")
                    else:
                        st.warning(f"No se encontraron surebets para los deportes y mercado '{selected_market_name}' seleccionados.")
                else:
                    st.success(f"¡Se encontraron **{len(all_surebets)}** oportunidades de surebet!")
                    
                    df = pd.DataFrame(all_surebets)
                    
                    st.subheader("Resultados de Surebets Encontradas")
                    st.info("Haz clic en 'Cargar en Calculadora' para llevar los datos de una surebet específica a la calculadora manual.")
                    
                    # Mostrar resultados individuales con botón para cargar en calculadora
                    for i, row in df.iterrows():
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"**Evento:** {row['Evento']} | **Deporte:** {row['Deporte']} | **Liga:** {row['Liga/Torneo']} | **Fecha:** {row['Fecha (UTC)']}")
                            st.markdown(f"**Mercado:** {row['Mercado']} | **Utilidad:** **{row['Utilidad (%)']}**")
                            # Formato específico para H2H, Totales o Spreads
                            if "Selección 2" in row and row["Selección 2"] != "N/A":
                                st.markdown(f"**{row['Selección 1']}:** {row['Mejor Cuota 1']} ({row['Casa de Apuestas 1']}) | **{row['Selección 2']}:** {row['Mejor Cuota 2']} ({row['Casa de Apuestas 2']})")
                            else: # En caso de que se necesite un formato más genérico si hay mercados con más de 2 selecciones
                                st.markdown(f"**Cuota 1:** {row['Mejor Cuota 1']} ({row['Casa de Apuestas 1']})")
                                # Puedes añadir más selecciones si los mercados lo requieren
                        with col2:
                            if st.button("Cargar en Calculadora", key=f"load_surebet_{i}"):
                                # Cargar datos en el estado de sesión para la calculadora
                                st.session_state.calc_event_data = {
                                    'Evento': row['Evento'],
                                    'Fecha (UTC)': row['Fecha (UTC)'],
                                    'Mercado': row['Mercado'], 
                                    'Cuota Local': row['Mejor Cuota 1'],
                                    'Cuota Empate': 1.01, # Resetear para H2H/Totales/Spreads cargado (si no aplica)
                                    'Cuota Visitante': row['Mejor Cuota 2'],
                                    'Selección 1': row['Selección 1'],
                                    'Selección 2': row['Selección 2'],
                                    'Casa Local': row['Casa de Apuestas 1'],
                                    'Casa Empate': 'N/A', # Resetear para H2H/Totales/Spreads cargado
                                    'Casa Visitante': row['Casa de Apuestas 2']
                                }
                                # Precargar la primera posición de la calculadora manual con los datos
                                st.session_state.cuotas_local_manual[0] = row['Mejor Cuota 1']
                                st.session_state.nombres_casas_manual[0] = row['Casa de Apuestas 1']
                                st.session_state.cuotas_visitante_manual[0] = row['Mejor Cuota 2']
                                st.session_state.nombres_casas_manual[1] = row['Casa de Apuestas 2'] 
                                # Asegurar que los campos de empate se reseteen si se cambia a H2H/Totales/Spreads
                                st.session_state.cuotas_empate_manual[0] = 1.01
                                st.session_state.nombres_casas_manual[2] = "N/A"

                                st.toast("Evento cargado en la calculadora. ¡Dirígete a la pestaña 'Calculadora Manual' para ajustar y calcular!")
                                st.rerun() # Recargar la página para que la calculadora muestre los datos

# --- TAB 2: Calculadora Manual ---
with tab2:
    st.header("🧮 Calculadora Manual de Surebets (hasta 6 casas)")
    st.markdown("""
    Ingresa o ajusta las cuotas y el capital para calcular la distribución óptima de apuestas.
    Los campos de evento y cuotas pueden ser rellenados automáticamente desde el buscador.
    """)

    # --- Sección de Ingreso de Evento y Configuración General ---
    st.subheader("📝 Ingresar evento y configuración")

    evento_calc = st.text_input("Nombre del evento", value=st.session_state.calc_event_data['Evento'], key="manual_evento")
    fecha_calc = st.text_input("Fecha del evento (UTC)", value=st.session_state.calc_event_data['Fecha (UTC)'], key="manual_fecha")
    
    moneda = st.selectbox("Divisa", ["COP", "EUR", "USD"], key="manual_moneda")
    presupuesto = st.number_input(f"Presupuesto total ({moneda})", min_value=10, value=100000, step=1000, format="%d", key="manual_presupuesto")

    # Opciones de mercado para la calculadora manual (se mantiene flexible para permitir 1X2 manualmente)
    tipo_mercado_options = ["2 Resultados (1/2)", "3 Resultados (1/X/2)"]
    # Establece el valor por defecto basado en el evento cargado o H2H si no hay carga
    default_market_idx = 0 if st.session_state.calc_event_data['Mercado'] == "Ganador (Moneyline/H2H)" else 1
    tipo_mercado = st.radio("Tipo de mercado", tipo_mercado_options, index=default_market_idx, key="manual_tipo_mercado")

    st.subheader("🏠 Ingresar cuotas por casa de apuestas")

    num_casas = st.slider("Número de casas a considerar", min_value=2, max_value=6, value=3, key="manual_num_casas")

    # Actualizar nombres por defecto y resetear cuotas si la divisa cambia
    if moneda != st.session_state.last_moneda_manual:
        st.session_state.nombres_casas_manual = [casas_predefinidas_manual[moneda][i] for i in range(6)]
        st.session_state.cuotas_local_manual = [1.01] * 6
        st.session_state.cuotas_empate_manual = [1.01] * 6
        st.session_state.cuotas_visitante_manual = [1.01] * 6
    st.session_state.last_moneda_manual = moneda


    casas_manual_input = []
    for i in range(num_casas):
        st.markdown(f"### Casa {i+1}")
        
        nombre_casa_default = st.session_state.nombres_casas_manual[i]
        cuota_local_default = st.session_state.cuotas_local_manual[i]
        cuota_empate_default = st.session_state.cuotas_empate_manual[i]
        cuota_visitante_default = st.session_state.cuotas_visitante_manual[i]

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            nombre = st.text_input(f"Nombre", value=nombre_casa_default, key=f"manual_nombre_{i}")
            st.session_state.nombres_casas_manual[i] = nombre
        with col2:
            cuota_local = st.number_input(f"Cuota Local / Jugador 1", min_value=1.01, value=cuota_local_default, step=0.01, key=f"manual_local_{i}")
            st.session_state.cuotas_local_manual[i] = cuota_local
        
        cuota_empate = 1.01 # Valor por defecto si no se muestra el campo
        if tipo_mercado == "3 Resultados (1/X/2)":
            with col3:
                cuota_empate = st.number_input(f"Cuota Empate", min_value=1.01, value=cuota_empate_default, step=0.01, key=f"manual_empate_{i}")
                st.session_state.cuotas_empate_manual[i] = cuota_empate
        else: 
             # Si se cambia a 2 resultados, asegúrate de que la cuota de empate esté en su valor neutro
             if st.session_state.cuotas_empate_manual[i] != 1.01: 
                 st.session_state.cuotas_empate_manual[i] = 1.01


        with col4:
            cuota_visitante = st.number_input(f"Cuota Visitante / Jugador 2", min_value=1.01, value=cuota_visitante_default, step=0.01, key=f"manual_visitante_{i}")
            st.session_state.cuotas_visitante_manual[i] = cuota_visitante
        
        casas_manual_input.append((nombre, cuota_local, cuota_empate, cuota_visitante))

    st.markdown("---")

    # --- Lógica de Cálculo y Muestra de Resultados Manuales ---
    if st.button("🔍 Calcular Surebet Manualmente", key="calcular_manual_btn"):
        mejores = []

        if tipo_mercado == "2 Resultados (1/2)":
            # Para 2 resultados (H2H), necesitamos seleccionar la mejor cuota para cada lado
            # de casas potencialmente diferentes. Se prueban todas las combinaciones de 2 casas.
            for i in range(num_casas):
                for j in range(num_casas):
                    if i == j: # Las cuotas para la surebet deben venir de casas distintas para H2H
                        continue
                    
                    nombre1, c1_local, _, _ = casas_manual_input[i]
                    nombre2, _, _, c2_visit = casas_manual_input[j]

                    # Calcula la surebet con la cuota de Local de la casa i y la de Visitante de la casa j
                    stake1, stake2, ganancia, roi, c_l, c_v = calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto)
                    if ganancia is not None: # Si se encontró una surebet rentable
                        mejores.append({
                            "tipo": "2 Resultados",
                            "apuesta1_casa": nombre1,
                            "apuesta1_rol": st.session_state.calc_event_data['Selección 1'],
                            "apuesta1_cuota": c_l,
                            "apuesta1_stake": stake1,
                            "apuesta2_casa": nombre2,
                            "apuesta2_rol": st.session_state.calc_event_data['Selección 2'],
                            "apuesta2_cuota": c_v,
                            "apuesta2_stake": stake2,
                            "ganancia": ganancia,
                            "roi": roi
                        })
                    
        else: # 3 Resultados (1/X/2)
            # Para 3 resultados (1X2), se seleccionan las mejores cuotas para Local, Empate y Visitante.
            # Se prueban todas las combinaciones posibles de 3 casas.
            # Se utiliza `combinations` para obtener grupos únicos de índices de casas.
            # Luego, se asigna cada índice a un rol (Local, Empate, Visitante).
            # Para simplificar la lógica y evitar la explosión combinatoria de 3 ciclos anidados,
            # podríamos buscar directamente las 3 mejores cuotas (una por resultado) entre todas las casas.
            # Sin embargo, el enfoque actual de 3 loops asegura que cada combinación posible de casas sea evaluada
            # lo cual es más exhaustivo, aunque potencialmente más lento con muchas casas.
            for i_l in range(num_casas):
                for i_x in range(num_casas):
                    for i_v in range(num_casas):
                        # Las casas para 1, X y 2 pueden ser la misma o diferentes
                        # Depende de dónde se encuentre la mejor cuota para cada resultado
                        nombre_l, c_l, _, _ = casas_manual_input[i_l]
                        nombre_x, _, c_x, _ = casas_manual_input[i_x]
                        nombre_v, _, _, c_v = casas_manual_input[i_v]
                        
                        stake_l, stake_x, stake_v, ganancia, roi, cuota_l, cuota_x, cuota_v = \
                            calcular_surebet_3_resultados(c_l, c_x, c_v, presupuesto)

                        if ganancia is not None:
                            mejores.append({
                                "tipo": "3 Resultados",
                                "apuesta1_casa": nombre_l,
                                "apuesta1_rol": st.session_state.calc_event_data['Selección 1'],
                                "apuesta1_cuota": cuota_l,
                                "apuesta1_stake": stake_l,
                                "apuesta2_casa": nombre_x,
                                "apuesta2_rol": "Empate",
                                "apuesta2_cuota": cuota_x,
                                "apuesta2_stake": stake_x,
                                "apuesta3_casa": nombre_v,
                                "apuesta3_rol": st.session_state.calc_event_data['Selección 2'],
                                "apuesta3_cuota": cuota_v,
                                "apuesta3_stake": stake_v,
                                "ganancia": ganancia,
                                "roi": roi
                            })

        # --- Mostrar el Mejor Resultado Encontrado Manualmente ---
        if mejores:
            st.success("✅ ¡Surebet encontrada manualmente!")
            
            # Ordenar por ROI para encontrar la mejor surebet
            top_surebet = sorted(mejores, key=lambda x: x["roi"], reverse=True)[0]

            st.markdown("---")
            st.subheader("🏆 La Mejor Surebet Encontrada (Manual)")
            st.markdown(f"**🎯 Evento:** {evento_calc}")
            st.markdown(f"**📅 Fecha:** {fecha_calc}")
            st.markdown(f"📈 ROI: **{top_surebet['roi']}%**")
            st.markdown(f"💰 Ganancia asegurada: **${top_surebet['ganancia']:,d} {moneda}**")
            st.markdown("---")

            st.subheader("🏦 Apuestas a Realizar:")
            
            if top_surebet['tipo'] == "2 Resultados":
                st.markdown(f"""
- **{top_surebet['apuesta1_casa']}** (para **{top_surebet['apuesta1_rol']}**):
  - Cuota: {top_surebet['apuesta1_cuota']}
  - **Apostar: ${top_surebet['apuesta1_stake']:,d} {moneda}**
- **{top_surebet['apuesta2_casa']}** (para **{top_surebet['apuesta2_rol']}**):
  - Cuota: {top_surebet['apuesta2_cuota']}
  - **Apostar: ${top_surebet['apuesta2_stake']:,d} {moneda}**
""")
            elif top_surebet['tipo'] == "3 Resultados":
                st.markdown(f"""
- **{top_surebet['apuesta1_casa']}** (para **{top_surebet['apuesta1_rol']}**):
  - Cuota: {top_surebet['apuesta1_cuota']}
  - **Apostar: ${top_surebet['apuesta1_stake']:,d} {moneda}**
- **{top_surebet['apuesta2_casa']}** (para **{top_surebet['apuesta2_rol']}**):
  - Cuota: {top_surebet['apuesta2_cuota']}
  - **Apostar: ${top_surebet['apuesta2_stake']:,d} {moneda}**
- **{top_surebet['apuesta3_casa']}** (para **{top_surebet['apuesta3_rol']}**):
  - Cuota: {top_surebet['apuesta3_cuota']}
  - **Apostar: ${top_surebet['apuesta3_stake']:,d} {moneda}**
""")
            
        else:
            st.warning("❌ No se encontraron combinaciones rentables para el tipo de mercado seleccionado con las cuotas ingresadas. Intenta ajustar los valores.")

    st.markdown("---")
    st.info("⚠️ **¡Advertencia Importante!** Las cuotas en las casas de apuestas cambian **constantemente**. Siempre verifica las cuotas directamente en las casas antes de realizar cualquier apuesta.")


# --- Información de API en la barra lateral ---
st.sidebar.markdown("---")
st.sidebar.header("Información de API")
st.sidebar.write(f"Total de API Keys disponibles: **{len(API_KEYS)}**")

# Mostrar la próxima API Key a usar sin consumirla
# Se obtiene de nuevo porque la función `get_next_available_api_key_info()` avanza el índice.
# Esto asegura que el display siempre muestre la siguiente key que *será* usada.
temp_key_idx = st.session_state.api_key_index
temp_key = API_KEYS[temp_key_idx] if API_KEYS else None
if st.session_state.api_key_status.get(temp_key, False): # Verificar si la clave es activa para mostrarla como "próxima"
    st.sidebar.info(f"Próxima API Key a usar: #{temp_key_idx} (termina en **{temp_key[-4:]}**)")
else:
    # Si la clave en el índice actual no está activa, buscar la primera activa para mostrarla como "próxima"
    found_active_for_display = False
    for i in range(len(API_KEYS)):
        display_key_idx = (temp_key_idx + i) % len(API_KEYS)
        display_key = API_KEYS[display_key_idx]
        if st.session_state.api_key_status.get(display_key, False):
            st.sidebar.info(f"Próxima API Key a usar: #{display_key_idx} (termina en **{display_key[-4:]}**)")
            found_active_for_display = True
            break
    if not found_active_for_display:
        st.sidebar.warning("🚫 No quedan API Keys activas para usar. Por favor, actualiza o espera el reseteo.")

st.sidebar.markdown("---")
st.sidebar.subheader("Claves API Agotadas")
if st.session_state.depleted_api_keys:
    for depleted_key in st.session_state.depleted_api_keys:
        st.sidebar.error(f"❌ Agotada: **{depleted_key[-4:]}**")
else:
    st.sidebar.success("✅ Todas las API Keys están activas (o no se han detectado agotadas aún).")
st.sidebar.markdown("---")
st.sidebar.markdown("Autor: **JAPH99** 🇨🇴")
