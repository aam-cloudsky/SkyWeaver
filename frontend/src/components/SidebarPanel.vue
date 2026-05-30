<template>

  <div class="sidebar-panel glass-panel">

  <section class="sidebar-hero">
    <div class="panel-title">Operational Console</div>
    <div class="panel-heading">Scenario Workspace</div>
    <p class="sidebar-copy">
      Live airspace layers, runtime controls, and scenario inspection.
    </p>
  </section>

  <section class="panel-card">
    <LayerTree />
  </section>

  <section class="panel-card">
    <MetricsPanel />
  </section>

  <section class="panel-card">
    <ScenarioControls />
  </section>

  <section class="panel-card">
    <InspectorPanel />
  </section>

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
  width: 100%;
  height: 100%;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sidebar-hero {
  padding: 4px 2px 10px;
}

.sidebar-copy {
  margin-top: 8px;
  color: var(--text-secondary);
  line-height: 1.45;
}

.panel-card {
  padding: 14px 16px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
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