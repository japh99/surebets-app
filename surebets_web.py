import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import time
from itertools import combinations

# --- Configuración de la Página y Título ---
st.set_page_config(
    page_title="Surebets: Buscador & Calculadora",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Buscador y Calculadora de Surebets 1X2")
st.markdown("""
Esta aplicación **detecta oportunidades de surebets (arbitraje deportivo)** en tiempo real exclusivamente para el **mercado 1X2 (Resultado Final)** y te permite **calcularlas** de forma sencilla.
""")

# --- Lista de API Keys (Misma que la anterior) ---
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
    "Béisbol": "baseball_mlb",
}

# --- Diccionario de Mercados (SOLO 1X2) ---
MARKETS = {
    "1X2 (Resultado Final)": "full_time_result",
}

# --- Estado de la Sesión para API Keys y Calculadora ---
if 'api_key_index' not in st.session_state:
    st.session_state.api_key_index = 0
if 'api_key_status' not in st.session_state:
    st.session_state.api_key_status = {key: True for key in API_KEYS}
if 'depleted_api_keys' not in st.session_state:
    st.session_state.depleted_api_keys = []

# Estado para la calculadora (lo inicializamos con valores por defecto)
if 'calc_event_data' not in st.session_state:
    st.session_state.calc_event_data = {
        'Evento': 'Ej: Nacional vs Millonarios',
        'Fecha (UTC)': 'N/A',
        'Cuota Local': 1.01,
        'Cuota Empate': 1.01,
        'Cuota Visitante': 1.01,
        'Selección 1': 'Equipo Local',
        'Selección 2': 'Equipo Visitante',
        'Casa Local': 'Casa de Apuestas 1',
        'Casa Empate': 'Casa de Apuestas 2',
        'Casa Visitante': 'Casa de Apuestas 3'
    }
# Estado para la calculadora manual
if 'nombres_casas_manual' not in st.session_state:
    st.session_state.nombres_casas_manual = ["Casa 1", "Casa 2", "Casa 3", "Casa 4", "Casa 5", "Casa 6"]
if 'cuotas_local_manual' not in st.session_state:
    st.session_state.cuotas_local_manual = [1.01] * 6
if 'cuotas_empate_manual' not in st.session_state:
    st.session_state.cuotas_empate_manual = [1.01] * 6
if 'cuotas_visitante_manual' not in st.session_state:
    st.session_state.cuotas_visitante_manual = [1.01] * 6
if 'last_moneda_manual' not in st.session_state:
    st.session_state.last_moneda_manual = "COP" # Default para la calculadora manual

# --- Funciones Auxiliares del Buscador ---
def get_next_available_api_key_info():
    """Obtiene la próxima API key disponible y su índice."""
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

