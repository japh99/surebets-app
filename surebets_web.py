import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# --- APIKeyManager Class (as provided previously) ---
class APIKeyManager:
    """
    Gestiona la rotación de claves de API y el seguimiento de sus créditos.
    """
    def __init__(self, api_keys, default_credits_per_key=500):
        """
        Inicializa el gestor de claves API.

        Args:
            api_keys (list): Una lista de cadenas con las claves de API.
            default_credits_per_key (int): El número de créditos inicial para cada clave.
        """
        self.api_keys = list(api_keys)
        self.key_credits = {key: default_credits_per_key for key in self.api_keys}
        self.current_key_index = 0
        # print(f"✅ APIKeyManager inicializado con {len(self.api_keys)} claves.")

    def get_current_key(self):
        """
        Devuelve la clave API actual en uso.

        Returns:
            str: La clave API actual.
        """
        if not self.api_keys:
            # st.error("❌ No hay claves API disponibles.")
            return None
        if self.current_key_index >= len(self.api_keys):
            self.current_key_index = 0
        return self.api_keys[self.current_key_index]

    def use_credit(self, amount=1):
        """
        Simula el uso de un crédito para la clave API actual.
        Si la clave actual se agota, rota a la siguiente.

        Args:
            amount (int): Cantidad de créditos a usar. Por defecto es 1.

        Returns:
            bool: True si el crédito fue usado con éxito, False si no hay créditos
                  o la clave ya está agotada.
        """
        key = self.get_current_key()
        if key is None:
            return False

        if self.key_credits.get(key, 0) <= 0:
            # st.warning(f"⚠️ La clave '{key}' no tiene créditos disponibles. Rotando...")
            self._rotate_key()
            key = self.get_current_key()
            if key is None or self.key_credits.get(key, 0) <= 0:
                # st.error(f"🚨 La nueva clave '{key}' también está agotada o no hay más claves.")
                return False

        self.key_credits[key] -= amount
        # st.info(f"➡️ Usado {amount} crédito(s) para la clave '{key[:6]}...'. Restantes: {self.key_credits[key]}")

        if self.key_credits[key] <= 0:
            # st.warning(f"🚨 Clave '{key[:6]}...' agotada. Rotando a la siguiente.")
            self._rotate_key()
        return True

    def _rotate_key(self):
        """
        Rota a la siguiente clave API disponible. Si todas las claves están agotadas,
        se imprime un mensaje de advertencia.
        """
        if not self.api_keys:
            return

        initial_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

        while self.key_credits[self.api_keys[self.current_key_index]] <= 0:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            if self.current_key_index == initial_index:
                st.error("⛔ Todas las claves API están agotadas. Considera reiniciar o esperar el nuevo ciclo.")
                break

        # st.success(f"🔄 Rotado a la clave: '{self.get_current_key()[:6]}...' (Índice: {self.current_key_index})")

    def get_remaining_credits(self, key=None):
        """
        Devuelve los créditos restantes para una clave específica o la clave actual.
        """
        if key:
            return self.key_credits.get(key, 0)
        return self.key_credits.get(self.get_current_key(), 0)

    def reset_credits(self, key=None):
        """
        Reinicia los créditos para una clave específica o para todas las claves.
        """
        if key and key in self.key_credits:
            self.key_credits[key] = 500
            # st.success(f"🔄 Créditos de la clave '{key[:6]}...' reseteados a 500.")
        elif key is None:
            for k in self.api_keys:
                self.key_credits[k] = 500
            # st.success("🔄 Todos los créditos de las claves API han sido reseteados a 500.")
        else:
            st.error(f"❌ La clave '{key}' no fue encontrada.")


# --- Tu lista de API Keys ---
api_keys_list = [
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
    "cc16776a60e3eee3e10535577216b7a29", "a0cc233165bc0ed04ee42feeaf2c9d30",
    "d2afc749fc6b64adb4d8361b0fe58b4b", "b351eb6fb3f5e95b019c18117e93db1b",
    "74dbc42e50dd64687dc1fad8af59c490", "7b4a5639cbe63ddf37b64d7e327d3e71",
    "20cec1e2b8c3fd9bb86d9e4fad7e6081", "1352436d9a0e223478ec83aec230b4aa",
    "29257226d1c9b6a15c141d989193ef72", "24677adc5f5ff8401c6d98ea033e0f0b",
    "54e84a82251def9696ba767d6e2ca76c", "ff3e9e3a12c2728c6c4ddea087bc51a9",
    "f3ff0fb5d7a7a683f88b8adec904e7b8", "1e0ab1ff51d111c88aebe4723020946a",
    "6f74a75a76f42fabaa815c4461c59980", "86de2f86b0b628024ef6d5546b479c0f"
]

# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="Buscador de Surebets de Fútbol",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Buscador de Surebets de Fútbol")
st.markdown("---")

# Initialize API Key Manager in session state
if 'api_manager' not in st.session_state:
    st.session_state.api_manager = APIKeyManager(api_keys_list)

