# Guide de téléchargement et d'intégration à Render - Générateur de clips "Best Of"

Ce guide vous explique comment télécharger le code source du générateur de clips "Best Of", le préparer pour le déploiement, et l'intégrer à Render pour une mise en production gratuite.

## Table des matières

1. [Téléchargement du code source](#1-téléchargement-du-code-source)
2. [Préparation du projet pour Render](#2-préparation-du-projet-pour-render)
3. [Configuration de GitHub](#3-configuration-de-github)
4. [Configuration de Render](#4-configuration-de-render)
5. [Configuration de Stripe](#5-configuration-de-stripe)
6. [Configuration du stockage S3](#6-configuration-du-stockage-s3)
7. [Configuration des tâches planifiées](#7-configuration-des-tâches-planifiées)
8. [Vérification du déploiement](#8-vérification-du-déploiement)

## 1. Téléchargement du code source

### Option 1 : Téléchargement direct

1. Créez un dossier sur votre ordinateur pour le projet
2. Téléchargez tous les fichiers du projet depuis la conversation actuelle
3. Organisez les fichiers selon la structure du projet décrite dans AVANCEMENT_PROJET.md

### Option 2 : Clonage depuis GitHub (si vous avez déjà un dépôt)

```bash
git clone https://github.com/votre-organisation/generateur-clips-bestof.git
cd generateur-clips-bestof
```

## 2. Préparation du projet pour Render

### Création des fichiers nécessaires

1. **requirements.txt** - Créez ce fichier à la racine du projet avec les dépendances suivantes :

```
Flask==2.2.3
Flask-Login==0.6.2
Flask-SQLAlchemy==3.0.3
Flask-WTF==1.1.1
Flask-Migrate==4.0.4
Flask-CORS==3.0.10
SQLAlchemy==2.0.7
Werkzeug==2.2.3
WTForms==3.0.1
stripe==5.4.0
gunicorn==20.1.0
psycopg2-binary==2.9.5
python-dotenv==1.0.0
boto3==1.26.135
pytest==7.3.1
Flask-Testing==0.8.1
```

2. **runtime.txt** - Créez ce fichier pour spécifier la version de Python :

```
python-3.9.16
```

3. **render.yaml** - Créez ce fichier pour la configuration Render :

```yaml
services:
  - type: web
    name: generateur-clips-bestof
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: FLASK_APP
        value: app.py
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: STRIPE_PUBLIC_KEY
        sync: false
      - key: STRIPE_SECRET_KEY
        sync: false
      - key: STRIPE_WEBHOOK_SECRET
        sync: false
      - key: AWS_ACCESS_KEY
        sync: false
      - key: AWS_SECRET_KEY
        sync: false
      - key: S3_BUCKET_NAME
        sync: false
      - key: MAINTENANCE_API_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: generateur-clips-db
          property: connectionString

databases:
  - name: generateur-clips-db
    databaseName: generateur_clips
    user: generateur_clips_user
```

4. **Procfile** - Créez ce fichier pour Gunicorn :

```
web: gunicorn app:app
```

### Adaptation pour le stockage S3

1. Créez le fichier `storage/s3_storage.py` :

```python
import boto3
import os
from botocore.exceptions import ClientError

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
)

BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

def save_clip(file_path, clip_id):
    """Sauvegarde un clip sur S3."""
    try:
        s3_client.upload_file(
            file_path, 
            BUCKET_NAME, 
            f"clips/{clip_id}.mp4",
            ExtraArgs={'ACL': 'public-read'}
        )
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/clips/{clip_id}.mp4"
    except ClientError as e:
        print(f"Erreur lors de l'upload sur S3: {e}")
        return None

def get_clip_path(clip_id):
    """Récupère l'URL d'un clip sur S3."""
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/clips/{clip_id}.mp4"
```

2. Modifiez les imports dans les fichiers qui utilisent le stockage local pour utiliser S3 à la place.

### Adaptation pour les tâches planifiées

Ajoutez les endpoints API dans `app.py` :

```python
@app.route('/api/maintenance/reset-counters', methods=['POST'])
def api_reset_counters():
    """Endpoint API pour réinitialiser les compteurs mensuels."""
    # Vérifier le token de sécurité
    token = request.headers.get('X-API-Key')
    if token != os.environ.get('MAINTENANCE_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from api.subscription import reset_monthly_counters
    result = reset_monthly_counters()
    return jsonify({'status': 'success', 'message': result})

@app.route('/api/maintenance/check-subscriptions', methods=['POST'])
def api_check_subscriptions():
    """Endpoint API pour vérifier les abonnements expirés."""
    # Vérifier le token de sécurité
    token = request.headers.get('X-API-Key')
    if token != os.environ.get('MAINTENANCE_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from api.subscription import check_expired_subscriptions
    result = check_expired_subscriptions()
    return jsonify({'status': 'success', 'message': result})

@app.route('/api/maintenance/delete-expired-clips', methods=['POST'])
def api_delete_expired_clips():
    """Endpoint API pour supprimer les clips expirés."""
    # Vérifier le token de sécurité
    token = request.headers.get('X-API-Key')
    if token != os.environ.get('MAINTENANCE_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from api.subscription import delete_expired_clips
    result = delete_expired_clips()
    return jsonify({'status': 'success', 'message': result})
```

## 3. Configuration de GitHub

1. Créez un nouveau dépôt sur GitHub
2. Initialisez Git dans votre dossier local et poussez le code :

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/votre-organisation/generateur-clips-bestof.git
git push -u origin main
```

## 4. Configuration de Render

1. Créez un compte sur [Render](https://render.com) (inscription gratuite)
2. Connectez-vous à votre compte Render
3. Cliquez sur "New" et sélectionnez "Blueprint"
4. Connectez votre compte GitHub
5. Sélectionnez le dépôt que vous venez de créer
6. Render détectera automatiquement le fichier `render.yaml` et configurera les services
7. Remplissez les variables d'environnement manquantes :
   - STRIPE_PUBLIC_KEY : Votre clé publique Stripe
   - STRIPE_SECRET_KEY : Votre clé secrète Stripe
   - STRIPE_WEBHOOK_SECRET : Laissez vide pour l'instant
   - AWS_ACCESS_KEY : Votre clé d'accès AWS
   - AWS_SECRET_KEY : Votre clé secrète AWS
   - S3_BUCKET_NAME : Le nom de votre bucket S3
8. Cliquez sur "Apply" pour démarrer le déploiement

## 5. Configuration de Stripe

1. Créez un compte sur [Stripe](https://stripe.com) si vous n'en avez pas déjà un
2. Dans le dashboard Stripe, allez dans Développeurs > Clés API pour obtenir vos clés
3. Créez les produits et les prix pour vos plans d'abonnement :
   - Plan Premium : 9,99€/mois
   - Plan Pro : 24,99€/mois
4. Notez les IDs des prix (price_xxx) et mettez-les à jour dans le fichier `api/payment.py`
5. Dans le dashboard Stripe, allez dans Développeurs > Webhooks
6. Ajoutez un endpoint avec l'URL `https://votre-app.onrender.com/webhook`
7. Sélectionnez les événements à écouter :
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
8. Copiez la clé de signature du webhook
9. Retournez sur Render, allez dans Environment > Environment Variables
10. Ajoutez la clé de signature du webhook dans la variable STRIPE_WEBHOOK_SECRET

## 6. Configuration du stockage S3

1. Créez un compte AWS si vous n'en avez pas déjà un
2. Allez dans la console AWS et créez un bucket S3
3. Configurez le bucket pour permettre l'accès public aux objets
4. Créez un utilisateur IAM avec les permissions nécessaires pour accéder au bucket
5. Notez les clés d'accès et secrètes de l'utilisateur IAM
6. Retournez sur Render, allez dans Environment > Environment Variables
7. Mettez à jour les variables AWS_ACCESS_KEY, AWS_SECRET_KEY et S3_BUCKET_NAME

## 7. Configuration des tâches planifiées

1. Créez un compte sur [cron-job.org](https://cron-job.org) (gratuit)
2. Créez trois tâches planifiées :
   - Réinitialisation des compteurs mensuels (1er jour du mois à 00:01)
     - URL: https://votre-app.onrender.com/api/maintenance/reset-counters
     - Méthode: POST
     - En-têtes: X-API-Key: valeur de MAINTENANCE_API_KEY
   - Vérification des abonnements expirés (tous les jours à 01:00)
     - URL: https://votre-app.onrender.com/api/maintenance/check-subscriptions
     - Méthode: POST
     - En-têtes: X-API-Key: valeur de MAINTENANCE_API_KEY
   - Suppression des clips expirés (tous les jours à 02:00)
     - URL: https://votre-app.onrender.com/api/maintenance/delete-expired-clips
     - Méthode: POST
     - En-têtes: X-API-Key: valeur de MAINTENANCE_API_KEY

## 8. Vérification du déploiement

1. Accédez à votre application sur https://votre-app.onrender.com
2. Créez un compte utilisateur
3. Testez la génération de clips
4. Testez le processus d'abonnement avec Stripe en mode test
5. Vérifiez que les webhooks Stripe fonctionnent correctement

## Paramètres à configurer dans l'ordre

1. **GitHub** : Créer un dépôt et pousser le code
2. **AWS S3** : Créer un bucket et un utilisateur IAM
3. **Stripe** : Créer un compte et configurer les produits/prix
4. **Render** : Déployer l'application
5. **Stripe Webhooks** : Configurer les webhooks pour l'URL de Render
6. **cron-job.org** : Configurer les tâches planifiées

## Résolution des problèmes courants

1. **L'application ne démarre pas sur Render**
   - Vérifiez les logs dans Render > votre-app > Logs
   - Assurez-vous que toutes les dépendances sont dans requirements.txt

2. **Les webhooks Stripe ne fonctionnent pas**
   - Vérifiez les logs des webhooks dans le dashboard Stripe
   - Assurez-vous que la clé de signature est correcte

3. **Les uploads vers S3 échouent**
   - Vérifiez les permissions du bucket S3
   - Vérifiez que les clés AWS sont correctes

4. **Les tâches planifiées ne s'exécutent pas**
   - Vérifiez les logs sur cron-job.org
   - Assurez-vous que la clé API de maintenance est correcte
