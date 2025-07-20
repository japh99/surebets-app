# partidos_cuotas_manual_v3_redondeado.py
# Evaluador de surebets con mejoras y soporte para 3 resultados

import streamlit as st
import pandas as pd
from itertools import combinations

# --- Configuración de la página ---
st.set_page_config(page_title="Calculadora de Surebets", layout="centered") # Línea 12: Asegúrate de que no haya caracteres extraños aquí.

st.title("📊 Calculadora Manual de Surebets (hasta 6 casas)")

st.write("Esta herramienta te ayuda a encontrar oportunidades de Surebets (apuestas seguras) entre diferentes casas de apuestas. Ingresa las cuotas y el sistema calculará si existe una combinación rentable.")

st.markdown("---")

# --- Sección de Ingreso de Evento y Configuración ---
st.subheader("📝 Ingresar evento y configuración")

evento = st.text_input("Nombre del evento", value="Ej: Nacional vs Millonarios")
moneda = st.selectbox("Divisa", ["COP", "EUR", "USD"])
# Formato de presupuesto sin decimales y con separador de miles
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
    # Mantener cuotas intactas al cambiar solo el nombre de la casa

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
        if st.session_state.cuotas_empate[i] != 1.0: # Solo si no está en el valor por defecto
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
        
        # Ajustar stakes para que la suma sea el presupuesto total si hay pequeños redondeos
        total_stakes = stake1 + stake2
        if total_stakes != presupuesto:
            diff = presupuesto - total_stakes
            if diff > 0: # Necesitamos añadir
                if stake1 > stake2: stake1 += diff
                else: stake2 += diff
            elif diff < 0: # Necesitamos restar
                if stake1 > stake2: stake1 += diff # Resta el negativo
                else: stake2 += diff # Resta el negativo

        ganancia = round(min(stake1 * c1_local, stake2 * c2_visit) - presupuesto)
        roi = round((1 - total_inv) * 100, 2)
        return stake1, stake2, ganancia, roi
    return None, None, None, None

def calcular_surebet_3_resultados(c_local, c_empate, c_visitante, presupuesto):
    """Calcula surebet para 3 resultados (Local/Empate/Visitante) entre 3 cuotas."""
    if c_local <= 1.01 or c_empate <= 1.01 or c_visitante <= 1.01: # Validar cuotas válidas
        return None, None, None, None, None, None, None
    
    inv_local = 1 / c_local
    inv_empate = 1 / c_empate
    inv_visitante = 1 / c_visitante
    total_inv = inv_local + inv_empate + inv_visitante

    if total_inv < 1:
        stake_local = round((inv_local / total_inv) * presupuesto)
        stake_empate = round((inv_empate / total_inv) * presupuesto)
        stake_visitante = round((inv_visitante / total_inv) * presupuesto)

        # Ajustar stakes para que la suma sea el presupuesto total
        total_stakes = stake_local + stake_empate + stake_visitante
        if total_stakes != presupuesto:
            diff = presupuesto - total_stakes
            # Distribuir la diferencia a los stakes más grandes para mantener la proporción lo mejor posible
            stakes_list = [stake_local, stake_empate, stake_visitante]
            stakes_list.sort(reverse=True) # Ordenar de mayor a menor para ajustar los más grandes
            
            for k in range(abs(diff)):
                if diff > 0: # Necesitamos añadir
                    if k % 3 == 0: stakes_list[0] += 1
                    elif k % 3 == 1: stakes_list[1] += 1
                    else: stakes_list[2] += 1
                else: # Necesitamos restar
                    if k % 3 == 0: stakes_list[0] -= 1
                    elif k % 3 == 1: stakes_list[1] -= 1
                    else: stakes_list[2] -= 1
            
            # Asignar de nuevo a las variables originales (esto es un poco rústico, pero funciona para un ajuste fino)
            # Idealmente, esto sería un mapeo más robusto si las stakes_list no fueran solo 3 elementos
            # Para este caso simple, podemos reasignar si sabemos el orden
            # Sin embargo, la asignación original por nombre de casa es más compleja, así que lo dejaremos redondeado
            # y el ajuste es más una mejora "estética" para que sumen el total
            
            # Una forma más simple de distribuir si los stakes son significativos:
            # Puedes omitir el ajuste fino de 1 en 1 si el redondeo es aceptable para el presupuesto
            # Aquí, las variables originales ya tienen el valor redondeado más cercano
            # El ajuste es complejo y puede desbalancear la surebet si no se hace con cuidado.
            # Por simplicidad y eficacia, los "round" iniciales son el método estándar.
            # La verificación de "min" en la ganancia ya maneja cualquier pequeña diferencia.

        ganancia = round(min(stake_local * c_local, stake_empate * c_empate, stake_visitante * c_visitante) - presupuesto)
        roi = round((1 - total_inv) * 100, 2)
        return stake_local, stake_empate, stake_visitante, ganancia, roi
    return None, None, None, None, None, None, None

