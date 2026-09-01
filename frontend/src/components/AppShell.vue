<template>

  <div class="app-shell">
    
    <header class="top-navbar">

      <div class="navbar-brand">

        <div class="brand-title">
          SkyWeaver
        </div>

        <div class="brand-subtitle">
          Operational Airspace Sandbox
        </div>

      </div>

      <div class="navbar-actions">

        <button
          class="navbar-button"
          title="Center Domain"
          @click="focusDomain"
        >
          ⌖
        </button>

      </div>

    </header>

    <MapCanvas />

    <div class="floating-toolbar">

      <button title="Inspect">
        🖱
      </button>

      <div class="tool-wrapper">

        <button
          title="Add"
          @click="showAddMenu = !showAddMenu"
        >
          ➕
        </button>

        <div
          v-if="showAddMenu"
          class="add-menu"
        >

          <button
            class="add-option"
            @click="selectTool('droneport')"
          >
            <span class="add-icon">🛸</span>
            <span class="add-label">Droneport</span>
          </button>

          <button
            class="add-option"
            @click="selectTool('vertiport')"
          >
            <span class="add-icon">🚁</span>
            <span class="add-label">Vertiport</span>
          </button>

        </div>

        <div
          v-if="operationalStore.activeTool"
          class="tool-coordinates"
        >
          {{ operationalStore.activeTool }}
          ·
          {{ mouseCoordinates }}
        </div>

      </div>

      <button title="Add Restriction">
        🚫
      </button>

      <button title="Measure">
        📏
      </button>

    </div>

    <div class="backend-status">

      <div
        class="status-dot"
        :class="{
          connected: backendConnected,
          disconnected: !backendConnected,
        }"
      />

      {{
        backendConnected
          ? 'Connected'
          : 'Offline'
      }}

    </div>

    <VueDraggableResizable
  v-if="!sidebarCollapsed"
  :w="340"
  :h="700"
  :x="sidebarPosition.x"
  :y="sidebarPosition.y"
  :resizable="false"
  :active="false"
  class="draggable-panel"
  @dragging="handleDrag"
>
  <aside class="sidebar">
    <SidebarPanel />
  </aside>
</VueDraggableResizable>
    <button
      class="sidebar-toggle"
      @click="sidebarCollapsed = !sidebarCollapsed"
    >
      ☰
    </button>

  </div>


</template>

<script setup lang="ts">

import { ref, onMounted } from 'vue'

document.body.classList.add('theme-dark')

import SidebarPanel from './SidebarPanel.vue'
import MapCanvas from './MapCanvas.vue'
import VueDraggableResizable from 'vue-draggable-resizable'
import 'vue-draggable-resizable/style.css'
const mouseCoordinates = ref('')
const sidebarCollapsed = ref(false)
const showAddMenu = ref(false)


const backendConnected = ref(false)
let websocket: WebSocket | null = null


import { useOperationalStore } from '@/core/state/operationalStore.ts'
import { useRuntimeStore } from '@/core/state/runtimeStore.ts'
const sidebarPosition = ref({
  x: 20,
  y: 90,
})
const operationalStore =
  useOperationalStore()

// Future improvement:
// replace flat map interaction with globe projection support.
// Candidate approaches:
// - MapLibre globe mode
// - deck.gl GlobeView
// - Mapbox globe projection compatibility layer
function focusDomain() {

  window.dispatchEvent(
    new CustomEvent('skyweaver-focus-domain')
  )
}

onMounted(async () => {


  

    window.addEventListener(
  'skyweaver-tool-change',
  ((event: any) => {

    operationalStore.activeTool = event.detail

    if (!event.detail) {
      mouseCoordinates.value = ''
    }

  }) as EventListener
)
    window.addEventListener(
  'skyweaver-mouse-position',
  ((event: any) => {

    const { lat, lng } = event.detail

    mouseCoordinates.value =
      `${lat.toFixed(5)}, ${lng.toFixed(5)}`
  }) as EventListener
)
  const savedX = localStorage.getItem('sidebar-x')
  const savedY = localStorage.getItem('sidebar-y')

  if (savedX && savedY) {
    sidebarPosition.value.x = Number(savedX)
    sidebarPosition.value.y = Number(savedY)
  }

  const connectWebSocket = () => {

    websocket = new WebSocket(
      'ws://127.0.0.1:8000/ws'
    )

    websocket.onopen = () => {

      backendConnected.value = true

      console.log(
        '[SkyWeaver] WebSocket connected'
      )
    }

    websocket.onclose = () => {

      backendConnected.value = false

      console.log(
        '[SkyWeaver] WebSocket disconnected'
      )

      setTimeout(
        connectWebSocket,
        2000,
      )
    }

    websocket.onerror = () => {

      backendConnected.value = false
    }

    websocket.onmessage = (event) => {
  const scene = JSON.parse(event.data)

  console.log(
    '[SkyWeaver] websocket scene received:',
    scene
  )

  console.log(
    '[SkyWeaver] scene layer ids:',
    scene.layers?.map((layer: any) => layer.id)
  )

  runtimeStore.applyScene(scene)
}
  }

  connectWebSocket()
})
function handleDrag(x: number, y: number) {

  sidebarPosition.value = { x, y }

  localStorage.setItem('sidebar-x', String(x))
  localStorage.setItem('sidebar-y', String(y))
}

