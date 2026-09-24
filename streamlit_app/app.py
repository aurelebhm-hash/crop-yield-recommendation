# ============================================================
# APPLICATION STREAMLIT - CROP YIELD
# ============================================================
# Cette application constitue uniquement le front-end.
#
# Elle ne charge pas le modèle de Machine Learning.
# Toutes les prédictions sont réalisées par FastAPI.


import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

# Adresse de FastAPI en développement local.
API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Crop Yield",
    page_icon="🌱",
    layout="centered"
)


# ============================================================
# EN-TÊTE
# ============================================================

st.title("🌱 Crop Yield")

st.write(
    "Estimation du rendement agricole et recommandation "
    "de cultures selon les conditions de la parcelle."
)

st.divider()


# ============================================================
# CONNEXION À FASTAPI
# ============================================================

# Streamlit vérifie que l'API fonctionne puis récupère
# les cultures et les zones connues du modèle.

try:

    # --------------------------------------------------------
    # Vérification de l'état de l'API
    # --------------------------------------------------------

    health_response = requests.get(
        f"{API_URL}/health",
        timeout=5
    )

    health_response.raise_for_status()

    # --------------------------------------------------------
    # Récupération des métadonnées
    # --------------------------------------------------------

    metadata_response = requests.get(
        f"{API_URL}/metadata",
        timeout=5
    )

    metadata_response.raise_for_status()

    api_metadata = metadata_response.json()

    # Ces listes proviennent désormais directement de FastAPI.
    # Elles ne sont plus écrites manuellement dans Streamlit.
    available_crops = api_metadata[
        "available_crops"
    ]

    available_areas = api_metadata[
        "available_areas"
    ]

    st.success(
        "API connectée et modèle disponible."
    )


except requests.RequestException:

    st.error(
        "Impossible de contacter l'API FastAPI. "
        "Vérifiez qu'elle est bien démarrée."
    )

    # Sans FastAPI, l'application ne peut ni prédire
    # ni recommander. On arrête donc son exécution.
    st.stop()


# ============================================================
# CHOIX DU MODE
# ============================================================

mode = st.radio(
    "Choisissez un mode",
    [
        "Prédiction",
        "Recommandation"
    ],
    horizontal=True
)

st.divider()


# ============================================================
# MODE PRÉDICTION
# ============================================================

if mode == "Prédiction":

    st.subheader(
        "Prédiction du rendement"
    )

    st.write(
        "Renseignez la culture et les conditions de "
        "la parcelle pour obtenir une estimation "
        "du rendement."
    )

    # --------------------------------------------------------
    # CULTURE
    # --------------------------------------------------------

    # La liste vient directement des métadonnées de FastAPI.
    crop = st.selectbox(
        "Culture",
        available_crops
    )

    # --------------------------------------------------------
    # ZONE
    # --------------------------------------------------------

    # Contrairement à l'ancienne version, la zone n'est plus
    # un champ texte libre.
    #
    # L'utilisateur choisit uniquement une zone réellement
    # observée pendant l'entraînement du modèle.
    area = st.selectbox(
        "Zone / pays",
        available_areas,
        index=(
            available_areas.index("France")
            if "France" in available_areas
            else 0
        )
    )

    # --------------------------------------------------------
    # ANNÉE
    # --------------------------------------------------------

    # Le jeu de données couvre la période historique
    # utilisée dans le projet.
    #
    # On évite donc de proposer des années très éloignées
    # comme 2050 ou 2100 pour lesquelles le modèle
    # n'a pas été conçu.
    year = st.number_input(
        "Année",
        min_value=1990,
        max_value=2013,
        value=2012,
        step=1
    )

    # --------------------------------------------------------
    # PRÉCIPITATIONS
    # --------------------------------------------------------

    rainfall = st.number_input(
        "Précipitations annuelles (mm)",
        min_value=0.0,
        value=800.0,
        step=10.0
    )

    # --------------------------------------------------------
    # PESTICIDES
    # --------------------------------------------------------

    pesticides = st.number_input(
        "Utilisation de pesticides (tonnes)",
        min_value=0.0,
        value=5000.0,
        step=100.0
    )

    # --------------------------------------------------------
    # TEMPÉRATURE
    # --------------------------------------------------------

    temperature = st.number_input(
        "Température moyenne (°C)",
        value=12.0,
        step=0.5
    )

    st.divider()

    # ========================================================
    # ENVOI DE LA PRÉDICTION
    # ========================================================

    if st.button(
        "Prédire le rendement",
        type="primary"
    ):

        # JSON attendu par POST /predict.
        payload = {
            "area": area,
            "crop": crop,
            "year": int(year),
            "rainfall_mm": rainfall,
            "pesticides_tonnes": pesticides,
            "avg_temp": temperature
        }

        try:

            # Streamlit transmet les données à FastAPI.
            response = requests.post(
                f"{API_URL}/predict",
                json=payload,
                timeout=10
            )

            response.raise_for_status()

            result = response.json()

            predicted_yield = result[
                "predicted_yield_t_ha"
            ]

            # ------------------------------------------------
            # AFFICHAGE DU RÉSULTAT
            # ------------------------------------------------

            st.success(
                "Prédiction réalisée avec succès."
            )

            st.metric(
                label=(
                    f"Rendement prédit — {crop}"
                ),
                value=(
                    f"{predicted_yield:.2f} t/ha"
                )
            )

            st.caption(
                "Cette valeur correspond à une estimation "
                "du modèle et non à un rendement garanti."
            )


        except requests.RequestException as error:

            st.error(
                "Erreur lors de l'appel à l'API : "
                f"{error}"
            )


