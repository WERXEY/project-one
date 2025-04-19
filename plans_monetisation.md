# Structure des plans de monétisation pour le générateur de clips "Best Of"

## Vue d'ensemble des plans

| Fonctionnalité | Free | Premium | Pro |
|----------------|------|---------|-----|
| Prix mensuel | 0€ | 9,99€ | 24,99€ |
| Clips par mois | 3 | 20 | Illimité |
| Types de clips | Courts uniquement | Courts et longs | Courts et longs |
| Qualité vidéo | Standard (720p) | Haute (1080p) | Maximale (4K) |
| Filigrane | Oui | Non | Non |
| Transitions personnalisées | Non | Oui | Oui |
| Logo personnalisé | Non | Non | Oui |
| API dédiée | Non | Non | Oui |
| Support | Email | Prioritaire | 24/7 |

## Détails des plans

### Plan Free (Gratuit)
- **Objectif**: Permettre aux utilisateurs de découvrir le service
- **Limitations**:
  - Maximum de 3 clips générés par mois
  - Uniquement des clips courts (max 3 minutes)
  - Qualité vidéo limitée à 720p
  - Filigrane "Généré avec Best Of Clips" sur toutes les vidéos
  - Transitions de base uniquement
  - Pas de personnalisation avancée
  - Support par email uniquement (réponse sous 48h)
- **Fonctionnalités**:
  - Génération de clips courts à partir de vidéos YouTube
  - Stockage des clips pendant 30 jours
  - Téléchargement des clips générés
  - Partage des clips via URL

### Plan Premium
- **Objectif**: Répondre aux besoins des créateurs de contenu réguliers
- **Prix**: 9,99€ par mois
- **Fonctionnalités**:
  - Maximum de 20 clips générés par mois
  - Clips courts et longs (jusqu'à 10 minutes)
  - Qualité vidéo jusqu'à 1080p
  - Sans filigrane
  - Transitions personnalisées (5 styles disponibles)
  - Stockage des clips pendant 90 jours
  - Support prioritaire (réponse sous 24h)
  - Téléchargement des clips en différents formats (MP4, MOV)
  - Options de partage avancées (réseaux sociaux, intégration)

### Plan Pro
- **Objectif**: Répondre aux besoins des professionnels et des entreprises
- **Prix**: 24,99€ par mois
- **Fonctionnalités**:
  - Clips illimités
  - Clips courts et longs (jusqu'à 30 minutes)
  - Qualité vidéo maximale (jusqu'à 4K)
  - Sans filigrane
  - Transitions personnalisées (tous les styles disponibles)
  - Ajout de logo personnalisé
  - Stockage permanent des clips
  - Support 24/7
  - API dédiée pour l'intégration avec d'autres services
  - Téléchargement des clips en tous formats
  - Statistiques d'utilisation détaillées
  - Possibilité de créer des modèles de clips réutilisables

## Implémentation technique

### Modifications du modèle User
```python
class User(db.Model, UserMixin):
    # Champs existants...
    
    # Nouveaux champs à ajouter
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    payment_id = db.Column(db.String(100))  # ID de paiement externe (Stripe)
    custom_logo = db.Column(db.String(200))  # Chemin vers le logo personnalisé
    
    # Méthodes existantes...
    
    def get_video_quality(self):
        """Retourne la qualité vidéo maximale selon le plan."""
        if self.plan == 'free':
            return '720p'
        elif self.plan == 'premium':
            return '1080p'
        elif self.plan == 'pro':
            return '4k'
        return '720p'
    
    def get_max_clip_duration(self):
        """Retourne la durée maximale d'un clip selon le plan."""
        if self.plan == 'free':
            return 180  # 3 minutes en secondes
        elif self.plan == 'premium':
            return 600  # 10 minutes en secondes
        elif self.plan == 'pro':
            return 1800  # 30 minutes en secondes
        return 180
    
    def has_watermark(self):
        """Indique si les clips doivent avoir un filigrane."""
        return self.plan == 'free'
    
    def can_use_custom_transitions(self):
        """Indique si l'utilisateur peut utiliser des transitions personnalisées."""
        return self.plan in ['premium', 'pro']
    
    def can_use_custom_logo(self):
        """Indique si l'utilisateur peut ajouter un logo personnalisé."""
        return self.plan == 'pro'
    
    def get_clip_storage_days(self):
        """Retourne la durée de stockage des clips en jours."""
        if self.plan == 'free':
            return 30
        elif self.plan == 'premium':
            return 90
        elif self.plan == 'pro':
            return 365 * 10  # "Permanent" (10 ans)
        return 30
    
    def can_access_api(self):
        """Indique si l'utilisateur peut accéder à l'API dédiée."""
        return self.plan == 'pro'
```

### Modifications du modèle Clip
```python
class Clip(db.Model):
    # Champs existants...
    
    # Nouveaux champs à ajouter
    quality = db.Column(db.String(10), default='720p')  # Qualité vidéo
    watermark = db.Column(db.Boolean, default=True)  # Filigrane
    custom_logo_path = db.Column(db.String(200))  # Chemin vers le logo personnalisé
    transition_style = db.Column(db.String(50), default='basic')  # Style de transition
    expiration_date = db.Column(db.DateTime)  # Date d'expiration du clip
```

## Gestion des abonnements

### Cycle de vie d'un abonnement
1. **Inscription**: L'utilisateur s'inscrit et choisit un plan
2. **Période d'essai**: Pour les plans payants, possibilité d'offrir 7 jours d'essai
3. **Premier paiement**: À la fin de la période d'essai ou immédiatement si pas d'essai
4. **Renouvellement**: Automatique à la fin de chaque période (mensuelle)
5. **Changement de plan**: Possible à tout moment
   - Upgrade: Effet immédiat, facturation au prorata
   - Downgrade: Effet à la fin de la période en cours
6. **Annulation**: L'utilisateur peut annuler à tout moment
   - Le plan reste actif jusqu'à la fin de la période payée
   - Passage automatique au plan gratuit ensuite

### Gestion des limites mensuelles
- Réinitialisation du compteur `clips_generated_this_month` à chaque renouvellement d'abonnement
- Vérification de la limite avant chaque génération de clip
- Notification à l'utilisateur lorsqu'il approche de sa limite (80%)
- Proposition d'upgrade lorsque la limite est atteinte

## Interface utilisateur

### Page de gestion d'abonnement
- Affichage du plan actuel
- Historique des paiements
- Option pour changer de plan
- Option pour annuler l'abonnement
- Informations sur l'utilisation (clips générés/restants)

### Indicateurs visuels
- Badge indiquant le plan actuel dans l'interface
- Compteur de clips restants pour le mois
- Barre de progression pour la limite mensuelle
- Icônes spécifiques pour les fonctionnalités premium/pro

## Stratégie de conversion

### Incitations à l'upgrade
- Bouton "Débloquer plus de clips" lorsque la limite est atteinte
- Message "Améliorez votre plan pour accéder aux clips longs" pour les utilisateurs gratuits
- Comparaison des plans lors de la génération d'un clip avec des options non disponibles
- Offres promotionnelles ponctuelles (premier mois à -50%, etc.)

### Rétention des utilisateurs
- Email de bienvenue avec tutoriel pour les nouveaux utilisateurs
- Notification avant le renouvellement de l'abonnement
- Email de suivi après génération de clips pour encourager le partage
- Programme de parrainage (1 mois gratuit pour chaque ami inscrit)
