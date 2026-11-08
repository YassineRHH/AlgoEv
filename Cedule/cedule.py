"""
Cédule de maintenance de centrales par algorithme génétique (version simplifiée).

Codage     : 7 gènes de 4 bits (un par unité), "1" = unité en maintenance pendant l'intervalle.
Fitness    : plus petite réserve de puissance sur les 4 intervalles (0 si négative).
Sélection  : loterie (roulette).
Croisement : en un point, entre deux gènes.
Mutation   : inversion d'une partie des gènes, suivie d'une réparation.
"""
import random

CAPACITES = [20, 15, 35, 40, 15, 15, 10]    # MW
DUREES = [2, 2, 1, 1, 1, 1, 1]              # intervalles de maintenance requis
DEMANDES = [80, 90, 65, 70]                 # MW par intervalle

# Gènes valides selon la durée de maintenance de l'unité
GENES = {1: ["1000", "0100", "0010", "0001"],
         2: ["1100", "0110", "0011"]}


def fitness(chromosome):
    """Plus petite réserve : capacité totale - puissance en maintenance - demande."""
    reserves = []
    for t in range(4):
        perdue = sum(c for c, gene in zip(CAPACITES, chromosome) if gene[t] == "1")
        reserves.append(sum(CAPACITES) - perdue - DEMANDES[t])
    return max(0, min(reserves))


def individu_aleatoire():
    return [random.choice(GENES[d]) for d in DUREES]


def selection_roulette(population, fits):
    """Loterie : la probabilité d'un individu est proportionnelle à sa fitness."""
    total = sum(fits)
    if total == 0:
        return random.choice(population)
    rho = random.uniform(0, total)
    cumul = 0
    for individu, f in zip(population, fits):
        cumul += f
        if rho <= cumul:
            return individu
    return population[-1]


def croisement(p1, p2):
    point = random.randint(1, 6)                 # coupure entre deux gènes
    return p1[:point] + p2[point:], p2[:point] + p1[point:]


def mutation_inversion(chromosome):
    """Inverse l'ordre des gènes entre deux positions, puis répare chaque gène."""
    i, j = sorted(random.sample(range(7), 2))
    gene_inverses = chromosome[:i] + chromosome[i:j + 1][::-1] + chromosome[j + 1:]
    resultat = []
    for u, gene in enumerate(gene_inverses):
        valides = GENES[DUREES[u]]
        # on garde l'intervalle de début, on impose la durée de l'unité
        resultat.append(valides[min(gene.index("1"), len(valides) - 1)])
    return resultat


def algorithme_genetique(taille=49, generations=100, pc=0.8, pm=0.2):
    population = [individu_aleatoire() for _ in range(taille)]
    for _ in range(generations):
        fits = [fitness(c) for c in population]
        nouvelle = [max(population, key=fitness)]          # élitisme : on garde le meilleur
        while len(nouvelle) < taille:
            p1 = selection_roulette(population, fits)
            p2 = selection_roulette(population, fits)
            e1, e2 = croisement(p1, p2) if random.random() < pc else (p1, p2)
            for enfant in (e1, e2):
                if random.random() < pm:
                    enfant = mutation_inversion(enfant)
                nouvelle.append(enfant)
        population = nouvelle[:taille]
    return max(population, key=fitness)


if __name__ == "__main__":
    random.seed(42)
    meilleur = algorithme_genetique()
    print("Meilleure cédule :", " ".join(meilleur))
    for u, gene in enumerate(meilleur):
        intervalles = [t + 1 for t in range(4) if gene[t] == "1"]
        print(f"  unité {u + 1} ({CAPACITES[u]} MW) : maintenance aux intervalles {intervalles}")
    print("Fitness (plus petite réserve) :", fitness(meilleur), "MW")