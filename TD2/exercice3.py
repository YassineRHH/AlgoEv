"""
EXERCICE 3 - Voyageur de commerce (TSP) à 8 villes
Résolution par : 1) recherche tabou   2) recuit simulé   3) algorithme génétique
==================================================================================

LE PROBLÈME
-----------
Un représentant doit visiter les 8 villes UNE FOIS chacune et revenir à son point de départ,
en parcourant la plus petite distance totale possible.
Certaines routes n'existent pas (les "-" du tableau de l'énoncé).

COMMENT ON REPRÉSENTE LES DONNÉES
---------------------------------
- Une TOURNÉE est une liste de villes, par exemple (0, 1, 2, 3, 4, 5, 6, 7).
  Les villes sont numérotées de 0 à 7 dans le programme (ville 1 de l'énoncé = indice 0).
  A l'affichage on remet les numéros de l'énoncé (1 à 8) avec afficher_tournee().
- La tournée est FERMÉE : après la dernière ville on retourne à la première.
- La ville 1 reste toujours en première position : cela évite de compter 8 fois la même tournée
  (décalée) et réduit le nombre de tournées à 7! = 5040.
- Route inexistante : on lui donne une distance énorme (PENALITE_ROUTE_ABSENTE). Une tournée qui
  l'utilise devient très longue et sera donc rejetée naturellement par les algorithmes.

LE VOISINAGE UTILISÉ (tabou et recuit) : 2-OPT
----------------------------------------------
On choisit deux positions debut < fin dans la tournée et on INVERSE le segment entre elles.
Exemple : (1, 8, 7, 6, 5, 4, 2, 3) avec debut=1, fin=6  ->  (1, 2, 4, 5, 6, 7, 8, 3)
La ville 1 (position 0) ne bouge pas : il y a C(7,2) = 21 voisins pour chaque tournée.
"""

import itertools
import math
import random
from collections import deque
from functools import lru_cache

# ----------------------------------------------------------------------------
# 1) LES DONNÉES DU PROBLÈME
# ----------------------------------------------------------------------------
NB_VILLES = 8
PENALITE_ROUTE_ABSENTE = 1000      # distance donnée aux routes qui n'existent pas

# Routes qui existent : (ville_a, ville_b, distance), villes numérotées de 1 à 8 comme dans l'énoncé
ROUTES_EXISTANTES = [
    (1, 2, 14), (1, 3, 15), (1, 8, 17),
    (2, 3, 13), (2, 4, 14), (2, 5, 20), (2, 8, 21),
    (3, 4, 11), (3, 5, 21), (3, 6, 17), (3, 7, 9), (3, 8, 9),
    (4, 5, 11), (4, 6, 10), (4, 7, 8), (4, 8, 20),
    (5, 6, 15), (5, 7, 18),
    (6, 7, 9),
    (7, 8, 13),
]


def construire_matrice_distances():
    """Matrice symétrique : distances[a][b] = distance entre les villes a et b (indices 0 à 7)."""
    distances = [[PENALITE_ROUTE_ABSENTE] * NB_VILLES for _ in range(NB_VILLES)]
    for ville in range(NB_VILLES):
        distances[ville][ville] = 0                       # distance d'une ville à elle-même
    for ville_a, ville_b, distance in ROUTES_EXISTANTES:
        distances[ville_a - 1][ville_b - 1] = distance    # -1 : numéro de l'énoncé -> indice
        distances[ville_b - 1][ville_a - 1] = distance    # la route marche dans les deux sens
    return distances


DISTANCES = construire_matrice_distances()


# ----------------------------------------------------------------------------
# 2) OUTILS : LONGUEUR ET AFFICHAGE D'UNE TOURNÉE
# ----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def longueur_tournee(tournee):
    """Longueur totale de la tournée fermée (somme des distances entre villes consécutives).
    `tournee` est un TUPLE : c'est ce qui permet à lru_cache de mémoriser le résultat.
    Optimisation : une tournée déjà évaluée n'est jamais recalculée (utile pour l'algorithme génétique,
    où les mêmes tournées sont évaluées plusieurs fois)."""
    total = 0
    for position in range(NB_VILLES):
        ville_actuelle = tournee[position]
        ville_suivante = tournee[(position + 1) % NB_VILLES]   # % : après la dernière on revient à la première
        total += DISTANCES[ville_actuelle][ville_suivante]
    return total


def afficher_tournee(tournee):
    """Ex : (0,1,2,...,7) -> '1-2-3-4-5-6-7-8-1' (numéros de l'énoncé, retour à la ville de départ)."""
    return "-".join(str(ville + 1) for ville in tournee) + f"-{tournee[0] + 1}"