function selectTool(tool: string) {

  operationalStore.activeTool = tool

  showAddMenu.value = false

  window.dispatchEvent(
  new CustomEvent(
    'skyweaver-tool-change',
    {
      detail: tool,
    }
  )
  
)
}

const runtimeStore =
  useRuntimeStore()
</script>

<style scoped>

.top-navbar {

  position: absolute;

  top: 20px;
  left: 50%;

  transform: translateX(-50%);

  width: min(760px, calc(100vw - 40px));

  display: flex;

  align-items: center;
  justify-content: space-between;

  padding: 10px 18px;

  border-radius: 22px;

  background: rgba(2,6,23,0.82);

  backdrop-filter: blur(28px);

  border:
    1px solid rgba(255,255,255,0.06);

  box-shadow:
    0 12px 34px rgba(0,0,0,0.22);

  z-index: 2500;
}

.navbar-brand {

  display: flex;

  flex-direction: column;

  gap: 2px;
}

.brand-title {

  font-size: 17px;

  font-weight: 700;

  color: #f8fafc;
}

.brand-subtitle {

  font-size: 11px;

  font-weight: 500;

  color: #94a3b8;
}

.navbar-actions {

  display: flex;

  align-items: center;

  gap: 12px;
}

.navbar-button {

  width: 40px;
  height: 40px;

  border: none;

  border-radius: 16px;

  cursor: pointer;

  font-size: 18px;

  background:
    rgba(15,23,42,0.78);

  color: #f8fafc;

  backdrop-filter: blur(20px);

  transition:
    transform 0.15s ease,
    background 0.15s ease;
}

.navbar-button:hover {

  transform: scale(1.08);

  background:
    rgba(30,41,59,0.92);

  box-shadow:
    0 0 18px rgba(59,130,246,0.18);
}

:global(body.theme-dark) {
  background: #020617;
}

:global(body.theme-dark) .top-navbar,
:global(body.theme-dark) .sidebar,
:global(body.theme-dark) .backend-status,
:global(body.theme-dark) .tool-coordinates,
:global(body.theme-dark) .add-menu,
:global(body.theme-dark) .floating-toolbar button,
:global(body.theme-dark) .navbar-button,
:global(body.theme-dark) .add-option {

  background: rgba(15,23,42,0.72) !important;

  border:
    1px solid rgba(255,255,255,0.08) !important;

  color: #f8fafc !important;
}

:global(body.theme-dark) .brand-title,
:global(body.theme-dark) .add-label,
:global(body.theme-dark) .backend-status,
:global(body.theme-dark) .tool-coordinates {
  color: #f8fafc !important;
}

:global(body.theme-dark) .brand-subtitle {
  color: #94a3b8 !important;
}

.tool-wrapper {
  position: relative;
}

.add-menu {
  position: absolute;

  top: 0;
  right: 78px;

  display: flex;
  flex-direction: row;

  gap: 18px;

  padding: 20px;

  border-radius: 28px;

  background: rgba(2,6,23,0.88);

  backdrop-filter: blur(28px);

  border:
    1px solid rgba(255,255,255,0.35);

  box-shadow:
    0 10px 30px rgba(0,0,0,0.12);
}

