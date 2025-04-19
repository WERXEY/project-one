# Déploiement sur Render - Générateur de clips "Best Of"

Ce guide vous explique comment déployer votre générateur de clips "Best Of" sur Render, une plateforme moderne qui offre un niveau gratuit pour les applications web.

## Prérequis

- Un compte GitHub avec votre code source
- Un compte Render (inscription gratuite sur [render.com](https://render.com))
- Un compte Stripe pour les paiements

## Étapes de déploiement

### 1. Préparation du projet

Assurez-vous que votre projet contient les fichiers suivants :

- `requirements.txt` : Liste toutes les dépendances Python
- `runtime.txt` : Spécifie la version de Python (ex: `python-3.9.7`)
- `gunicorn.conf.py` : Configuration de Gunicorn (déjà créé)

Créez un fichier `render.yaml` à la racine de votre projet :

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
      - key: DATABASE_URL
        fromDatabase:
          name: generateur-clips-db
          property: connectionString

databases:
  - name: generateur-clips-db
    databaseName: generateur_clips
    user: generateur_clips_user
```

### 2. Adaptation pour le stockage des fichiers

Comme Render ne permet pas de stocker des fichiers de manière permanente sur le système de fichiers, modifiez votre application pour utiliser un service de stockage cloud comme AWS S3 ou Cloudinary.

Exemple d'adaptation pour utiliser S3 :

1. Ajoutez boto3 à votre `requirements.txt` :
```
boto3==1.24.71
```

2. Créez un module de stockage S3 (`storage/s3_storage.py`) :
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

3. Ajoutez les variables d'environnement dans Render :
   - AWS_ACCESS_KEY
   - AWS_SECRET_KEY
   - S3_BUCKET_NAME

### 3. Adaptation pour les tâches planifiées

Comme les tâches cron ne sont pas disponibles dans le niveau gratuit de Render, vous pouvez utiliser des alternatives :

1. **Utiliser des webhooks temporisés** : Services comme cron-job.org ou Zapier pour appeler des endpoints API à intervalles réguliers.

2. **Intégrer les tâches dans les requêtes utilisateur** : Par exemple, vérifier et réinitialiser les compteurs lors de la connexion d'un utilisateur.

Créez des endpoints API pour vos tâches planifiées :

```python
@app.route('/api/maintenance/reset-counters', methods=['POST'])
def api_reset_counters():
    """Endpoint API pour réinitialiser les compteurs mensuels."""
    # Vérifier le token de sécurité
    token = request.headers.get('X-API-Key')
    if token != os.environ.get('MAINTENANCE_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    result = reset_monthly_counters()
    return jsonify({'status': 'success', 'message': result})

@app.route('/api/maintenance/check-subscriptions', methods=['POST'])
def api_check_subscriptions():
    """Endpoint API pour vérifier les abonnements expirés."""
    # Vérifier le token de sécurité
    token = request.headers.get('X-API-Key')
    if token != os.environ.get('MAINTENANCE_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    result = check_expired_subscriptions()
    return jsonify({'status': 'success', 'message': result})

@app.route('/api/maintenance/delete-expired-clips', methods=['POST'])
def api_delete_expired_clips():
    """Endpoint API pour supprimer les clips expirés."""
    # Vérifier le token de sécurité
    token = request.headers.get('X-API-Key')
    if token != os.environ.get('MAINTENANCE_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    result = delete_expired_clips()
    return jsonify({'status': 'success', 'message': result})
```

Ajoutez la variable d'environnement `MAINTENANCE_API_KEY` dans Render.

### 4. Déploiement sur Render

1. Connectez-vous à votre compte Render
2. Cliquez sur "New" et sélectionnez "Blueprint"
3. Connectez votre dépôt GitHub
4. Sélectionnez le dépôt contenant votre application
5. Render détectera automatiquement le fichier `render.yaml` et configurera les services
6. Remplissez les variables d'environnement manquantes (clés Stripe, etc.)
7. Cliquez sur "Apply" pour démarrer le déploiement

### 5. Configuration de Stripe

1. Dans le dashboard Stripe, allez dans Développeurs > Webhooks
2. Ajoutez un endpoint avec l'URL `https://votre-app.onrender.com/webhook`
3. Sélectionnez les événements à écouter (checkout.session.completed, customer.subscription.updated, customer.subscription.deleted)
4. Copiez la clé de signature du webhook et ajoutez-la comme variable d'environnement dans Render

### 6. Configuration des tâches planifiées avec cron-job.org

1. Créez un compte sur [cron-job.org](https://cron-job.org) (gratuit)
2. Créez trois tâches planifiées :
   - Réinitialisation des compteurs mensuels (1er jour du mois à 00:01)
     - URL: https://votre-app.onrender.com/api/maintenance/reset-counters
     - Méthode: POST
     - En-têtes: X-API-Key: votre_clé_de_maintenance
   - Vérification des abonnements expirés (tous les jours à 01:00)
     - URL: https://votre-app.onrender.com/api/maintenance/check-subscriptions
     - Méthode: POST
     - En-têtes: X-API-Key: votre_clé_de_maintenance
   - Suppression des clips expirés (tous les jours à 02:00)
     - URL: https://votre-app.onrender.com/api/maintenance/delete-expired-clips
     - Méthode: POST
     - En-têtes: X-API-Key: votre_clé_de_maintenance

## Limitations du niveau gratuit de Render

- Les services web gratuits sont mis en veille après 15 minutes d'inactivité
- Le réveil peut prendre environ 30 secondes lors de la première requête
- Bande passante limitée à 100 GB/mois
- Pas de domaine personnalisé dans le niveau gratuit
- Base de données PostgreSQL disponible uniquement dans les plans payants (période d'essai gratuite de 90 jours)

## Passage à l'échelle

Lorsque votre application se développe, vous pouvez facilement passer aux plans payants de Render pour obtenir :
- Des services web qui ne se mettent jamais en veille
- Plus de ressources CPU et mémoire
- Des domaines personnalisés avec HTTPS
- Des bases de données PostgreSQL permanentes

## Ressources supplémentaires

- [Documentation Render](https://render.com/docs)
- [Déploiement d'applications Flask sur Render](https://render.com/docs/deploy-flask)
- [Documentation Stripe](https://stripe.com/docs)
- [Documentation cron-job.org](https://docs.cron-job.org)
