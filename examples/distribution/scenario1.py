
import matplotlib.pyplot as plt
import numpy as np

from skyweaver.core.logistics.depot import Depot
from skyweaver.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution

Depot()
# ---------------------------------------------
# Setup
# ---------------------------------------------
rng = np.random.default_rng(42)

dist = UAVMAVUAVDistribution(
    rng=rng,
    n_uav=20,
    n_mav=10,
    domain=((-1000, 1000), (-1000, 1000)),
    center_fraction=0.3,
)

# 🔎 Leitura correta: via view do BaseDistribution
config = dist.outpost.airspace_points

print("\n=== [UAV–MAV–UAV Distribution Debug] ===")
print(f"Domain: {config.domain}")
print(f"UAV Points: {len(config.uav_points)}")
print(f"MAV Points: {len(config.mav_points)}")

print("\nFirst 3 UAV points:")
for p in config.uav_points[:3]:
    print(f"  ({p.x:.2f}, {p.y:.2f})")

print("\nFirst 3 MAV points:")
for p in config.mav_points[:3]:
    print(f"  ({p.x:.2f}, {p.y:.2f})")

# ---------------------------------------------
# Visualization
# ---------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))
ax.set_title("UAV–MAV–UAV Distribution Scenario")
ax.set_xlabel("X coordinate")
ax.set_ylabel("Y coordinate")

uav_x = [p.x for p in config.uav_points]
uav_y = [p.y for p in config.uav_points]
ax.scatter(uav_x, uav_y, c="green", label="UAV POIs", s=40, alpha=0.7)

mav_x = [p.x for p in config.mav_points]
mav_y = [p.y for p in config.mav_points]
ax.scatter(mav_x, mav_y, c="blue", label="MAV POIs", s=40, alpha=0.7)

(x_min, x_max), (y_min, y_max) = config.domain
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
ax.grid(True, linestyle="--", alpha=0.6)
ax.legend()
plt.tight_layout()
plt.show()
