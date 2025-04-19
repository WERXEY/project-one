#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scripts pour les tâches planifiées du générateur de clips "Best Of".
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/generateur-clips/cron.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importer les fonctions nécessaires
from api.subscription import reset_monthly_counters, check_expired_subscriptions, delete_expired_clips

def main():
    """Fonction principale pour exécuter les tâches planifiées."""
    if len(sys.argv) < 2:
        print("Usage: python cron_tasks.py [reset_counters|check_subscriptions|delete_clips]")
        sys.exit(1)
    
    task = sys.argv[1]
    
    try:
        if task == 'reset_counters':
            logger.info("Réinitialisation des compteurs mensuels...")
            result = reset_monthly_counters()
            logger.info(result)
        
        elif task == 'check_subscriptions':
            logger.info("Vérification des abonnements expirés...")
            result = check_expired_subscriptions()
            logger.info(result)
        
        elif task == 'delete_clips':
            logger.info("Suppression des clips expirés...")
            result = delete_expired_clips()
            logger.info(result)
        
        else:
            logger.error(f"Tâche inconnue: {task}")
            print(f"Tâche inconnue: {task}")
            sys.exit(1)
        
        logger.info("Tâche terminée avec succès.")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la tâche {task}: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
