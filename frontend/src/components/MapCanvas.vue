<template>
  <div id="map"></div>
</template>

<script setup lang="ts">
import { MapboxOverlay } from '@deck.gl/mapbox'
import {
  ScatterplotLayer,
  PolygonLayer,
  IconLayer,
  PathLayer,
} from '@deck.gl/layers'
import { circle as turfCircle } from '@turf/turf'

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

const OPERATIONAL_RANGE_KM = 10
const HELIPORT_RANGE_NM = 2
const NAUTICAL_MILE_TO_KM = 1.852
const OPERATIONAL_RANGE_STEPS = 64

type InfrastructureType =
  | 'droneport'
  | 'heliport'

const droneportIcon =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='128' height='128' viewBox='0 0 128 128'%3E%3Ccircle cx='64' cy='64' r='44' fill='%238b5cf6' fill-opacity='0.96'/%3E%3Cpath d='M64 24 L92 64 L64 104 L36 64 Z' fill='white' fill-opacity='0.98'/%3E%3Ccircle cx='64' cy='64' r='10' fill='%238b5cf6'/%3E%3C/svg%3E"

const heliportIcon =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='128' height='128' viewBox='0 0 128 128'%3E%3Ccircle cx='64' cy='64' r='44' fill='%23dc2626' fill-opacity='0.96'/%3E%3Ccircle cx='64' cy='64' r='34' fill='%23ef4444' fill-opacity='0.92'/%3E%3Ctext x='64' y='81' text-anchor='middle' font-size='50' font-weight='bold' fill='white' font-family='Arial'%3EH%3C/text%3E%3C/svg%3E"

const INFRASTRUCTURE_STYLE = {
  droneport: {
    operationalRadiusKm:
      OPERATIONAL_RANGE_KM,

    fillColor:
      [139, 92, 246, 14],

    lineColor:
      [168, 85, 247, 110],

    pulseFillColor:
      [168, 85, 247],

    pulseLineColor:
      [216, 180, 255],

    icon:
      droneportIcon,
  },

  heliport: {
    operationalRadiusKm:
      HELIPORT_RANGE_NM * NAUTICAL_MILE_TO_KM,

    fillColor:
      [220, 38, 38, 18],

    lineColor:
      [239, 68, 68, 180],

    pulseFillColor:
      [220, 38, 38],

    pulseLineColor:
      [254, 202, 202],

    icon:
      heliportIcon,
  },
} as const

type InfrastructurePoint = {
  position: [number, number]
  type: InfrastructureType
}

type LayerVisibilityState = {
  droneports: boolean
  heliports: boolean
}

const selectedInfrastructure = {
  position: null as [number, number] | null,
  type: null as InfrastructureType | null,
}

const layerVisibility: LayerVisibilityState = {
  droneports: true,
  heliports: true,
}

const pulseAnimation = {
  phase: 0,
  lastTimestamp: 0,
}

const corridorAnimation = {
  phase: 0,
}
  const getCorridorLayerData = () => {
  const layer =
    runtimeStore.getLayer('routes')

  //console.log(
  //  '[SkyWeaver] raw routes layer:',
  //  layer
  //)

  if (!layer?.geojson?.features) {
    //console.log(
     // '[SkyWeaver] routes layer missing or without features'
    //)
    return []
  }

  const lineFeatures = layer.geojson.features.filter((feature: any) => {
    return feature.geometry?.type === 'LineString'
  })

  //console.log(
   // '[SkyWeaver] route line features count:',
   // lineFeatures.length
  

  if (lineFeatures.length > 0) {
    console.log(
      '[SkyWeaver] first route feature:',
      lineFeatures[0]
    )

    console.log(
      '[SkyWeaver] first route coordinates sample:',
      (lineFeatures[0].geometry as GeoJSON.LineString).coordinates.slice(0, 5)
    )
  }

  return lineFeatures.map((feature: any) => ({
    path: (feature.geometry as GeoJSON.LineString).coordinates,
  }))
}