manager = st.session_state.api_manager

# --- Helper Functions ---
def calculate_surebet_roi(odds):
    """Calcula el ROI de una surebet a partir de las cuotas."""
    inverse_sum = sum(1 / odd for odd in odds)
    if inverse_sum < 1:
        return (1 - inverse_sum) * 100
    return 0

def get_best_odds(bookmakers, outcome_name):
    """Obtiene la mejor cuota para un resultado específico entre los bookmakers."""
    best_odd = 0.0
    best_bookmaker = None
    for bm in bookmakers:
        for market in bm['markets']:
            if market['key'] == 'h2h' or market['key'] == 'totals': # Considerar ambos mercados
                for outcome in market['outcomes']:
                    if outcome['name'] == outcome_name:
                        if outcome['price'] > best_odd:
                            best_odd = outcome['price']
                            best_bookmaker = bm['title']
    return best_odd, best_bookmaker

def get_best_over_under_odds(bookmakers, market_key='totals', point=2.5):
    """Obtiene las mejores cuotas para 'Over' y 'Under' en un punto dado."""
    best_over_odd = 0.0
    best_under_odd = 0.0
    best_over_bookmaker = None
    best_under_bookmaker = None

    for bm in bookmakers:
        for market in bm['markets']:
            if market['key'] == market_key and market.get('last_update'): # Ensure market exists and has update time
                for outcome in market['outcomes']:
                    if outcome['name'] == 'Over' and outcome['point'] == point:
                        if outcome['price'] > best_over_odd:
                            best_over_odd = outcome['price']
                            best_over_bookmaker = bm['title']
                    elif outcome['name'] == 'Under' and outcome['point'] == point:
                        if outcome['price'] > best_under_odd:
                            best_under_odd = outcome['price']
                            best_under_bookmaker = bm['title']
    return best_over_odd, best_over_bookmaker, best_under_odd, best_under_bookmaker


