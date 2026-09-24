# ============================================================
# API FASTAPI - CROP YIELD
# ============================================================
# Cette API charge le pipeline de Machine Learning entraîné
# et expose des endpoints pour :
# - vérifier l'état de l'API ;
# - récupérer les métadonnées ;
# - prédire le rendement d'une culture ;
# - recommander les cultures selon leur rendement prédit.


from pathlib import Path
import json

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# ============================================================
# CHEMINS DU PROJET
# ============================================================

# Racine du projet.
BASE_DIR = Path(__file__).resolve().parent.parent

# Modèle entraîné.
MODEL_PATH = (
    BASE_DIR
    / "models"
    / "crop_yield_pipeline.joblib"
)

# Métadonnées associées au modèle.
METADATA_PATH = (
    BASE_DIR
    / "models"
    / "model_metadata.json"
)


# ============================================================
# CHARGEMENT DU MODÈLE ET DES MÉTADONNÉES
# ============================================================

# Le modèle est chargé une seule fois au démarrage de l'API.
model = joblib.load(MODEL_PATH)

# Chargement des informations utiles :
# cultures, zones, métriques, variables, etc.
with open(
    METADATA_PATH,
    "r",
    encoding="utf-8"
) as f:
    metadata = json.load(f)


# ============================================================
# INITIALISATION DE FASTAPI
# ============================================================

app = FastAPI(
    title="Crop Yield API",
    description=(
        "API de prédiction du rendement agricole "
        "et de recommandation de cultures"
    ),
    version="1.0.0"
)


# ============================================================
# SCHÉMAS DES DONNÉES EN ENTRÉE
# ============================================================

# Données nécessaires pour prédire le rendement
# d'une culture précise.
class PredictionInput(BaseModel):

    area: str

    crop: str

    year: int = Field(
        ge=1900,
        le=2100
    )

    rainfall_mm: float = Field(
        ge=0
    )

    pesticides_tonnes: float = Field(
        ge=0
    )

    avg_temp: float


# Données nécessaires pour comparer toutes les cultures.
# La culture n'est pas demandée car l'API va automatiquement
# tester toutes les cultures disponibles.
class RecommendationInput(BaseModel):

    area: str

    year: int = Field(
        ge=1900,
        le=2100
    )

    rainfall_mm: float = Field(
        ge=0
    )

    pesticides_tonnes: float = Field(
        ge=0
    )

    avg_temp: float


# ============================================================
# ENDPOINT RACINE
# ============================================================

@app.get("/")
def root():

    return {
        "status": "ok",
        "message": "Crop Yield API is running"
    }


# ============================================================
# ENDPOINT HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model_loaded": True,
        "available_crops": len(
            metadata["available_crops"]
        ),
        "available_areas": len(
            metadata["available_areas"]
        )
    }


# ============================================================
# ENDPOINT MÉTADONNÉES
# ============================================================

# Cet endpoint permet à Streamlit de récupérer les cultures
# et zones réellement connues pendant l'entraînement.
#
# Ainsi, Streamlit n'a pas besoin d'accéder directement
# au fichier model_metadata.json.
@app.get("/metadata")
def get_metadata():

    return {
        "available_crops": metadata[
            "available_crops"
        ],
        "available_areas": metadata[
            "available_areas"
        ]
    }


# ============================================================
# ENDPOINT DE PRÉDICTION
# ============================================================

@app.post("/predict")
def predict(data: PredictionInput):

    # --------------------------------------------------------
    # Vérification de la culture
    # --------------------------------------------------------

    # Une culture inconnue ne doit pas être envoyée au modèle.
    if data.crop not in metadata["available_crops"]:

        raise HTTPException(
            status_code=400,
            detail=f"Culture inconnue : {data.crop}"
        )

    # --------------------------------------------------------
    # Vérification de la zone
    # --------------------------------------------------------

    # On limite volontairement les prédictions aux zones
    # réellement observées pendant l'entraînement.
    if data.area not in metadata["available_areas"]:

        raise HTTPException(
            status_code=400,
            detail=f"Zone inconnue : {data.area}"
        )

    # --------------------------------------------------------
    # Construction des données attendues par le pipeline
    # --------------------------------------------------------

    input_df = pd.DataFrame([
        {
            "Area_std": data.area,
            "Item": data.crop,
            "Year": data.year,
            "rainfall_mm": data.rainfall_mm,
            "pesticides_tonnes":
                data.pesticides_tonnes,
            "avg_temp": data.avg_temp
        }
    ])

    # --------------------------------------------------------
    # Prédiction
    # --------------------------------------------------------

    prediction = model.predict(
        input_df
    )[0]

    # --------------------------------------------------------
    # Réponse JSON
    # --------------------------------------------------------

    return {
        "crop": data.crop,
        "predicted_yield_t_ha": round(
            float(prediction),
            3
        )
    }


# ============================================================
# ENDPOINT DE RECOMMANDATION
# ============================================================

@app.post("/recommend")
def recommend(data: RecommendationInput):

    # --------------------------------------------------------
    # Vérification de la zone
    # --------------------------------------------------------

    if data.area not in metadata["available_areas"]:

        raise HTTPException(
            status_code=400,
            detail=f"Zone inconnue : {data.area}"
        )

    # --------------------------------------------------------
    # Récupération des cultures disponibles
    # --------------------------------------------------------

    crops = metadata["available_crops"]

    # --------------------------------------------------------
    # Création d'une observation par culture
    # --------------------------------------------------------

    # Les conditions restent identiques.
    # Seule la culture change.
    candidates = pd.DataFrame(
        {
            "Area_std":
                [data.area] * len(crops),

            "Item":
                crops,

            "Year":
                [data.year] * len(crops),

            "rainfall_mm":
                [data.rainfall_mm] * len(crops),

            "pesticides_tonnes":
                [data.pesticides_tonnes] * len(crops),

            "avg_temp":
                [data.avg_temp] * len(crops)
        }
    )

    # --------------------------------------------------------
    # Prédictions
    # --------------------------------------------------------

    predictions = model.predict(
        candidates
    )

    # --------------------------------------------------------
    # Construction des résultats
    # --------------------------------------------------------

    recommendations = [
        {
            "crop": crop,
            "predicted_yield_t_ha": round(
                float(prediction),
                3
            )
        }
        for crop, prediction in zip(
            crops,
            predictions
        )
    ]

    # --------------------------------------------------------
    # Classement
    # --------------------------------------------------------

    # Les cultures sont classées du rendement prédit
    # le plus élevé au plus faible.
    recommendations.sort(
        key=lambda x:
            x["predicted_yield_t_ha"],
        reverse=True
    )

    return {
        "recommendations": recommendations
    }