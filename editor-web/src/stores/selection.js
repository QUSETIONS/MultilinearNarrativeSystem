/**
 * Shared state for the selected chapter/node in the canvas.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSelectionStore = defineStore('selection', () => {
    const selectedChapterId = ref(null)
    const selectedNodeId = ref(null)

    function selectChapter(id) {
        selectedChapterId.value = id
        selectedNodeId.value = null
    }

    function selectNode(nodeId) {
        selectedNodeId.value = nodeId
    }

    function clearNode() {
        selectedNodeId.value = null
    }

    return { selectedChapterId, selectedNodeId, selectChapter, selectNode, clearNode }
})
