# optimize_airspace.py

import numpy as np
from pyswarm import pso
from skyweaver.airspace_environment import AirspaceEnv
from skyweaver.paths import prepare_data_path, change_to_project_root

# -----------------------------
# Setup do ambiente
# -----------------------------
change_to_project_root()

grid_path = prepare_data_path("municipios_rj", "rio_niteroi.geojson")
heliport_path = prepare_data_path("geojson", "heliport.geojson")

env = AirspaceEnv(
    city_geojson_path=str(grid_path),
    restrictions_geojson_path=str(heliport_path),
    cell_size=50
)

obs, _ = env.reset()
restriction_ids = list(obs.keys())
n_restrictions = len(restriction_ids)

# -----------------------------
# Função objetivo
# -----------------------------


def fitness(x):
    """
    Cost function to PSO.
    """
    # Monta dict {restriction_id: rotation_norm}
    actions = {rid: val for rid, val in zip(restriction_ids, x)}

    # Aplica ação e calcula reward
    obs, reward, done, _, _ = env.step(actions)

    # Reward = [0,1], max better. But pyswarm minimizes it.
    return 1-reward


# -----------------------------
# Rodando o PSO
# -----------------------------
lb = [-1.0] * n_restrictions  # limites inferiores
ub = [1.0] * n_restrictions   # limites superiores

best_x, best_cost = pso(
    fitness,
    lb,
    ub,
    swarmsize=30,
    maxiter=50,
    debug=True
)

#print("\nMelhor solução encontrada:")
#for rid, val in zip(restriction_ids, best_x):
    #print(f"  Restrição {rid}: rotação normalizada {val:.4f}")

print(f"Melhor reward: {-best_cost:.4f} (space saved %)")

# Plot final
env.plot_graph()
