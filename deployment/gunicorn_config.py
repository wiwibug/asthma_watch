bind = "0.0.0.0:8050"
workers = 2  # Réduire si besoin pour économiser la RAM (1 si mémoire limitée)
threads = 4  # Ajouter des threads pour mieux gérer les requêtes concurrentes
timeout = 120  # Augmenter le timeout pour éviter les erreurs de "Worker Timeout"
keepalive = 5  # Réduire le keepalive pour libérer plus vite les connexions
errorlog = "-"  # Rediriger les erreurs vers la sortie standard
accesslog = "-"  # Rediriger les logs d'accès vers la sortie standard
loglevel = "info"  # Définir le niveau des logs pour voir ce qui se passe
