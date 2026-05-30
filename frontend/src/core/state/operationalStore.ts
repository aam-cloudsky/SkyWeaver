import { defineStore } from 'pinia'

export const useOperationalStore =
    defineStore('operational', {

        state: () => ({

            activeTool: null as string | null,

            backendConnected: false,

            mouseCoordinates: '',

        }),
    })