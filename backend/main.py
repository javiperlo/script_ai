import joblib
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse  
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import warnings
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

# --- 1. Setup ---
warnings.filterwarnings('ignore')
app = FastAPI(title="API Completa de Churn (con Preprocesamiento)")
MODEL_PATH = "backend/models/modelo_xgb.joblib"

genai.configure(api_key=os.getenv("GEMINI_API"))

modelo_cargado = None
columnas_modelo = None # Lista de TODAS las columnas que el modelo espera

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir carpeta /frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join("frontend", "index.html"))

# --- 2. Cargar Modelo (Solo al inicio) ---
@app.on_event("startup")
def cargar_modelo():
    global modelo_cargado, columnas_modelo
    
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Error: No se encuentra el modelo en {MODEL_PATH}")
        
    modelo_cargado = joblib.load(MODEL_PATH)
    
    try:
        # Esto es vital: obtenemos la lista de todas las columnas del modelo
        columnas_modelo = modelo_cargado.feature_names_in_
        print(f"Modelo cargado. Espera {len(columnas_modelo)} columnas.")
    except AttributeError:
        raise RuntimeError("Error: El modelo no tiene 'feature_names_in_'. No se puede alinear.")

# --- 3. Definir Entrada (¡TODAS las 19 columnas crudas!) ---
class DatosCliente(BaseModel):
    gender: str                 # 'Female', 'Male'
    SeniorCitizen: int          # 0, 1
    Partner: str                # 'Yes', 'No'
    Dependents: str             # 'Yes', 'No'
    tenure: int                 # 1, 34, 45...
    PhoneService: str           # 'Yes', 'No'
    MultipleLines: str          # 'No phone service', 'No', 'Yes'
    InternetService: str        # 'DSL', 'Fiber optic', 'No'
    OnlineSecurity: str         # 'No', 'Yes', 'No internet service'
    OnlineBackup: str           # 'Yes', 'No', 'No internet service'
    DeviceProtection: str       # 'No', 'Yes', 'No internet service'
    TechSupport: str            # 'No', 'Yes', 'No internet service'
    StreamingTV: str            # 'No', 'Yes', 'No internet service'
    StreamingMovies: str        # 'No', 'Yes', 'No internet service'
    Contract: str               # 'Month-to-month', 'One year', 'Two year'
    PaperlessBilling: str       # 'Yes', 'No'
    PaymentMethod: str          # 'Electronic check', 'Mailed check', ...
    MonthlyCharges: float       # 29.85, 56.95,...
    TotalCharges: float | str   # Acepta float o string (ej. " " o "29.85")
    
    class Config:
        extra = 'ignore' # Ignora campos extra si el usuario los envía


# --- 4. Endpoint de Predicción ---
@app.post("/predict") # Cambiado de /predict_simple a /predict
async def predecir(datos: DatosCliente): # Cambiado de DatosSencillos a DatosCliente
    if modelo_cargado is None:
        raise HTTPException(status_code=500, detail="El modelo no está cargado.")

    try:
        # a. Convertir datos de Pydantic a DataFrame de 1 fila
        cliente_df = pd.DataFrame([datos.model_dump()])
        
        # b. ¡AQUÍ VA EL PREPROCESAMIENTO COMPLETO!
        df_procesado = cliente_df.copy()

        # b1. Manejar 'TotalCharges' (convertir " " a 0)
        df_procesado['TotalCharges'] = pd.to_numeric(df_procesado['TotalCharges'], errors='coerce').fillna(0)

        # b2. Mapear columnas binarias (Yes/No y Gender)
        map_yes_no = {'Yes': 1, 'No': 0}
        df_procesado['Partner'] = df_procesado['Partner'].map(map_yes_no)
        df_procesado['Dependents'] = df_procesado['Dependents'].map(map_yes_no)
        df_procesado['PhoneService'] = df_procesado['PhoneService'].map(map_yes_no)
        df_procesado['PaperlessBilling'] = df_procesado['PaperlessBilling'].map(map_yes_no)
        df_procesado['gender'] = df_procesado['gender'].map({'Female': 0, 'Male': 1}) # Asumiendo Female=0

        # b3. Crear Variables Dummy (One-Hot Encoding)
        columnas_dummies = [
            'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
            'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
            'Contract', 'PaymentMethod'
        ]
        df_procesado = pd.get_dummies(df_procesado, columns=columnas_dummies)
        
        # c. ¡EL TRUCO! Crear el DataFrame completo que el modelo espera
        #    Rellena con 0 las columnas que el cliente no tiene
        cliente_df_final = df_procesado.reindex(columns=columnas_modelo, fill_value=0)

        # d. Hacer la predicción
        probabilidades = modelo_cargado.predict_proba(cliente_df_final)
        prob_churn = probabilidades[0][1] # Probabilidad de Churn (Clase 1)

        # e. Devolver el resultado (con tu lógica de umbral)
        
        THREESHOLD = 0.65 # Puedes ajustar este umbral de negocio
        churn = False
        if float(prob_churn) > THREESHOLD:
            churn = True
        
        return {
            "probabilidad_churn": float(round(prob_churn, 4)),
            "CHURN": churn,
            "umbral_utilizado": THREESHOLD
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la predicción: {e}")
    
# Modelo de entrada
class Cliente(BaseModel):
    nombre: str
    edad: int
    probabilidad_churn: float  # 👈 ahora añadimos también este campo

@app.post("/generate_script")
async def generate_script(cliente: Cliente):
    nombre = cliente.nombre
    edad = cliente.edad
    prob = cliente.probabilidad_churn

    # Definir tono según el riesgo de churn
    if prob > 0.65:
        tono = "urgente y muy persuasivo"
        enfoque = "ofrece descuentos exclusivos y beneficios fuertes"
    elif prob > 0.45:
        tono = "convincente y amable"
        enfoque = "resalta comodidad, soporte y beneficios del servicio"
    else:
        tono = "relajado y de agradecimiento"
        enfoque = "refuerza la satisfacción del cliente y su buena decisión"

    # Prompt dinámico para Gemini
    prompt = f"""
    Añade como header: {prob} en porcentaje. De la siguiente manera. Posibilidad CHURN: 83% (por) 
    Eres un asistente experto en retención de clientes para un call center de telecomunicaciones.
    Tu tarea es generar un guion breve con 3 ideas claras y persuasivas (en formato de viñetas)
    que el agente pueda usar para convencer a {nombre} de seguir siendo cliente.

    👉 Datos relevantes del cliente:
    - Edad aproximada: {edad} años
    - Probabilidad estimada de abandono: {(prob * 100):.1f}%

    📋 Instrucciones específicas:
    - Crea exactamente 3 bullet points (uno por línea, con "•" al inicio).
    - Cada punto debe ser concreto, amable y fácil de decir por teléfono.
    - Enfócate en beneficios reales (ahorro, comodidad, atención personalizada, tecnología, soporte, etc.).
    - Usa un tono {tono}, y {enfoque}.
    - No incluyas frases introductorias ni conclusiones.
    - No uses lenguaje técnico, sino cercano y convincente.
    - No repitas ideas.

    🎯 Objetivo:
    Que {nombre} sienta que quedarse con la empresa es su mejor opción y se sienta valorado.
    """

    # Generar contenido con Gemini
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)

    return {"guion": response.text}