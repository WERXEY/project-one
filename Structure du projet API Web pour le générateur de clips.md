# Structure du projet API Web pour le générateur de clips

Voici la structure de fichiers que nous allons créer pour l'API web du générateur de clips "Best Of" :

```
project_one/
│
├── api/
│   ├── __init__.py           # Initialisation de l'application Flask
│   ├── routes.py             # Définition des endpoints de l'API
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── clip_controller.py # Logique de génération des clips
│   │   └── user_controller.py # Gestion des utilisateurs (pour plus tard)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── clip.py           # Modèle de données pour les clips
│   │   └── user.py           # Modèle de données pour les utilisateurs (pour plus tard)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── youtube_extractor.py # Extraction des données YouTube
│       └── clip_generator.py    # Génération des clips
│
├── storage/
│   ├── __init__.py
│   ├── local_storage.py      # Gestion du stockage local
│   └── cloud_storage.py      # Gestion du stockage cloud (pour plus tard)
│
├── static/                   # Fichiers statiques pour l'interface web (pour plus tard)
│   ├── css/
│   ├── js/
│   └── img/
│
├── templates/                # Templates HTML pour l'interface web (pour plus tard)
│
├── tests/                    # Tests unitaires et d'intégration
│   ├── __init__.py
│   ├── test_api.py
│   └── test_clip_generator.py
│
├── config.py                 # Configuration de l'application
├── requirements.txt          # Dépendances du projet
├── app.py                    # Point d'entrée de l'application
└── README.md                 # Documentation du projet
```

Cette structure suit les bonnes pratiques de développement Python et permet une séparation claire des responsabilités :
- `api/` contient tout le code lié à l'API web
- `storage/` gère le stockage des clips générés
- `static/` et `templates/` seront utilisés plus tard pour l'interface utilisateur
- `tests/` contient les tests pour assurer la qualité du code
- Les fichiers à la racine sont des fichiers de configuration et le point d'entrée de l'application
