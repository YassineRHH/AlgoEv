"""
EXERCICE 2 - Livraison de containers (problème de transport) par RECHERCHE TABOU
=================================================================================

LE PROBLÈME
-----------
Deux dépôts (D1, D2) ont des containers en stock. Trois magasins (M1, M2, M3) en commandent.
On connaît le coût de transport d'UN container de chaque dépôt vers chaque magasin :

                 M1   M2   M3  |  Stock du dépôt
        D1        5    3    4  |        8
        D2        6    7    2  |        9
        Demande   4    5    8  |   (17 = 17)

BUT : décider combien de containers envoyer de chaque dépôt vers chaque magasin
      pour que le coût total de transport soit le plus petit possible.

LE MODÈLE (programmation linéaire en nombres entiers)
-----------------------------------------------------
    livraisons[d][m] = nombre de containers envoyés du dépôt d vers le magasin m (entier >= 0)

    minimiser   somme sur (d, m) de   couts_transport[d][m] * livraisons[d][m]
    sous contraintes
        somme sur m de livraisons[d][m] = stocks_depots[d]        (chaque dépôt vide tout son stock)
        somme sur d de livraisons[d][m] = demandes_magasins[m]    (chaque magasin reçoit sa demande)

COMMENT LA RECHERCHE TABOU RÉSOUT CE PROBLÈME
---------------------------------------------
1. On part d'une solution réalisable quelconque (règle du coin nord-ouest).
2. A chaque itération, on regarde tous les "voisins" de la solution courante
   (solutions obtenues en déplaçant UN container) et on va vers le meilleur voisin,
   même s'il coûte plus cher que la solution actuelle (c'est ce qui permet de sortir
   d'un optimum local).
3. Pour ne pas tourner en rond, on interdit pendant quelques itérations le mouvement
   qui annulerait celui qu'on vient de faire (liste tabou).
4. Exception (critère d'aspiration) : un mouvement tabou est quand même autorisé
   s'il donne une solution meilleure que la meilleure trouvée jusque-là.
"""

from collections import deque          # file à longueur limitée : parfaite pour la liste tabou
from itertools import combinations     # pour parcourir les paires de magasins

# ----------------------------------------------------------------------------
# 1) LES DONNÉES DU PROBLÈME
# ----------------------------------------------------------------------------
COUTS_TRANSPORT = [[5, 3, 4],          # coût d'un container : D1 -> M1, M2, M3
                   [6, 7, 2]]          #                       D2 -> M1, M2, M3
STOCKS_DEPOTS = [8, 9]                 # containers disponibles dans D1 et D2
DEMANDES_MAGASINS = [4, 5, 8]          # containers commandés par M1, M2, M3

NB_DEPOTS = len(STOCKS_DEPOTS)
NB_MAGASINS = len(DEMANDES_MAGASINS)


# ----------------------------------------------------------------------------
# 2) OUTILS : COÛT ET VALIDITÉ D'UNE SOLUTION
# ----------------------------------------------------------------------------
def calculer_cout(livraisons):
    """Coût total d'une solution = somme de (coût unitaire x nombre de containers)."""
    cout = 0
    for depot in range(NB_DEPOTS):
        for magasin in range(NB_MAGASINS):
            cout += COUTS_TRANSPORT[depot][magasin] * livraisons[depot][magasin]
    return cout


def est_realisable(livraisons):
    """Vérifie les contraintes du modèle : pas de quantité négative, stocks vidés, demandes servies."""
    if any(q < 0 for ligne in livraisons for q in ligne):
        return False
    for depot in range(NB_DEPOTS):
        if sum(livraisons[depot]) != STOCKS_DEPOTS[depot]:
            return False
    for magasin in range(NB_MAGASINS):
        total_recu = sum(livraisons[depot][magasin] for depot in range(NB_DEPOTS))
        if total_recu != DEMANDES_MAGASINS[magasin]:
            return False
    return True


# ----------------------------------------------------------------------------
# 3) SOLUTION INITIALE : RÈGLE DU COIN NORD-OUEST
# ----------------------------------------------------------------------------
def construire_solution_initiale():
    """On remplit la case en haut à gauche au maximum, puis on avance vers la droite (magasin
    suivant) ou vers le bas (dépôt suivant). Résultat : une solution réalisable, pas forcément bonne."""
    stock_restant = STOCKS_DEPOTS[:]            # copies : on ne modifie pas les données d'origine
    demande_restante = DEMANDES_MAGASINS[:]
    livraisons = [[0] * NB_MAGASINS for _ in range(NB_DEPOTS)]

    depot, magasin = 0, 0
    while depot < NB_DEPOTS and magasin < NB_MAGASINS:
        quantite = min(stock_restant[depot], demande_restante[magasin])
        livraisons[depot][magasin] = quantite
        stock_restant[depot] -= quantite
        demande_restante[magasin] -= quantite
        if stock_restant[depot] == 0:
            depot += 1          # ce dépôt est vide : on passe au dépôt suivant
        else:
            magasin += 1        # ce magasin est servi : on passe au magasin suivant
    return livraisons


