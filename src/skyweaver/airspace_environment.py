# src/skyweaver/envs/airspace_env.py

from __future__ import annotations
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, List, Optional, Tuple

from shapely.geometry import Point

from skyweaver.managers.geo_json_manager import GeoJSONManager
from skyweaver.managers.airspace_grid_manager import AirspaceGrid




from skyweaver.enums.shapes import RestrictionShape
from skyweaver.enums.restriction_source import RestrictionSource
from skyweaver.enums.grid_channels import GridChannels
from skyweaver.paths import prepare_data_path, change_to_project_root



class AirspaceEnv(gym.Env):
    """
    Gymnasium/Farama environment that orchestrates:
      - Loading GeoJSONs (city/base map and restriction POIs)
      - Building the AirspaceGrid
      - Managing intrinsic rotations of restrictions
      - Stepping a cycle: reset restriction layer -> apply rotations -> stamp -> compute metrics

    Observation space:
      - 1D Box in [0, 1], where each entry is the *intrinsic rotation* of a restriction,
        normalized from radians ([-pi, +pi] or [0, 2pi], configurable) to [0, 1].

    Action space:
      - 1D Box in [-1, 1], same length as observation.
      - Interpreted as *delta* of normalized rotation to be applied this step, scaled by `max_delta_rad`.

    Notes:
      - This environment focuses on *intrinsic rotation* of the stamp (the geometry spins around its own center).
      - No "orbital" movement (translating centers) is performed here.
      - Reward is a simple placeholder based on restricted cells (negative occupancy).
    """

    # ---------------------------
    # ---- Initialization ----
    # ---------------------------
    def __init__(
        self,
        city_geojson_path: str,
        restrictions_geojson_path: str,
        cell_size: float = 50.0,
        max_steps: int = 500_000,
    ) -> None:
        super().__init__()

        self.city_geojson_path = city_geojson_path
        self.restrictions_geojson_path = restrictions_geojson_path
        self.cell_size = cell_size
        self.max_steps = max_steps

        self.geojson_manager = GeoJSONManager()
        source_map = self.geojson_manager.read_geojson(self.city_geojson_path, use_cache=True)

        self.airspace_grid = AirspaceGrid(source_map=source_map, cell_size=self.cell_size)
        restrictions_geojson = self.geojson_manager.read_geojson(self.restrictions_geojson_path, use_cache=True)
        self._load_restrictions_from_geojson(restrictions_geojson)
    
    def _load_restrictions_from_geojson(self, gdf_restr):
        """
        Load restrictions from a GeoDataFrame WITHOUT forcing CRS relabeling.
        Each feature should be a Point with properties:
        - shape: "DISK" | "CIRCULAR_SECTOR" | "RECTANGLE" (string, default "DISK")
        - radius: float in meters (default 500.0)
        - rotation: float in radians (default 0.0)
        - source: string (default "UNKNOWN")
        The true CRS of 'gdf_restr' is passed down to AirspaceGrid so it can transform properly.
        """
        crs_str = str(gdf_restr.crs) if gdf_restr.crs else "EPSG:4326"
        NM_IN_METERS = 1852.0

        # Keep internal state as dict id->radians (raw). Observation will return normalized.
        self._restriction_ids: Dict[int, float] = {}

        for _, row in gdf_restr.iterrows():
            geom = row.geometry
            if not isinstance(geom, Point):
                # If your dataset may have non-points, you may fallback to centroids, e.g.:
                # if geom is not None and hasattr(geom, "centroid"): geom = geom.centroid
                # else: continue
                continue
            
            shape_name = str("CIRCULAR_SECTOR").upper()
            radius_val = 2 * NM_IN_METERS #2 milhas nauticas #float(row.get("radius", 500.0))
            rotation_val = float(row.get("rotation", 0.0))
            source_name = str(row.get("source", "UNKNOWN")).upper()

            try:
                shape_enum = RestrictionShape[shape_name]
            except KeyError:
                shape_enum = RestrictionShape.DISK

            try:
                source_enum = RestrictionSource[source_name]
            except KeyError:
                source_enum = RestrictionSource.UNKNOWN

            rid = self.airspace_grid.add_restriction(
                shape=shape_enum,
                radius=radius_val,
                location=geom,
                source=source_enum,
                rotation=rotation_val,
                location_epsg=crs_str,
            )
            # Store raw radians internally; we'll normalize in compute_observation().
            self._restriction_ids[rid] = rotation_val


        

    def reset(self, seed: Optional[int] = None):
        self.seed = seed
        self.current_step = 0

        self.airspace_grid.reset()

        observation = self.compute_observation()
        info = {}

        return observation, info


    def _rad_to_norm(self, rad: float) -> float:
        """
        Normalize radians to [0,1] using [-pi, +pi] as the canonical range.
        """
        # Wrap to [-pi, pi] first
        wrapped = (rad + math.pi) % (2 * math.pi) - math.pi
        return float((wrapped + math.pi) / (2 * math.pi))
    
    def _norm_to_rad(self, norm: float) -> float:
        """
        Denormalize a value from [0,1] back to radians using [-pi, +pi] as the canonical range.
        """
        return float(norm * 2 * math.pi - math.pi)
    
    def denormalize_action(self, action: Dict[int, float]) -> Dict[int, float]:
        """
        Normalize action values from [-1, 1] to [0, 1] for each restriction id.
        """
        rad = {}
        for rid, norm in action.items():
            rad[rid] = self._norm_to_rad(norm)
        return rad

    def compute_observation(self) -> Dict[int, float]:
        """
        Return a dict {restriction_id: normalized_rotation_in_[0,1]}.
        The normalization is deterministic and wraps angles to [-pi, pi] first.
        """
        obs: Dict[int, float] = {}
        for rid in list(self._restriction_ids.keys()):
            rad = self.airspace_grid.get_restriction_rotation(rid)
            rad = 0.0 if rad is None else float(rad)
            obs[rid] = self._rad_to_norm(rad)
            # Keep internal mirror as raw radians (optional)
            self._restriction_ids[rid] = rad
        return obs


    def compute_reward(self) -> float:
        # Compute the reward based on the current state of the airspace grid
        return self.airspace_grid.compute_free_space_pct()

    def compute_done(self) -> bool:
        return self.current_step >= self.max_steps

    def _set_rotations(self, id_to_rad: Dict[int, float]) -> None:
        """Update intrinsic rotations by restriction id (radians)."""
        self.airspace_grid.rotate_restrictions(id_to_rad)


    def step(self, norm_rotations: Dict[int, float]):
        self.current_step += 1
        
        # 1) clear dynamic layer
        self.airspace_grid.reset()

        # 2) apply new rotations (intrinsic)
        denormalized_rotations = self.denormalize_action(norm_rotations)
        self._set_rotations(denormalized_rotations)

        # 3) stamp + metrics
        self.airspace_grid.apply_restrictions()

        observation = self.compute_observation()
        reward = self.compute_reward()
        terminated = self.compute_done()
        return observation, reward, terminated, False, {}

    
    def plot_graph(self):
        self.airspace_grid.plot_graph()

    
if __name__ == "__main__":
    import cProfile, pstats, io

    pr = cProfile.Profile()
    pr.enable()

    change_to_project_root()
    grid_path = prepare_data_path("municipios_rj", "rio_niteroi.geojson")
    heliport_path = prepare_data_path("geojson", "heliport.geojson")

    env = AirspaceEnv(
        city_geojson_path=str(grid_path),
        restrictions_geojson_path=str(heliport_path),
        cell_size=50
    )

    observation, info = env.reset()

    for _ in range(1):
        action = {}
        for rid, rotation in observation.items():
            action[rid] = rotation + np.random.uniform(-0.1, 0.1)  # Random delta for demonstration
        observation, reward, terminated, _, _ = env.step(norm_rotations=action)
        env.plot_graph()

        if terminated:
            break

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(50)  # top 50 lines
    print(s.getvalue())
    ps.dump_stats("prof_airspace_env.stats")  # para abrir no Snakeviz
