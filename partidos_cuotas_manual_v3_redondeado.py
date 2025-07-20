# partidos_cuotas_manual_v3_redondeado.py
# Evaluador de surebets con mejoras y soporte para 3 resultados

import streamlit as st
import pandas as pd
from itertools import combinations

# --- Configuración de la página ---
st.set_page_config(page_title="Calculadora de Surebets", layout="centered")

st.title("📊 Calculadora Manual de Surebets (hasta 6 casas)")

st.write("Esta herramienta te ayuda a encontrar oportunidades de Surebets (apuestas seguras) entre diferentes casas de apuestas. Ingresa las cuotas y el sistema calculará si existe una combinación rentable.")

st.markdown("---")

# --- Sección de Ingreso de Evento y Configuración ---
st.subheader("📝 Ingresar evento y configuración")

evento = st.text_input("Nombre del evento", value="Ej: Nacional vs Millonarios")
moneda = st.selectbox("Divisa", ["COP", "EUR", "USD"])
# SOLUCIÓN para la advertencia anterior: Cambiar los valores de min_value, value y step a enteros
presupuesto = st.number_input(f"Presupuesto total ({moneda})", min_value=10, value=100000, step=1000, format="%d")

# Opciones de mercado
tipo_mercado = st.radio("Tipo de mercado", ["2 Resultados (1/2)", "3 Resultados (1/X/2)"], index=0)

# Definir casas por divisa
casas_predefinidas = {
    "COP": ["BetPlay", "Wplay", "Stake", "Bwin", "Betsson", "Luckia"],
    "EUR": ["Casa EU 1", "Casa EU 2", "Casa EU 3", "Casa EU 4", "Casa EU 5", "Casa EU 6"],
    "USD": ["Casa US 1", "Casa US 2", "Casa US 3", "Casa US 4", "Casa US 5", "Casa US 6"],
}

st.subheader("🏠 Ingresar cuotas por casa de apuestas")

# Slider para el número de casas a considerar
num_casas = st.slider("Número de casas a considerar", min_value=2, max_value=6, value=3)

# --- Manejo del estado de la sesión para persistencia de datos ---
# Inicializar estados de las casas si no existen
if 'nombres_casas' not in st.session_state:
    st.session_state.nombres_casas = [casas_predefinidas[moneda][i] for i in range(6)]
if 'cuotas_local' not in st.session_state:
    st.session_state.cuotas_local = [1.0] * 6
if 'cuotas_empate' not in st.session_state:
    st.session_state.cuotas_empate = [1.0] * 6
if 'cuotas_visitante' not in st.session_state:
    st.session_state.cuotas_visitante = [1.0] * 6
if 'last_moneda' not in st.session_state:
    st.session_state.last_moneda = moneda

# Actualizar nombres por defecto si la divisa cambia
if moneda != st.session_state.last_moneda:
    st.session_state.nombres_casas = [casas_predefinidas[moneda][i] for i in range(6)]

st.session_state.last_moneda = moneda # Actualizar la última moneda seleccionada

casas = []
for i in range(num_casas): # Usamos num_casas del slider
    st.markdown(f"### Casa {i+1}")
    
    # Obtener valores por defecto del estado de la sesión
    nombre_casa_default = st.session_state.nombres_casas[i]
    cuota_local_default = st.session_state.cuotas_local[i]
    cuota_empate_default = st.session_state.cuotas_empate[i]
    cuota_visitante_default = st.session_state.cuotas_visitante[i]

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        # El valor se actualiza en el estado de la sesión al cambiar el input
        nombre = st.text_input(f"Nombre", value=nombre_casa_default, key=f"nombre_{i}")
        st.session_state.nombres_casas[i] = nombre # Actualizar el estado de la sesión
    with col2:
        cuota_local = st.number_input(f"Cuota Local", min_value=1.0, value=cuota_local_default, step=0.01, key=f"local_{i}")
        st.session_state.cuotas_local[i] = cuota_local # Actualizar el estado de la sesión
    
    cuota_empate = 0.0 # Valor por defecto si no es un mercado de 3 resultados
    if tipo_mercado == "3 Resultados (1/X/2)":
        with col3:
            cuota_empate = st.number_input(f"Cuota Empate", min_value=1.0, value=cuota_empate_default, step=0.01, key=f"empate_{i}")
            st.session_state.cuotas_empate[i] = cuota_empate # Actualizar el estado de la sesión
    else:
        # Si el mercado cambia de 3 a 2 resultados, reseteamos la cuota de empate en sesión
        if st.session_state.cuotas_empate[i] != 1.0:
             st.session_state.cuotas_empate[i] = 1.0 # O cualquier otro valor que indique "no aplica"

    with col4:
        cuota_visitante = st.number_input(f"Cuota Visitante", min_value=1.0, value=cuota_visitante_default, step=0.01, key=f"visitante_{i}")
        st.session_state.cuotas_visitante[i] = cuota_visitante # Actualizar el estado de la sesión
    
    casas.append((nombre, cuota_local, cuota_empate, cuota_visitante))

