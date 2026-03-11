import streamlit as st
import pandas as pd
import os
import pytz
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
    "Seleccione...", "JUAN URIBE", "JULIO ÁVILA", "FEDERIC DIAZ", "IVÁN SCHMUCK", 
    "IVÁN RODRIGUEZ", "LEITON MENDEZ", "Planta 1", "Planta 3"
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
    operador = st.selectbox("Operador/Planta", LISTA_OPERADORES)
    equipo = st.selectbox("Equipo", LISTA_EQUIPOS)
    tipo_grasa = st.selectbox("Tipo de Grasa", LISTA_GRASAS)
    patente = st.selectbox("Patente", LISTA_PATENTES)
    cantidad = st.number_input("Cantidad(L/kg)", min_value=0, step=1)
    conn = st.connection("gsheets", type=GSheetsConnection)
    btn_guardar = st.form_submit_button("Guardar Registro y Generar Vale")

# --- LÓGICA DE GUARDADO EN GOOGLE SHEETS ---
if btn_guardar:
    if operador == "Seleccione..." or equipo == "Seleccione..." or tipo_grasa == "Seleccione..." or patente == "Seleccione...":
        st.warning("⚠️ Por favor, seleccione todos los campos.")
    elif cantidad <= 0:
        st.error("⚠️ La cantidad debe ser mayor a 0.")
    else:
        # 1. Definir la zona horaria
        zona_chile = pytz.timezone('America/Santiago')
        
        # 2. Pasamos 'zona_chile' dentro de now() para que use la hora de Chile
        fecha_actual = datetime.now(zona_chile).strftime("%Y-%m-%d %H:%M:%S")
        
        nuevo_registro = pd.DataFrame({
            "Fecha y Hora": [fecha_actual],
            "Operador/Planta": [operador],
            "Equipo": [equipo],
            "Patente": [patente],
            "Tipo de Grasa": [tipo_grasa],
            "Cantidad": [cantidad]
        })
        
        try:
            # 1. LEER: Es fundamental usar ttl=0 aquí para ver TODAS las filas reales
            df_existente = conn.read(ttl=0)
            
            # Limpiamos filas vacías que puedan haber quedado por borrados manuales
            df_existente = df_existente.dropna(how='all')
            
            # 2. UNIR: Concatenamos lo viejo con lo nuevo
            df_actualizado = pd.concat([df_existente, nuevo_registro], ignore_index=True)
            
            # 3. ACTUALIZAR: Subimos la lista completa de nuevo a Google
            conn.update(data=df_actualizado)
            
            # Generar PDF y mostrar éxito
            ruta_pdf = generar_vale_pdf(fecha_actual, operador, equipo, patente, tipo_grasa, cantidad)
            st.success("✅ ¡Registro guardado exitosamente!")
            
            with open(ruta_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📄 Descargar Vale PDF",
                    data=pdf_file,
                    file_name=ruta_pdf.split('/')[-1],
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"❌ Error al conectar con Google Sheets: {e}")
            
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
            # --- TABLA DE RESUMEN (Historial) ---
st.markdown("---")
st.subheader("📊 Últimos 5 Registros")

try:
    # Volvemos a leer para mostrar lo más nuevo
    df_visualizacion = conn.read()
    if not df_visualizacion.empty:
        # Mostramos los últimos 5, ordenados por los más recientes arriba
        st.dataframe(df_visualizacion.tail(5).iloc[::-1], use_container_width=True)
    else:
        st.info("Aún no hay registros en la base de datos.")
except:
    st.write("Cargando historial...")







