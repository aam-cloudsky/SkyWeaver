import { defineStore } from 'pinia'

export type TransportLayer = {
    id: string
    geometry_type: string
    crs: string
    geojson: GeoJSON.FeatureCollection
}

export type TransportScene = {
    layers: TransportLayer[]
}

export const useRuntimeStore =
    defineStore('runtime', {

        state: () => ({

            scene: {
                layers: [],
            } as TransportScene,
        }),

        getters: {

            getLayer: (state) => {

                return (
                    layerId: string,
                ): TransportLayer | undefined => {

                    return state.scene.layers.find(
                        (layer) => layer.id === layerId,
                    )
                }
            },
        },

        actions: {

            applyScene(scene: TransportScene) {

                this.scene = scene
            },
        },
    })