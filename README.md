# Crop Yield Recommendation System

[![CI - Crop Yield](https://github.com/aurelebhm-hash/crop-yield-recommendation/actions/workflows/ci.yml/badge.svg)](https://github.com/aurelebhm-hash/crop-yield-recommendation/actions/workflows/ci.yml)

## Présentation

Ce projet développe un système de prédiction et de recommandation de cultures à partir de données agricoles et climatiques.

L'application propose deux fonctionnalités principales :

- **Prédiction** : estimer le rendement d'une culture pour un contexte donné.
- **Recommandation** : comparer les rendements prédits des cultures disponibles et les classer par rendement décroissant.

Le système repose sur un modèle de Machine Learning exposé par une API FastAPI et utilisé par une interface Streamlit.

> La recommandation correspond à une optimisation du **rendement prédit** et non de la rentabilité économique. Les données utilisées ne contiennent pas les prix de vente et les coûts nécessaires au calcul d'un profit.

---

## Architecture

```text
Données agricoles
       |
       v
Préparation et fusion
       |
       v
Modélisation Machine Learning
       |
       v
crop_yield_pipeline.joblib
       |
       v
API FastAPI
   |         |
   v         v
/predict   /recommend
       |
       v
Interface Streamlit
```

L'intégration continue est assurée par GitHub Actions :

```text
Push / Pull Request
        |
        v
Récupération du dépôt + Git LFS
        |
        v
Tests automatisés Pytest
        |
        v
Build de l'image Docker
```

Le build Docker n'est exécuté que si les tests réussissent.

---

## Structure du projet

```text
crop-yield-recommendation/
|
├── .github/
│   └── workflows/
│       └── ci.yml
|
├── api/
│   └── main.py
|
├── models/
│   ├── crop_yield_pipeline.joblib
│   └── model_metadata.json
|
├── streamlit_app/
│   ├── app.py
│   └── requirements.txt
|
├── tests/
│   └── test_api.py
|
├── 01_exploration_preparation_donnees.ipynb
├── 02_modelisation_optimisation.ipynb
├── Dockerfile
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .gitattributes
└── README.md
```

---

## Données

La préparation des données est réalisée dans :

```text
01_exploration_preparation_donnees.ipynb
```

Les différentes sources sont explorées, contrôlées et fusionnées afin de construire un jeu de données consolidé.

Les principales variables utilisées par le modèle sont :

- zone géographique ;
- culture ;
- année ;
- précipitations ;
- utilisation de pesticides ;
- température moyenne.

La variable cible est le rendement agricole exprimé en tonnes par hectare.

---

## Modélisation

La modélisation est réalisée dans :

```text
02_modelisation_optimisation.ipynb
```

Plusieurs modèles ont été comparés à l'aide d'une validation temporelle :

- DummyRegressor ;
- Ridge ;
- RandomForestRegressor ;
- HistGradientBoostingRegressor.

Le modèle retenu est un **Random Forest Regressor** intégré dans un pipeline scikit-learn comprenant les transformations nécessaires.

### Performances finales

Sur la période de test 2010–2013 :

| Métrique | Résultat |
|---|---:|
| MAE | 1.147 t/ha |
| RMSE | 2.334 t/ha |
| R² | 0.926 |

À titre de comparaison, le modèle baseline DummyRegressor obtient un RMSE de **8.661 t/ha** sur le même jeu de test.

Le modèle final est enregistré dans :

```text
models/crop_yield_pipeline.joblib
```

Les métadonnées nécessaires à l'application sont enregistrées dans :

```text
models/model_metadata.json
```

---

## API FastAPI

L'API est définie dans :

```text
api/main.py
```

Elle charge le pipeline Machine Learning et expose notamment les endpoints suivants.

### `GET /health`

Vérifie que l'API et le modèle sont disponibles.

### `GET /metadata`

Retourne les cultures et les zones géographiques disponibles.

### `POST /predict`

Estime le rendement pour une culture et un contexte donnés.

Exemple de données envoyées :

```json
{
  "Area_std": "France",
  "Item": "Cassava",
  "Year": 2012,
  "rainfall_mm": 800,
  "pesticides_tonnes": 5000,
  "avg_temp": 12
}
```

### `POST /recommend`

Prédit le rendement de toutes les cultures disponibles pour un même contexte, puis retourne un classement décroissant.

---

## Installation

Le projet utilise Python 3.11.

Cloner le dépôt :

```bash
git clone https://github.com/aurelebhm-hash/crop-yield-recommendation.git
cd crop-yield-recommendation
```

Le modèle est stocké avec **Git LFS**. Git LFS doit donc être installé sur la machine.

```bash
git lfs install
git lfs pull
```

Créer puis activer un environnement virtuel.

Sous Windows :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## Lancer l'API

Depuis la racine du projet :

```bash
python -m uvicorn api.main:app --reload
```

L'API est alors disponible localement sur le port `8000`.

La documentation interactive FastAPI est accessible via :

```text
http://localhost:8000/docs
```

---

## Lancer l'interface Streamlit

Installer les dépendances du frontend :

```bash
pip install -r streamlit_app/requirements.txt
```

Puis lancer :

```bash
streamlit run streamlit_app/app.py
```

L'interface permet de choisir entre :

- la prédiction du rendement d'une culture ;
- la recommandation des cultures selon leur rendement prédit.

L'API FastAPI doit être accessible par l'application Streamlit.

---

## Tests automatisés

Les tests sont définis dans :

```text
tests/test_api.py
```

Ils contrôlent notamment :

- l'état de santé de l'API ;
- les métadonnées ;
- une prédiction valide ;
- une recommandation valide ;
- le classement des recommandations ;
- le rejet des cultures inconnues ;
- le rejet des zones inconnues ;
- la validation des valeurs numériques incorrectes.

Pour lancer les tests :

```bash
python -m pytest tests/ -v
```

---

## Docker

L'API peut être construite sous forme d'image Docker.

Construction :

```bash
docker build -t crop-yield-api .
```

Exécution :

```bash
docker run --rm -p 8000:8000 crop-yield-api
```

L'API devient alors accessible localement sur le port `8000`.

---

## CI/CD avec GitHub Actions

Le workflow est défini dans :

```text
.github/workflows/ci.yml
```

Il est automatiquement déclenché lors :

- d'un `push` ;
- d'une `pull_request`.

Le pipeline exécute successivement :

1. récupération du dépôt ;
2. récupération du modèle avec Git LFS ;
3. installation des dépendances ;
4. exécution des tests Pytest ;
5. construction de l'image Docker si les tests réussissent.

La dépendance entre les jobs garantit que l'image Docker n'est pas construite lorsque les tests échouent.

L'état actuel du workflow est visible grâce au badge placé en haut de ce README.

---

## Git LFS

Le modèle Machine Learning étant volumineux, le fichier :

```text
models/crop_yield_pipeline.joblib
```

est versionné avec **Git Large File Storage (Git LFS)**.

Le fichier `.gitattributes` contient la règle correspondante :

```text
*.joblib filter=lfs diff=lfs merge=lfs -text
```

Le workflow GitHub Actions récupère explicitement les fichiers LFS avant les tests et le build Docker.

---

## Limites

Plusieurs limites doivent être prises en compte lors de l'interprétation des résultats :

- les prédictions dépendent de la représentativité des données d'entraînement ;
- les recommandations maximisent uniquement le rendement agricole prédit ;
- aucune causalité ne peut être déduite de l'importance des variables ;
- les performances peuvent diminuer sur des périodes ou des contextes éloignés des données d'entraînement ;
- une zone géographique inconnue du modèle n'est pas acceptée par l'API ;
- l'année n'a pas montré d'importance prédictive mesurable dans l'analyse finale du modèle.

Une évolution future pourrait intégrer des données économiques, comme les prix de vente et les coûts de production, afin de produire des recommandations fondées sur une estimation de rentabilité.

---

## Technologies

- Python
- pandas
- NumPy
- scikit-learn
- MLflow
- FastAPI
- Uvicorn
- Streamlit
- Pytest
- Docker
- Git / GitHub
- Git LFS
- GitHub Actions