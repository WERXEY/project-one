#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion des abonnements pour le générateur de clips "Best Of".
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from api.models import db, User
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/subscription', methods=['GET'])
@login_required
def subscription_page():
    """Page de gestion d'abonnement."""
    return render_template('subscription.html')

@subscription_bp.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Mise à niveau de l'abonnement."""
    plan = request.form.get('plan')
    
    if not plan or plan not in ['free', 'premium', 'pro']:
        flash('Plan invalide.')
        return redirect(url_for('subscription.subscription_page'))
    
    # Si c'est un downgrade, on ne change pas immédiatement
    if (current_user.plan == 'pro' and plan in ['premium', 'free']) or \
       (current_user.plan == 'premium' and plan == 'free'):
        current_user.plan = plan
        # Pour un downgrade, on garde l'abonnement actif jusqu'à la fin de la période
        flash('Votre abonnement sera modifié à la fin de votre période de facturation actuelle.')
        db.session.commit()
        return redirect(url_for('subscription.subscription_page'))
    
    # Pour un upgrade ou un changement de plan gratuit
    try:
        current_user.upgrade_plan(plan)
        flash('Votre abonnement a été mis à jour avec succès.')
    except Exception as e:
        flash(f'Erreur lors de la mise à jour de votre abonnement: {str(e)}')
    
    return redirect(url_for('subscription.subscription_page'))

@subscription_bp.route('/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Annulation de l'abonnement."""
    if current_user.plan == 'free':
        flash('Vous n\'avez pas d\'abonnement actif à annuler.')
        return redirect(url_for('subscription.subscription_page'))
    
    # Garder l'abonnement actif jusqu'à la fin de la période
    flash('Votre abonnement sera annulé à la fin de votre période de facturation actuelle.')
    
    # Programmer le passage au plan gratuit à la fin de la période
    current_user.plan = 'free'
    db.session.commit()
    
    return redirect(url_for('subscription.subscription_page'))

@subscription_bp.route('/api/subscription/status', methods=['GET'])
@login_required
def subscription_status():
    """API pour obtenir le statut de l'abonnement."""
    return jsonify({
        'plan': current_user.plan,
        'clips_generated': current_user.clips_generated_this_month,
        'clips_limit': current_user.get_clip_limit() if current_user.plan != 'pro' else 'unlimited',
        'is_active': current_user.is_subscription_active(),
        'days_until_renewal': current_user.days_until_renewal(),
        'features': {
            'long_clips': current_user.plan != 'free',
            'no_watermark': current_user.plan != 'free',
            'custom_transitions': current_user.can_use_custom_transitions(),
            'custom_logo': current_user.can_use_custom_logo(),
            'api_access': current_user.can_access_api(),
            'max_quality': current_user.get_video_quality(),
            'max_duration': current_user.get_max_clip_duration(),
            'storage_days': current_user.get_clip_storage_days()
        }
    })

@subscription_bp.route('/api/subscription/plans', methods=['GET'])
def subscription_plans():
    """API pour obtenir les détails des plans d'abonnement."""
    return jsonify({
        'plans': [
            {
                'id': 'free',
                'name': 'Gratuit',
                'price': 0,
                'clips_limit': 3,
                'features': {
                    'long_clips': False,
                    'no_watermark': False,
                    'custom_transitions': False,
                    'custom_logo': False,
                    'api_access': False,
                    'max_quality': '720p',
                    'max_duration': 180,
                    'storage_days': 30
                }
            },
            {
                'id': 'premium',
                'name': 'Premium',
                'price': 9.99,
                'clips_limit': 20,
                'features': {
                    'long_clips': True,
                    'no_watermark': True,
                    'custom_transitions': True,
                    'custom_logo': False,
                    'api_access': False,
                    'max_quality': '1080p',
                    'max_duration': 600,
                    'storage_days': 90
                }
            },
            {
                'id': 'pro',
                'name': 'Pro',
                'price': 24.99,
                'clips_limit': 'unlimited',
                'features': {
                    'long_clips': True,
                    'no_watermark': True,
                    'custom_transitions': True,
                    'custom_logo': True,
                    'api_access': True,
                    'max_quality': '4k',
                    'max_duration': 1800,
                    'storage_days': 3650
                }
            }
        ]
    })

# Tâche planifiée pour réinitialiser les compteurs mensuels
# Cette fonction devrait être appelée par un planificateur de tâches (cron, celery, etc.)
def reset_monthly_counters():
    """Réinitialise les compteurs mensuels pour tous les utilisateurs."""
    users = User.query.all()
    for user in users:
        user.clips_generated_this_month = 0
    
    db.session.commit()
    return f"Compteurs réinitialisés pour {len(users)} utilisateurs."

# Tâche planifiée pour vérifier les abonnements expirés
# Cette fonction devrait être appelée par un planificateur de tâches (cron, celery, etc.)
def check_expired_subscriptions():
    """Vérifie les abonnements expirés et les passe au plan gratuit."""
    now = datetime.utcnow()
    expired_users = User.query.filter(
        User.plan.in_(['premium', 'pro']),
        User.subscription_end_date < now
    ).all()
    
    for user in expired_users:
        user.plan = 'free'
    
    db.session.commit()
    return f"Abonnements expirés traités pour {len(expired_users)} utilisateurs."

# Tâche planifiée pour supprimer les clips expirés
# Cette fonction devrait être appelée par un planificateur de tâches (cron, celery, etc.)
def delete_expired_clips():
    """Supprime les clips expirés."""
    from api.models import Clip
    import os
    
    now = datetime.utcnow()
    expired_clips = Clip.query.filter(
        Clip.expiration_date < now
    ).all()
    
    deleted_count = 0
    for clip in expired_clips:
        # Supprimer le fichier physique si possible
        if clip.file_path and os.path.exists(clip.file_path):
            try:
                os.remove(clip.file_path)
            except:
                pass
        
        db.session.delete(clip)
        deleted_count += 1
    
    db.session.commit()
    return f"Suppression de {deleted_count} clips expirés."
