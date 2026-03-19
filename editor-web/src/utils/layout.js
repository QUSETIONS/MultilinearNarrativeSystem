/**
 * Auto-layout using Dagre for the flowchart nodes.
 * Returns updated nodes with x/y positions.
 */
import dagre from '@dagrejs/dagre'

const NODE_WIDTH = 260
const NODE_HEIGHT = 120

export function layoutNodes(nodes, edges, direction = 'LR') {
    const g = new dagre.graphlib.Graph()
    g.setDefaultEdgeLabel(() => ({}))
    g.setGraph({ rankdir: direction, nodesep: 60, ranksep: 120 })

    for (const node of nodes) {
        g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
    }

    for (const edge of edges) {
        g.setEdge(edge.source, edge.target)
    }

    dagre.layout(g)

    return nodes.map(node => {
        const { x, y } = g.node(node.id)
        return {
            ...node,
            position: {
                x: x - NODE_WIDTH / 2,
                y: y - NODE_HEIGHT / 2
            }
        }
    })
}
