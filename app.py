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
    st.markdown("**La Rienda - Sistema de Gestión y Registros**")

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
    
    *(Nota: El marcador HMS2 se omitirá automáticamente si se deja en blanco, para dar soporte a análisis de laboratorio antiguos).*
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
st.caption("💡 **Tip:** Haz un solo clic en la celda y escribe directamente la letra. Puedes usar la tecla 'Tab' o las flechas de tu teclado para moverte más rápido.")

# Aplicamos estilo de Pandas para centrar el texto
styled_df = st.session_state.df.style.set_properties(**{'text-align': 'center'})

# Agregamos max_chars=1 para limitar a una sola letra por celda
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

# 5. Lógica Genética
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

    # EXCEPCIÓN: Marcador HMS2 en análisis viejos
    if row['Marcador'] == 'HMS2' and (not c_alelos or (not m_alelos and not p_alelos)):
        return "Omitido"

    if not c_alelos: return "Faltan datos"
    if not m_alelos and not p_alelos: return "Faltan datos"

    # Verificación de exclusión Mendeliana
    if m_alelos and p_alelos:
        if len(c_alelos) == 1:
            c_val = list(c_alelos)[0]
            if c_val in m_alelos and c_val in p_alelos: return "Compatible"
            else: return "Excluido"
        else:
            ca, cb = list(c_alelos)[0], list(c_alelos)[1]
            if (ca in m_alelos and cb in p_alelos) or (cb in m_alelos and ca in p_alelos):
                return "Compatible"
            else: return "Excluido"
    elif m_alelos:
        if any(a in m_alelos for a in c_alelos): return "Compatible"
        else: return "Excluido"
    elif p_alelos:
        if any(a in p_alelos for a in c_alelos): return "Compatible"
        else: return "Excluido"
    
    return "Error"

st.markdown("---")

# 6. Procesamiento y Dictamen Final
if st.button("🔍 Validar Compatibilidad", type="primary", use_container_width=False):
    edited_df['Resultado'] = edited_df.apply(validar_marcador, axis=1)
    
    # Filtramos tanto los que faltan datos como el omitido a propósito para que no cuenten como error
    marcadores_evaluados = edited_df[~edited_df['Resultado'].isin(["Faltan datos", "Error", "Omitido"])]
    excluidos = marcadores_evaluados[marcadores_evaluados['Resultado'] == "Excluido"].shape[0]
    
    # Detectar qué progenitores fueron cargados (ignorando la fila del HMS2 para no dar falsos negativos)
    df_sin_hms2 = edited_df[edited_df['Marcador'] != 'HMS2']
    hay_madre = df_sin_hms2['Madre_A1'].replace("", None).notna().any() or df_sin_hms2['Madre_A2'].replace("", None).notna().any()
    hay_padre = df_sin_hms2['Padre_A1'].replace("", None).notna().any() or df_sin_hms2['Padre_A2'].replace("", None).notna().any()
    hay_cria = df_sin_hms2['Cria_A1'].replace("", None).notna().any() or df_sin_hms2['Cria_A2'].replace("", None).notna().any()

    st.markdown("### 📋 Dictamen Final")
    
    if not hay_cria or (not hay_madre and not hay_padre):
        st.info("⚠️ Ingresa los datos de la cría y de al menos un progenitor para obtener el dictamen.")
    else:
        if excluidos > 0:
            st.error("🚨 **No compatible**")
        else:
            if hay_madre and hay_padre:
                st.success("✅ **Coincide con Padre y Madre**")
            elif hay_madre:
                st.success("✅ **Coincide con Madre**")
            elif hay_padre:
                st.success("✅ **Coincide con Padre**")
                
    st.markdown("### 📊 Detalle por Marcador")
    
    df_visual = edited_df[['Marcador', 'Resultado']].copy()
    df_visual['Resultado'] = df_visual['Resultado'].replace({
        "Compatible": "✅ Compatible", 
        "Excluido": "❌ Excluido",
        "Omitido": "⚪ Omitido (Análisis antiguo)"
    })
    
    styled_visual = df_visual.style.set_properties(**{'text-align': 'center'})
    st.dataframe(styled_visual, hide_index=True, use_container_width=False, height=565)
