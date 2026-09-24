# D5

Jeu de combat PvP en arène pour deux joueurs, développé avec Python et
Pygame. Le jeu propose deux personnages, des projectiles, des boucliers, des
animations et plusieurs backgrounds sélectionnés aléatoirement au début de
chaque manche.

## Installation

Le projet utilise Python 3.14 et `pygame-ce`.

### Linux et macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pygame-ce
```

### Windows PowerShell

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pygame-ce
```

Vérifier l’installation :

```bash
python -c "import pygame; print(pygame.version.ver)"
```

Quitter l’environnement virtuel :

```bash
deactivate
```

## Lancer le jeu

Depuis la racine du projet, avec `venv` activé :

```bash
python -m src.main
```

La fenêtre du jeu s’appelle `D5` et utilise actuellement une résolution de
`960×540`.

## Fonctionnement actuel

- Le menu est affiché au démarrage.
- Le menu présente Sam et Emma avec leurs contrôles.
- `Entrée` ou `Espace` lance une manche.
- Un background de `assets/bg/` est choisi aléatoirement au début de chaque
  manche.
- `Échap` met la partie en pause ; `Échap` à nouveau reprend la partie.
- Quand un joueur n’a plus de points de vie, l’écran de victoire apparaît.
- L’écran de victoire affiche le personnage gagnant et son animation dédiée
  lorsqu’elle est disponible.
- `Entrée` ou `Espace` permet de recommencer une manche.
- `Échap` permet de revenir au menu depuis l’écran de victoire.

## Contrôles

| Action | Sam — Joueur 1 | Emma — Joueur 2 |
|---|---|---|
| Déplacement gauche/droite | `Q` / `D` | `←` / `→` |
| Saut / double saut | `Z` | `↑` |
| Attaque chargée | maintenir `Shift gauche`, puis relâcher | maintenir `Shift droit`, puis relâcher |
| Bouclier | `S` | `↓` |

Le HUD affiche les noms, les HP numériques, la barre de vie, la durabilité du
bouclier et la progression de charge du tir.

## Organisation des rôles

### Développeur 1 — Architecture et intégration

- boucle principale et états du jeu : menu, partie, victoire ;
- création et coordination des joueurs, du monde et des projectiles ;
- intégration des branches des autres développeurs ;
- validation des Pull Requests et tests finaux.

**Fichiers principaux :** `src/main.py`, `src/game.py`, `src/settings.py`.

**Missions détaillées :**

- initialiser Pygame, la fenêtre `960×540`, l’horloge et le cycle de jeu ;
- organiser les états `MENU`, `PLAYING` et `GAME_OVER` ;
- appeler les systèmes dans le bon ordre : événements, contrôles, physique,
  combat, affichage ;
- créer les deux joueurs, le monde, les projectiles et le HUD ;
- détecter la fin d’une manche et identifier le gagnant ;
- gérer le redémarrage d’une manche et le retour au menu ;
- définir les constantes et les interfaces communes entre développeurs ;
- tester les branches avant leur fusion et résoudre les conflits Git ;
- ne pas réécrire la physique, les contrôles ou le combat sans coordination
  avec les développeurs responsables.

### Développeur 2 — Monde et physique

- plateformes ;
- gravité ;
- collisions verticales ;
- comportement du joueur sur le sol et les plateformes.

**Fichiers principaux :** `src/world.py` et, si nécessaire, les éléments de
collision associés au monde.

**Missions détaillées :**

- définir les plateformes solides et leurs rectangles de collision ;
- appliquer la gravité à chaque joueur à chaque frame ;
- arrêter la chute lorsqu’un joueur atteint le dessus d’une plateforme ;
- remettre la vitesse verticale à zéro lors de l’atterrissage ;
- réinitialiser les sauts disponibles lorsque le joueur touche le sol ;
- gérer les limites et les règles de déplacement liées à l’arène ;
- fournir à `Game` des méthodes simples comme
  `world.apply_gravity(player)` ;
- ne pas gérer le HUD, les armes ou les règles de victoire.

### Développeur 3 — Joueurs et contrôles

- déplacement et saut ;
- double saut et dash ;
- orientation et états du joueur ;
- configuration des touches.

**Fichier principal :** `src/player.py`.