def find_surebets_for_sport_1x2(sport_name, sport_key, api_key, api_key_idx, min_surebet_profit_pct):
    """Busca surebets exclusivamente para el mercado 1X2."""
    surebets_found = []
    selected_market_key = "full_time_result"
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    
    params = {
        "apiKey": api_key,
        "regions": "us,eu,uk,au",
        "markets": selected_market_key,
        "oddsFormat": "decimal",
        "bookmakers": "all" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code in [401, 402]:
            st.session_state.api_key_status[api_key] = False
            if api_key not in st.session_state.depleted_api_keys:
                st.session_state.depleted_api_keys.append(api_key)
            st.error(f"⚠️ **Error: La API Key #{api_key_idx} (últimos 4 digitos: {api_key[-4:]}) ha agotado sus créditos.**")
            return []
        
        if response.status_code == 404:
            st.error(f"⚠️ **Error 404 para {sport_name} en '{selected_market_key}'**: URL no encontrada.")
            return []
        
        if response.status_code == 422: 
            st.error(f"⚠️ **Error 422 para {sport_name} en '{selected_market_key}'**: Parámetros de solicitud inválidos.")
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
            
            best_odds_1x2 = {
                home_team: {'price': 0, 'bookmaker': ''}, 
                'Draw': {'price': 0, 'bookmaker': ''}, 
                away_team: {'price': 0, 'bookmaker': ''}
            }
            expected_outcomes = {home_team, 'Draw', away_team}

            for bookmaker in event['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == selected_market_key:
                        found_outcomes_for_bookmaker = set()
                        current_bookmaker_outcomes = {}
                        
                        for outcome in market['outcomes']:
                            outcome_name = outcome['name']
                            price = outcome['price']
                            
                            if outcome_name in expected_outcomes:
                                current_bookmaker_outcomes[outcome_name] = price
                                found_outcomes_for_bookmaker.add(outcome_name)
                        
                        if found_outcomes_for_bookmaker == expected_outcomes:
                            for outcome_key, price_val in current_bookmaker_outcomes.items():
                                if price_val > best_odds_1x2[outcome_key]['price']:
                                    best_odds_1x2[outcome_key]['price'] = price_val
                                    best_odds_1x2[outcome_key]['bookmaker'] = bookmaker['title']
                        break 

            odds1 = best_odds_1x2[home_team]['price']
            oddsX = best_odds_1x2['Draw']['price']
            odds2 = best_odds_1x2[away_team]['price']

            if odds1 > 0 and oddsX > 0 and odds2 > 0:
                utilidad = (1 - (1/odds1 + 1/oddsX + 1/odds2)) * 100
                
                if utilidad > min_surebet_profit_pct:
                    surebets_found.append({
                        "Deporte": sport_name,
                        "Liga/Torneo": event['sport_title'],
                        "Estado": status,
                        "Evento": f"{home_team} vs {away_team}",
                        "Fecha (UTC)": datetime.fromisoformat(event['commence_time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M'),
                        "Utilidad (%)": f"{utilidad:.2f}%",
                        "Selección 1": home_team,
                        "Mejor Cuota 1": odds1,
                        "Casa de Apuestas 1": best_odds_1x2[home_team]['bookmaker'],
                        "Selección X": "Empate",
                        "Mejor Cuota X": oddsX,
                        "Casa de Apuestas X": best_odds_1x2['Draw']['bookmaker'],
                        "Selección 2": away_team,
                        "Mejor Cuota 2": odds2,
                        "Casa de Apuestas 2": best_odds_1x2[away_team]['bookmaker'],
                    })
        return surebets_found

    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión o API para {sport_name} en mercado '{selected_market_key}': {e}")
        return []
    except Exception as e:
        st.warning(f"No se encontraron datos o ocurrió un error inesperado para {sport_name} en mercado '{selected_market_key}': {e}")
        return []

# --- Funciones de Cálculo de Surebets (de tu código) ---

def calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto):
    """Calcula surebet para 2 resultados (Local/Visitante)."""
    if c1_local <= 1.01 or c2_visit <= 1.01:
        return None, None, None, None

    inv1 = 1 / c1_local
    inv2 = 1 / c2_visit
    total_inv = inv1 + inv2

    if total_inv < 1:
        stake1 = round((inv1 / total_inv) * presupuesto)
        stake2 = round((inv2 / total_inv) * presupuesto)
        
        ganancia = round(min(stake1 * c1_local, stake2 * c2_visit) - presupuesto)
        roi = round((1 - total_inv) * 100, 2)
        return stake1, stake2, ganancia, roi
    return None, None, None, None

def calcular_surebet_3_resultados(c_local, c_empate, c_visitante, presupuesto):
    """Calcula surebet para 3 resultados (Local/Empate/Visitante) entre 3 cuotas."""
    if c_local <= 1.01 or c_empate <= 1.01 or c_visitante <= 1.01:
        return None, None, None, None, None
    
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
        return stake_local, stake_empate, stake_visitante, ganancia, roi
    return None, None, None, None, None


# --- Secciones de la Aplicación con Tabs ---
tab1, tab2 = st.tabs(["🔎 Buscador de Surebets 1X2", "🧮 Calculadora Manual"])

with tab1:
    st.header("🔎 Buscador de Surebets 1X2 (Resultado Final)")
    st.markdown("""
    Aquí puedes buscar surebets en tiempo real para el mercado 1X2.
    """)

    st.sidebar.header("Panel de Control del Buscador")

    selected_sports = st.sidebar.multiselect(
        "Selecciona los deportes a escanear (solo se buscará 1X2):",
        options=list(SPORTS.keys()),
        default=["Fútbol"]
    )

    st.sidebar.markdown("**Mercado seleccionado: 1X2 (Resultado Final)**")
    st.sidebar.markdown("*(Este mercado se busca por defecto)*")

    min_surebet_profit_pct = st.sidebar.slider(
        "Utilidad mínima de Surebet (%)",
        min_value=0.0,
        max_value=5.0,
        value=0.5, 
        step=0.1,
        help="Define el porcentaje mínimo de ganancia. Se recomienda 0.5% o más para mayor estabilidad."
    )

    if st.sidebar.button("🚀 Iniciar Búsqueda de Surebets 1X2"):
        if not selected_sports:
            st.warning("Por favor, selecciona al menos un deporte para buscar en el mercado 1X2.")
        else:
            results_placeholder = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_surebets = []
            total_searches = len(selected_sports) 
            search_count = 0

            for sport_name in selected_sports:
                sport_key = SPORTS[sport_name]

                if sport_key != 'soccer':
                    st.warning(f"El mercado '1X2' es principalmente para fútbol. Pocos resultados para '{sport_name}'.")
                
                api_key, api_key_idx = get_next_available_api_key_info()
                
                if api_key is None:
                    st.error("❌ Todas las API Keys disponibles han agotado sus créditos.")
                    break 
                
                status_text.text(f"Buscando en: {sport_name} - Mercado: 1X2 (todas las ligas) usando API Key #{api_key_idx}...")
                
                sport_surebets = find_surebets_for_sport_1x2(sport_name, sport_key, api_key, api_key_idx, min_surebet_profit_pct)
                
                if sport_surebets:
                    all_surebets.extend(sport_surebets)
                
                search_count += 1
                progress = search_count / total_searches if total_searches > 0 else 1
                progress_bar.progress(progress)
                time.sleep(1) 

            if api_key is not None:
                status_text.success("¡Búsqueda de 1X2 completada!")
            progress_bar.empty()

            with results_placeholder.container():
                if not all_surebets:
                    st.warning("No se encontraron surebets en el mercado 1X2 para los deportes seleccionados, o hubo problemas con la API.")
                else:
                    st.success(f"¡Se encontraron {len(all_surebets)} oportunidades de surebet 1X2!")
                    
                    df = pd.DataFrame(all_surebets)
                    
                    st.subheader("Resultados de Surebets 1X2 Encontradas")
                    st.info("Haz clic en 'Cargar en Calculadora' para llevar los datos de una surebet a la calculadora manual.")
                    
                    # Mostrar cada surebet con un botón "Cargar en Calculadora"
                    for i, row in df.iterrows():
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"**Evento:** {row['Evento']} | **Deporte:** {row['Deporte']} | **Liga:** {row['Liga/Torneo']} | **Fecha:** {row['Fecha (UTC)']}")
                            st.markdown(f"**Utilidad:** {row['Utilidad (%)']} | **Local:** {row['Mejor Cuota 1']} ({row['Casa de Apuestas 1']}) | **Empate:** {row['Mejor Cuota X']} ({row['Casa de Apuestas X']}) | **Visitante:** {row['Mejor Cuota 2']} ({row['Casa de Apuestas 2']})")
                        with col2:
                            if st.button("Cargar en Calculadora", key=f"load_surebet_{i}"):
                                st.session_state.calc_event_data = {
                                    'Evento': row['Evento'],
                                    'Fecha (UTC)': row['Fecha (UTC)'],
                                    'Cuota Local': row['Mejor Cuota 1'],
                                    'Cuota Empate': row['Mejor Cuota X'],
                                    'Cuota Visitante': row['Mejor Cuota 2'],
                                    'Selección 1': row['Selección 1'],
                                    'Selección 2': row['Selección 2'],
                                    'Casa Local': row['Casa de Apuestas 1'],
                                    'Casa Empate': row['Casa de Apuestas X'],
                                    'Casa Visitante': row['Casa de Apuestas 2']
                                }
                                # También precargar las cuotas en el estado de la calculadora manual
                                # Esto es para el caso en que el usuario no cambie el número de casas y quiera usar las cuotas precargadas
                                st.session_state.cuotas_local_manual[0] = row['Mejor Cuota 1']
                                st.session_state.cuotas_empate_manual[0] = row['Mejor Cuota X']
                                st.session_state.cuotas_visitante_manual[0] = row['Mejor Cuota 2']
                                st.session_state.nombres_casas_manual[0] = row['Casa de Apuestas 1']
                                st.session_state.nombres_casas_manual[1] = row['Casa de Apuestas X']
                                st.session_state.nombres_casas_manual[2] = row['Casa de Apuestas 2']


                                st.toast("Evento cargado en la calculadora. ¡Dirígete a la pestaña 'Calculadora Manual'!")
                                # st.rerun() # Esto recargará la página para actualizar la calculadora si es necesario
                                # Para cambiar de tab automáticamente:
                                st.session_state.active_tab = "Calculadora Manual"


with tab2:
    st.header("🧮 Calculadora Manual de Surebets (hasta 6 casas)")
    st.markdown("""
    Ingresa o ajusta las cuotas y el capital para calcular la distribución óptima de apuestas.
    Los campos de evento y cuotas pueden ser rellenados automáticamente desde el buscador.
    """)

    # --- Sección de Ingreso de Evento y Configuración (de tu código) ---
    st.subheader("📝 Ingresar evento y configuración")

    # Autocompletado del nombre del evento y fecha
    evento_calc = st.text_input("Nombre del evento", value=st.session_state.calc_event_data['Evento'], key="manual_evento")
    fecha_calc = st.text_input("Fecha del evento (UTC)", value=st.session_state.calc_event_data['Fecha (UTC)'], key="manual_fecha")
    
    moneda = st.selectbox("Divisa", ["COP", "EUR", "USD"], key="manual_moneda")
    presupuesto = st.number_input(f"Presupuesto total ({moneda})", min_value=10, value=100000, step=1000, format="%d", key="manual_presupuesto")

    # Opciones de mercado (fijo en 3 resultados para simplificar la integración con 1X2 del buscador)
    # Ya que el buscador solo es 1X2, la calculadora se enfoca en 3 resultados
    tipo_mercado = st.radio("Tipo de mercado", ["3 Resultados (1/X/2)"], index=0, key="manual_tipo_mercado") # Fijo a 3 resultados

    # Definir casas por divisa
    casas_predefinidas = {
        "COP": ["BetPlay", "Wplay", "Stake", "Bwin", "Betsson", "Luckia"],
        "EUR": ["Casa EU 1", "Casa EU 2", "Casa EU 3", "Casa EU 4", "Casa EU 5", "Casa EU 6"],
        "USD": ["Casa US 1", "Casa US 2", "Casa US 3", "Casa US 4", "Casa US 5", "Casa US 6"],
    }

    st.subheader("🏠 Ingresar cuotas por casa de apuestas")

    num_casas = st.slider("Número de casas a considerar", min_value=2, max_value=6, value=3, key="manual_num_casas")

    # Actualizar nombres por defecto si la divisa cambia (para la calculadora manual)
    if moneda != st.session_state.last_moneda_manual:
        st.session_state.nombres_casas_manual = [casas_predefinidas[moneda][i] for i in range(6)]
        st.session_state.last_moneda_manual = moneda

    casas_manual_input = []
    for i in range(num_casas):
        st.markdown(f"### Casa {i+1}")
        
        # Obtener valores por defecto del estado de la sesión (persistencia)
        nombre_casa_default = st.session_state.nombres_casas_manual[i]
        cuota_local_default = st.session_state.cuotas_local_manual[i]
        cuota_empate_default = st.session_state.cuotas_empate_manual[i]
        cuota_visitante_default = st.session_state.cuotas_visitante_manual[i]

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            nombre = st.text_input(f"Nombre", value=nombre_casa_default, key=f"manual_nombre_{i}")
            st.session_state.nombres_casas_manual[i] = nombre
        with col2:
            cuota_local = st.number_input(f"Cuota Local", min_value=1.01, value=cuota_local_default, step=0.01, key=f"manual_local_{i}")
            st.session_state.cuotas_local_manual[i] = cuota_local
        
        cuota_empate = 0.0 # Valor por defecto si no es un mercado de 3 resultados
        # Ahora siempre será 3 resultados en esta calculadora
        with col3:
            cuota_empate = st.number_input(f"Cuota Empate", min_value=1.01, value=cuota_empate_default, step=0.01, key=f"manual_empate_{i}")
            st.session_state.cuotas_empate_manual[i] = cuota_empate

        with col4:
            cuota_visitante = st.number_input(f"Cuota Visitante", min_value=1.01, value=cuota_visitante_default, step=0.01, key=f"manual_visitante_{i}")
            st.session_state.cuotas_visitante_manual[i] = cuota_visitante
        
        casas_manual_input.append((nombre, cuota_local, cuota_empate, cuota_visitante))

    st.markdown("---")

    # --- Lógica de Evaluación de la Calculadora Manual ---
    if st.button("🔍 Calcular Surebet Manualmente", key="calcular_manual_btn"):
        mejores = []

        # Siempre 3 Resultados en esta pestaña
        # Iterar sobre todas las combinaciones de 3 casas para (Local, Empate, Visitante)
        for i_l in range(num_casas):
            for i_x in range(num_casas):
                for i_v in range(num_casas):
                    # Considerar también la misma casa para diferentes resultados si el usuario así lo desea
                    
                    nombre_l, c_l, _, _ = casas_manual_input[i_l]
                    nombre_x, _, c_x, _ = casas_manual_input[i_x]
                    nombre_v, _, _, c_v = casas_manual_input[i_v]
                    
                    stake_l, stake_x, stake_v, ganancia, roi = \
                        calcular_surebet_3_resultados(c_l, c_x, c_v, presupuesto)

                    if ganancia is not None:
                        mejores.append({
                            "tipo": "3 Resultados",
                            "apuesta1_casa": nombre_l,
                            "apuesta1_rol": "Local",
                            "apuesta1_cuota": c_l,
                            "apuesta1_stake": stake_l,
                            "apuesta2_casa": nombre_x,
                            "apuesta2_rol": "Empate",
                            "apuesta2_cuota": c_x,
                            "apuesta2_stake": stake_x,
                            "apuesta3_casa": nombre_v,
                            "apuesta3_rol": "Visitante",
                            "apuesta3_cuota": c_v,
                            "apuesta3_stake": stake_v,
                            "ganancia": ganancia,
                            "roi": roi
                        })

        # --- Mostrar el Mejor Resultado ---
        if mejores:
            st.success("✅ ¡Surebet encontrada manualmente!")
            
            top_surebet = sorted(mejores, key=lambda x: x["roi"], reverse=True)[0]

            st.markdown("---")
            st.subheader("🏆 La Mejor Surebet Encontrada (Manual)")
            st.markdown(f"**🎯 Evento:** {evento_calc}")
            st.markdown(f"**📅 Fecha:** {fecha_calc}")
            st.markdown(f"📈 ROI: **{top_surebet['roi']}%**")
            st.markdown(f"💰 Ganancia asegurada: **${top_surebet['ganancia']:,d} {moneda}**")
            st.markdown("---")

            st.subheader("🏦 Apuestas a Realizar:")
            
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
st.sidebar.write(f"Total de API Keys disponibles: {len(API_KEYS)}")

next_key_to_use, next_key_idx_to_use = get_next_available_api_key_info()
if next_key_to_use:
    st.sidebar.info(f"Próxima API Key a usar: #{next_key_idx_to_use} (termina en **{next_key_to_use[-4:]}**)")
else:
    st.sidebar.warning("🚫 No quedan API Keys activas para usar.")

st.sidebar.markdown("---")
st.sidebar.subheader("Claves API Agotadas")
if st.session_state.depleted_api_keys:
    for depleted_key in st.session_state.depleted_api_keys:
        st.sidebar.error(f"❌ Agotada: **{depleted_key[-4:]}** - Reemplazar")
else:
    st.sidebar.success("✅ Todas las API Keys están activas (o no se han detectado agotadas aún).")
st.sidebar.markdown("---")
st.sidebar.markdown("Autor: **JAPH99** 🇨🇴")
