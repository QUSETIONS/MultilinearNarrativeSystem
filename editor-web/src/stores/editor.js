import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAssetsStore } from './assets'

/**
 * Root store for the project JSON document.
 * Phase 35: Removed chapter/node editing (no longer in scope).
 * Maintains import/export for the full JSON structure, but the
 * platform focuses on asset extraction and generation only.
 */
export const useEditorStore = defineStore('editor', () => {
    const assetsStore = useAssetsStore()

    const filename = ref('')
    // chapters are stored for import/export fidelity but not editable in the UI
    const chapters = ref([])
    
    // Proxy assets for backward compat
    const assets = ref(assetsStore.assets)
    const characterById = computed(() => {
        const map = {}
        for (const ch of assets.value.characters || []) { map[ch.id] = ch }
        return map
    })
    const backgroundById = computed(() => {
        const map = {}
        for (const bg of assets.value.backgrounds || []) { map[bg.id] = bg }
        return map
    })

    // ---- Import ----
    function importJSON(jsonText, fname) {
        filename.value = fname || 'story.json'
        const raw = JSON.parse(jsonText)

        // Parse assets
        const rawAssets = raw.assets || {}
        const chars = []
        if (rawAssets.character) {
            for (const [id, info] of Object.entries(rawAssets.character)) {
                const portraits = []
                if (info.portraits) {
                    for (const [pKey, pLabel] of Object.entries(info.portraits)) {
                        portraits.push({ path: pKey, label: pLabel })
                    }
                }
                chars.push({ id, name: info.name || id, description: info.description || '', portraits })
            }
        }
        assets.value.characters = chars

        const bgs = []
        if (rawAssets.backgrounds) {
            for (const [path, desc] of Object.entries(rawAssets.backgrounds)) {
                bgs.push({ id: path, name: desc, path })
            }
        }
        assets.value.backgrounds = bgs
        assets.value.bgm = rawAssets.bgm || {}

        // Parse chapters (stored for export fidelity, not UI-editable)
        const chapterList = []
        if (raw.chapters && Array.isArray(raw.chapters)) {
            for (const ch of raw.chapters) {
                chapterList.push({
                    id: String(ch.id),
                    title: ch.title || '',
                    order: ch.order || 0,
                    start_node_id: String(ch.start_node_id || ''),
                    description: ch.description || '',
                    nodes: ch.nodes || []
                })
            }
        } else if (raw.nodes && Array.isArray(raw.nodes)) {
            chapterList.push({
                id: 'main', title: '主线', order: 0,
                start_node_id: raw.start_node_id ? String(raw.start_node_id) : '',
                description: '',
                nodes: raw.nodes || []
            })
        }

        chapters.value = chapterList
    }

    // ---- Export ----
    function exportJSON() {
        const raw = { assets: {}, chapters: [] }
        raw.assets.character = {}
        for (const c of assets.value.characters) {
            const portraits = {}
            for (const p of c.portraits) { portraits[p.path] = p.label }
            raw.assets.character[c.id] = { name: c.name, description: c.description, portraits }
        }
        raw.assets.backgrounds = {}
        for (const b of assets.value.backgrounds) { raw.assets.backgrounds[b.path] = b.name }
        raw.assets.bgm = { ...assets.value.bgm }

        // Pass chapters through unchanged
        raw.chapters = chapters.value.map(ch => ({
            id: ch.id, title: ch.title, order: ch.order,
            start_node_id: ch.start_node_id, description: ch.description,
            nodes: ch.nodes
        }))
        return JSON.stringify(raw, null, 2)
    }

    function reset() {
        filename.value = ''
        assets.value = { characters: [], backgrounds: [], bgm: {} }
        chapters.value = []
    }

    // ---- Script Authoring CRUD ----
    function addChapter(title = '新章节') {
        const id = 'ch_' + Date.now()
        chapters.value.push({
            id,
            title,
            order: chapters.value.length,
            start_node_id: '',
            description: '',
            nodes: []
        })
        return id
    }

    function removeChapter(chapterId) {
        chapters.value = chapters.value.filter(c => c.id !== chapterId)
    }

    function addNode(chapterId, nodeData = {}) {
        const idx = chapters.value.findIndex(c => c.id === chapterId)
        if (idx !== -1) {
            const nodeId = 'n_' + Date.now() + Math.floor(Math.random() * 1000)
            const newNode = {
                id: nodeId,
                type: 'dialogue', // default
                speaker: '',
                text: '',
                bg: '',
                music: '',
                ...nodeData
            }
            chapters.value[idx].nodes.push(newNode)
            return nodeId
        }
        return null
    }

    function updateNode(chapterId, nodeId, newData) {
        const cIdx = chapters.value.findIndex(c => c.id === chapterId)
        if (cIdx !== -1) {
            const nIdx = chapters.value[cIdx].nodes.findIndex(n => n.id === nodeId)
            if (nIdx !== -1) {
                chapters.value[cIdx].nodes[nIdx] = {
                    ...chapters.value[cIdx].nodes[nIdx],
                    ...newData
                }
            }
        }
    }

    function removeNode(chapterId, nodeId) {
        const cIdx = chapters.value.findIndex(c => c.id === chapterId)
        if (cIdx !== -1) {
            chapters.value[cIdx].nodes = chapters.value[cIdx].nodes.filter(n => n.id !== nodeId)
        }
    }

    return {
        // State
        filename, chapters, assets, characterById, backgroundById,
        // Methods
        importJSON, exportJSON, reset,
        addChapter, removeChapter, addNode, updateNode, removeNode
    }
})