# ----------------------------------------------------------------------------
# 4) LE VOISINAGE : DÉPLACER UN CONTAINER
# ----------------------------------------------------------------------------
# Un MOUVEMENT est un tuple (depot_x, depot_y, magasin_1, magasin_2) avec magasin_1 < magasin_2 :
#     - depot_x envoie 1 container de MOINS à magasin_1 et 1 de PLUS à magasin_2
#     - depot_y fait l'inverse : 1 container de PLUS à magasin_1 et 1 de MOINS à magasin_2
# Les totaux par ligne (stocks) et par colonne (demandes) ne changent pas :
# le voisin est donc TOUJOURS réalisable, sans avoir besoin de le vérifier.
#
# On impose magasin_1 < magasin_2 pour qu'un même changement ne s'écrive qu'UNE seule fois.
# Sans cela, la liste tabou ne reconnaîtrait pas un mouvement écrit autrement et l'algorithme
# tournerait en boucle.

def variation_de_cout(mouvement):
    """Calcule de combien le coût change si on applique le mouvement, SANS construire le voisin.
    Optimisation : 4 additions au lieu de recopier la matrice et de recalculer tout le coût."""
    depot_x, depot_y, magasin_1, magasin_2 = mouvement
    return (COUTS_TRANSPORT[depot_x][magasin_2] - COUTS_TRANSPORT[depot_x][magasin_1]
            + COUTS_TRANSPORT[depot_y][magasin_1] - COUTS_TRANSPORT[depot_y][magasin_2])


def lister_mouvements_possibles(livraisons):
    """Tous les mouvements applicables à la solution courante.
    Condition : on ne peut retirer un container que d'une case qui en contient (pas de quantité négative)."""
    mouvements = []
    for magasin_1, magasin_2 in combinations(range(NB_MAGASINS), 2):   # magasin_1 < magasin_2
        for depot_x in range(NB_DEPOTS):
            for depot_y in range(NB_DEPOTS):
                if depot_x == depot_y:
                    continue
                peut_retirer_x = livraisons[depot_x][magasin_1] > 0
                peut_retirer_y = livraisons[depot_y][magasin_2] > 0
                if peut_retirer_x and peut_retirer_y:
                    mouvements.append((depot_x, depot_y, magasin_1, magasin_2))
    return mouvements


def appliquer_mouvement(livraisons, mouvement):
    """Construit le voisin : copie de la solution + déplacement d'un container."""
    depot_x, depot_y, magasin_1, magasin_2 = mouvement
    voisin = [ligne[:] for ligne in livraisons]       # copie profonde (liste de listes)
    voisin[depot_x][magasin_1] -= 1
    voisin[depot_x][magasin_2] += 1
    voisin[depot_y][magasin_1] += 1
    voisin[depot_y][magasin_2] -= 1
    return voisin


def mouvement_inverse(mouvement):
    """Le mouvement qui ANNULE le précédent : les deux dépôts échangent leurs rôles."""
    depot_x, depot_y, magasin_1, magasin_2 = mouvement
    return (depot_y, depot_x, magasin_1, magasin_2)


def decrire_mouvement(mouvement):
    """Phrase lisible pour l'affichage (utile pour expliquer chaque itération dans le rendu)."""
    depot_x, depot_y, magasin_1, magasin_2 = mouvement
    return (f"D{depot_x + 1} : -1 vers M{magasin_1 + 1}, +1 vers M{magasin_2 + 1} ; "
            f"D{depot_y + 1} : +1 vers M{magasin_1 + 1}, -1 vers M{magasin_2 + 1}")


