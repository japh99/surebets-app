# partidos_cuotas_manual_v3.py
# Evaluador de surebets manual con hasta 6 casas y tabla de sugerencias ampliada

import streamlit as st
import pandas as pd

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
st.set_page_config(page_title="Evaluador de Surebets Manual v3", layout="centered")
st.title("📊 Evaluador Manual de Cuotas para Surebets (hasta 6 casas)")

st.subheader("📘 Cuotas sugeridas y ROI estimado para grandes ganancias")

# Supongamos presupuesto de 100,000 COP
presupuesto_cop = 100000
datos = []
cuotas_a = [1.20, 1.25, 1.30, 1.40, 1.50, 1.60, 1.70]
for cuota_a in cuotas_a:
    inv_a = 1 / cuota_a
    for cuota_b in [x / 100 for x in range(300, 1001, 25)]:
        inv_b = 1 / cuota_b
        total = inv_a + inv_b
        if total < 1:
            roi = round((1 - total) * 100, 2)
            stake_a = (inv_a / total) * presupuesto_cop
            stake_b = (inv_b / total) * presupuesto_cop
            ganancia = round(min(stake_a * cuota_a, stake_b * cuota_b) - presupuesto_cop, 2)
            if ganancia >= 40000:
                datos.append({
                    "Cuota A": cuota_a,
                    "Cuota B": round(cuota_b, 2),
                    "ROI (%)": roi,
                    "Ganancia (COP)": ganancia
                })

tabla_sugerencias = pd.DataFrame(datos).sort_values(by="Ganancia (COP)", ascending=False).head(20)
st.dataframe(tabla_sugerencias)

# -----------------------------
# INGRESO DE DATOS MANUAL
# -----------------------------
st.subheader("📝 Ingresar evento y cuotas de hasta 6 casas")

evento = st.text_input("Nombre del evento", value="Ej: Nacional vs Millonarios")
moneda = st.selectbox("Divisa", ["COP", "EUR", "USD"])
presupuesto = st.number_input(f"Presupuesto total ({moneda})", min_value=10.0, value=100000.0, step=1000.0)

casas = []
for i in range(6):
    st.markdown(f"### 🏠 Casa {i+1}")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        nombre = st.text_input(f"Nombre de la casa {i+1}", value=f"Casa {i+1}", key=f"nombre_{i}")
    with col2:
        cuota_local = st.number_input(f"Cuota Local", min_value=1.0, value=1.0, step=0.01, key=f"local_{i}")
    with col3:
        cuota_visitante = st.number_input(f"Cuota Visitante", min_value=1.0, value=1.0, step=0.01, key=f"visitante_{i}")
    casas.append((nombre, cuota_local, cuota_visitante))

# -----------------------------
# CÁLCULO AUTOMÁTICO DE LA MEJOR COMBINACIÓN
# -----------------------------
if st.button("🔍 Evaluar combinaciones"):
    mejores = []
    for i in range(len(casas)):
        for j in range(len(casas)):
            if i == j:
                continue
            nombre1, cuota1_local, cuota1_visitante = casas[i]
            nombre2, cuota2_local, cuota2_visitante = casas[j]

            if cuota1_local > 1 and cuota2_visitante > 1:
                inv1 = 1 / cuota1_local
                inv2 = 1 / cuota2_visitante
                total_inv = inv1 + inv2
                if total_inv < 1:
                    stake1 = round((inv1 / total_inv) * presupuesto)
                    stake2 = round((inv2 / total_inv) * presupuesto)
                    ganancia = round(min(stake1 * cuota1_local, stake2 * cuota2_visitante) - presupuesto, 2)
                    roi = round((1 - total_inv) * 100, 2)
                    mejores.append({
                        "tipo": "Local / Visitante",
                        "casa1": nombre1,
                        "cuota1": cuota1_local,
                        "stake1": stake1,
                        "casa2": nombre2,
                        "cuota2": cuota2_visitante,
                        "stake2": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })

            if cuota2_local > 1 and cuota1_visitante > 1:
                inv1 = 1 / cuota2_local
                inv2 = 1 / cuota1_visitante
                total_inv = inv1 + inv2
                if total_inv < 1:
                    stake1 = round((inv1 / total_inv) * presupuesto)
                    stake2 = round((inv2 / total_inv) * presupuesto)
                    ganancia = round(min(stake1 * cuota2_local, stake2 * cuota1_visitante) - presupuesto, 2)
                    roi = round((1 - total_inv) * 100, 2)
                    mejores.append({
                        "tipo": "Visitante / Local",
                        "casa1": nombre2,
                        "cuota1": cuota2_local,
                        "stake1": stake1,
                        "casa2": nombre1,
                        "cuota2": cuota1_visitante,
                        "stake2": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })

    if mejores:
        top = sorted(mejores, key=lambda x: x["ganancia"], reverse=True)[0]
        st.success("✅ ¡Se encontró una surebet rentable!")
        st.markdown(f"""
**🎯 Evento:** {evento}

🏦 Apostar en:
- **{top['casa1']}**: {top['stake1']} {moneda} a cuota {top['cuota1']}
- **{top['casa2']}**: {top['stake2']} {moneda} a cuota {top['cuota2']}

📈 ROI estimado: **{top['roi']}%**  
💰 Ganancia garantizada: **{top['ganancia']} {moneda}**
""")
    else:
        st.warning("❌ No se encontraron combinaciones rentables con las cuotas ingresadas.")
