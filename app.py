import streamlit as st
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# Configuración básica de la página
st.set_page_config(page_title="Control de Engrasante", layout="centered")
CARPETA_VALES = 'Vales'

# Crear carpeta de Vales si no existe (temporal para la nube)
if not os.path.exists(CARPETA_VALES):
    os.makedirs(CARPETA_VALES)

# --- LISTAS DE DATOS ---
LISTA_OPERADORES = [
    "Seleccione...", "JUAN PEREZ", "PEDRO GOMEZ", "DIEGO LOPEZ", "CARLOS SOTO", 
    "LUIS MARTINEZ", "MIGUEL SILVA", "JORGE ROJAS", "FRANCISCO VEGA", 
    "ALBERTO CASTRO", "MANUEL MUNOZ"
]
LISTA_PATENTES = [
    "Seleccione...", "CXKW-59", "LWTT-25", "KFLP-14", "JTJG-20", "KPDH-49", "FLCC-13", "HZXR-52", "HVBC-43", "FGPJ-94", "ZB40-03"
]
LISTA_EQUIPOS = [
    "Seleccione...", "KOMATSU PC300", "CATERPILLAR 314E", "LIUGONG 922E", "CATERPILLAR 950H", "JHON DEERE 350G", "LIUGONG 922D",
    "LIUGONG 836", "JHON DEERE 210G", "JHON DEERE 724", "KOMATSU PC200"
]

LISTA_GRASAS = [
    "Seleccione...", "MULTIUSO AZUL", "NEGRA DE GRAFITO"
]

# --- FUNCIÓN PARA CREAR EL PDF ---
def generar_vale_pdf(fecha, operador, equipo, patente, tipo_grasa, cantidad):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Insertar el logo (Verifica que el archivo exista para evitar errores)
    ruta_logo = "logo.png"  # Si tu logo es JPG, cámbialo a "logo.jpg"
    if os.path.exists(ruta_logo):
        # image(ruta, posición_X, posición_Y, ancho)
        pdf.image(ruta_logo, x=10, y=8, w=30)
    
    # Título y Encabezado
    pdf.set_font("Arial", 'B', 16)
    # Movemos un poco el texto a la derecha si el logo ocupa espacio en la izquierda
    pdf.cell(200, 10, txt="EMPRESA ARIDOS - SUCURSAL PUERTO MONTT", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="VALE DE ENTREGA DE LUBRICANTE", ln=True, align='C')
    pdf.ln(15) # Salto de línea un poco más grande
    
    # Datos del registro
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Fecha y Hora: {fecha}", ln=True)
    pdf.cell(200, 10, txt=f"Operador Responsable: {operador}", ln=True)
    pdf.cell(200, 10, txt=f"Equipo / Maquinaria: {equipo}", ln=True)
    pdf.cell(200, 10, txt=f"Patente: {patente}", ln=True)
    pdf.cell(200, 10, txt=f"Tipo de Grasa: {tipo_grasa}", ln=True)
    pdf.cell(200, 10, txt=f"Cantidad Entregada: {cantidad} unidades", ln=True)
    
    # Espacio para la firma
    pdf.ln(30)
    pdf.cell(200, 10, txt="_______________________________________", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Firma: {operador}", ln=True, align='C')
    pdf.cell(200, 10, txt="Recibe Conforme", ln=True, align='C')
    
    # Guardar el archivo con nombre único
    nombre_archivo = f"{CARPETA_VALES}/Vale_{patente}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo

# --- INTERFAZ VISUAL ---
st.title("⚙️ Sistema de Control de Engrasante")

with st.form("formulario_engrasante", clear_on_submit=True):
    operador = st.selectbox("Operador", LISTA_OPERADORES)
    equipo = st.selectbox("Equipo", LISTA_EQUIPOS)
    tipo_grasa = st.selectbox("Tipo de Grasa", LISTA_GRASAS)
    patente = st.selectbox("Patente", LISTA_PATENTES)
    cantidad = st.number_input("Cantidad(L/kg)", min_value=0, step=1)
    conn = st.connection("gsheets", type=GSheetsConnection)
    btn_guardar = st.form_submit_button("Guardar Registro y Generar Vale")

# --- LÓGICA DE GUARDADO EN GOOGLE SHEETS ---
if btn_guardar:
    if operador == "Seleccione..." or equipo == "Seleccione..." or tipo_grasa == "Seleccione..." or patente == "Seleccione...":
        st.warning("⚠️ Por favor, seleccione Operador, Equipo, Tipo de Grasa y Patente.")
    elif cantidad <= 0:
        st.error("⚠️ La cantidad debe ser mayor a 0.")
    else:
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        patente_mayus = patente.upper()
        
        # 1. Preparar el nuevo registro
        nuevo_registro = pd.DataFrame({
            "Fecha y Hora": [fecha_actual],
            "Operador": [operador],
            "Equipo": [equipo],
            "Patente": [patente_mayus],
            "Tipo de Grasa": [tipo_grasa],
            "Cantidad": [cantidad]
        })

        try:
            # 2. Conectar a Google Sheets y actualizar
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_existente = conn.read()
            
            # Unir los datos antiguos con el nuevo registro
            df_actualizado = pd.concat([df_existente, nuevo_registro], ignore_index=True)
            
            # Enviar la actualización a Google
            conn.update(data=df_actualizado)
            
            # 3. Generar el PDF
            ruta_pdf = generar_vale_pdf(fecha_actual, operador, equipo, patente_mayus, tipo_grasa, cantidad)
            
            st.success("✅ ¡Registro guardado exitosamente en Google Sheets!")
            
            # 4. Mostrar botón para descargar PDF
            with open(ruta_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📄 Descargar Vale PDF para Firmar",
                    data=pdf_file,
                    file_name=ruta_pdf.split('/')[-1],
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"❌ Ocurrió un error de conexión: {e}. Revisa tus credenciales de Google y asegúrate de que el archivo 'secrets.toml' esté configurado.")