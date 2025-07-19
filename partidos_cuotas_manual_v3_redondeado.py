# partidos_cuotas_manual_simple.py
# Evaluador de surebets simplificado sin tabla de sugerencias

import streamlit as st

st.set_page_config(page_title="Calculadora de Surebets", layout="centered")
st.title("📊 Calculadora Manual de Surebets (hasta 6 casas)")

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

if st.button("🔍 Evaluar combinaciones"):
    mejores = []
    for i in range(len(casas)):
        for j in range(len(casas)):
            if i == j:
                continue
            nombre1, c1_local, c1_visit = casas[i]
            nombre2, c2_local, c2_visit = casas[j]

            # 1) Local / Visitante
            if c1_local > 1 and c2_visit > 1:
                inv1 = 1 / c1_local
                inv2 = 1 / c2_visit
                total_inv = inv1 + inv2
                if total_inv < 1:
                    stake1 = round((inv1 / total_inv) * presupuesto)
                    stake2 = round((inv2 / total_inv) * presupuesto)
                    ganancia = round(min(stake1 * c1_local, stake2 * c2_visit) - presupuesto)
                    roi = round((1 - total_inv) * 100, 2)
                    mejores.append({
                        "tipo": "Local / Visitante",
                        "casa1": nombre1,
                        "cuota1": c1_local,
                        "stake1": stake1,
                        "casa2": nombre2,
                        "cuota2": c2_visit,
                        "stake2": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })

            # 2) Visitante / Local
            if c2_local > 1 and c1_visit > 1:
                inv1 = 1 / c2_local
                inv2 = 1 / c1_visit
                total_inv = inv1 + inv2
                if total_inv < 1:
                    stake1 = round((inv1 / total_inv) * presupuesto)
                    stake2 = round((inv2 / total_inv) * presupuesto)
                    ganancia = round(min(stake1 * c2_local, stake2 * c1_visit) - presupuesto)
                    roi = round((1 - total_inv) * 100, 2)
                    mejores.append({
                        "tipo": "Visitante / Local",
                        "casa1": nombre2,
                        "cuota1": c2_local,
                        "stake1": stake1,
                        "casa2": nombre1,
                        "cuota2": c1_visit,
                        "stake2": stake2,
                        "ganancia": ganancia,
                        "roi": roi
                    })

    if mejores:
        top = sorted(mejores, key=lambda x: x["ganancia"], reverse=True)[0]
        st.success("✅ ¡Surebet encontrada!")
        st.markdown(f"""
**🎯 Evento:** {evento}

🏦 Apuesta recomendada:
- **{top['casa1']}**: **${top['stake1']:,} {moneda}** a cuota {top['cuota1']}
- **{top['casa2']}**: **${top['stake2']:,} {moneda}** a cuota {top['cuota2']}

📈 ROI: **{top['roi']}%**  
💰 Ganancia asegurada: **${top['ganancia']:,} {moneda}**
""")
    else:
        st.warning("❌ No se encontraron combinaciones rentables.")
