\# 📊 Générateur de Rapports IA / AI Report Generator

Application web professionnelle pour générer automatiquement des rapports d'analyse de données avec insights IA.

Professional web application to automatically generate data analysis reports with AI insights.

## Fonctionnalités
- Auto-inscription
- 3 rapports gratuits
- Exports HTML/Word
- Bilingue FR/EN


\### 📁 Gestion des Données

\- \*\*Multi-format\*\* : CSV, Excel (.xlsx, .xls), JSON, Parquet

\- \*\*Nettoyage automatique\*\* : Détection des colonnes vides, doublons, valeurs aberrantes

\- \*\*Score de qualité\*\* : Évaluation automatique de la qualité des données



\### 📊 Analyse \& Visualisations

\- \*\*Analyse statistique complète\*\* : Moyennes, médianes, écarts-types, quartiles

\- \*\*6 types de visualisations\*\* :

&nbsp; - Distributions (histogrammes)

&nbsp; - Détection d'outliers (boxplots)

&nbsp; - Matrice de corrélation (heatmap)

&nbsp; - Analyses catégorielles (barplots)

&nbsp; - Relations bivariées (scatter plots)

&nbsp; - Distributions catégorielles (pie charts)



\### 🧠 Modes IA (3 options)

1\. \*\*Mode Basique\*\* : Analyse sans IA (gratuit)

2\. \*\*Ollama Local\*\* : Modèles IA locaux (gratuit, confidentialité maximale)

3\. \*\*Anthropic API\*\* : Claude AI pour insights avancés (payant, haute qualité)



\### 📄 Exports Professionnels

\- \*\*HTML\*\* : Rapport imprimable en PDF avec graphiques intégrés

\- \*\*Word (.docx)\*\* : Document éditable avec graphiques et tableaux



\### 🌍 Interface Bilingue

\- Français 🇫🇷

\- English 🇬🇧



\## 🚀 Installation



\### 1. Prérequis

\- Python 3.9+

\- pip



\### 2. Cloner le projet



```bash

git clone <votre-repo>

cd report-generator

```



\### 3. Créer un environnement virtuel



```bash

\# Windows

python -m venv venv

venv\\Scripts\\activate



\# Mac/Linux

python3 -m venv venv

source venv/bin/activate

```



\### 4. Installer les dépendances



```bash

pip install -r requirements.txt

```



\## 📁 Structure du Projet



```

report-generator/

├── app.py                      # Application principale Streamlit

├── config.py                   # Configuration et traductions

├── requirements.txt            # Dépendances Python

├── README.md                   # Documentation

│

├── utils/                      # Modules utilitaires

│   ├── \_\_init\_\_.py

│   ├── data\_loader.py         # Chargement fichiers

│   ├── data\_cleaner.py        # Nettoyage données

│   ├── analyzer.py            # Analyses statistiques

│   ├── visualizations.py      # Création graphiques

│   ├── ai\_insights.py         # Insights IA 

│   └── local\_llm.py           # Gestion Ollama

└── exports/                    # Modules d'export

&nbsp;   ├── \_\_init\_\_.py

&nbsp;   ├── html\_export.py         # Export HTML

&nbsp;   └── word\_export.py         # Export Word

```



\## 🎯 Utilisation



\### Lancer l'application



```bash

streamlit run app.py

```



L'application s'ouvre automatiquement à `http://localhost:8501`



\### Workflow complet



1\. \*\*📁 Upload\*\* : Glissez-déposez votre fichier (CSV, Excel, JSON, Parquet)

2\. \*\*🧹 Nettoyage\*\* : L'app identifie automatiquement les bruits dans les données

3\. \*\*👀 Exploration\*\* : Naviguez dans les onglets pour explorer les données

4\. \*\*📊 Visualisations\*\* : Consultez les 6 graphiques générés automatiquement

5\. \*\*🧠 Insights\*\* : Choisissez votre mode IA et générez les insights