.add-option {

  border: none;

  background:
    rgba(15,23,42,0.82);

  width: 132px;
  height: 160px;

  padding: 16px;

  border-radius: 28px;

  cursor: pointer;

  display: flex;
  flex-direction: column;

  align-items: center;
  justify-content: center;

  gap: 14px;

  overflow: hidden;

  transition:
    transform 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.add-option:hover {
  transform:
    translateY(-2px) scale(1.03);

  background:
    rgba(255,255,255,0.82);

  box-shadow:
    0 8px 18px rgba(0,0,0,0.10);
}

.add-icon {

  display: flex;

  align-items: center;
  justify-content: center;

  width: 72px;
  height: 72px;

  font-size: 42px;

  line-height: 1;

  flex-shrink: 0;
}

.add-label {

  display: block;

  width: 100%;

  text-align: center;

  font-size: 17px;

  font-weight: 600;

  line-height: 1.2;

  color: #f8fafc;

  flex-shrink: 0;
}
.floating-toolbar {
  position: absolute;

  top: 84px;
  right: 20px;

  display: flex;
  flex-direction: column;

  gap: 14px;

  z-index: 1200;
}

.floating-toolbar button {

  width: 58px;
  height: 58px;

  border: none;
  border-radius: 20px;

  cursor: pointer;

  background:
    rgba(15,23,42,0.82);

  color: #f8fafc;

  font-size: 22px;

  backdrop-filter:
    blur(28px);

  border:
    1px solid rgba(255,255,255,0.35);

  box-shadow:
    0 8px 24px rgba(0,0,0,0.10);

  transition:
    transform 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.floating-toolbar button:hover {

  transform:
    scale(1.20);

  background:
    rgba(30,41,59,0.92);

  box-shadow:
    0 0 18px rgba(59,130,246,0.18);
}

.app-shell {
  position: fixed;

  inset: 0;

  width: 100%;
  height: 100%;

  overflow: hidden;
}

.sidebar {
  width: 340px;
  max-height: calc(100vh - 40px);

  padding: 0;

  overflow: hidden;

  border-radius: 32px;

  background: rgba(15,23,42,0.82);

  backdrop-filter: blur(32px);

  border:
    1px solid rgba(255,255,255,0.06);

  box-shadow:
    0 12px 32px rgba(0,0,0,0.18);

  z-index: 3000;

  transition:
    transform 0.25s ease,
    opacity 0.25s ease;

  display: flex;
  flex-direction: column;
}

.sidebar-toggle {
  position: absolute;

  top: 76px;
  left: 16px;

  z-index: 20000;

  width: 56px;
  height: 56px;

  border: none;

  border-radius: 18px;

  background:
    rgba(15,23,42,0.82);

  color: #f8fafc;

  cursor: pointer;

  font-size: 22px;

  backdrop-filter:
    blur(24px);

  border:
    1px solid rgba(255,255,255,0.08);

  box-shadow:
    0 10px 28px rgba(0,0,0,0.18);

  transition:
    transform 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.sidebar-toggle:hover {

  transform:
    scale(1.08);

  background:
    rgba(30,41,59,0.92);

  box-shadow:
    0 0 18px rgba(59,130,246,0.18);
}

:deep(.draggable-panel) {
  z-index: 9999 !important;
}

:deep(.vdr) {
  z-index: 9999 !important;
  border: none !important;
}

:deep(.vdr) {
  border: none !important;
}

:deep(.vdr.active) {
  border: none !important;
}

:deep(.vdr-stick) {
  display: none !important;
}

:global(body.cursor-droneport) {
  cursor: crosshair;
}

:global(body.cursor-vertiport) {
  cursor: copy;
}

.tool-coordinates {

  position: absolute;

  top: 72px;
  right: 82px;

  padding:
    10px 14px;

  border-radius: 16px;

  background:
    rgba(15,23,42,0.82);

  backdrop-filter:
    blur(24px);

  border:
    1px solid rgba(255,255,255,0.35);

  box-shadow:
    0 8px 24px rgba(0,0,0,0.10);

  font-size: 14px;

  font-weight: 500;

  color: #f8fafc;

  white-space: nowrap;

  z-index: 2000;
}

.backend-status {

  position: absolute;

  bottom: 24px;
  left: 24px;

  display: flex;

  align-items: center;

  gap: 10px;

  padding:
    10px 16px;

  border-radius: 18px;

  background:
    rgba(15,23,42,0.82);

  backdrop-filter:
    blur(24px);

  border:
    1px solid rgba(255,255,255,0.35);

  box-shadow:
    0 8px 24px rgba(0,0,0,0.10);

  z-index: 99999;

  font-size: 14px;

  font-weight: 600;

  color: #f8fafc;
}

.status-dot {

  width: 10px;
  height: 10px;

  border-radius: 999px;
}

.status-dot.connected {
  background: #22c55e;
}

.status-dot.disconnected {
  background: #ef4444;
}
</style>