def fetch_and_process_soccer_odds(manager):
    """
    Realiza la solicitud a The Odds API para fútbol (soccer)
    y procesa los datos para encontrar surebets en 1x2 y Over/Under 2.5.
    """
    sport_key = 'soccer' # Deporte fijo: fútbol
    regions = 'us'       # O ajusta según las regiones que te interesen
    markets = 'h2h,totals' # Solicita ambos mercados: 1x2 (h2h) y Over/Under (totals)
    odds_format = 'decimal'
    days_from = 2 # Buscar eventos en las próximas 48 horas

    all_surebets = []
    surebet_found_count = 0

    st.info(f"🔎 Buscando surebets para **{sport_key.capitalize()}** en mercados **1x2 y Over/Under 2.5**...")
    progress_bar = st.progress(0)
    status_text = st.empty()

    current_api_key = manager.get_current_key()
    if not current_api_key:
        st.error("No hay claves API disponibles para realizar la búsqueda.")
        return pd.DataFrame() # Retorna un DataFrame vacío si no hay claves

    url = f"https://api.theoddsapi.com/v4/sports/{sport_key}/odds/?apiKey={current_api_key}&regions={regions}&markets={markets}&oddsFormat={odds_format}&dateFormat=unix&daysFrom={days_from}"

    try:
        status_text.text(f"Realizando solicitud con clave: {current_api_key[:6]}...")
        response = requests.get(url, timeout=10) # Añadir un timeout
        response.raise_for_status() # Lanza una excepción para errores HTTP

        data = response.json()

        # Usar un crédito si la llamada fue exitosa
        manager.use_credit()
        st.sidebar.markdown(f"**Créditos actuales para {current_api_key[:6]}...:** {manager.get_remaining_credits(current_api_key)}")
        
        # Filtrar solo eventos con al menos 2 casas de apuestas para h2h y totals
        filtered_events = [
            event for event in data
            if any(bm for bm in event['bookmakers'] if 'h2h' in [m['key'] for m in bm['markets']]) and
               any(bm for bm in event['bookmakers'] if 'totals' in [m['key'] for m in bm['markets']]) and
               len(event['bookmakers']) >= 2 # Asegurarse de tener al menos 2 bookmakers en general
        ]

        if not filtered_events:
            st.warning("No se encontraron eventos de fútbol con datos suficientes para los mercados 1x2 y Over/Under 2.5.")
            return pd.DataFrame()

        for i, event in enumerate(filtered_events):
            home_team = event['home_team']
            away_team = event['away_team']
            commence_time_unix = event['commence_time']
            commence_datetime = datetime.fromtimestamp(commence_time_unix)
            
            # Determinar si es en vivo o pre-partido
            is_live = False
            if 'last_update' in event: # The Odds API v4 usa 'last_update' para eventos en vivo
                # Si el tiempo de inicio ha pasado, y hay un 'last_update' reciente, es probable que esté en vivo
                if datetime.now() > commence_datetime and (datetime.now() - datetime.fromtimestamp(event['last_update'])).total_seconds() < 3600:
                    is_live = True
            
            event_type = "🔴 En vivo" if is_live else "🟢 Pre-partido"


            # --- Procesar Mercado 1x2 (Head-to-Head) ---
            best_home_odd, home_bookmaker = get_best_odds(event['bookmakers'], home_team)
            best_away_odd, away_bookmaker = get_best_odds(event['bookmakers'], away_team)
            
            # Necesitamos la cuota del empate (Draw) para el 1x2
            best_draw_odd, draw_bookmaker = get_best_odds(event['bookmakers'], 'Draw')


            if best_home_odd and best_away_odd and best_draw_odd and \
               len(set([home_bookmaker, away_bookmaker, draw_bookmaker])) >= 2: # Al menos 2 casas distintas para 1X2
                
                odds_1x2 = [best_home_odd, best_draw_odd, best_away_odd]
                roi_1x2 = calculate_surebet_roi(odds_1x2)

                if roi_1x2 > 0:
                    surebet_found_count += 1
                    all_surebets.append({
                        "Deporte": "Fútbol",
                        "Tipo de Evento": event_type,
                        "Partido": f"{home_team} vs {away_team}",
                        "Mercado": "1x2",
                        "Cuota Local": f"{best_home_odd} ({home_bookmaker})",
                        "Cuota Empate": f"{best_draw_odd} ({draw_bookmaker})",
                        "Cuota Visitante": f"{best_away_odd} ({away_bookmaker})",
                        "Utilidad (%)": f"{roi_1x2:.2f}%",
                        "Hora de Inicio": commence_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    })

            # --- Procesar Mercado Over/Under 2.5 (Totals) ---
            best_over_odd, over_bookmaker, best_under_odd, under_bookmaker = \
                get_best_over_under_odds(event['bookmakers'], point=2.5)

            if best_over_odd and best_under_odd and \
               len(set([over_bookmaker, under_bookmaker])) >= 2: # Al menos 2 casas distintas para Over/Under
                
                odds_ou = [best_over_odd, best_under_odd]
                roi_ou = calculate_surebet_roi(odds_ou)

                if roi_ou > 0:
                    surebet_found_count += 1
                    all_surebets.append({
                        "Deporte": "Fútbol",
                        "Tipo de Evento": event_type,
                        "Partido": f"{home_team} vs {away_team}",
                        "Mercado": "Over/Under 2.5",
                        "Cuota Over": f"{best_over_odd} ({over_bookmaker})",
                        "Cuota Under": f"{best_under_odd} ({under_bookmaker})",
                        "Utilidad (%)": f"{roi_ou:.2f}%",
                        "Hora de Inicio": commence_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    })

            progress_bar.progress((i + 1) / len(filtered_events))
            status_text.text(f"Procesando evento {i+1}/{len(filtered_events)}: {home_team} vs {away_team}")

        progress_bar.empty()
        status_text.empty()
        if surebet_found_count == 0:
            st.info("No se encontraron surebets con utilidad positiva en los mercados especificados.")
        else:
            st.success(f"¡Búsqueda completada! Se encontraron **{surebet_found_count}** surebets de fútbol con utilidad positiva.")

        return pd.DataFrame(all_surebets)

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al realizar la solicitud a la API: {e}")
        st.warning("Verifica tu conexión a internet o el estado de las claves API.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Se produjo un error inesperado: {e}")
        return pd.DataFrame()


# --- Streamlit UI ---

st.sidebar.header("Opciones de Búsqueda")
# Botón para iniciar la búsqueda
if st.sidebar.button("🚀 Buscar Surebets de Fútbol"):
    st.session_state.surebets_data = fetch_and_process_soccer_odds(manager)
    st.session_state.last_search_time = datetime.now()

# Mostrar resultados de la última búsqueda
if 'surebets_data' in st.session_state and not st.session_state.surebets_data.empty:
    st.markdown("## 📊 Resultados de Surebets Encontradas")
    st.dataframe(st.session_state.surebets_data, use_container_width=True, hide_index=True)
    st.info(f"Última búsqueda realizada: {st.session_state.last_search_time.strftime('%Y-%m-%d %H:%M:%S')}")
elif 'surebets_data' in st.session_state and st.session_state.surebets_data.empty:
    st.info("No se encontraron surebets en la última búsqueda.")

st.markdown("---")
st.sidebar.header("Estado de las Claves API")
# Mostrar el estado de los créditos de las API keys en la barra lateral
for key in manager.api_keys:
    st.sidebar.text(f"- {key[:6]}...: {manager.get_remaining_credits(key)} créditos")

# Botón para reiniciar los créditos (útil para pruebas o al inicio de un nuevo mes)
if st.sidebar.button("🔄 Reiniciar todos los Créditos API"):
    manager.reset_credits()
    st.sidebar.success("¡Créditos de todas las API keys reiniciados!")
    # Forzar una actualización de la visualización de créditos
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("Este proyecto detecta surebets de fútbol en los mercados 1x2 y Over/Under 2.5, rotando automáticamente entre las claves API para optimizar su uso.")