# ============================================================
# MODE RECOMMANDATION
# ============================================================

elif mode == "Recommandation":

    st.subheader(
        "Recommandation de cultures"
    )

    st.write(
        "Renseignez les conditions de la parcelle. "
        "Le système comparera les cultures disponibles "
        "selon leur rendement prédit."
    )

    # --------------------------------------------------------
    # ZONE
    # --------------------------------------------------------

    # Là encore, seules les zones connues à l'entraînement
    # sont proposées.
    area_rec = st.selectbox(
        "Zone / pays",
        available_areas,
        index=(
            available_areas.index("France")
            if "France" in available_areas
            else 0
        ),
        key="area_recommendation"
    )

    # --------------------------------------------------------
    # ANNÉE
    # --------------------------------------------------------

    year_rec = st.number_input(
        "Année",
        min_value=1990,
        max_value=2013,
        value=2012,
        step=1,
        key="year_recommendation"
    )

    # --------------------------------------------------------
    # PRÉCIPITATIONS
    # --------------------------------------------------------

    rainfall_rec = st.number_input(
        "Précipitations annuelles (mm)",
        min_value=0.0,
        value=800.0,
        step=10.0,
        key="rainfall_recommendation"
    )

    # --------------------------------------------------------
    # PESTICIDES
    # --------------------------------------------------------

    pesticides_rec = st.number_input(
        "Utilisation de pesticides (tonnes)",
        min_value=0.0,
        value=5000.0,
        step=100.0,
        key="pesticides_recommendation"
    )

    # --------------------------------------------------------
    # TEMPÉRATURE
    # --------------------------------------------------------

    temperature_rec = st.number_input(
        "Température moyenne (°C)",
        value=12.0,
        step=0.5,
        key="temperature_recommendation"
    )

    st.divider()

    # ========================================================
    # ENVOI DE LA RECOMMANDATION
    # ========================================================

    if st.button(
        "Recommander les cultures",
        type="primary"
    ):

        # La culture n'est volontairement pas envoyée.
        # FastAPI testera toutes les cultures disponibles.
        payload = {
            "area": area_rec,
            "year": int(year_rec),
            "rainfall_mm": rainfall_rec,
            "pesticides_tonnes":
                pesticides_rec,
            "avg_temp": temperature_rec
        }

        try:

            response = requests.post(
                f"{API_URL}/recommend",
                json=payload,
                timeout=10
            )

            response.raise_for_status()

            result = response.json()

            recommendations = result[
                "recommendations"
            ]

            # ------------------------------------------------
            # CONVERSION POUR L'AFFICHAGE
            # ------------------------------------------------

            # Le DataFrame sert uniquement à présenter
            # les résultats. Il ne réalise aucun calcul ML.
            recommendations_df = pd.DataFrame(
                recommendations
            )

            recommendations_df = (
                recommendations_df.rename(
                    columns={
                        "crop":
                            "Culture",

                        "predicted_yield_t_ha":
                            "Rendement prédit (t/ha)"
                    }
                )
            )

            st.success(
                "Recommandations calculées avec succès."
            )

            # =================================================
            # CULTURE AU RENDEMENT PRÉDIT LE PLUS ÉLEVÉ
            # =================================================

            # FastAPI renvoie déjà les résultats
            # dans l'ordre décroissant.
            best_crop = (
                recommendations_df.iloc[0]
            )

            st.metric(
                label=(
                    "Culture avec le rendement "
                    "prédit le plus élevé"
                ),
                value=best_crop["Culture"],
                delta=(
                    f'{best_crop["Rendement prédit (t/ha)"]:.2f} '
                    "t/ha"
                )
            )

            st.divider()

            # =================================================
            # GRAPHIQUE
            # =================================================

            st.subheader(
                "Comparaison des rendements prédits"
            )

            chart_df = (
                recommendations_df.set_index(
                    "Culture"
                )
            )

            st.bar_chart(
                chart_df[
                    "Rendement prédit (t/ha)"
                ]
            )

            # =================================================
            # TABLEAU
            # =================================================

            st.subheader(
                "Classement des cultures"
            )

            display_df = (
                recommendations_df.copy()
            )

            # Ajout d'un rang de 1 à 10.
            display_df.insert(
                0,
                "Rang",
                range(
                    1,
                    len(display_df) + 1
                )
            )

            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True
            )

            # ------------------------------------------------
            # LIMITE DE L'INTERPRÉTATION
            # ------------------------------------------------

            st.caption(
                "Les cultures sont classées selon leur "
                "rendement prédit en t/ha. "
                "Ce classement ne constitue pas une "
                "estimation de rentabilité économique."
            )


        except requests.RequestException as error:

            st.error(
                "Erreur lors de l'appel à l'API : "
                f"{error}"
            )