onMounted(() => {

  const map = new maplibregl.Map({
    container: 'map',

    style:
      'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',

    center: [-43.1729, -22.9068],
    zoom: 9.8,

    pitch: 0,
    bearing: 0,

    pitchWithRotate: false,
    dragRotate: true,
    touchPitch: false,

    attributionControl: false,
    maxPitch: 0,
  })

  map.on('style.load', () => {
    ;(map as any).setProjection({
      type: 'mercator',
    })
  })

  map.addControl(
    new maplibregl.NavigationControl({
      visualizePitch: false,
      showCompass: false,
    }),
    'bottom-right'
  )

  const readPointLayer = (
    layerId: string,
    type: InfrastructurePoint['type'],
  ): InfrastructurePoint[] => {
    const layer =
      runtimeStore.getLayer(layerId)

    if (!layer?.geojson?.features) {
      return []
    }

    return layer.geojson.features
      .filter((feature: any) => {
        return feature.geometry?.type === 'Point'
      })
      .map((feature: any) => ({
        position: feature.geometry.coordinates as [number, number],
        type,
      }))
  }

  const getInfrastructureLayerData = (): InfrastructurePoint[] => {
    const droneports =
      layerVisibility.droneports
        ? readPointLayer('vertiports', 'droneport')
        : []

    const heliports =
      layerVisibility.heliports
        ? readPointLayer('heliports', 'heliport')
        : []

    return [
      ...droneports,
      ...heliports,
    ]
  }

  const buildOperationalRangeFeatures = () => {
    return getInfrastructureLayerData()
      .map((point) => {
        const radiusKm =
          INFRASTRUCTURE_STYLE[
            point.type
          ].operationalRadiusKm

        const polygon = turfCircle(
          point.position,
          radiusKm,
          {
            steps: OPERATIONAL_RANGE_STEPS,
            units: 'kilometers',
          }
        )

        return {
          polygon:
            polygon.geometry.coordinates[0],

          type: point.type,

          radiusKm,
        }
      })
  }

  const buildLayers = () => {
    const shouldRenderOperationalRanges = true

    const infrastructurePoints =
      getInfrastructureLayerData()

    const corridorPaths =
      getCorridorLayerData()

    const operationalRangePolygons =
      buildOperationalRangeFeatures()

    const pulseData =
      selectedInfrastructure.position &&
      selectedInfrastructure.type
        ? [{
            position:
              selectedInfrastructure.position,

            type:
              selectedInfrastructure.type,
          }]
        : []

    return [
      new PathLayer<any>({
        id: 'corridor-background',

        data: corridorPaths,

        getPath: (d: any) => d.path,

        getColor: [34, 211, 238, 42],

        widthUnits: 'pixels',

        getWidth: 10,

        rounded: true,
        capRounded: true,
        jointRounded: true,

        opacity: 0.18,

        pickable: false,
      }),

      new PathLayer<any>({
        id: 'corridor-flow',

        data: corridorPaths,

        getPath: (d: any) => {
          const path = d.path

          if (!Array.isArray(path) || path.length < 2) {
            return path
          }

          const animationOffset =
            corridorAnimation.phase % path.length

          return [
            ...path.slice(animationOffset),
            ...path.slice(0, animationOffset),
          ]
        },

        getColor: [103, 232, 249, 220],

        widthUnits: 'pixels',

        getWidth: 3.2,

        rounded: true,
        capRounded: true,
        jointRounded: true,

        opacity: 0.95,

        pickable: false,

        updateTriggers: {
          getPath: corridorAnimation.phase,
        },
      }),
      ...(shouldRenderOperationalRanges
        ? [
            new PolygonLayer<any>({
              id: 'droneports-range',

              data: operationalRangePolygons,

              getPolygon: (d: any) => d.polygon,

              filled: true,

              stroked: true,

              getFillColor: (d: {
                type: InfrastructureType
              }) => {
                return INFRASTRUCTURE_STYLE[
                  d.type
                ].fillColor
              },

              getLineColor: (d: {
                type: InfrastructureType
              }) => {
                return INFRASTRUCTURE_STYLE[
                  d.type
                ].lineColor
              },

              getLineWidth: 2,

              lineWidthUnits: 'pixels',

              opacity: 0.10,

              pickable: false,
            }),
          ]
        : []),

      new IconLayer<any>({
        id: 'vertiport-icons',

        data: infrastructurePoints,

        pickable: true,

        onClick: (info: any) => {
          if (!info.object) {
            return
          }

          selectedInfrastructure.position =
            info.object.position

          selectedInfrastructure.type =
            info.object.type

          pulseAnimation.phase = 0

          overlay.setProps({
            layers: buildLayers(),
          })
        },

        getPosition: (d: InfrastructurePoint) => d.position,

        getIcon: (d: InfrastructurePoint) => ({
          url:
            INFRASTRUCTURE_STYLE[
              d.type
            ].icon,

          width: 128,
          height: 128,
          anchorY: 64,
        }),

        getSize: () => 42,

        sizeUnits: 'pixels',

        sizeMinPixels: 34,
      }),

      new ScatterplotLayer<any>({
        id: 'vertiport-pulse',

        data: pulseData,

        getPosition: (d: any) => d.position,

        radiusUnits: 'meters',

        stroked: true,

        filled: true,

        lineWidthUnits: 'pixels',

        getLineWidth: 2,

        lineWidthMinPixels: 1,

        getRadius: (d: {
          type: InfrastructureType
        }) => {
          const phase = pulseAnimation.phase % 220

          const operationalRadiusMeters =
            INFRASTRUCTURE_STYLE[
              d.type
            ].operationalRadiusKm * 1000

          const minRadius = 400

          const maxRadius =
            operationalRadiusMeters * 0.995

          const normalized = phase / 220

          return (
            minRadius +
            normalized * (maxRadius - minRadius)
          )
        },

        getFillColor: (d: {
          type: InfrastructureType
        }) => {
          const phase = pulseAnimation.phase % 220

          const normalized = phase / 220

          const alpha = Math.max(0, 52 * (1 - normalized))

          const baseColor =
            INFRASTRUCTURE_STYLE[
              d.type
            ].pulseFillColor

          return [
            baseColor[0],
            baseColor[1],
            baseColor[2],
            alpha,
          ]
        },

        getLineColor: (d: {
          type: InfrastructureType
        }) => {
          const phase = pulseAnimation.phase % 220

          const normalized = phase / 220

          const alpha = Math.max(0, 255 * (1 - normalized))

          const baseColor =
            INFRASTRUCTURE_STYLE[
              d.type
            ].pulseLineColor

          return [
            baseColor[0],
            baseColor[1],
            baseColor[2],
            alpha,
          ]
        },

        opacity: 1,
        radiusMinPixels: 12,
        radiusMaxPixels: 900,

        updateTriggers: {
          getRadius: pulseAnimation.phase,
          getFillColor: pulseAnimation.phase,
          getLineColor: pulseAnimation.phase,
        },
        pickable: false,
      }),

      new ScatterplotLayer({
        id: 'droneports',

        data: infrastructurePoints,

        getPosition: (d: InfrastructurePoint) => d.position,

        getRadius: 8,

        radiusUnits: 'meters',

        getFillColor: [192, 132, 252, 0],

        stroked: false,

        opacity: 1,

        pickable: true,
      }),
    ]
  }

  const overlay = new MapboxOverlay({
    interleaved: true,
    layers: buildLayers(),
  })

  const animatePulse = (timestamp = 0) => {

    if (!pulseAnimation.lastTimestamp) {
      pulseAnimation.lastTimestamp = timestamp
    }

    const delta =
      timestamp - pulseAnimation.lastTimestamp

    if (delta > 10) {
      pulseAnimation.phase += 2
      //corridorAnimation.phase += 0.02

      pulseAnimation.lastTimestamp = timestamp

      overlay.setProps({
        layers: buildLayers(),
      })

      map.triggerRepaint()
    }

    requestAnimationFrame(animatePulse)
  }

  animatePulse()

  map.addControl(overlay)

  const canvas = map.getCanvas()

  window.addEventListener(
    'skyweaver-focus-domain',
    () => {

      map.easeTo({
        center: [-43.1729, -22.9068],
        zoom: 9.8,

        pitch: 0,
        bearing: 0,

        duration: 2200,

        easing: (t) => t * (2 - t),
      })
    }
  )

  window.addEventListener(
    'skyweaver-layer-visibility-change',
    ((event: any) => {

      const detail = event.detail

      if (!detail) {
        return
      }

      if (typeof detail.droneports === 'boolean') {
        layerVisibility.droneports =
          detail.droneports
      }

      if (typeof detail.heliports === 'boolean') {
        layerVisibility.heliports =
          detail.heliports
      }

      overlay.setProps({
        layers: buildLayers(),
      })

      map.triggerRepaint()
    }) as EventListener
  )

  watch(
  () => runtimeStore.scene,
  (scene) => {
    console.log(
      '[SkyWeaver] scene layers:',
      scene.layers.map((layer) => ({
        id: layer.id,
        geometry_type: layer.geometry_type,
        features:
          layer.geojson?.features?.length ?? 0,
      }))
    )

    const routesLayer =
      scene.layers.find((layer) => layer.id === 'routes')

    console.log(
      '[SkyWeaver] routes layer from store:',
      routesLayer
    )

    overlay.setProps({
      layers: buildLayers(),
    })

    map.triggerRepaint()
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
})
</script>

<style scoped>

#map {
  position: absolute;

  inset: 0;
}

:deep(.skyweaver-layer-hidden) {
  opacity: 0.35;
}
</style>