6\. \*\*📄 Export\*\* : Téléchargez votre rapport (HTML ou Word)



\## 🤖 Configuration des Modes IA



\### Mode 1 : Basique (Sans IA)

\*\*Gratuit | Aucune configuration\*\*



\- Sélectionnez "None" dans la sidebar

\- Génère des insights basiques sans IA

\- Idéal pour tester l'application



\### Mode 2 : Ollama Local

\*\*Gratuit | Confidentialité maximale | Hors ligne\*\*



\#### Installation d'Ollama



1\. \*\*Télécharger\*\* : \[ollama.ai](https://ollama.ai)

2\. \*\*Installer\*\* l'application

3\. \*\*Terminal\*\* :

&nbsp;  ```bash

&nbsp;  # Télécharger un modèle (llama3.2 recommandé)

&nbsp;  ollama pull llama3.2:3b

&nbsp;  

&nbsp;  # Lancer le serveur

&nbsp;  ollama serve

&nbsp;  ```

4\. \*\*Relancer\*\* l'app Streamlit



\#### Modèles recommandés

\- `llama3.2:3b` (3GB RAM) - Rapide, bon équilibre

\- `mistral:7b` (5GB RAM) - Qualité supérieure

\- `llama3.2:1b` (1GB RAM) - Très rapide, qualité basique



\### Mode 3 : Anthropic API

\*\*Payant | Haute qualité | Internet requis\*\*



\#### Obtenir une clé API



1\. Visitez \[console.anthropic.com](https://console.anthropic.com)

2\. Créez un compte

3\. Générez une clé API (commence par `sk-ant-`)

4\. Copiez-la dans la sidebar de l'app


\## 📊 Formats Supportés



\### CSV (.csv)

```csv

nom,age,ville

Alice,25,Paris

Bob,30,Lyon

```



\### Excel (.xlsx, .xls)

\- Fichiers Microsoft Excel

\- LibreOffice Calc

\- Google Sheets (exportés)



\### JSON (.json)

```json

\[

&nbsp; {"nom": "Alice", "age": 25, "ville": "Paris"},

&nbsp; {"nom": "Bob", "age": 30, "ville": "Lyon"}

]

```



\### Parquet (.parquet)

\- Format Apache Parquet

\- Idéal pour big data



\## 📄 Export des Rapports



\### HTML → PDF (Recommandé)



\*\*Avantages\*\* :

\- Mise en page parfaite

\- Graphiques en haute résolution

\- Couleurs préservées

\- Gratuit (pas de logiciel supplémentaire)



\*\*Méthode\*\* :

1\. Téléchargez le fichier HTML

2\. Ouvrez dans un navigateur (Chrome, Firefox, Edge)

3\. `Ctrl+P` (ou `Cmd+P` sur Mac)

4\. Sélectionnez "Enregistrer en PDF"

5\. ✅ PDF professionnel généré !



\### Word (.docx)



\*\*Avantages\*\* :

\- Éditable après export

\- Personnalisable (styles, couleurs)

\- Compatible Word, Google Docs, LibreOffice



\*\*Utilisation\*\* :

1\. Téléchargez le .docx

2\. Ouvrez dans Word/Google Docs

3\. Modifiez le contenu

4\. Exportez en PDF si nécessaire



\## 🛠️ Technologies Utilisées



\- \*\*\[Streamlit](https://streamlit.io)\*\* : Framework web

\- \*\*\[Pandas](https://pandas.pydata.org)\*\* : Manipulation données

\- \*\*\[Matplotlib](https://matplotlib.org)\*\* \& \*\*\[Seaborn](https://seaborn.pydata.org)\*\* : Visualisations

\- \*\*\[Python-docx](https://python-docx.readthedocs.io)\*\* : Export Word

\- \*\*\[Anthropic Claude](https://www.anthropic.com)\*\* : IA avancée

\- \*\*\[Ollama](https://ollama.ai)\*\* : LLM locaux (optionnel)



\## 🐛 Résolution de Problèmes


\### Ollama ne se connecte pas

```bash

\# Vérifier qu'Ollama est lancé

ollama serve



\# Vérifier les modèles installés

ollama list



\# Si pas de modèle, en installer un

ollama pull llama3.2:3b

```



\### Erreur lors du chargement d'un fichier Excel

```bash

pip install openpyxl

```



\### Erreur lors du chargement d'un fichier Parquet

```bash

pip install pyarrow

```



\### Les graphiques ne s'affichent pas dans le Word

\- C'est normal ! Matplotlib génère les images

\- Si problème, réinstallez Pillow :

```bash

pip install --upgrade Pillow

```



\## 💰 Monétisation / Commercialisation



Ce projet peut être commercialisé de plusieurs façons :



\### 1. Licence Standalone

\- \*\*Prix\*\* : 2 000€ - 5 000€

\- Client héberge sur son serveur

\- Support inclus 6-12 mois



\### 2. SaaS (Software as a Service)

\- \*\*Prix\*\* : 28€ - 100€/mois par utilisateur

\- Hébergement cloud

\- Mises à jour automatiques

\- Support premium



\### 3. Consulting / Sur-mesure

\- \*\*Prix\*\* : 5 000€ - 15 000€

\- Développement personnalisé

\- Intégration dans le système existant

\- Formation des équipes



\### 4. Freemium

\- Version gratuite : Mode basique uniquement

\- Version Pro : 20€/mois (Ollama local)

\- Version Enterprise : 100€/mois (API + support)



\## 🚀 Déploiement en Production



\### Option 1 : Streamlit Cloud (Gratuit)



1\. Créez un compte sur \[streamlit.io](https://streamlit.io)

2\. Connectez votre repo GitHub

3\. Déployez en un clic

4\. URL publique générée automatiquement



\*\*Limites\*\* : Pas de persistance des fichiers



\### Option 2 : Heroku



```bash

\# Créer un Procfile

echo "web: streamlit run app.py" > Procfile



\# Déployer

heroku create

git push heroku main

```



\### Option 3 : VPS (AWS, Azure, GCP, OVH)



```bash

\# Installer les dépendances

pip install -r requirements.txt



\# Lancer avec screen (pour garder actif)

screen -S report-app

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

```



\### Option 4 : Docker



```dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD \["streamlit", "run", "app.py"]

```



```bash

docker build -t report-generator .

docker run -p 8501:8501 report-generator

```



\## 🤝 Contribution



Les contributions sont les bienvenues !



1\. Fork le projet

2\. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`)

3\. Commit vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)

4\. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)

5\. Ouvrez une Pull Request



\## 📝 Licence



Ce projet est sous licence MIT - voir le fichier \[LICENSE](LICENSE) pour plus de détails.



\## 👨‍💻 Auteur



\*\*Franklin Agouanet\*\*

\- 🌐 Site web :
\- 💼 LinkedIn : \[Franklin platini Agouanet](www.linkedin.com/in/franklin-platini-agouanet-29a081156)

\- 📧 Email : agouanetf@yahoo.com



\## 🙏 Remerciements



\- \[Anthropic](https://www.anthropic.com) pour Claude AI

\- \[Streamlit](https://streamlit.io) pour le framework web

\- \[Ollama](https://ollama.ai) pour les modèles locaux

\- La communauté open source



---



\*\*⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile !\*\*



\## 📚 Documentation Supplémentaire



\- \[Guide d'utilisation détaillé](docs/USER\_GUIDE.md) \*(à créer)\*

\- \[Documentation technique](docs/TECHNICAL.md) \*(à créer)\*

\- \[FAQ](docs/FAQ.md) \*(à créer)\*

\- \[Changelog](CHANGELOG.md) \*(à créer)\*

