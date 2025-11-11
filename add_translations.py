#!/usr/bin/env python3
"""
Quick script to add French translations to the .po file
"""

translations = {
    # Navigation & Common
    "Smart Store": "Magasin Intelligent",
    "Dashboard": "Tableau de Bord",
    "Shop Now": "Magasiner Maintenant",
    "My Account": "Mon Compte",
    "Logout": "Déconnexion",
    "Login": "Connexion",
    "Sign Up": "S'inscrire",
    
    # Home Page
    "Welcome to Smart Store": "Bienvenue au Magasin Intelligent",
    "Your modern self-checkout smart store with RFID & barcode scanning. Shop for cold drinks, chocolates, and energy beverages with our intelligent refrigeration monitoring system — keeping products perfectly chilled, all the time.": "Votre magasin moderne avec libre-service automatisé utilisant RFID et codes-barres. Achetez des boissons froides, chocolats et boissons énergisantes avec notre système intelligent de surveillance de réfrigération — gardant les produits parfaitement refroidis en tout temps.",
    "Get Started - Create Account": "Commencer - Créer un Compte",
    "Customer Login": "Connexion Client",
    "© 2025 Smart Store IoT Project. Phase 2 & 3 Complete.": "© 2025 Projet IdO Magasin Intelligent. Phase 2 & 3 Complète.",
}

# Read the .po file
po_file_path = "translations/fr/LC_MESSAGES/messages.po"
with open(po_file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace empty msgstr with French translations
for english, french in translations.items():
    # Find the pattern: msgid "english text"\nmsgstr ""
    pattern = f'msgid "{english}"'
    if pattern in content:
        # Replace the empty msgstr with the French translation
        old_pattern = f'msgid "{english}"\nmsgstr ""'
        new_pattern = f'msgid "{english}"\nmsgstr "{french}"'
        content = content.replace(old_pattern, new_pattern)
        print(f"✓ Translated: {english[:50]}...")

# Write back
with open(po_file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Translations added to {po_file_path}")
print("Now compile with: pybabel compile -d translations")
