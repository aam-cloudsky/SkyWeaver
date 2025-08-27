# optimize_airspace_scipy.py

import numpy as np
from scipy.optimize import differential_evolution
from skyweaver.airspace_environment import AirspaceEnv
from skyweaver.paths import prepare_data_path, change_to_project_root

# =================
# Setup do ambiente
# =================
change_to_project_root()
grid_path = prepare_data_path("municipios_rj", "rio_niteroi.geojson")
heliport_path = prepare_data_path("geojson", "heliport.geojson")

env = AirspaceEnv(
    city_geojson_path=str(grid_path),
    restrictions_geojson_path=str(heliport_path),
    cell_size=50,
    GUI=True
)

obs, _ = env.reset()
n_vars = len(obs)  # número de variáveis = nº de restrições

# =================
# Função objetivo
# =================


def objective(x):
    """
    Converte vetor numpy -> dict esperado pelo env.step()
    Retorna negativo do reward, pois o scipy.optimize minimiza.
    """
    action = {rid: float(val) for rid, val in zip(obs.keys(), x)}
    _, reward, _, _, _ = env.step(action)
    if env.current_step % 100 == 0:
        #pass
        env.export_grid_to_geopackage(path="air_space_optimization_output")
        #TODO: Polygons in QGIS are broken
    return -reward  # invertendo para maximizar reward


# =================
# Otimização com Differential Evolution
# =================
bounds = [(-1.0, 1.0)] * n_vars

result = differential_evolution(
    objective,
    bounds,
    strategy='best1bin',
    maxiter=1000,       # número máximo de gerações
    popsize=15,        # tamanho da população
    tol=1e-6,
    mutation=(0.5, 1),
    recombination=0.7,
    polish=True,       # refinamento final
    disp=True
)

best_solution = result.x
best_reward = -result.fun  # invertendo para o valor real do reward

print("\nBest solution found:", best_solution)
print(f"Occupation optimized in: {best_reward *100:.1f}%")
