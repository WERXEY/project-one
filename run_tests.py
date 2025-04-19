#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal pour exécuter les tests du générateur de clips "Best Of".
"""

import unittest
import sys
import os

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les suites de tests
from tests.test_auth import AuthTestCase
from tests.test_monetization import MonetizationTestCase
from tests.test_payment import PaymentTestCase

if __name__ == '__main__':
    # Créer une suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter les tests à la suite
    suite.addTests(loader.loadTestsFromTestCase(AuthTestCase))
    suite.addTests(loader.loadTestsFromTestCase(MonetizationTestCase))
    suite.addTests(loader.loadTestsFromTestCase(PaymentTestCase))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Sortir avec un code d'erreur si des tests ont échoué
    sys.exit(not result.wasSuccessful())
