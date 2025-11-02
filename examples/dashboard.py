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
    """Simulate a long optimization that updates results over time."""

    state = AirspaceState()
    rng = np.random.default_rng(42)
    distribution = UAVMAVUAVDistribution(
        rng=rng,
        n_uav=20,
        n_mav=10,
        domain=((-1000, 1000), (-1000, 1000)),
        center_fraction=0.3,
    )

    json.dump(state.to_json(), output_file.open("w"))

    clustering = HDBSCANClustering()
    config = clustering.fit()

    json.dump(state.to_json(), output_file.open("w"))
    
    
    for i in range(100):
        # Simulate computation
        time.sleep(0.3)

        # Generate intermediate "points" and a fake metric
        points = np.random.uniform(-100, 100, (10, 2))
        result = {
            "iteration": i,
            "points": points.tolist(),
            "score": float(np.random.rand())
        }

        # Save intermediate state to JSON file
        with output_file.open("w") as f:
            json.dump(result, f)


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
            fig.update_xaxes(range=[-100, 100])
            fig.update_yaxes(range=[-100, 100])

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
