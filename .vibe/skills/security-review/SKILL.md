---
name: security-review
description: Checklist de revue de sécurité pour les changements de code — secrets, validation des entrées, autorisation et journalisation d'audit
user-invocable: true
---

# Revue de sécurité

Appliquer cette checklist lors de l'écriture ou de la revue de code qui manipule des
entrées non fiables, de l'authentification ou des données sensibles. Elle va de pair
avec le hook de journal d'audit de conformité dans `.vibe/hooks.toml`. Dans un
contexte régulé comme celui de la Caisse des Dépôts, ces contrôles ne sont pas
optionnels : audit, souveraineté et protection des données sensibles sont des
exigences de premier ordre.

## Secrets & configuration
- Aucun secret dans le code ni dans l'historique git — utiliser des variables
  d'environnement ou un gestionnaire de secrets
- Les fichiers `.env` sont ignorés par git ; seul `.env.example` (avec des valeurs
  vides) est commité
- Aucun identifiant, token ou clé privée dans les logs ou les messages d'erreur

## Validation des entrées
- Valider et typer toute entrée externe à la frontière (modèles Pydantic pour les
  API)
- Traiter les paramètres de chemin, de requête, d'en-tête et de corps comme non
  fiables
- Paramétrer les requêtes base de données — ne jamais construire du SQL par
  concaténation de chaînes
- Borner les tailles (charges utiles, uploads, longueurs de listes) pour éviter
  l'épuisement des ressources

## AuthN / AuthZ
- Chaque endpoint protégé vérifie l'authentification ET l'autorisation (pas
  seulement la connexion)
- Appliquer le moindre privilège — refuser par défaut, accorder explicitement
- Ne pas faire confiance aux identifiants fournis par le client pour les décisions
  d'accès (par ex. `user_id` dans le corps)

## Sorties & erreurs
- Renvoyer des messages d'erreur génériques aux clients ; journaliser les détails
  côté serveur
- Ne jamais renvoyer de stack trace ni de chemins internes dans les réponses de
  l'API
- Utiliser le bon code de statut (401 vs 403 vs 404)

## Auditabilité
- Journaliser les événements pertinents pour la sécurité (authentification,
  changements de permissions, accès aux données) de façon structurée
- Consigner qui / quoi / quand — ne jamais journaliser le secret lui-même
- Tenir une piste d'audit en ajout seul pour les actions sensibles

## Souveraineté & données personnelles
- Données et exécution en Europe : vérifier qu'aucun traitement ni transfert ne
  sort de ce périmètre sans validation explicite
- Minimisation des données (esprit RGPD) : ne collecter et ne conserver que ce qui
  est nécessaire ; documenter la finalité

## Dépendances
- Épingler les versions des dépendances ; relire les nouvelles dépendances avant de
  les ajouter
- Surveiller les paquets présentant des vulnérabilités connues