# ----------------------------------------------------------------------------
# 5) LA RECHERCHE TABOU
# ----------------------------------------------------------------------------
def recherche_tabou(duree_tabou=3, nb_iterations=12, afficher=True):
    """
    duree_tabou   : nombre de mouvements interdits gardés en mémoire (taille de la liste tabou).
                    Trop petit : on risque de tourner en rond. Trop grand : on s'interdit trop de choses.
    nb_iterations : critère d'arrêt.
    """
    solution_courante = construire_solution_initiale()
    cout_courant = calculer_cout(solution_courante)

    meilleure_solution = [ligne[:] for ligne in solution_courante]    # le "record" à conserver
    meilleur_cout = cout_courant

    # deque(maxlen=n) : quand elle est pleine, ajouter un élément supprime automatiquement
    # le plus ancien. C'est exactement le fonctionnement d'une liste tabou.
    liste_tabou = deque(maxlen=duree_tabou)

    if afficher:
        print(f"Solution initiale (coin nord-ouest) : {solution_courante}  coût = {cout_courant}\n")

    for iteration in range(1, nb_iterations + 1):

        # --- a) Choisir le meilleur mouvement autorisé ---------------------------------------
        meilleur_mouvement = None
        meilleure_variation = float("inf")

        for mouvement in lister_mouvements_possibles(solution_courante):
            variation = variation_de_cout(mouvement)
            cout_du_voisin = cout_courant + variation

            est_interdit = mouvement in liste_tabou
            bat_le_record = cout_du_voisin < meilleur_cout        # critère d'aspiration

            # Un mouvement est autorisé s'il n'est pas tabou, OU s'il bat le record.
            if (not est_interdit or bat_le_record) and variation < meilleure_variation:
                meilleur_mouvement = mouvement
                meilleure_variation = variation

        if meilleur_mouvement is None:      # tous les mouvements sont interdits : on arrête
            break

        # --- b) Se déplacer (même si le coût augmente) ---------------------------------------
        solution_courante = appliquer_mouvement(solution_courante, meilleur_mouvement)
        cout_courant += meilleure_variation

        # --- c) Mettre à jour la mémoire : interdire de défaire ce qu'on vient de faire ------
        liste_tabou.append(mouvement_inverse(meilleur_mouvement))

        # --- d) Mettre à jour le record --------------------------------------------------------
        if cout_courant < meilleur_cout:
            meilleure_solution = [ligne[:] for ligne in solution_courante]
            meilleur_cout = cout_courant

        if afficher:
            print(f"Itération {iteration:2d}")
            print(f"   mouvement choisi : {decrire_mouvement(meilleur_mouvement)}")
            print(f"   solution         : {solution_courante}")
            print(f"   coût courant     : {cout_courant}   (variation {meilleure_variation:+d})   "
                  f"meilleur coût : {meilleur_cout}")
            print(f"   liste tabou      : {list(liste_tabou)}\n")

    return meilleure_solution, meilleur_cout


# ----------------------------------------------------------------------------
# 6) VÉRIFICATION : ENUMÉRATION DE TOUTES LES SOLUTIONS (possible car le problème est petit)
# ----------------------------------------------------------------------------
def verifier_par_enumeration():
    """Teste toutes les façons de remplir la ligne de D1 ; la ligne de D2 s'en déduit
    (demande du magasin - ce que D1 lui envoie). On garde la moins chère.
    Sert uniquement à CONTRÔLER le résultat de la recherche tabou."""
    meilleur = (float("inf"), None)
    for vers_m1 in range(DEMANDES_MAGASINS[0] + 1):
        for vers_m2 in range(DEMANDES_MAGASINS[1] + 1):
            vers_m3 = STOCKS_DEPOTS[0] - vers_m1 - vers_m2        # D1 doit vider son stock
            ligne_d1 = [vers_m1, vers_m2, vers_m3]
            ligne_d2 = [DEMANDES_MAGASINS[m] - ligne_d1[m] for m in range(NB_MAGASINS)]
            livraisons = [ligne_d1, ligne_d2]
            if est_realisable(livraisons):
                cout = calculer_cout(livraisons)
                if cout < meilleur[0]:
                    meilleur = (cout, livraisons)
    return meilleur


# ----------------------------------------------------------------------------
# 7) PROGRAMME PRINCIPAL
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    solution, cout = recherche_tabou()

    print("=" * 60)
    print("RÉSULTAT DE LA RECHERCHE TABOU")
    for depot in range(NB_DEPOTS):
        details = "  ".join(f"M{m + 1}:{solution[depot][m]}" for m in range(NB_MAGASINS))
        print(f"  D{depot + 1} -> {details}")
    print(f"Coût total minimal trouvé : {cout}")
    print(f"Solution réalisable       : {est_realisable(solution)}")

    cout_optimal, solution_optimale = verifier_par_enumeration()
    print(f"Vérification par énumération complète : coût optimal = {cout_optimal}  {solution_optimale}")
    print("La recherche tabou a trouvé l'optimum." if cout == cout_optimal
          else "La recherche tabou n'a pas trouvé l'optimum.")
