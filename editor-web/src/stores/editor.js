import { defineStore, storeToRefs } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useChaptersStore } from './chapters'
import { useAssetsStore } from './assets'

/**
 * Root facade store for the entire JSON document.
 * Phase 32: Split into Chapters and Assets stores to avoid God Object pattern.
 * Provides backwards compatibility for existing Vue components.
 */
export const useEditorStore = defineStore('editor', () => {
    const chaptersStore = useChaptersStore()
    const assetsStore = useAssetsStore()

    const { chapters } = storeToRefs(chaptersStore)
    const { assets, characterById, backgroundById } = storeToRefs(assetsStore)

    const filename = ref('')
    // History for Undo/Redo
    const history = ref([])
    const historyIndex = ref(-1)

    // ---- History Management ----
    // Make sure we save the unwrapped values into snapshot
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
                const nodes = (ch.nodes || []).map(n => chaptersStore.normalizeNode(n))
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
                nodes: raw.nodes.map(n => chaptersStore.normalizeNode(n)),
                _editorExpanded: true
            })
        }

        chapters.value = chapterList

        // Init history
        history.value = []
        historyIndex.value = -1
        saveState()
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

    // Wrappers for backward compatibility that also call saveState automatically
    function updateNode(chapterId, nodeId, patch) {
        chaptersStore.updateNode(chapterId, nodeId, patch)
        saveState()
    }
    function addNode(chapterId, type) {
        const id = chaptersStore.addNode(chapterId, type)
        saveState()
        return id
    }
    function deleteNode(chapterId, nodeId) {
        chaptersStore.deleteNode(chapterId, nodeId)
        saveState()
    }
    function addChapter() {
        const id = chaptersStore.addChapter()
        saveState()
        return id
    }
    function deleteChapter(chapterId) {
        chaptersStore.deleteChapter(chapterId)
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
        // State
        filename, historyIndex, history,
        
        // Proxied State
        chapters, assets, characterById, backgroundById,
        
        // Methods
        importJSON, exportJSON, reset, undo, redo, saveState,
        updateNode, addNode, deleteNode, addChapter, deleteChapter
    }
})
