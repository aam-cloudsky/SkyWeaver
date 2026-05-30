<template>
  <div id="map"></div>
</template>

<script setup lang="ts">
import { MapboxOverlay } from '@deck.gl/mapbox'
import { ScatterplotLayer } from '@deck.gl/layers'

import {
  onMounted,
  watch,
} from 'vue'
import maplibregl from 'maplibre-gl'

import 'maplibre-gl/dist/maplibre-gl.css'
import { useOperationalStore } from '@/core/state/operationalStore'
import { useRuntimeStore } from '@/core/state/runtimeStore'

const operationalStore =
  useOperationalStore()

const runtimeStore =
  useRuntimeStore()

onMounted(() => {

  const map = new maplibregl.Map({
    container: 'map',
    //cooperativeGestures: true,

    style: {
      version: 8,
      sources: {
        voyager: {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution:
            '&copy; OpenStreetMap contributors &copy; CARTO',
        },
      },
      layers: [
        {
          id: 'voyager',
          type: 'raster',
          source: 'voyager',
        },
      ],
    },

    center: [-43.1729, -22.9068],
    zoom: 11,

    pitch: 0,
    bearing: 0,

    pitchWithRotate: true,
    dragRotate: true,
    touchPitch: true,

    attributionControl: false,
  })

  map.addControl(
    new maplibregl.NavigationControl({
      visualizePitch: false,
      showCompass: false,
    }),
    'bottom-right'
  )

  const getVertiportsLayerData = () => {
    const layer =
      runtimeStore.getLayer('vertiports')

    if (!layer?.geojson?.features) {
      return []
    }

    return layer.geojson.features
      .filter((feature: any) => {
        return feature.geometry?.type === 'Point'
      })
      .map((feature: any) => ({
        position: feature.geometry.coordinates,
      }))
  }

  const buildLayers = () => {

    return [
      new ScatterplotLayer({
        id: 'droneports',

        data: getVertiportsLayerData(),

        getPosition: (d: any) => d.position,

        getRadius: 250,

        radiusUnits: 'meters',

        getFillColor: [168, 85, 247, 25],

        opacity: 0.85,

        pickable: true,
      }),

      new ScatterplotLayer({
        id: 'droneports-glow',

        data: getVertiportsLayerData(),

        getPosition: (d: any) => d.position,

        getRadius: 5000,

        radiusUnits: 'meters',

        getFillColor: [180, 120, 255, 40],

        stroked: false,
      }),
    ]
  }

  const overlay = new MapboxOverlay({
    layers: buildLayers(),
  })

  map.addControl(overlay)
  watch(
    () => runtimeStore.scene,
    () => {
      overlay.setProps({
        layers: buildLayers(),
      })
    },
    {
      deep: true,
    }
  )
  map.on('click', async (event) => {

    if (operationalStore.activeTool === 'droneport') {

      const response = await fetch(
        'http://127.0.0.1:8000/intent/add-vertiport',
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            latitude: event.lngLat.lat,
            longitude: event.lngLat.lng,
          }),
        }
      )

      await response.json()

      if (!response.ok) {
        console.error(
          '[SkyWeaver] Failed to create vertiport'
        )

        return
      }

      operationalStore.activeTool = null

      canvas.style.cursor = ''
    }
  })
  map.on('mousemove', (event) => {

    const lat = event.lngLat.lat
    const lng = event.lngLat.lng

    window.dispatchEvent(
      new CustomEvent(
        'skyweaver-mouse-position',
        {
          detail: {
            lat,
            lng,
          },
        }
      )
    )
  })
  map.getCanvas().addEventListener('contextmenu', (event) => {

    event.preventDefault()

    canvas.style.cursor = ''

    window.dispatchEvent(
      new CustomEvent(
        'skyweaver-tool-change',
        {
          detail: null,
        }
      )
    )
  })
  const canvas = map.getCanvas()

  window.addEventListener('skyweaver-tool-change', ((event: any) => {

    const tool = event.detail

    if (tool === 'droneport') {

      canvas.style.cursor =
        "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48'%3E%3Ctext y='36' font-size='36'%3E🛸%3C/text%3E%3C/svg%3E\") 24 24, auto"

      return
    }

    if (tool === 'vertiport') {

      canvas.style.cursor =
        "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48'%3E%3Ctext y='36' font-size='36'%3E🚁%3C/text%3E%3C/svg%3E\") 24 24, auto"

      return
    }

    canvas.style.cursor = ''
  }) as EventListener)

})



</script>

<style scoped>

#map {
  position: absolute;

  inset: 0;
}
</style>