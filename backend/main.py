import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
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

warnings.filterwarnings('ignore')
app = FastAPI(title="API | Tarea CHURN")

MODEL_PATH = "backend/models/modelo_xgb.joblib"
FRONTEND_DIR = "frontend"
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

genai.configure(api_key=os.getenv("GEMINI_API"))

modelo_cargado = None
columnas_modelo = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def cargar_modelo():
    global modelo_cargado, columnas_modelo
    
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Error: No se encuentra el modelo en {MODEL_PATH}")
        
    modelo_cargado = joblib.load(MODEL_PATH)
    
    try:
        columnas_modelo = modelo_cargado.feature_names_in_
        print(f"✅ Modelo cargado. Espera {len(columnas_modelo)} columnas.")
    except AttributeError:
        raise RuntimeError("Error: El modelo no tiene 'feature_names_in_'.")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html no encontrado")
    return FileResponse(index_path)

# --- 4. Definir Entrada ---
class DatosCliente(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float | str
    
@app.post("/predict")
async def predecir(datos: DatosCliente):
    if modelo_cargado is None:
        raise HTTPException(status_code=500, detail="El modelo no está cargado.")

    try:
        cliente_df = pd.DataFrame([datos.model_dump()])
        df_procesado = cliente_df.copy()

        df_procesado['TotalCharges'] = pd.to_numeric(df_procesado['TotalCharges'], errors='coerce').fillna(0)

        map_yes_no = {'Yes': 1, 'No': 0}
        df_procesado['Partner'] = df_procesado['Partner'].map(map_yes_no)
        df_procesado['Dependents'] = df_procesado['Dependents'].map(map_yes_no)
        df_procesado['PhoneService'] = df_procesado['PhoneService'].map(map_yes_no)
        df_procesado['PaperlessBilling'] = df_procesado['PaperlessBilling'].map(map_yes_no)
        df_procesado['gender'] = df_procesado['gender'].map({'Female': 0, 'Male': 1})

        columnas_dummies = [
            'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
            'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
            'Contract', 'PaymentMethod'
        ]
        df_procesado = pd.get_dummies(df_procesado, columns=columnas_dummies)
        
        cliente_df_final = df_procesado.reindex(columns=columnas_modelo, fill_value=0)

        probabilidades = modelo_cargado.predict_proba(cliente_df_final)
        prob_churn = probabilidades[0][1]

        THREESHOLD = 0.65
        churn = float(prob_churn) > THREESHOLD
        
        return {
            "probabilidad_churn": float(round(prob_churn, 4)),
            "CHURN": churn,
            "umbral_utilizado": THREESHOLD
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la predicción: {e}")

# Aquí creamos el modelo de Cliente y los datos que recibirá
# Tengo que mejorarlo el prompt y el objeto en sí aun

class Cliente(BaseModel):
    nombre: str
    edad: int
    probabilidad_churn: float
    

# Creamos el endpoint que recibirá el json

@app.post("/generate_script")
async def generate_script(cliente: Cliente):
    nombre = cliente.nombre
    edad = cliente.edad
    prob = cliente.probabilidad_churn

    if prob > 0.65:
        tono = "urgente y muy persuasivo"
        enfoque = "ofrece descuentos exclusivos y beneficios fuertes"
    elif prob > 0.45:
        tono = "convincente y amable"
        enfoque = "resalta comodidad, soporte y beneficios del servicio"
    else:
        tono = "relajado y de agradecimiento"
        enfoque = "refuerza la satisfacción del cliente y su buena decisión"

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

    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)

    return {"guion": response.text}