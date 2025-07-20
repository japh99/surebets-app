# partidos_cuotas_manual_simple.py
# Evaluador de surebets con mejoras y soporte para 3 resultados

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calculadora de Surebets", layout="centered")
st.title("📊 Calculadora Manual de Surebets (hasta 6 casas)")

st.write("Esta herramienta te ayuda a encontrar oportunidades de Surebets (apuestas seguras) entre diferentes casas de apuestas. Ingresa las cuotas y el sistema calculará si existe una combinación rentable.")

---

st.subheader("📝 Ingresar evento y configuración")

evento = st.text_input("Nombre del evento", value="Ej: Nacional vs Millonarios")
moneda = st.selectbox("Divisa", ["COP", "EUR", "USD"])
presupuesto = st.number_input(f"Presupuesto total ({moneda})", min_value=10.0, value=100000.0, step=1000.0, format="%d")

# Opciones de mercado
tipo_mercado = st.radio("Tipo de mercado", ["2 Resultados (1/2)", "3 Resultados (1/X/2)"], index=0)

# Definir casas por divisa
casas_predefinidas = {
    "COP": ["BetPlay", "Wplay", "Stake", "Bwin", "Betsson", "Luckia"],
    "EUR": ["Casa EU 1", "Casa EU 2", "Casa EU 3", "Casa EU 4", "Casa EU 5", "Casa EU 6"],
    "USD": ["Casa US 1", "Casa US 2", "Casa US 3", "Casa US 4", "Casa US 5", "Casa US 6"],
}

st.subheader("🏠 Ingresar cuotas por casa de apuestas")

casas = []
num_casas = st.slider("Número de casas a considerar", min_value=2, max_value=6, value=3)

# Inicializar o cargar estados de las casas para persistencia
if 'nombres_casas' not in st.session_state:
    st.session_state.nombres_casas = [casas_predefinidas[moneda][i] for i in range(6)]
if 'cuotas_local' not in st.session_state:
    st.session_state.cuotas_local = [1.0] * 6
if 'cuotas_empate' not in st.session_state:
    st.session_state.cuotas_empate = [1.0] * 6
if 'cuotas_visitante' not in st.session_state:
    st.session_state.cuotas_visitante = [1.0] * 6

# Actualizar nombres por defecto si la divisa cambia
current_moneda_state = st.session_state.get('last_moneda', 'COP')
if moneda != current_moneda_state:
    st.session_state.nombres_casas = [casas_predefinidas[moneda][i] for i in range(6)]
    st.session_state.last_moneda = moneda # Guardar la moneda actual

for i in range(num_casas):
    st.markdown(f"### Casa {i+1}")
    
    # Usar el estado de la sesión para los valores por defecto editables
    nombre_casa_default = st.session_state.nombres_casas[i]
    cuota_local_default = st.session_state.cuotas_local[i]
    cuota_empate_default = st.session_state.cuotas_empate[i]
    cuota_visitante_default = st.session_state.cuotas_visitante[i]

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        nombre = st.text_input(f"Nombre", value=nombre_casa_default, key=f"nombre_{i}")
        # Actualizar el estado de la sesión
        st.session_state.nombres_casas[i] = nombre
    with col2:
        cuota_local = st.number_input(f"Cuota Local", min_value=1.0, value=cuota_local_default, step=0.01, key=f"local_{i}")
        st.session_state.cuotas_local[i] = cuota_local
    if tipo_mercado == "3 Resultados (1/X/2)":
        with col3:
            cuota_empate = st.number_input(f"Cuota Empate", min_value=1.0, value=cuota_empate_default, step=0.01, key=f"empate_{i}")
            st.session_state.cuotas_empate[i] = cuota_empate
    else:
        cuota_empate = 0.0 # No relevante para 2 resultados
    with col4:
        cuota_visitante = st.number_input(f"Cuota Visitante", min_value=1.0, value=cuota_visitante_default, step=0.01, key=f"visitante_{i}")
        st.session_state.cuotas_visitante[i] = cuota_visitante
    
    casas.append((nombre, cuota_local, cuota_empate, cuota_visitante))


---

def calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto):
    """Calcula surebet para 2 resultados (Local/Visitante)."""
    if c1_local <= 1 or c2_visit <= 1: # Validar cuotas válidas
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
    if c_local <= 1 or c_empate <= 1 or c_visitante <= 1: # Validar cuotas válidas
        return None, None, None, None, None, None, None
    
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
    return None, None, None, None, None, None, None