def trouver_optimum_exact():
    """CONTRÔLE : teste les 7! = 5040 tournées (la ville 1 est fixée au départ) et garde la plus courte.
    Possible seulement parce que le problème est petit. Sert à vérifier les résultats des 3 méthodes."""
    meilleure = None
    for ordre in itertools.permutations(range(1, NB_VILLES)):
        tournee = (0,) + ordre
        longueur = longueur_tournee(tournee)
        if meilleure is None or longueur < meilleure[0]:
            meilleure = (longueur, tournee)
    return meilleure


# ----------------------------------------------------------------------------
# 3) LE VOISINAGE 2-OPT
# ----------------------------------------------------------------------------
def appliquer_2opt(tournee, debut, fin):
    """Inverse le segment tournee[debut..fin] (positions comprises). Les autres villes ne bougent pas."""
    segment_inverse = tournee[debut:fin + 1][::-1]
    return tournee[:debut] + segment_inverse + tournee[fin + 1:]


def variation_longueur_2opt(tournee, debut, fin):
    """Variation de longueur provoquée par l'inversion, SANS recalculer toute la tournée.
    Inverser un segment ne change que 2 routes : les deux routes qui "entrent" et "sortent" du segment.
    (Les routes à l'intérieur du segment gardent la même longueur, juste parcourues à l'envers.)
        avant :  ville_avant -> tournee[debut] ...... tournee[fin] -> ville_apres
        après :  ville_avant -> tournee[fin]   ...... tournee[debut] -> ville_apres
    Optimisation : 4 lectures de distance au lieu de 8 (et pas de nouvelle tournée construite)."""
    ville_avant = tournee[debut - 1]
    ville_apres = tournee[(fin + 1) % NB_VILLES]      # si fin = dernière position, on retombe sur la ville 1
    premiere = tournee[debut]
    derniere = tournee[fin]
    ancien = DISTANCES[ville_avant][premiere] + DISTANCES[derniere][ville_apres]
    nouveau = DISTANCES[ville_avant][derniere] + DISTANCES[premiere][ville_apres]
    return nouveau - ancien


def tous_les_mouvements_2opt():
    """Les 21 mouvements possibles : toutes les paires de positions (debut, fin), debut < fin.
    On commence à 1 car la position 0 (ville 1) ne doit jamais bouger."""
    return list(itertools.combinations(range(1, NB_VILLES), 2))


# ----------------------------------------------------------------------------
# 4) MÉTHODE 1 : RECHERCHE TABOU
# ----------------------------------------------------------------------------
def recherche_tabou(nb_iterations=10, duree_tabou=3):
    """
    Principe : à chaque itération on va vers le MEILLEUR voisin autorisé, même s'il est moins bon
    que la tournée actuelle. Les derniers mouvements sont mémorisés (liste tabou) et interdits.

    nb_iterations : critère d'arrêt.
    duree_tabou   : nombre de mouvements gardés en mémoire (taille de la liste tabou).
    """
    tournee_courante = tuple(range(NB_VILLES))               # départ imposé : 1-2-3-4-5-6-7-8-1
    longueur_courante = longueur_tournee(tournee_courante)

    meilleure_tournee = tournee_courante                     # le "record" à conserver
    meilleure_longueur = longueur_courante

    # deque(maxlen=n) : quand elle est pleine, ajouter supprime automatiquement le plus ancien.
    liste_tabou = deque(maxlen=duree_tabou)

    print(f"Solution initiale : {afficher_tournee(tournee_courante)}  longueur = {meilleure_longueur}")

    for iteration in range(1, nb_iterations + 1):

        # --- a) Choisir le meilleur mouvement autorisé ---------------------------------------
        mouvement_choisi = None
        variation_choisie = None
        for mouvement in tous_les_mouvements_2opt():
            debut, fin = mouvement
            variation = variation_longueur_2opt(tournee_courante, debut, fin)
            longueur_du_voisin = longueur_courante + variation

            est_interdit = mouvement in liste_tabou
            bat_le_record = longueur_du_voisin < meilleure_longueur      # critère d'aspiration

            # Interdit ET ne bat pas le record -> on l'ignore.
            if est_interdit and not bat_le_record:
                continue
            if variation_choisie is None or variation < variation_choisie:
                mouvement_choisi, variation_choisie = mouvement, variation

        # --- b) Se déplacer (même si la tournée s'allonge) ----------------------------------
        tournee_courante = appliquer_2opt(tournee_courante, *mouvement_choisi)
        longueur_courante += variation_choisie

        # --- c) Mémoriser le mouvement : on s'interdit de le refaire pendant `duree_tabou` itérations
        liste_tabou.append(mouvement_choisi)

        # --- d) Mettre à jour le record -------------------------------------------------------
        if longueur_courante < meilleure_longueur:
            meilleure_tournee, meilleure_longueur = tournee_courante, longueur_courante

        print(f"it {iteration:2d} | inversion positions {mouvement_choisi} -> {afficher_tournee(tournee_courante)}"
              f" | L = {longueur_courante:3d} | meilleur = {meilleure_longueur} | tabou = {list(liste_tabou)}")

    return meilleure_tournee, meilleure_longueur


