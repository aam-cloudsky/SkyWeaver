import streamlit as st
import plotly.graph_objects as go
import threading
import time
import numpy as np
import json
from pathlib import Path

import streamlit.components.v1 as components
from skyweaver.airspace.airspace_state import AirspaceState
from skyweaver.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution
from skyweaver.instance_segmentation.clustering.hdbscan_clustering import HDBSCANClustering
from skyweaver.airspace.airspace_simulation import AirspaceSimulation


# [ ] “Refactor to custom component to stabilise DOM and maintain scroll position”

st.set_page_config(page_title="Async Live Plotly Demo", layout="wide")
st.markdown("""
<script>
const y = sessionStorage.getItem("scrollTop");
if (y) window.scrollTo(0, y);
window.addEventListener("beforeunload", ()=>sessionStorage.setItem("scrollTop", window.scrollY));
</script>
""", unsafe_allow_html=True)

_my_plotly_component = components.declare_component(
    "my_plotly_component",
    url="http://localhost:3001"  # dev server URL for your component
)


def my_plotly_component(spec, key=None):
    return _my_plotly_component(spec=spec, key=key)
# ==========================================================
# BACKGROUND TASK: simulates heavy optimization
# ==========================================================


def heavy_optimization(output_file: Path):
    """
    Simulate a long optimization process that updates results over time.
    The results are periodically written to a JSON file (latest.json),
    which Streamlit can re-read to update the visualization.
    """
    # --- Initialize simulation ---
    simulation = AirspaceSimulation()

    # Run the full setup pipeline once
    simulation.run_distribution()
    simulation.run_clustering()
    simulation.run_optimization()

    # --- Main loop simulating progress ---
    for i in range(100):
        time.sleep(0.3)  # Simulate computation time

        state = simulation.state

        # Safely extract Voronoi seed points as plain floats
        points = [
            [float(cell.seed_point.x), float(cell.seed_point.y)]
            for cell in state.voronoi_cells
        ]

        print(points)

        # Compute a mock "score" for demonstration
        score = float(np.random.uniform(0, 1))

        # Build the serializable snapshot
        result = {
            "iteration": i,
            "score": score,
            "points": points,
        }

        # --- Write to JSON file ---
        try:
            with output_file.open("w") as f:
                json.dump(result, f)
        except Exception as e:
            print(f"[WARN] Failed to write JSON at iteration {i}: {e}")
            continue

    print("✅ Heavy optimization completed.")



# ==========================================================
# STREAMLIT APP: visualize the results
# ==========================================================
st.set_page_config(page_title="Async Live Plotly Demo", layout="wide")
st.title("⚡ Asynchronous Live Plotly Visualization")

output_file = Path("latest.json")

# Persistent app state
if "running" not in st.session_state:
    st.session_state.running = False

# Start button
if st.button("Start Optimization") and not st.session_state.running:
    st.session_state.running = True
    thread = threading.Thread(
        target=heavy_optimization, args=(output_file,), daemon=True)
    thread.start()
    st.success("✅ Optimization started in background.")

# Live placeholder for chart and progress
chart_placeholder = st.empty()
progress_placeholder = st.empty()
status_placeholder = st.empty()

# Main display loop (runs continuously while optimization thread works)
# This loop redraws the chart every 500 ms, but Streamlit remains interactive.
while st.session_state.running:
    if output_file.exists():
        try:
            data = json.loads(output_file.read_text())
            points = np.array(data["points"])
            iteration = data["iteration"]
            score = data["score"]

            # Build Plotly figure
            # Build Plotly figure
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=points[:, 0],
                    y=points[:, 1],
                    mode="markers",
                    marker=dict(size=10, color="royalblue"),
                    name="Points"
                )
            )

            # --- Fixed axis ranges ---
            fig.update_xaxes(range=[-1000, 1000])
            fig.update_yaxes(range=[-1000, 1000])

            # Layout configuration
            fig.update_layout(
                title=f"Iteration {iteration} — Score: {score:.3f}",
                xaxis_title="X",
                yaxis_title="Y",
                width=700,
                height=700
            )

            # Update Streamlit placeholders
            chart_placeholder.plotly_chart(fig, use_container_width=True)
            progress_placeholder.progress((iteration + 1) / 100)
            status_placeholder.info(
                f"Running iteration {iteration+1}/100 | Score={score:.3f}")


            # End condition
            if iteration >= 99:
                st.session_state.running = False
                st.success("✅ Optimization complete.")
        except Exception:
            pass

    time.sleep(0.5)  # refresh interval
