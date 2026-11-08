# Cédule de maintenance de centrales électriques par algorithme génétique

Projet du cours Heuristiques et Méta-heuristiques (LSI3, FSS Sfax).
Un algorithme génétique (AG) en Python qui planifie la maintenance de 7 centrales électriques sur 4 intervalles de l'année, en maximisant la puissance en réserve.

## Le problème

L'année est divisée en 4 intervalles, de demande 80, 90, 65 et 70 MW. Chaque unité doit être arrêtée pour maintenance pendant 1 ou 2 intervalles consécutifs :

| Unité | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Capacité (MW) | 20 | 15 | 35 | 40 | 15 | 15 | 10 |
| Intervalles de maintenance | 2 | 2 | 1 | 1 | 1 | 1 | 1 |

La capacité totale est de 150 MW. Pendant qu'une unité est en maintenance, sa capacité est perdue. La réserve d'un intervalle vaut :

```
réserve(t) = capacité totale - puissance en maintenance(t) - demande(t)
```

**Objectif :** trouver la cédule qui maximise la **plus petite réserve** sur les 4 intervalles.

## Codage d'une solution

Un chromosome est une liste de 7 gènes, un par unité. Chaque gène est une chaîne de 4 bits, un bit par intervalle : `1` veut dire en maintenance, `0` pas de maintenance.

| Unités | Gènes possibles |
|---|---|
| 1 et 2 (2 intervalles) | `1100`, `0110`, `0011` |
| 3 à 7 (1 intervalle) | `1000`, `0100`, `0010`, `0001` |

Exemple : `1100 0011 0001 0010 0100 1000 1000` signifie que l'unité 1 est en maintenance aux intervalles 1 et 2, l'unité 2 aux intervalles 3 et 4, l'unité 3 à l'intervalle 4, et ainsi de suite.

Comme on ne tire que des gènes valides, les contraintes de durée et de maintenance consécutive sont toujours respectées. Il y a 3 × 3 × 4^5 = 9 216 cédules possibles.

## Fonctionnement du code

Le fichier `ordonnancement_ag_simple.py` ne dépend que de la bibliothèque standard de Python 3.

| Élément | Rôle |
|---|---|
| `fitness(chromosome)` | Calcule la réserve de chaque intervalle et retourne la plus petite (0 si elle est négative). |
| `individu_aleatoire()` | Crée un chromosome en tirant un gène valide pour chaque unité. |
| `selection_roulette(population, fits)` | Sélection par loterie : un individu est choisi avec une probabilité proportionnelle à sa fitness. On cumule les fitness, on tire un nombre entre 0 et la somme, puis on retourne l'individu dont le segment contient ce nombre. |
| `croisement(p1, p2)` | Croisement en un point, placé entre deux gènes. Les deux enfants échangent leurs queues et restent valides. |
| `mutation_inversion(chromosome)` | Tire deux positions, inverse l'ordre des gènes entre elles, puis répare chaque gène pour respecter la durée de son unité. |
| `algorithme_genetique(...)` | Boucle principale : évaluation, élitisme, sélection, croisement, mutation, nouvelle génération. |

### La mutation par inversion et sa réparation

Inverser des gènes peut donner à une unité un gène qui ne lui convient pas, parce que les unités 1 et 2 ont une durée de 2 et les autres une durée de 1. La réparation garde l'intervalle de début du gène et impose la durée de l'unité qui le reçoit.

```
Avant       : 1100 0011 0001 0010 0100 1000 1000
Inversion   : 1100 0100 0010 0001 0011 1000 1000    (gènes 2 à 5 inversés)
Réparation  : 1100 0110 0010 0001 0010 1000 1000
              unité 2 reçoit 0100 (durée 1) : devient 0110 (durée 2)
              unité 5 reçoit 0011 (durée 2) : devient 0010 (durée 1)
```

### Paramètres

| Paramètre | Valeur par défaut | Signification |
|---|---|---|
| `taille` | 49 | Taille de la population (7 variables x 7) |
| `generations` | 100 | Nombre de générations |
| `pc` | 0,8 | Probabilité de croisement d'un couple |
| `pm` | 0,2 | Probabilité de mutation d'un enfant |

L'élitisme recopie le meilleur individu sans modification à chaque génération. Les valeurs se changent dans l'appel `algorithme_genetique(...)` en bas du fichier.

## Exécution

```
python ordonnancement_ag_simple.py
```

La graine aléatoire est fixée (`random.seed(42)`), donc le résultat est reproductible. Sortie obtenue :

```
Meilleure cédule : 1100 0011 0001 0010 0100 1000 1000
  unité 1 (20 MW) : maintenance aux intervalles [1, 2]
  unité 2 (15 MW) : maintenance aux intervalles [3, 4]
  unité 3 (35 MW) : maintenance aux intervalles [4]
  unité 4 (40 MW) : maintenance aux intervalles [3]
  unité 5 (15 MW) : maintenance aux intervalles [2]
  unité 6 (15 MW) : maintenance aux intervalles [1]
  unité 7 (10 MW) : maintenance aux intervalles [1]
Fitness (plus petite réserve) : 25 MW
```

### Lecture de la sortie

- La première ligne est le meilleur chromosome trouvé, gène par gène (unité 1 à unité 7).
- Les lignes suivantes décodent ce chromosome : pour chaque unité, les intervalles où elle est arrêtée.
- La dernière ligne est la fitness, c'est-à-dire la plus petite réserve de l'année.

Vérification des réserves de cette cédule :

| Intervalle | Unités en maintenance | Puissance perdue | Demande | Réserve |
|---|---|---|---|---|
| 1 | 1, 6, 7 | 20 + 15 + 10 = 45 | 80 | 150 - 45 - 80 = 25 |
| 2 | 1, 5 | 20 + 15 = 35 | 90 | 150 - 35 - 90 = 25 |
| 3 | 2, 4 | 15 + 40 = 55 | 65 | 150 - 55 - 65 = 30 |
| 4 | 2, 3 | 15 + 35 = 50 | 70 | 150 - 50 - 70 = 30 |

La plus petite réserve est 25 MW, qui est la valeur affichée.

## Résultats

- **25 MW est l'optimum.** La puissance perdue sur l'année vaut 20x2 + 15x2 + 35 + 40 + 15 + 15 + 10 = 185 MW, donc la somme des quatre réserves est 4 x 150 - 185 - 305 = 110 MW, soit 27,5 MW en moyenne. Les valeurs étant des multiples de 5, la plus petite réserve ne peut pas dépasser 25. Un test de toutes les 9 216 cédules confirme que 43 d'entre elles atteignent 25.
- **Fiabilité de l'AG.** Sur 30 exécutions avec des graines différentes (0 à 29), l'optimum de 25 MW est trouvé 29 fois, et la fitness moyenne finale est de 24,83 MW.
- **Opérateurs valides.** Sur 5 000 essais aléatoires, le croisement et la mutation ont toujours produit des chromosomes valides.

## Limites

- Le problème est petit : tester les 9 216 cédules donne l'optimum immédiatement. L'AG sert ici d'illustration et devient utile quand le nombre d'unités ou d'intervalles augmente.
- La sélection par roulette est peu sélective quand les fitness sont proches (de 0 à 25 ici). Un tournoi ou une sélection par rang donnerait une pression plus forte.
- Le modèle ignore les pannes, les délais d'équipements et les coûts.
