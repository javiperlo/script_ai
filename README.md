# 📞 Script AI - Predicción de Churn + Generación de Guiones con IA

Este proyecto tiene como objetivo identificar a los clientes que están en **riesgo de abandonar el servicio** en un futuro cercano para poder ofrecerles **incentivos personalizados** (descuentos, mejoras de servicios, etc.) antes de que tomen la decisión de irse.

<p align="center">
  <img src="documentation/imgs/script_ai_project.png"/>
</p>


---

## 🧭 Metodología CRISP-DM

Para el desarrollo del proyecto se ha seguido la metodología **CRISP-DM**, la cual consta de 6 fases:

1. [**Entendimiento del negocio**](documentation/data_analysis.ipynb)
2. [**Entendimiento de los datos**](documentation/data_analysis.ipynb)
3. [**Preparación de los datos**](documentation/model_creation.ipynb)
4. [**Modelado**](documentation/model_creation.ipynb)
5. [**Evaluación**](documentation/model_creation.ipynb)
6. [**Despliegue**](documentation/model_creation.ipynb)

---

## 🚀 Más allá del proyecto original

He decidido llevar este proyecto mucho más allá de lo que se nos pide.  
Quiero crear el modelo predictivo, pero que podamos acceder a este **mediante una API desde cualquier lugar (subido en la nube)** y que, con los datos que le introduzcamos, haga una **predicción de riesgo de abandono**.  

Con esa predicción, **Gemini** generará automáticamente una **campaña publicitaria personalizada** de *email marketing*, con **imágenes generadas por IA** adaptadas a cada cliente.

---

## 🧩 Arquitectura general del proyecto

La estructura conceptual del sistema es la siguiente:

<p align="center">
  <img src="documentation/imgs/EsquemaProyectoDibujo_mejorado.png" width="600" />
</p>

---

## ⚙️ Instalación y ejecución

### 1️⃣ Clonar el repositorio
```bash
git clone https://github.com/tuusuario/script_ai.git
cd script_ai
