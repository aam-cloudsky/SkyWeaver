<template>

  <div class="sidebar-panel">

    <h1>SkyWeaver</h1>

    <p>Operational GIS Sandbox</p>

    <hr />

    <LayerTree />

    <MetricsPanel />

    <ScenarioControls />

    <InspectorPanel />

    <div class="panel-section">
  <h2>Layers</h2>

</div>

<div class="panel-section">
  <h2>Metrics</h2>

</div>

  </div>

</template>

<script setup lang="ts">
import LayerTree from './LayerTree.vue'
import MetricsPanel from './MetricsPanel.vue'
import ScenarioControls from './ScenarioControls.vue'
import InspectorPanel from './InspectorPanel.vue'
</script>

<style scoped>

.sidebar-panel {
  padding: 16px;
}

.panel-section {
  margin-bottom: 24px;

  padding: 16px;

  border-radius: 18px;

  background:
    rgba(255,255,255,0.04);

  border:
    1px solid rgba(255,255,255,0.05);
}
</style>