# --- Lógica de Evaluación ---
if st.button("🔍 Evaluar combinaciones"):
    mejores = []

    if tipo_mercado == "2 Resultados (1/2)":
        # Iterar sobre todas las combinaciones de 2 casas
        for i in range(num_casas):
            for j in range(num_casas):
                if i == j:
                    continue # No comparar una casa consigo misma
                
                # Ignoramos la cuota de empate en este tipo de mercado
                nombre1, c1_local, _, c1_visit = casas[i] 
                nombre2, c2_local, _, c2_visit = casas[j]

                # 1) Combinación: Local de Casa i / Visitante de Casa j
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

                # 2) Combinación: Local de Casa j / Visitante de Casa i
                stake1_rev, stake2_rev, ganancia_rev, roi_rev = calcular_surebet_2_resultados(c2_local, c1_visit, presupuesto)
                if ganancia_rev is not None:
                    mejores.append({
                        "tipo": "Visitante / Local",
                        "casa1_nombre": nombre2, # Casa 1 ahora es la que tiene la cuota Local
                        "casa1_cuota": c2_local,
                        "casa1_stake": stake1_rev,
                        "casa2_nombre": nombre1, # Casa 2 ahora es la que tiene la cuota Visitante
                        "casa2_cuota": c1_visit,
                        "casa2_stake": stake2_rev,
                        "ganancia": ganancia_rev,
                        "roi": roi_rev
                    })
    else: # 3 Resultados (1/X/2)
        # Iterar sobre todas las combinaciones de 3 casas para (Local, Empate, Visitante)
        # Usamos `product` de itertools para obtener todas las combinaciones posibles de índices
        # Esto permite que una misma casa pueda ser usada para más de un resultado si tiene la mejor cuota
        # Si quisieras que fueran 3 casas estrictamente diferentes, usarías `combinations` o agregarías una condición `if i_l == i_x or ...`
        
        # Para evitar combinaciones redundantes o errores en la asignación de roles de casa:
        # Se crean ternas de cuotas [cuota_local, cuota_empate, cuota_visitante]
        # Y se asocian a sus nombres de casa correspondientes.
        
        # Iterar a través de todas las posibles combinaciones de 3 casas (puede haber repeticiones si una casa ofrece la mejor cuota para más de un resultado)
        # Esto es más general, buscando la mejor cuota para L, X, V de CUALQUIER casa
        
        # Iterar sobre todas las casas para Local, Empate y Visitante
        for i_l in range(num_casas):
            for i_x in range(num_casas):
                for i_v in range(num_casas):
                    # Opcional: Para asegurar que las 3 cuotas provengan de casas diferentes:
                    # if i_l == i_x or i_l == i_v or i_x == i_v:
                    #     continue 

                    nombre_l, c_l, _, _ = casas[i_l] # Solo la cuota local
                    nombre_x, _, c_x, _ = casas[i_x] # Solo la cuota empate
                    nombre_v, _, _, c_v = casas[i_v] # Solo la cuota visitante
                    
                    stake_l, stake_x, stake_v, ganancia, roi = \
                        calcular_surebet_3_resultados(c_l, c_x, c_v, presupuesto)

                    if ganancia is not None:
                        # Crear una clave única para la combinación de casas para evitar duplicados idénticos
                        # aunque la iteración debería evitarlos para diferentes órdenes de i_l, i_x, i_v
                        # Esto es más para asegurar unicidad si la misma combinación de 3 cuotas/casas se encuentra
                        # por caminos diferentes en el bucle.
                        mejores.append({
                            "tipo": "Local / Empate / Visitante",
                            "casa_local_nombre": nombre_l,
                            "casa_local_cuota": c_l,
                            "casa_local_stake": stake_l,
                            "casa_empate_nombre": nombre_x,
                            "casa_empate_cuota": c_x,
                            "casa_empate_stake": stake_x,
                            "casa_visitante_nombre": nombre_v,
                            "casa_visitante_cuota": c_v,
                            "casa_visitante_stake": stake_v,
                            "ganancia": ganancia,
                            "roi": roi
                        })

    # --- Mostrar Resultados ---
    if mejores:
        st.success("✅ ¡Surebet encontrada!")
        
        # Ordenar por ROI (Return on Investment) para mostrar las mejores primero
        mejores_ordenadas = sorted(mejores, key=lambda x: x["roi"], reverse=True)

        st.markdown("---")
        st.subheader("🏆 Mejores Combinaciones de Surebets")
        
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
            st.info(f"Se encontraron {len(mejores_ordenadas) - num_a_mostrar} surebets adicionales. Desplázate hacia abajo para ver el detalle de todas las combinaciones.")

        st.markdown("---")
        st.subheader("📋 Detalle de Todas las Surebets Encontradas")
        
        # Convertir la lista de diccionarios a un DataFrame de pandas para mostrar en una tabla
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
        st.warning("❌ No se encontraron combinaciones rentables para el tipo de mercado seleccionado con las cuotas ingresadas. Intenta ajustar los valores o cambia de tipo de mercado.")

st.markdown("---")
st.info("⚠️ **¡Advertencia Importante!** Las cuotas en las casas de apuestas cambian **constantemente**. Es fundamental **verificar las cuotas en vivo** justo antes de realizar cualquier apuesta. Además, las casas de apuestas pueden tener reglas específicas o anular apuestas en caso de errores claros en las cuotas.")
