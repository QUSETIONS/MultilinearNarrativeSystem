import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChaptersStore = defineStore('chapters', () => {
    const chapters = ref([])

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

    function updateNode(chapterId, nodeId, patch) {
        const ch = chapters.value.find(c => c.id === chapterId)
        if (!ch) return
        const node = ch.nodes.find(n => n.id === nodeId)
        if (!node) return
        Object.assign(node, patch)
        // Note: undo/redo saveState is currently managed by the root editor store
        // If needed, the root store can watch changes or we emit events.
        // For backwards compatibility, the facade will wrap these to call saveState.
    }

    function addNode(chapterId, type = 'dialogue') {
        const ch = chapters.value.find(c => c.id === chapterId)
        if (!ch) return
        const newId = `n_${Date.now()}`
        ch.nodes.push(normalizeNode({ id: newId, type }))
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
    }

    function addChapter() {
        const newId = `ch_${Date.now()}`
        chapters.value.push({
            id: newId, title: '新章节', order: chapters.value.length,
            start_node_id: '', description: '', nodes: [], _editorExpanded: true
        })
        return newId
    }

    function deleteChapter(chapterId) {
        chapters.value = chapters.value.filter(c => c.id !== chapterId)
    }

    return { 
        chapters, normalizeNode, 
        updateNode, addNode, deleteNode, 
        addChapter, deleteChapter 
    }
})
