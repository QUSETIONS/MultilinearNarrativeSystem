import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAssetsStore = defineStore('assets', () => {
    const assets = ref({
        characters: [],   // [{ id, name, description, portraits: [{path, label}] }]
        backgrounds: [],  // [{ id, name, path }]
        bgm: {}           // { key: description }
    })

    const characterById = computed(() => {
        const map = {}
        assets.value.characters.forEach(c => { map[c.id] = c })
        return map
    })

    const backgroundById = computed(() => {
        const map = {}
        assets.value.backgrounds.forEach(b => { map[b.id] = b })
        return map
    })

    return { 
        assets, 
        characterById, 
        backgroundById 
    }
})
