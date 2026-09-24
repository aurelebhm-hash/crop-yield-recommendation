# ============================================================
# TESTS AUTOMATISÉS DE L'API FASTAPI
# ============================================================
# Ces tests vérifient les endpoints critiques de l'API :
#
# - GET  /health
# - GET  /metadata
# - POST /predict
# - POST /recommend
#
# Ils vérifient également plusieurs cas d'erreur :
# - culture inconnue ;
# - zone inconnue ;
# - précipitations négatives ;
# - pesticides négatifs.
#
# FastAPI TestClient permet de tester l'application
# directement sans démarrer manuellement Uvicorn.


from fastapi.testclient import TestClient

from api.main import app


# ============================================================
# INITIALISATION DU CLIENT DE TEST
# ============================================================

client = TestClient(app)


# ============================================================
# DONNÉES VALIDES UTILISÉES PAR LES TESTS
# ============================================================

# France fait partie des zones connues du modèle.
# Cassava fait partie des cultures disponibles.
VALID_PREDICTION_PAYLOAD = {
    "area": "France",
    "crop": "Cassava",
    "year": 2012,
    "rainfall_mm": 800.0,
    "pesticides_tonnes": 5000.0,
    "avg_temp": 12.0
}


VALID_RECOMMENDATION_PAYLOAD = {
    "area": "France",
    "year": 2012,
    "rainfall_mm": 800.0,
    "pesticides_tonnes": 5000.0,
    "avg_temp": 12.0
}


# ============================================================
# TEST 1 — HEALTH
# ============================================================

def test_health():

    response = client.get("/health")

    # L'API doit répondre correctement.
    assert response.status_code == 200

    data = response.json()

    # Vérification de l'état du service.
    assert data["status"] == "healthy"

    # Le modèle doit être chargé.
    assert data["model_loaded"] is True

    # Notre modèle connaît 10 cultures.
    assert data["available_crops"] == 10

    # Notre modèle connaît 113 zones d'entraînement.
    assert data["available_areas"] == 113


# ============================================================
# TEST 2 — MÉTADONNÉES
# ============================================================

def test_metadata():

    response = client.get("/metadata")

    assert response.status_code == 200

    data = response.json()

    # Les deux listes nécessaires à Streamlit
    # doivent être présentes.
    assert "available_crops" in data
    assert "available_areas" in data

    # Vérification du nombre de valeurs disponibles.
    assert len(data["available_crops"]) == 10
    assert len(data["available_areas"]) == 113

    # Vérification de valeurs connues.
    assert "Cassava" in data["available_crops"]
    assert "France" in data["available_areas"]


# ============================================================
# TEST 3 — PRÉDICTION VALIDE
# ============================================================

def test_predict_valid():

    response = client.post(
        "/predict",
        json=VALID_PREDICTION_PAYLOAD
    )

    assert response.status_code == 200

    data = response.json()

    # La réponse doit identifier la culture.
    assert data["crop"] == "Cassava"

    # Le rendement prédit doit être présent.
    assert "predicted_yield_t_ha" in data

    # Le résultat doit être numérique.
    assert isinstance(
        data["predicted_yield_t_ha"],
        (int, float)
    )

    # Le rendement agricole prédit doit être positif.
    assert data["predicted_yield_t_ha"] > 0


# ============================================================
# TEST 4 — RECOMMANDATION VALIDE
# ============================================================

def test_recommend_valid():

    response = client.post(
        "/recommend",
        json=VALID_RECOMMENDATION_PAYLOAD
    )

    assert response.status_code == 200

    data = response.json()

    assert "recommendations" in data

    recommendations = data["recommendations"]

    # Une recommandation doit être produite
    # pour chacune des 10 cultures.
    assert len(recommendations) == 10

    # Chaque recommandation doit avoir
    # une culture et un rendement prédit.
    for recommendation in recommendations:

        assert "crop" in recommendation

        assert (
            "predicted_yield_t_ha"
            in recommendation
        )

        assert isinstance(
            recommendation[
                "predicted_yield_t_ha"
            ],
            (int, float)
        )


# ============================================================
# TEST 5 — CLASSEMENT DES RECOMMANDATIONS
# ============================================================

def test_recommend_sorted_descending():

    response = client.post(
        "/recommend",
        json=VALID_RECOMMENDATION_PAYLOAD
    )

    assert response.status_code == 200

    recommendations = response.json()[
        "recommendations"
    ]

    # Extraction des rendements dans l'ordre
    # retourné par FastAPI.
    yields = [
        recommendation[
            "predicted_yield_t_ha"
        ]
        for recommendation in recommendations
    ]

    # Vérifie que les rendements sont bien classés
    # du plus élevé au plus faible.
    assert yields == sorted(
        yields,
        reverse=True
    )


# ============================================================
# TEST 6 — CULTURE INCONNUE
# ============================================================

def test_predict_unknown_crop():

    payload = VALID_PREDICTION_PAYLOAD.copy()

    payload["crop"] = "CultureInconnue"

    response = client.post(
        "/predict",
        json=payload
    )

    # Notre API doit refuser explicitement
    # une culture inconnue.
    assert response.status_code == 400

    data = response.json()

    assert "Culture inconnue" in data["detail"]


# ============================================================
# TEST 7 — ZONE INCONNUE POUR /predict
# ============================================================

def test_predict_unknown_area():

    payload = VALID_PREDICTION_PAYLOAD.copy()

    payload["area"] = "PaysQuiNExistePas"

    response = client.post(
        "/predict",
        json=payload
    )

    assert response.status_code == 400

    data = response.json()

    assert "Zone inconnue" in data["detail"]


# ============================================================
# TEST 8 — ZONE INCONNUE POUR /recommend
# ============================================================

def test_recommend_unknown_area():

    payload = VALID_RECOMMENDATION_PAYLOAD.copy()

    payload["area"] = "PaysQuiNExistePas"

    response = client.post(
        "/recommend",
        json=payload
    )

    assert response.status_code == 400

    data = response.json()

    assert "Zone inconnue" in data["detail"]


# ============================================================
# TEST 9 — PRÉCIPITATIONS NÉGATIVES
# ============================================================

def test_negative_rainfall():

    payload = VALID_PREDICTION_PAYLOAD.copy()

    payload["rainfall_mm"] = -100

    response = client.post(
        "/predict",
        json=payload
    )

    # Pydantic doit rejeter la valeur avant même
    # l'appel au modèle.
    assert response.status_code == 422


# ============================================================
# TEST 10 — PESTICIDES NÉGATIFS
# ============================================================

def test_negative_pesticides():

    payload = VALID_PREDICTION_PAYLOAD.copy()

    payload["pesticides_tonnes"] = -100

    response = client.post(
        "/predict",
        json=payload
    )

    assert response.status_code == 422