**Missions détaillées :**

- définir la classe `Player` et son rectangle physique `rect` ;
- gérer le déplacement horizontal et l’orientation du personnage ;
- gérer le saut, le double saut et le dash ;
- gérer les états d’entrée précédents pour détecter un appui ou un relâchement ;
- fournir à `Game` les informations nécessaires au tir ;
- conserver les propriétés utilisées par les autres systèmes : `health`,
  `facing`, `velocity_y`, `on_ground` et `rect` ;
- ne pas dessiner le HUD et ne pas décider directement du gagnant.

### Développeur 4 — Combat

- projectiles et dégâts ;
- attaque chargée ;
- bouclier, parade et blocage ;
- collisions entre projectiles et joueurs.

**Fichiers principaux :** `src/combat.py` et la partie combat de l’intégration
dans `src/game.py`, après validation du Dev 1.

**Missions détaillées :**

- définir les projectiles et leurs propriétés : vitesse, direction, propriétaire
  et dégâts ;
- gérer les attaques normales et chargées ;
- supprimer un projectile lorsqu’il sort de l’écran ;
- détecter les impacts sur le rectangle du joueur adverse ;
- appliquer le bouclier : blocage, usure, parade et renvoi ;
- fournir un système extensible pour ajouter d’autres armes à distance ;
- ne pas modifier le menu, le HUD ou les assets sans coordination avec le
  Dev 5.

### Développeur 5 — Interface et assets

- HUD, noms et barres de vie ;
- barre de durabilité du bouclier ;
- menu et écran de victoire ;
- sprites, animations, backgrounds, sons et effets visuels.

**Fichiers principaux :** `src/ui.py`, `src/assets.py` et le dossier `assets/`.

**Missions détaillées :**

- afficher les noms `Sam` et `Emma` ;
- afficher les barres de vie et la durabilité des boucliers ;
- afficher les menus, les instructions, l’écran de victoire et les actions
  disponibles ;
- charger les spritesheets et leurs métadonnées JSON ;
- aligner les sprites avec les rectangles physiques sans modifier la collision ;
- sélectionner et afficher les backgrounds de l’arène ;
- préparer les sons de tir, de saut, d’impact et de victoire ;
- ajouter les effets visuels sans modifier les règles de jeu ;
- optimiser les assets chargés afin d’éviter de recharger les images à chaque
  frame ;
- ne pas modifier la gravité, les contrôles ou les dégâts.

## Structure du projet

```text
├── assets/
│   ├── alchemist/          # Sprites de Sam (Dev 5)
│   ├── arcane-mage/        # Sprites d’Emma (Dev 5)
│   └── bg/                 # Backgrounds de l’arène (Dev 5)
├── src/
│   ├── main.py             # Point d’entrée (Dev 1)
│   ├── game.py             # Boucle, états et intégration (Dev 1)
│   ├── player.py           # Joueurs, contrôles et états (Dev 3)
│   ├── world.py            # Plateformes et gravité (Dev 2)
│   ├── combat.py           # Projectiles et dégâts (Dev 4)
│   ├── assets.py           # Chargement des spritesheets (Dev 5)
│   ├── settings.py         # Constantes du projet (Dev 1)
│   └── ui.py               # HUD, menu et victoire (Dev 5)
└── README.md
```

## Règles Git

Ne jamais pousser directement sur `main`. Chaque développeur travaille sur
sa branche dédiée.

```bash
git fetch origin
git switch -c feature/nom-de-la-tache
```

Après une modification :

```bash
git add fichiers_modifies
git commit -m "description claire de la modification"
git push -u origin feature/nom-de-la-tache
```

Ensuite, ouvrir une Pull Request vers `main` ou vers la branche d’intégration
demandée. Le Dev 1 vérifie et teste la branche avant la fusion.

Pour mettre sa branche à jour après une fusion dans `main` :

```bash
git switch main
git pull origin main
git switch feature/nom-de-la-tache
git merge main
```

Ne jamais valider des marqueurs de conflit comme `<<<<<<<`, `=======` ou
`>>>>>>>`. Avant une Pull Request, vérifier :

```bash
python -m compileall -q src
rg -n '^(<<<<<<<|=======|>>>>>>>)' src
```
