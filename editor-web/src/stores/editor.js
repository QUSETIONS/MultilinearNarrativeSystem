import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * Root store for the entire JSON document.
 */
export const useEditorStore = defineStore('editor', () => {
    // ---- Raw state ----
    const filename = ref('')
    const assets = ref({
        characters: [],   // [{ id, name, description, portraits: [{path, label}] }]
        backgrounds: [],  // [{ id, name, path }]
        bgm: {}           // { key: description }
    })
    const chapters = ref([]) // normalized from JSON

    // History for Undo/Redo
    const history = ref([])
    const historyIndex = ref(-1)

    // ---- Computed helpers ----
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

    // ---- History Management ----
    function saveState() {
        const snapshot = JSON.stringify({
            assets: assets.value,
            chapters: chapters.value
        })

        // If we are back in history and make a change, branch off
        if (historyIndex.value < history.value.length - 1) {
            history.value = history.value.slice(0, historyIndex.value + 1)
        }

        history.value.push(snapshot)
        if (history.value.length > 50) {
            history.value.shift()
        } else {
            historyIndex.value++
        }
    }

    function undo() {
        if (historyIndex.value > 0) {
            historyIndex.value--
            const state = JSON.parse(history.value[historyIndex.value])
            assets.value = state.assets
            chapters.value = state.chapters
            ElMessage({ message: '已撤销 (Undo)', type: 'info', duration: 1000 })
        }
    }

    function redo() {
        if (historyIndex.value < history.value.length - 1) {
            historyIndex.value++
            const state = JSON.parse(history.value[historyIndex.value])
            assets.value = state.assets
            chapters.value = state.chapters
            ElMessage({ message: '已重做 (Redo)', type: 'info', duration: 1000 })
        }
    }

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

        const chapterList = []
        if (raw.chapters && Array.isArray(raw.chapters)) {
            for (const ch of raw.chapters) {
                const nodes = (ch.nodes || []).map(n => normalizeNode(n))
                chapterList.push({
                    id: String(ch.id),
                    title: ch.title || '',
                    order: ch.order || 0,
                    start_node_id: String(ch.start_node_id || ''),
                    description: ch.description || '',
                    nodes,
                    _editorExpanded: true
                })
            }
        } else if (raw.nodes && Array.isArray(raw.nodes)) {
            chapterList.push({
                id: 'main', title: '主线', order: 0,
                start_node_id: raw.start_node_id ? String(raw.start_node_id) : '',
                description: '',
                nodes: raw.nodes.map(n => normalizeNode(n)),
                _editorExpanded: true
            })
        }

        chapters.value = chapterList

        // Init history
        history.value = []
        historyIndex.value = -1
        saveState()
    }

    function normalizeNode(n) {
        return {
            id: String(n.id),
            type: n.type || 'dialogue',
            speaker: n.speaker || '',
            text: n.text || '',
            bg: n.bg || '',
            music: n.music || '',
            next: n.next ? String(n.next) : null,
            choices: (n.choices || []).map(c => ({
                text: c.text || '',
                next: c.next ? String(c.next) : null,
                set_variable: c.set_variable || null
            })),
            conditions: (n.conditions || []).map(c => ({
                variable: c.variable || '',
                value: c.value,
                next: c.next ? String(c.next) : null
            })),
            default: n.default ? String(n.default) : null,
            title: n.title || '',
            _x: n._editor_x ?? null,
            _y: n._editor_y ?? null
        }
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

        raw.chapters = chapters.value.map(ch => ({
            id: ch.id, title: ch.title, order: ch.order,
            start_node_id: ch.start_node_id, description: ch.description,
            nodes: ch.nodes.map(n => {
                const out = { id: n.id, type: n.type }
                if (n.speaker) out.speaker = n.speaker
                if (n.text) out.text = n.text
                if (n.bg) out.bg = n.bg
                if (n.music) out.music = n.music
                if (n.next) out.next = n.next
                if (n.choices && n.choices.length) out.choices = n.choices
                if (n.conditions && n.conditions.length) out.conditions = n.conditions
                if (n.default) out.default = n.default
                if (n.title) out.title = n.title
                if (n._x != null) out._editor_x = n._x
                if (n._y != null) out._editor_y = n._y
                return out
            })
        }))
        return JSON.stringify(raw, null, 2)
    }

    // ---- Mutation helpers ----
    function updateNode(chapterId, nodeId, patch) {
        const ch = chapters.value.find(c => c.id === chapterId)
        if (!ch) return
        const node = ch.nodes.find(n => n.id === nodeId)
        if (!node) return
        Object.assign(node, patch)
        saveState()
    }

    function addNode(chapterId, type = 'dialogue') {
        const ch = chapters.value.find(c => c.id === chapterId)
        if (!ch) return
        const newId = `n_${Date.now()}`
        ch.nodes.push(normalizeNode({ id: newId, type }))
        saveState()
        return newId
    }

    function deleteNode(chapterId, nodeId) {
        const ch = chapters.value.find(c => c.id === chapterId)
        if (!ch) return
        ch.nodes = ch.nodes.filter(n => n.id !== nodeId)
        // Remove dangling refs
        for (const n of ch.nodes) {
            if (n.next === nodeId) n.next = null
            for (const c of n.choices) { if (c.next === nodeId) c.next = null }
            for (const c of n.conditions) { if (c.next === nodeId) c.next = null }
            if (n.default === nodeId) n.default = null
        }
        saveState()
    }

    function addChapter() {
        const newId = `ch_${Date.now()}`
        chapters.value.push({
            id: newId, title: '新章节', order: chapters.value.length,
            start_node_id: '', description: '', nodes: [], _editorExpanded: true
        })
        saveState()
        return newId
    }

    function deleteChapter(chapterId) {
        chapters.value = chapters.value.filter(c => c.id !== chapterId)
        saveState()
    }

    function reset() {
        filename.value = ''
        assets.value = { characters: [], backgrounds: [], bgm: {} }
        chapters.value = []
        history.value = []
        historyIndex.value = -1
    }

    return {
        filename, assets, chapters,
        historyIndex, history,
        characterById, backgroundById,
        importJSON, exportJSON,
        updateNode, addNode, deleteNode,
        addChapter, deleteChapter, reset,
        undo, redo, saveState
    }
})
