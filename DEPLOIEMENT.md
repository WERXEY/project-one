# Documentation de déploiement - Générateur de clips "Best Of"

Ce document fournit les instructions détaillées pour déployer l'application de génération de clips "Best Of" en production.

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Base de données](#base-de-données)
5. [Intégration Stripe](#intégration-stripe)
6. [Déploiement](#déploiement)
7. [Tâches planifiées](#tâches-planifiées)
8. [Maintenance](#maintenance)
9. [Dépannage](#dépannage)

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- PostgreSQL 12 ou supérieur
- Serveur web (Nginx ou Apache)
- WSGI (Gunicorn ou uWSGI)
- Compte Stripe pour les paiements
- Serveur Linux (Ubuntu 20.04 LTS recommandé)
- Certificat SSL (Let's Encrypt recommandé)

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-organisation/generateur-clips-bestof.git
cd generateur-clips-bestof
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer FFmpeg (nécessaire pour le traitement vidéo)

```bash
sudo apt update
sudo apt install ffmpeg
```

## Configuration

### 1. Variables d'environnement

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```
# Configuration de l'application
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=votre_clé_secrète_très_longue_et_aléatoire

# Configuration de la base de données
DATABASE_URL=postgresql://utilisateur:mot_de_passe@localhost/nom_base_de_données

# Configuration de Stripe
STRIPE_PUBLIC_KEY=pk_live_votre_clé_publique
STRIPE_SECRET_KEY=sk_live_votre_clé_secrète
STRIPE_WEBHOOK_SECRET=whsec_votre_clé_webhook

# Configuration du stockage
STORAGE_PATH=/chemin/vers/stockage/clips
```

> **Important** : Ne jamais commiter le fichier `.env` dans le dépôt Git.

### 2. Configuration du serveur web (Nginx)

Créez un fichier de configuration Nginx :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    
    # Redirection vers HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name votre-domaine.com;
    
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Configuration SSL recommandée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    # Emplacement des fichiers statiques
    location /static {
        alias /chemin/vers/generateur-clips-bestof/static;
        expires 30d;
    }
    
    # Emplacement des clips générés
    location /clips {
        alias /chemin/vers/stockage/clips;
        expires 7d;
    }
    
    # Proxy vers l'application Flask
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Configuration pour les webhooks Stripe
    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Augmenter le timeout pour les webhooks
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

### 3. Configuration de Gunicorn

Créez un fichier `gunicorn.conf.py` :

```python
# Configuration de Gunicorn
bind = "127.0.0.1:8000"
workers = 4  # Nombre de workers = (2 * nombre de cœurs) + 1
worker_class = "gevent"
timeout = 120
keepalive = 5
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"
```

## Base de données

### 1. Création de la base de données PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE nom_base_de_données;
CREATE USER utilisateur WITH ENCRYPTED PASSWORD 'mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE nom_base_de_données TO utilisateur;
\q
```

### 2. Initialisation de la base de données

```bash
flask db upgrade
```

## Intégration Stripe

### 1. Configuration du compte Stripe

1. Créez un compte sur [Stripe](https://stripe.com) si vous n'en avez pas déjà un.
2. Dans le dashboard Stripe, allez dans Développeurs > Clés API pour obtenir vos clés.
3. Créez les produits et les prix pour vos plans d'abonnement :
   - Plan Premium : 9,99€/mois
   - Plan Pro : 24,99€/mois
4. Notez les IDs des prix (price_xxx) et mettez-les à jour dans le fichier `api/payment.py`.

### 2. Configuration des webhooks

1. Dans le dashboard Stripe, allez dans Développeurs > Webhooks.
2. Ajoutez un endpoint avec l'URL `https://votre-domaine.com/webhook`.
3. Sélectionnez les événements suivants à écouter :
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copiez la clé de signature du webhook et mettez-la dans votre fichier `.env`.

## Déploiement

### 1. Démarrage de l'application avec Gunicorn

Créez un fichier de service systemd pour gérer le démarrage automatique :

```bash
sudo nano /etc/systemd/system/generateur-clips.service
```

Contenu du fichier :

```ini
[Unit]
Description=Générateur de clips "Best Of"
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/chemin/vers/generateur-clips-bestof
Environment="PATH=/chemin/vers/generateur-clips-bestof/venv/bin"
EnvironmentFile=/chemin/vers/generateur-clips-bestof/.env
ExecStart=/chemin/vers/generateur-clips-bestof/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activez et démarrez le service :

```bash
sudo systemctl enable generateur-clips
sudo systemctl start generateur-clips
```

### 2. Vérification du déploiement

```bash
sudo systemctl status generateur-clips
```

## Tâches planifiées

Configurez des tâches cron pour exécuter les opérations de maintenance :

```bash
sudo crontab -e
```

Ajoutez les lignes suivantes :

```cron
# Réinitialisation des compteurs mensuels (1er jour du mois à 00:01)
1 0 1 * * /chemin/vers/generateur-clips-bestof/venv/bin/python /chemin/vers/generateur-clips-bestof/scripts/reset_monthly_counters.py

# Vérification des abonnements expirés (tous les jours à 01:00)
0 1 * * * /chemin/vers/generateur-clips-bestof/venv/bin/python /chemin/vers/generateur-clips-bestof/scripts/check_expired_subscriptions.py

# Suppression des clips expirés (tous les jours à 02:00)
0 2 * * * /chemin/vers/generateur-clips-bestof/venv/bin/python /chemin/vers/generateur-clips-bestof/scripts/delete_expired_clips.py
```

## Maintenance

### 1. Mise à jour de l'application

```bash
# Arrêter le service
sudo systemctl stop generateur-clips

# Mettre à jour le code
cd /chemin/vers/generateur-clips-bestof
git pull

# Activer l'environnement virtuel
source venv/bin/activate

# Mettre à jour les dépendances
pip install -r requirements.txt

# Mettre à jour la base de données
flask db upgrade

# Redémarrer le service
sudo systemctl start generateur-clips
```

### 2. Sauvegarde de la base de données

```bash
# Sauvegarde quotidienne
pg_dump -U utilisateur nom_base_de_données > /chemin/vers/sauvegardes/backup_$(date +%Y%m%d).sql
```

### 3. Rotation des logs

Configurez logrotate pour gérer la rotation des logs :

```bash
sudo nano /etc/logrotate.d/generateur-clips
```

Contenu du fichier :

```
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload generateur-clips
    endscript
}
```

## Dépannage

### Problèmes courants et solutions

1. **L'application ne démarre pas**
   - Vérifiez les logs : `sudo journalctl -u generateur-clips`
   - Vérifiez que toutes les variables d'environnement sont correctement définies

2. **Erreurs de base de données**
   - Vérifiez la connexion à la base de données : `psql -U utilisateur -h localhost nom_base_de_données`
   - Vérifiez que les migrations ont été appliquées : `flask db current`

3. **Problèmes avec Stripe**
   - Vérifiez les logs des webhooks dans le dashboard Stripe
   - Assurez-vous que les IDs des prix sont corrects dans le code

4. **Problèmes de génération de clips**
   - Vérifiez que FFmpeg est correctement installé : `ffmpeg -version`
   - Vérifiez les permissions du dossier de stockage : `ls -la /chemin/vers/stockage/clips`

### Logs à surveiller

- Logs de l'application : `/var/log/gunicorn/error.log` et `/var/log/gunicorn/access.log`
- Logs système : `sudo journalctl -u generateur-clips`
- Logs Nginx : `/var/log/nginx/error.log` et `/var/log/nginx/access.log`

### Contact support

Pour toute assistance supplémentaire, contactez l'équipe de support à support@votre-organisation.com ou ouvrez un ticket sur notre système de suivi des problèmes.
