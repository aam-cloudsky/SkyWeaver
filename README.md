# 🛰️ SkyWeaver

A modular simulator to organize airspace constraints and orchestrate future autonomous aerial operations.

---

To use QGIS library properly inside your virtualised environment, you have to linking it:
MACOS:
export PYTHONPATH="/Applications/QGIS-LTR.app/Contents/Resources/python:/Applications/QGIS-LTR.app/Contents/Resources/python/site-packages:$PYTHONPATH"


## 🌐 Context

**SkyWeaver** is a modular UTM (Unmanned Traffic Management) simulator designed to structure airspace constraints and enable future autonomous aerial operations.  

This project aims to provide an extensible, transparent infrastructure that prioritizes:

- ✅ Scalability
- ✅ Readability
- ✅ Easy debugging (bugs should be easy to detect)
- ✅ Ease of maintenance and onboarding

Every step is designed to be modular and clear, preparing the foundation for future modules (e.g., dynamic routing, autonomous agents).

---

## 🎯 Where we are now

At this stage, we are working on building the **spatial grid layer** and preparing the data ingestion foundation.  

This layer will serve as the backbone for:

- Modeling airspace restrictions.
- Visual validation in QGIS.
- Enabling future dynamic simulations (data playback, routing, agent-based behavior).

---

## 🚩 Roadmap & Next Steps (with context)

### 🟢 1️⃣ Grid script

**Context:**  
The spatial grid is the system's backbone. It defines the geographic coverage and will be used to associate restrictions, occupancy data, zones, and future routing.

**Details:**

- Generate a square (or hex) grid covering Rio de Janeiro.
- Clip grid using the city's polygon.
- Adjust resolution visually using QGIS.

---

### 📄 2️⃣ Reading data files

**Context:**  
Real-world data (GeoJSONs) will feed the grid with occupancy information and validate realistic scenarios.

**Details:**

- Read GeoJSON files (routes, AIS data, helipads, etc.).
- Normalize columns and structure.
- Prepare for integration with the grid.

---

### 🌐 3️⃣ Exporting integrated GeoJSON for QGIS

**Context:**  
Exporting to QGIS allows spatial validation and fine-tuning of cell granularity and restrictions before advancing to dynamic modules.

**Details:**

- Export clipped grid to GeoJSON.
- Visualize and review in QGIS.
- Adjust cell size if necessary.

---

### 🚁 4️⃣ Optimization of helipad restrictions — **FIRST MILESTONE**

**Context:**  
First practical application of restrictions on the grid. Validates whether we can apply and visualize restricted or priority zones.

**Details:**

- Add restrictions based on helipad locations.
- Generate visual layer for QGIS.
- Validate overlap with the grid.

---

### ▶️ 5️⃣ Data playback ("Play")

**Context:**  
Introduce temporal dynamics by simulating "movement" across the grid.

**Details:**

- Implement a player that traverses data in time.
- Update grid occupancy dynamically.
- Export snapshots or generate animation-ready outputs.

---

### 🛫 6️⃣ Grid-based route generation at a given instant — **SECOND MILESTONE**

**Context:**  
First experiment with dynamic routing, opening the way for future autonomous agent simulation.

**Details:**

- Compute an optimal route across the grid at a specific instant and set of constraints.
- Validate route over the restricted grid.
- Prepare foundation for future navigation logic.

---

## 🚩 Milestones summary

✅ **First milestone**: Grid + helipad restrictions.  
✅ **Second milestone**: Dynamic grid-based routing.  
🚀 Future: autonomous agents, multi-agent optimization, massive-scale simulations.

---

## 🚩 Next Steps

- Implement the grid covering Rio de Janeiro.
- Export the grid to QGIS for visual validation.
- Read the heliport restriction files.
- Optimize and apply heliport restrictions — **First Milestone**.


---

## 💬 How to contribute

Feel free to open issues or suggest improvements. The project is designed to be modular and highly maintainable.

---

## 🔥 Banner

> 🛰️ *"SkyWeaver: weaving grids, constraints, and future autonomous skies."*

---

## 📄 License

This project is currently private and all data is confidential. Unauthorized use or distribution is strictly prohibited.

---

I needed firstly find the qgis python 3.12

them install the project:
$ & "C:\Program Files\QGIS 3.40.8\apps\Python312\python.exe" -m pip install -e .

$ To Use QGIS's python: & "C:\Program Files\QGIS 3.40.8\apps\Python312\python.exe" 
$ pip: & "C:\Program Files\QGIS 3.40.8\apps\Python312\python.exe" -m pip
$ & "C:\Program Files\QGIS 3.40.8\apps\Python312\python.exe" -m poetry install
$ & "C:\Program Files\QGIS 3.40.8\apps\Python312\python.exe" -m skyweaver.distributions.uav_mav_uav_distribution
