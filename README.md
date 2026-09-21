# D5

# ⚔️ Projet Pygame : Plateforme  PvP (2 Joueurs)

Bienvenue dans le dépôt officiel de notre jeu de combat en arène ! Ce document sert de feuille de route et de guide de démarrage pour toute l'équipe. Lisez attentivement votre rôle et les règles de collaboration avant de pousser votre premier code.

---

## Configuration initiale

Chaque développeur doit créer puis activer un environnement virtuel avant
d’installer Pygame.

### Compatibilité avec Python 3.14 (`pygame-ce`)

Avec Python 3.14, installez `pygame-ce` plutôt que le paquet `pygame` :

```bash
python -m pip install pygame-ce
```

`pygame-ce` est une version communautaire compatible avec Python 3.14. Son
installation fournit toujours le module importé sous le nom `pygame`, donc le
code du projet ne change pas :

```python
import pygame
```

Si vous exécutez `python -m pip install pygame` avec Python 3.14, `pip` peut
télécharger une archive source (`pygame-2.6.1.tar.gz`) au lieu d'une version
précompilée. Il tente alors de compiler Pygame et échoue souvent avec des
messages comme `sdl2-config: not found` ou `freetype2 was not found`. Cette
erreur signifie généralement que la version classique de Pygame ne fournit
pas encore de paquet adapté à votre version de Python, et non qu'il y a un
problème dans le code du jeu.

Pour vérifier l'installation :

```bash
python -c "import pygame; print(pygame.version.ver)"
```

Avec Python 3.13 ou une version antérieure, `pygame` classique peut également
être utilisé :

```bash
python -m pip install pygame
```

### Linux (et macOS)

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pygame-ce
```

### Windows (PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pygame-ce
```

### Windows (Invite de commandes)

```bat
py -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pygame-ce
```

Pour quitter l’environnement virtuel :

```bash
deactivate
```

---

## Répartition des Rôles (Équipe de 5)

Pour éviter de travailler sur les mêmes lignes de code en même temps (et s'entretuer sur Git), les tâches sont strictement séparées :

###♂️ Développeur 1 : L'Intégrateur & Moteur Global (Lead Dev)
*   **Mission :** Créer la structure globale du projet (`main.py`, `game.py`) et centraliser le travail des autres.
*   **Tâches prioritaires :** 
    *   Mettre en place la boucle principale et la structure de fichiers.
    *   Créer l'état global du jeu (Écran titre, Écran de combat, Écran de fin).
    *   Valider et fusionner (merge) les branches des camarades.

### Développeur 2 : Le Maître de la Physique (Moteur de Gravité)
*   **Mission :** Gérer l'environnement, le sol et la physique du monde.
*   **Tâches prioritaires :**
    *   Créer la classe `Platform` (des rectangles solides).
    *   Développer le système de gravité constante appliquée aux joueurs.
    *   Gérer la collision verticale (le joueur s'arrête net quand il touche le sol ou une plateforme par le haut).

###♂️ Développeur 3 : Le Concepteur des Joueurs (Mécaniques & Inputs)
*   **Mission :** Donner vie aux deux combattants.
*   **Tâches prioritaires :**
    *   Créer la classe `Player` (héritant de `pygame.sprite.Sprite`).
    *   Mettre en place deux configurations de touches distinctes (Joueur 1 : `Z, Q, S, D` + `Espace` | Joueur 2 : `Flèches` + `Entrée`).
    *   Gérer les états du joueur (au sol, en l'air, direction du regard).

### Développeur 4 : Le Maître du Combat (Projectiles & Hitbox)
*   **Mission :** Gérer le système d'attaque et les dégâts.
*   **Tâches prioritaires :**
    *   Créer la classe `Bullet` (ou `Arrow`) déclenchée par la touche d'attaque.
    *   Gérer la trajectoire rectiligne du projectile selon l'orientation du joueur.
    *   Détecter la collision entre le projectile d'un joueur et le rectangle (hitbox) de l'autre joueur pour lui retirer des points de vie (HP).

### Développeur 5 : L'Artiste UI & Sound Designer (Interface & Ambiance)
*   **Mission :** Rendre le jeu beau, lisible et dynamique.
*   **Tâches prioritaires :**
    *   Afficher l'interface en jeu (Barres de vie `HP` en haut de l'écran, compteur de score).
    *   Intégrer les assets graphiques (sprites des joueurs, textures des plateformes).
    *   Gérer les effets sonores (bruit de saut, bruit de tir, musique de fond) avec le module `pygame.mixer`.

---

## Structure du Code Source (Architecture POO)

Pour travailler proprement, notre dossier `src/` sera découpé ainsi. Ne modifiez que les fichiers liés à votre rôle !

```text
├── assets/                  # Images, Sons, Polices (Dev 5)
├── src/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée (Dev 1)
│   ├── game.py              # Gestion des écrans et scores (Dev 1)
│   ├── player.py            # Classe du Joueur (Dev 3)
│   ├── world.py             # Physique et Plateformes (Dev 2)
│   ├── combat.py            # Projectiles et attaques (Dev 4)
│   └── ui.py                # Affichage des barres de vie (Dev 5)
└── README.md
```

### Lancer le jeu

Depuis la racine du projet, avec l’environnement virtuel activé :

```bash
python -m src.main
```

Le joueur 1 utilise `Q/D` pour se déplacer, `Espace` pour sauter et `E` pour
tirer. Le joueur 2 utilise les flèches, `↑` pour sauter et `Entrée` pour tirer.

---

## Les Règles d'or de Git pour l'Équipe
1.  **Interdiction stricte** de push directement sur la branche `main`.
2.  Chaque développeur crée une branche dédiée à sa tâche : `git checkout -b feature/nom-de-ma-tache`.
3.  Une fois votre fonctionnalité fonctionnelle en local, ouvrez une **Pull Request (PR)** sur GitHub et demandez la validation du Développeur 1 (L'Intégrateur).