# ----------------------------------------------------------------------------
# 5) MÉTHODE 2 : RECUIT SIMULÉ
# ----------------------------------------------------------------------------
def recuit_simule(temperature_initiale=10.0, facteur_refroidissement=0.8,
                  nb_iterations=5, graine_aleatoire=31):
    """
    Principe : à chaque itération on tire UN voisin au hasard.
      - S'il est meilleur (ou égal) : on l'accepte.
      - S'il est pire de `delta` : on l'accepte quand même avec la probabilité exp(-delta / T)
        (règle de Metropolis). T grand = on accepte presque tout ; T petit = presque rien.
      - T diminue à chaque itération : T <- facteur_refroidissement x T  (variation "empirique").

    graine_aleatoire = 31 : choisie pour que les 5 itérations montrent tous les cas
    (rejet, dégradation acceptée, amélioration). Avec une autre graine, les tirages changent.
    """
    hasard = random.Random(graine_aleatoire)

    tournee_courante = tuple(range(NB_VILLES))
    longueur_courante = longueur_tournee(tournee_courante)
    meilleure_tournee, meilleure_longueur = tournee_courante, longueur_courante
    temperature = temperature_initiale

    print(f"Solution initiale : {afficher_tournee(tournee_courante)}  L = {longueur_courante}, "
          f"T0 = {temperature_initiale}, T <- {facteur_refroidissement} x T")

    for iteration in range(1, nb_iterations + 1):

        # --- a) Tirer un voisin au hasard (une inversion 2-opt) -------------------------------
        debut, fin = sorted(hasard.sample(range(1, NB_VILLES), 2))
        voisin = appliquer_2opt(tournee_courante, debut, fin)
        longueur_voisin = longueur_courante + variation_longueur_2opt(tournee_courante, debut, fin)
        delta = longueur_voisin - longueur_courante      # delta > 0 : le voisin est PLUS LONG (pire)

        # --- b) Règle d'acceptation de Metropolis ----------------------------------------------
        if delta <= 0:
            accepte = True
            explication = "amélioration -> accepté"
        else:
            probabilite = math.exp(-delta / temperature)
            tirage = hasard.random()                     # nombre aléatoire entre 0 et 1
            accepte = tirage < probabilite               # accepté si le tirage tombe sous la probabilité
            explication = (f"p = exp(-{delta}/{temperature:.2f}) = {probabilite:.3f}, tirage = {tirage:.3f} -> "
                           + ("accepté" if accepte else "rejeté"))

        print(f"it {iteration} | T = {temperature:5.2f} | voisin {afficher_tournee(voisin)} "
              f"L = {longueur_voisin} | delta = {delta:+d} | {explication}")

        # --- c) Se déplacer si accepté, et mettre à jour le record ----------------------------
        if accepte:
            tournee_courante, longueur_courante = voisin, longueur_voisin
            if longueur_courante < meilleure_longueur:
                meilleure_tournee, meilleure_longueur = tournee_courante, longueur_courante

        # --- d) Refroidir ------------------------------------------------------------------------
        temperature *= facteur_refroidissement

    return meilleure_tournee, meilleure_longueur


# ----------------------------------------------------------------------------
# 6) MÉTHODE 3 : ALGORITHME GÉNÉTIQUE
# ----------------------------------------------------------------------------
# Vocabulaire :  individu = une tournée ;  population = un groupe de tournées ;
#                "fitness" = qualité d'un individu (ici : plus la tournée est COURTE, meilleur il est).