if st.button("🔍 Evaluar combinaciones"):
    mejores = []

    if tipo_mercado == "2 Resultados (1/2)":
        for i in range(num_casas):
            for j in range(num_casas):
                if i == j:
                    continue
                nombre1, c1_local, _, c1_visit = casas[i] # Ignorar empate
                nombre2, c2_local, _, c2_visit = casas[j] # Ignorar empate

                # 1) Local (Casa i) / Visitante (Casa j)
                stake1, stake2, ganancia, roi = calcular_surebet_2_resultados(c1_local, c2_visit, presupuesto)
                if ganancia is not None:
                    mejores.append({
                        "tipo": "Local / Visitante",
                        "casa1_nombre": nombre1,
                        "casa1_cuota": c1_local,
                        "casa1_stake": stake1,
                        "casa2_nombre": nombre2,
                        "casa2_cuota": c2_visit,
                        "casa2_stake": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })

                # 2) Visitante (Casa i) / Local (Casa j)
                stake1, stake2, ganancia, roi = calcular_surebet_2_resultados(c2_local, c1_visit, presupuesto)
                if ganancia is not None:
                    mejores.append({
                        "tipo": "Visitante / Local",
                        "casa1_nombre": nombre2,
                        "casa1_cuota": c2_local,
                        "casa1_stake": stake1,
                        "casa2_nombre": nombre1,
                        "casa2_cuota": c1_visit,
                        "casa2_stake": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })
    else: # 3 Resultados (1/X/2)
        # Para 3 resultados, se necesitan 3 cuotas diferentes de 3 casas (o 2 si una casa ofrece 2 cuotas óptimas)
        # La forma más robusta es iterar sobre todas las combinaciones posibles de 3 cuotas entre las casas
        
        # Generar todas las combinaciones únicas de casas para las 3 cuotas
        from itertools import product
        
        # Usamos índices para evitar repeticiones y asegurar que las cuotas provengan
        # de casas que puedan ser distintas para cada resultado (aunque una misma casa
        # podría ofrecer la mejor cuota para 2 resultados)
        
        # Iterar sobre las casas para Local, Empate y Visitante
        for i_local in range(num_casas):
            for i_empate in range(num_casas):
                for i_visitante in range(num_casas):
                    # Podemos permitir que una misma casa tenga la mejor cuota para 2 o 3 resultados,
                    # esto cubre escenarios donde una casa podría tener una cuota muy alta para uno.
                    # Sin embargo, generalmente las surebets se dan entre *diferentes* casas.
                    # Para simplificar y priorizar la lógica de surebet real (entre casas diferentes para cada outcome),
                    # podemos añadir una condición si queremos forzar 3 casas distintas.
                    # if i_local == i_empate or i_local == i_visitante or i_empate == i_visitante:
                    #     continue # Para asegurar 3 casas diferentes para cada parte de la surebet

                    nombre_local, c_local, _, _ = casas[i_local]
                    nombre_empate, _, c_empate, _ = casas[i_empate]
                    nombre_visitante, _, _, c_visitante = casas[i_visitante]
                    
                    # Asegurar que estamos usando las cuotas correctas del tipo de mercado
                    if tipo_mercado == "3 Resultados (1/X/2)":
                        stake_local, stake_empate, stake_visitante, ganancia, roi = \
                            calcular_surebet_3_resultados(casas[i_local][1], casas[i_empate][2], casas[i_visitante][3], presupuesto)
                    else: # Esto no debería ocurrir si ya estamos en el bloque de 3 resultados, pero por seguridad
                        continue

                    if ganancia is not None:
                        # Para evitar duplicados con el mismo set de casas y cuotas si el orden de iteración los genera
                        # Se podría usar un conjunto para guardar tuplas (casa_L, casa_X, casa_V) para evitar combinaciones idénticas
                        mejores.append({
                            "tipo": "Local / Empate / Visitante",
                            "casa_local_nombre": nombre_local,
                            "casa_local_cuota": casas[i_local][1],
                            "casa_local_stake": stake_local,
                            "casa_empate_nombre": nombre_empate,
                            "casa_empate_cuota": casas[i_empate][2],
                            "casa_empate_stake": stake_empate,
                            "casa_visitante_nombre": nombre_visitante,
                            "casa_visitante_cuota": casas[i_visitante][3],
                            "casa_visitante_stake": stake_visitante,
                            "ganancia": ganancia,
                            "roi": roi
                        })

    if mejores:
        st.success("✅ ¡Surebet encontrada!")
        
        # Ordenar por ROI para mostrar las mejores primero
        mejores_ordenadas = sorted(mejores, key=lambda x: x["roi"], reverse=True)

        st.markdown("---")
        st.subheader("Mejores Combinaciones de Surebets")
        
        # Mostrar las 5 mejores o todas si hay menos de 5
        num_a_mostrar = min(len(mejores_ordenadas), 5)
        
        for i in range(num_a_mostrar):
            surebet = mejores_ordenadas[i]
            st.markdown(f"**Combinación #{i+1} (ROI: {surebet['roi']}%)**")
            st.markdown(f"**🎯 Evento:** {evento}")
            st.markdown(f"💰 Ganancia asegurada: **${surebet['ganancia']:,d} {moneda}**")
            
            if surebet['tipo'] == "Local / Visitante" or surebet['tipo'] == "Visitante / Local":
                st.markdown(f"""
    - **{surebet['casa1_nombre']}**: **${surebet['casa1_stake']:,d} {moneda}** a cuota {surebet['casa1_cuota']}
    - **{surebet['casa2_nombre']}**: **${surebet['casa2_stake']:,d} {moneda}** a cuota {surebet['casa2_cuota']}
    """)
            elif surebet['tipo'] == "Local / Empate / Visitante":
                st.markdown(f"""
    - **{surebet['casa_local_nombre']}**: **${surebet['casa_local_stake']:,d} {moneda}** a cuota {surebet['casa_local_cuota']} (Local)
    - **{surebet['casa_empate_nombre']}**: **${surebet['casa_empate_stake']:,d} {moneda}** a cuota {surebet['casa_empate_cuota']} (Empate)
    - **{surebet['casa_visitante_nombre']}**: **${surebet['casa_visitante_stake']:,d} {moneda}** a cuota {surebet['casa_visitante_cuota']} (Visitante)
    """)
            st.markdown("---")
        
        if len(mejores_ordenadas) > num_a_mostrar:
            st.info(f"Se encontraron {len(mejores_ordenadas) - num_a_mostrar} surebets adicionales. Ajusta tus cuotas o presupuesto para encontrar más oportunidades.")

        st.markdown("---")
        st.subheader("Detalle de Todas las Surebets Encontradas")
        
        # Convertir la lista de diccionarios a un DataFrame de pandas para mostrar en una tabla
        # Se necesita adaptar las columnas para 2 o 3 resultados
        df_display_data = []
        for sb in mejores_ordenadas:
            if sb['tipo'] == "Local / Visitante" or sb['tipo'] == "Visitante / Local":
                df_display_data.append({
                    "Tipo": sb['tipo'],
                    "Casa 1": sb['casa1_nombre'],
                    "Cuota 1": sb['casa1_cuota'],
                    f"Stake 1 ({moneda})": f"${sb['casa1_stake']:,d}",
                    "Casa 2": sb['casa2_nombre'],
                    "Cuota 2": sb['casa2_cuota'],
                    f"Stake 2 ({moneda})": f"${sb['casa2_stake']:,d}",
                    "Casa 3": "-", "Cuota 3": "-", f"Stake 3 ({moneda})": "-", # Campos vacíos para consistencia
                    "Ganancia Segura": f"${sb['ganancia']:,d}",
                    "ROI (%)": sb['roi']
                })
            elif sb['tipo'] == "Local / Empate / Visitante":
                 df_display_data.append({
                    "Tipo": sb['tipo'],
                    "Casa 1": f"{sb['casa_local_nombre']} (Local)",
                    "Cuota 1": sb['casa_local_cuota'],
                    f"Stake 1 ({moneda})": f"${sb['casa_local_stake']:,d}",
                    "Casa 2": f"{sb['casa_empate_nombre']} (Empate)",
                    "Cuota 2": sb['casa_empate_cuota'],
                    f"Stake 2 ({moneda})": f"${sb['casa_empate_stake']:,d}",
                    "Casa 3": f"{sb['casa_visitante_nombre']} (Visitante)",
                    "Cuota 3": sb['casa_visitante_cuota'],
                    f"Stake 3 ({moneda})": f"${sb['casa_visitante_stake']:,d}",
                    "Ganancia Segura": f"${sb['ganancia']:,d}",
                    "ROI (%)": sb['roi']
                })
        
        df = pd.DataFrame(df_display_data)
        st.dataframe(df, hide_index=True)


    else:
        st.warning("❌ No se encontraron combinaciones rentables para el tipo de mercado seleccionado con las cuotas ingresadas. Intenta ajustar los valores.")

st.markdown("---")
st.info("Recuerda que las cuotas de las casas de apuestas cambian constantemente. Es fundamental verificar las cuotas en vivo antes de realizar cualquier apuesta.")