st.markdown("---")

# --- Funciones de Cálculo de Surebets ---

def calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto):
    """Calcula surebet para 2 resultados (Local/Visitante)."""
    if c1_local <= 1.01 or c2_visit <= 1.01: # Validar cuotas válidas (ligeramente por encima de 1.0)
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
    if c_local <= 1.01 or c_empate <= 1.01 or c_visitante <= 1.01: # Validar cuotas válidas
        return None, None, None, None, None # SOLUCIÓN: Ahora devuelve 5 None's
    
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
    return None, None, None, None, None # SOLUCIÓN: Ahora devuelve 5 None's

# --- Lógica de Evaluación ---
if st.button("🔍 Evaluar combinaciones"):
    mejores = []

    if tipo_mercado == "2 Resultados (1/2)":
        for i in range(num_casas):
            for j in range(num_casas):
                if i == j:
                    continue
                
                nombre1, c1_local, _, c1_visit = casas[i] 
                nombre2, c2_local, _, c2_visit = casas[j]

                # 1) Combinación: Local de Casa i / Visitante de Casa j
                stake1, stake2, ganancia, roi = calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto)
                if ganancia is not None:
                    mejores.append({
                        "tipo": "2 Resultados",
                        "apuesta1_casa": nombre1,
                        "apuesta1_rol": "Local",
                        "apuesta1_cuota": c1_local,
                        "apuesta1_stake": stake1,
                        "apuesta2_casa": nombre2,
                        "apuesta2_rol": "Visitante",
                        "apuesta2_cuota": c2_visit,
                        "apuesta2_stake": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })

                # 2) Combinación: Local de Casa j / Visitante de Casa i
                stake1_rev, stake2_rev, ganancia_rev, roi_rev = calcular_surebet_2_resultados(c2_local, c1_visit, presupuesto)
                if ganancia_rev is not None:
                    mejores.append({
                        "tipo": "2 Resultados",
                        "apuesta1_casa": nombre2,
                        "apuesta1_rol": "Local",
                        "apuesta1_cuota": c2_local,
                        "apuesta1_stake": stake1_rev,
                        "apuesta2_casa": nombre1,
                        "apuesta2_rol": "Visitante",
                        "apuesta2_cuota": c1_visit,
                        "apuesta2_stake": stake2_rev,
                        "ganancia": ganancia_rev,
                        "roi": roi_rev
                    })
    else: # 3 Resultados (1/X/2)
        # Iterar sobre todas las combinaciones de 3 casas para (Local, Empate, Visitante)
        for i_l in range(num_casas):
            for i_x in range(num_casas):
                for i_v in range(num_casas):
                    # Opcional: Para asegurar que las 3 cuotas provengan de casas diferentes:
                    # if i_l == i_x or i_l == i_v or i_x == i_v:
                    #     continue 

                    nombre_l, c_l, _, _ = casas[i_l] 
                    nombre_x, _, c_x, _ = casas[i_x] 
                    nombre_v, _, _, c_v = casas[i_v] 
                    
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
        st.success("✅ ¡Surebet encontrada!")
        
        # Ordenar por ROI para mostrar la mejor surebet
        top_surebet = sorted(mejores, key=lambda x: x["roi"], reverse=True)[0]

        st.markdown("---")
        st.subheader("🏆 La Mejor Surebet Encontrada")
        st.markdown(f"**🎯 Evento:** {evento}")
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
        st.warning("❌ No se encontraron combinaciones rentables para el tipo de mercado seleccionado con las cuotas ingresadas. Intenta ajustar los valores o cambia de tipo de mercado.")

st.markdown("---")
st.info("⚠️ **¡Advertencia Importante!** Las cuotas en las casas de apuestas cambian **constantemente**. Es fundamental **verificar las cuotas en vivo** justo antes de realizar cualquier apuesta. Además, las casas de apuestas pueden tener reglas específicas o anular apuestas en caso de errores claros en las cuotas.")