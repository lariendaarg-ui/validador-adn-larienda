import streamlit as st
import pandas as pd

# 1. Configuración general
st.set_page_config(page_title="Validador ADN Equino | La Rienda", page_icon="🐴", layout="wide")

# 2. Diseño de Cabecera
col1, col2 = st.columns([1, 6])

with col1:
    try:
        st.image("logo.png", width=120) 
    except FileNotFoundError:
        st.markdown("## 🐴")

with col2:
    st.title("Validador de ADN Equino")
    st.markdown("**La Rienda - Gestión Genealógica y Registros Equinos**")

st.markdown("---")

# 3. Panel de instrucciones
with st.expander("ℹ️ ¿Cómo funciona este validador?", expanded=False):
    st.markdown("""
    **Objetivo:**
    Verificar la compatibilidad genética entre una cría y sus presuntos progenitores antes de presentar el estudio oficial.
    
    **Instrucciones de uso:**
    1. Ingresa los alelos (letras) correspondientes a cada marcador según el certificado de ADN.
    2. Puedes validar contra ambos padres (Trío) o contra uno solo (Dúo).
    3. Presiona el botón **Validar Compatibilidad** al final de la tabla para obtener el dictamen.
    
    """)

# 4. Tabla de datos
marcadores = ['VHL20', 'HTG4', 'AHT4', 'HMS7', 'ASB2', 'ASB17', 'AHT5', 'HMS6', 'ASB23', 'HTG10', 'HMS3', 'HMS2', 'CA425', 'TKY325', 'TKY28']

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Marcador": marcadores,
        "Madre_A1": [""]*15, "Madre_A2": [""]*15,
        "Padre_A1": [""]*15, "Padre_A2": [""]*15,
        "Cria_A1": [""]*15,  "Cria_A2": [""]*15
    })

st.markdown("### 🧬 Datos Genéticos")
st.caption("💡 **Tip:** Haz un solo clic en la celda y escribe directamente la letra. Puedes usar la tecla 'Tab' o las flechas de tu teclado para moverte más rápido. Si estas desde el celular debes pulsar 2 veces sobre la celda para escribir")

styled_df = st.session_state.df.style.set_properties(**{'text-align': 'center'})

edited_df = st.data_editor(
    styled_df,
    column_config={
        "Marcador": st.column_config.TextColumn("Marcador", disabled=True),
        "Madre_A1": st.column_config.TextColumn("Madre 1", max_chars=1),
        "Madre_A2": st.column_config.TextColumn("Madre 2", max_chars=1),
        "Padre_A1": st.column_config.TextColumn("Padre 1", max_chars=1),
        "Padre_A2": st.column_config.TextColumn("Padre 2", max_chars=1),
        "Cria_A1": st.column_config.TextColumn("Cría 1", max_chars=1),
        "Cria_A2": st.column_config.TextColumn("Cría 2", max_chars=1),
    },
    hide_index=True,
    use_container_width=False,
    height=565,
    num_rows="fixed"
)

# 5. Lógica Genética Mejorada
def validar_marcador(row):
    def limpiar(val):
        return str(val).strip().upper() if pd.notna(val) and str(val).strip() != "" else None

    m1, m2 = limpiar(row['Madre_A1']), limpiar(row['Madre_A2'])
    p1, p2 = limpiar(row['Padre_A1']), limpiar(row['Padre_A2'])
    c1, c2 = limpiar(row['Cria_A1']), limpiar(row['Cria_A2'])

    if m1 and not m2: m2 = m1
    if m2 and not m1: m1 = m2
    if p1 and not p2: p2 = p1
    if p2 and not p1: p1 = p2
    if c1 and not c2: c2 = c1
    if c2 and not c1: c1 = c2

    c_alelos = {c1, c2} - {None}
    m_alelos = {m1, m2} - {None}
    p_alelos = {p1, p2} - {None}

    if row['Marcador'] == 'HMS2' and (not c_alelos or (not m_alelos and not p_alelos)):
        return "Omitido"

    if not c_alelos: return "Faltan datos"
    if not m_alelos and not p_alelos: return "Faltan datos"

    # Si se cargaron ambos padres
    if m_alelos and p_alelos:
        if len(c_alelos) == 1:
            c_val = list(c_alelos)[0]
            if c_val in m_alelos and c_val in p_alelos: 
                return "Compatible con Padre y Madre"
            elif c_val in m_alelos:
                return "Compatible con Madre"
            elif c_val in p_alelos:
                return "Compatible con Padre"
            else: 
                return "No compatible"
        else:
            ca, cb = list(c_alelos)[0], list(c_alelos)[1]
            both_match = (ca in m_alelos and cb in p_alelos) or (cb in m_alelos and ca in p_alelos)
            if both_match:
                return "Compatible con Padre y Madre"
            m_match = (ca in m_alelos) or (cb in m_alelos)
            p_match = (ca in p_alelos) or (cb in p_alelos)
            
            if m_match and p_match:
                return "Compatible con Padre y Madre"
            elif m_match:
                return "Compatible con Madre"
            elif p_match:
                return "Compatible con Padre"
            else:
                return "No compatible"
                
    elif m_alelos:
        if any(a in m_alelos for a in c_alelos): return "Compatible con Madre"
        else: return "No compatible"
        
    elif p_alelos:
        if any(a in p_alelos for a in c_alelos): return "Compatible con Padre"
        else: return "No compatible"
    
    return "Error"

