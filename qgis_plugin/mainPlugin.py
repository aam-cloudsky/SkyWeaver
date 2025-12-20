# mainPlugin.py

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject
import os
import sys

import qgis


class SkyWeaverPlugin:
    """Basic QGIS plugin entry point for SkyWeaver."""

    def __init__(self, iface):
        """Initialize the plugin."""
        self.iface = iface
        self.action = None

        # --- Add path to main SkyWeaver project (for imports) ---
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        srv_path = os.path.join(project_root, "srv")
        if srv_path not in sys.path:
            sys.path.append(srv_path)

    def initGui(self):
        """Called when plugin is loaded."""
        self.action = QAction("Run SkyWeaver", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&SkyWeaver", self.action)

    def unload(self):
        """Called when plugin is unloaded."""
        self.iface.removePluginMenu("&SkyWeaver", self.action)
        if self.action:
            self.action.deleteLater()

    def run(self):
        """Example of calling your simulation."""
        try:
            from skyweaver.airspace.airspace_state import AirspaceState

            QMessageBox.information(None, "SkyWeaver", "Plugin loaded successfully!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Could not load SkyWeaver:\n{e}")

    def renderTest(self, painter):
        # use painter for drawing to map canvas
        print("TestPlugin: renderTest called!")
