# 📞 Call Center AI – Asistente Inteligente de Retención de Clientes

Este proyecto utiliza **FastAPI** en el backend y un **frontend HTML/JS** simple para mostrar clientes con riesgo de abandono.  
Además, se integra con **Google Gemini (IA)** para generar guiones personalizados de retención basados en la probabilidad de churn.

---

## 🚀 Características

✅ Predicción del **riesgo de abandono (churn)** de clientes.  
✅ Generación de **guiones personalizados** para llamadas, con IA (Gemini).  
✅ Interfaz web sencilla e intuitiva.  
✅ Backend optimizado y preparado para **Docker**.  

---

## 🧩 Requisitos previos

Antes de comenzar, asegúrate de tener instalado:

- 🐍 **Python 3.11+**
- 🐳 **Docker** (opcional, si quieres ejecutar en contenedor)
- 💻 **Git**
- 📦 **pip**

---

## ⚙️ Instalación y configuración local

1️⃣ Clona el repositorio:

```bash
git clone https://github.com/tuusuario/callcenter-ai.git
cd callcenter-ai
```

`cp .env.example .env`

Rellene sus credenciales en este archivo 

```bash
docker build -t callcenter-ai .
docker run -d -p 8000:8000 callcenter-ai
```