st.markdown("---")

# 6. Procesamiento y Dictamen Final
if st.button("🔍 Validar Compatibilidad", type="primary", use_container_width=False):
    edited_df['Resultado'] = edited_df.apply(validar_marcador, axis=1)
    
    excluidos_madre = 0
    excluidos_padre = 0
    hay_madre = False
    hay_padre = False
    hay_cria = False
    
    for idx, row in edited_df.iterrows():
        def has_data(a1, a2):
            return (pd.notna(a1) and str(a1).strip() != "") or (pd.notna(a2) and str(a2).strip() != "")
            
        m_present = has_data(row['Madre_A1'], row['Madre_A2'])
        p_present = has_data(row['Padre_A1'], row['Padre_A2'])
        c_present = has_data(row['Cria_A1'], row['Cria_A2'])
        
        if m_present: hay_madre = True
        if p_present: hay_padre = True
        if c_present: hay_cria = True
        
        res = row['Resultado']
        if res in ["Faltan datos", "Error", "Omitido"]:
            continue
            
        if m_present and p_present:
            if res == "Compatible con Madre": excluidos_padre += 1
            elif res == "Compatible con Padre": excluidos_madre += 1
            elif res == "No compatible": 
                excluidos_madre += 1
                excluidos_padre += 1
        elif m_present:
            if res == "No compatible": excluidos_madre += 1
        elif p_present:
            if res == "No compatible": excluidos_padre += 1

    st.markdown("### 📋 Dictamen Final")
    
    if not hay_cria or (not hay_madre and not hay_padre):
        st.info("⚠️ Ingresa los datos de la cría y de al menos un progenitor para obtener el dictamen.")
    else:
        if hay_madre and hay_padre:
            if excluidos_madre == 0 and excluidos_padre == 0:
                st.success("✅ **Coincide con Padre y Madre**")
            elif excluidos_madre > 0 and excluidos_padre > 0:
                st.error("🚨 **No compatible con ninguno de los dos**")
            elif excluidos_padre > 0:
                st.success("✅ **Coincide con Madre**")
                st.warning(f"⚠️ El presunto padre está excluido ({excluidos_padre} marcadores fallidos).")
            elif excluidos_madre > 0:
                st.success("✅ **Coincide con Padre**")
                st.warning(f"⚠️ La presunta madre está excluida ({excluidos_madre} marcadores fallidos).")
        elif hay_madre:
            if excluidos_madre == 0:
                st.success("✅ **Coincide con Madre**")
            else:
                st.error(f"🚨 **No compatible** ({excluidos_madre} marcadores excluidos para la madre)")
        elif hay_padre:
            if excluidos_padre == 0:
                st.success("✅ **Coincide con Padre**")
            else:
                st.error(f"🚨 **No compatible** ({excluidos_padre} marcadores excluidos para el padre)")
                
    st.markdown("### 📊 Detalle por Marcador")
    
    df_visual = edited_df[['Marcador', 'Resultado']].copy()
    df_visual['Resultado'] = df_visual['Resultado'].replace({
        "Compatible con Padre y Madre": "✅ Compatible con Padre y Madre", 
        "Compatible con Madre": "✅ Compatible con Madre",
        "Compatible con Padre": "✅ Compatible con Padre",
        "No compatible": "❌ No compatible",
        "Omitido": "⚪ Omitido (Análisis antiguo)"
    })
    
    styled_visual = df_visual.style.set_properties(**{'text-align': 'center'})
    st.dataframe(styled_visual, hide_index=True, use_container_width=False, height=565)

# 7. Pie de página - Datos de Contacto
st.markdown("---")
st.markdown("### 📞 Contacto La Rienda")

col_contacto1, col_contacto2, col_contacto3 = st.columns(3)

with col_contacto1:
    st.markdown("📱 **WhatsApp:** [+54 9 11 3272-7729](https://wa.me/5491132727729)")
with col_contacto2:
    st.markdown("📧 **Email:** [larienda.arg@gmail.com](mailto:larienda.arg@gmail.com)")
with col_contacto3:
    st.markdown("📷 **Instagram:** [@larienda.arg](https://instagram.com/larienda.arg)")

st.caption("© 2026 La Rienda. Todos los derechos reservados.")