def croisement_ox(parent_1, parent_2, hasard):
    """Order Crossover (OX) : fabrique un enfant qui est TOUJOURS une tournée valide
    (chaque ville exactement une fois). Un croisement classique "coupe et recolle" répéterait des villes.
       1) on copie dans l'enfant un segment de parent_1 (positions debut..fin)
       2) on complète les cases vides avec les villes manquantes, dans l'ordre où elles apparaissent dans parent_2
    La ville 1 reste en position 0."""
    debut, fin = sorted(hasard.sample(range(1, NB_VILLES), 2))
    enfant = [None] * NB_VILLES
    enfant[0] = 0                                            # la ville 1 reste en tête
    enfant[debut:fin + 1] = parent_1[debut:fin + 1]          # étape 1 : segment hérité de parent_1
    villes_manquantes = [ville for ville in parent_2 if ville not in enfant]   # dans l'ordre de parent_2
    for position in range(NB_VILLES):                        # étape 2 : on remplit les trous
        if enfant[position] is None:
            enfant[position] = villes_manquantes.pop(0)
    return tuple(enfant)


def mutation_echange(tournee, hasard, probabilite_mutation=0.2):
    """Avec la probabilité `probabilite_mutation`, échange deux villes au hasard (hors ville 1).
    Rôle : ajouter un peu de nouveauté dans la population pour ne pas stagner."""
    if hasard.random() < probabilite_mutation:
        liste = list(tournee)
        position_a, position_b = hasard.sample(range(1, NB_VILLES), 2)
        liste[position_a], liste[position_b] = liste[position_b], liste[position_a]
        return tuple(liste)
    return tournee


def selection_par_tournoi(population, hasard, taille_tournoi=3):
    """Choisit un parent : on tire `taille_tournoi` individus au hasard et on garde le plus court.
    Les bons individus ont plus de chances d'être parents, mais les mauvais en ont encore un peu."""
    candidats = hasard.sample(population, taille_tournoi)
    return min(candidats, key=longueur_tournee)


def algorithme_genetique(taille_population=10, nb_generations=30, graine_aleatoire=1, afficher=True):
    hasard = random.Random(graine_aleatoire)

    # --- Population initiale : tournées aléatoires (ville 1 en tête) --------------------------
    population = []
    for _ in range(taille_population):
        autres_villes = list(range(1, NB_VILLES))
        hasard.shuffle(autres_villes)
        population.append((0,) + tuple(autres_villes))

    meilleure_tournee = min(population, key=longueur_tournee)
    if afficher:
        print("Population initiale :")
        for tournee in population:
            print("  ", afficher_tournee(tournee), "L =", longueur_tournee(tournee))

    for generation in range(1, nb_generations + 1):
        # Élitisme : le meilleur individu passe tel quel à la génération suivante (on ne perd jamais le record)
        nouvelle_population = [min(population, key=longueur_tournee)]

        # On complète avec des enfants : sélection de 2 parents -> croisement -> mutation
        while len(nouvelle_population) < taille_population:
            parent_1 = selection_par_tournoi(population, hasard)
            parent_2 = selection_par_tournoi(population, hasard)
            enfant = croisement_ox(parent_1, parent_2, hasard)
            nouvelle_population.append(mutation_echange(enfant, hasard))
        population = nouvelle_population

        meilleur_de_la_generation = min(population, key=longueur_tournee)
        if longueur_tournee(meilleur_de_la_generation) < longueur_tournee(meilleure_tournee):
            meilleure_tournee = meilleur_de_la_generation

        if afficher and (generation <= 5 or generation % 5 == 0):
            moyenne = sum(longueur_tournee(t) for t in population) / taille_population
            print(f"génération {generation:2d} | meilleur = {afficher_tournee(meilleur_de_la_generation)} "
                  f"L = {longueur_tournee(meilleur_de_la_generation)} | moyenne = {moyenne:.1f}")

    return meilleure_tournee, longueur_tournee(meilleure_tournee)


# ----------------------------------------------------------------------------
# 7) PROGRAMME PRINCIPAL
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Distances (1000 = route inexistante) ===")
    for ligne in DISTANCES:
        print(ligne)

    longueur_optimale, tournee_optimale = trouver_optimum_exact()
    print(f"\nOptimum exact (énumération des 5040 tournées) : {longueur_optimale}  "
          f"{afficher_tournee(tournee_optimale)}")

    print("\n=== 1) Recherche tabou ===")
    tournee, longueur = recherche_tabou()
    print(f"-> meilleure tournée : {afficher_tournee(tournee)}  longueur = {longueur}")

    print("\n=== 2) Recuit simulé ===")
    tournee, longueur = recuit_simule()
    print(f"-> meilleure tournée : {afficher_tournee(tournee)}  longueur = {longueur}")

    print("\n=== 3) Algorithme génétique ===")
    tournee, longueur = algorithme_genetique()
    print(f"-> meilleure tournée : {afficher_tournee(tournee)}  longueur = {longueur}")
