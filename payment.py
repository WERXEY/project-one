#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intégration de Stripe pour le système de paiement du générateur de clips "Best Of".
"""

import os
import stripe
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from api.models import db, User
from datetime import datetime, timedelta

payment_bp = Blueprint('payment', __name__)

# Initialisation de Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_test_key')

# Plans Stripe (à créer dans le dashboard Stripe)
STRIPE_PLANS = {
    'premium': {
        'id': 'price_premium',  # ID du prix dans Stripe
        'name': 'Premium',
        'price': 999,  # en centimes (9,99€)
        'interval': 'month'
    },
    'pro': {
        'id': 'price_pro',  # ID du prix dans Stripe
        'name': 'Pro',
        'price': 2499,  # en centimes (24,99€)
        'interval': 'month'
    }
}

@payment_bp.route('/checkout/<plan>', methods=['GET'])
@login_required
def checkout(plan):
    """Page de paiement pour un plan spécifique."""
    if plan not in ['premium', 'pro']:
        flash('Plan invalide.')
        return redirect(url_for('subscription.subscription_page'))
    
    # Récupérer les informations du plan
    stripe_plan = STRIPE_PLANS.get(plan)
    
    return render_template('checkout.html', plan=plan, stripe_plan=stripe_plan)

@payment_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Crée une session de paiement Stripe."""
    plan = request.form.get('plan')
    
    if plan not in ['premium', 'pro']:
        return jsonify({'error': 'Plan invalide'}), 400
    
    stripe_plan = STRIPE_PLANS.get(plan)
    
    try:
        # Créer une session de paiement Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': stripe_plan['id'],
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=url_for('payment.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment.cancel', _external=True),
            client_reference_id=current_user.id,
            customer_email=current_user.email,
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/success', methods=['GET'])
@login_required
def success():
    """Page de succès après un paiement réussi."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return redirect(url_for('subscription.subscription_page'))
    
    try:
        # Récupérer les informations de la session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Récupérer l'abonnement
        subscription = stripe.Subscription.retrieve(checkout_session.subscription)
        
        # Mettre à jour l'utilisateur avec les informations d'abonnement
        if subscription.plan.id == STRIPE_PLANS['premium']['id']:
            plan = 'premium'
        elif subscription.plan.id == STRIPE_PLANS['pro']['id']:
            plan = 'pro'
        else:
            plan = 'free'
        
        current_user.plan = plan
        current_user.payment_id = subscription.id
        current_user.subscription_start_date = datetime.fromtimestamp(subscription.current_period_start)
        current_user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
        
        db.session.commit()
        
        flash('Votre abonnement a été activé avec succès !')
        return redirect(url_for('subscription.subscription_page'))
    except Exception as e:
        flash(f'Une erreur est survenue lors de la validation de votre abonnement: {str(e)}')
        return redirect(url_for('subscription.subscription_page'))

@payment_bp.route('/cancel', methods=['GET'])
@login_required
def cancel():
    """Page d'annulation après un paiement annulé."""
    flash('Le processus de paiement a été annulé.')
    return redirect(url_for('subscription.subscription_page'))

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Webhook pour recevoir les événements Stripe."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')
        )
    except ValueError as e:
        # Payload invalide
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Signature invalide
        return jsonify({'error': str(e)}), 400
    
    # Gérer les événements
    if event['type'] == 'checkout.session.completed':
        # Paiement réussi, l'abonnement est créé
        session = event['data']['object']
        fulfill_order(session)
    elif event['type'] == 'customer.subscription.updated':
        # Mise à jour de l'abonnement
        subscription = event['data']['object']
        update_subscription(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        # Suppression de l'abonnement
        subscription = event['data']['object']
        cancel_subscription(subscription)
    
    return jsonify({'status': 'success'})

def fulfill_order(session):
    """Traite une commande réussie."""
    # Récupérer l'utilisateur
    user_id = session.get('client_reference_id')
    if not user_id:
        return
    
    user = User.query.get(user_id)
    if not user:
        return
    
    # Récupérer l'abonnement
    subscription_id = session.get('subscription')
    if not subscription_id:
        return
    
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Mettre à jour l'utilisateur
    if subscription.plan.id == STRIPE_PLANS['premium']['id']:
        user.plan = 'premium'
    elif subscription.plan.id == STRIPE_PLANS['pro']['id']:
        user.plan = 'pro'
    else:
        user.plan = 'free'
    
    user.payment_id = subscription.id
    user.subscription_start_date = datetime.fromtimestamp(subscription.current_period_start)
    user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
    
    db.session.commit()

def update_subscription(subscription):
    """Met à jour un abonnement existant."""
    # Récupérer l'utilisateur par l'ID de paiement
    user = User.query.filter_by(payment_id=subscription.id).first()
    if not user:
        return
    
    # Mettre à jour le plan
    if subscription.plan.id == STRIPE_PLANS['premium']['id']:
        user.plan = 'premium'
    elif subscription.plan.id == STRIPE_PLANS['pro']['id']:
        user.plan = 'pro'
    else:
        user.plan = 'free'
    
    # Mettre à jour les dates d'abonnement
    user.subscription_start_date = datetime.fromtimestamp(subscription.current_period_start)
    user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
    
    db.session.commit()

def cancel_subscription(subscription):
    """Annule un abonnement."""
    # Récupérer l'utilisateur par l'ID de paiement
    user = User.query.filter_by(payment_id=subscription.id).first()
    if not user:
        return
    
    # Garder l'abonnement actif jusqu'à la fin de la période
    # Le plan sera automatiquement changé en 'free' à l'expiration
    
    db.session.commit()

@payment_bp.route('/manage-subscription', methods=['GET'])
@login_required
def manage_subscription():
    """Page de gestion de l'abonnement Stripe."""
    if not current_user.payment_id or current_user.plan == 'free':
        flash('Vous n\'avez pas d\'abonnement actif.')
        return redirect(url_for('subscription.subscription_page'))
    
    try:
        # Créer un portail client Stripe
        session = stripe.billing_portal.Session.create(
            customer=current_user.payment_id,
            return_url=url_for('subscription.subscription_page', _external=True),
        )
        
        # Rediriger vers le portail client
        return redirect(session.url)
    except Exception as e:
        flash(f'Une erreur est survenue: {str(e)}')
        return redirect(url_for('subscription.subscription_page'))
