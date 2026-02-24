extends Control

var _segments: Array[Dictionary] = []


func set_graph_edges(edges: Array, centers: Dictionary) -> void:
	_segments.clear()
	for edge_variant in edges:
		if not (edge_variant is Dictionary):
			continue
		var edge: Dictionary = edge_variant
		var from_id = str(edge.get("from_chapter_id", ""))
		var to_id = str(edge.get("to_chapter_id", ""))
		if not centers.has(from_id) or not centers.has(to_id):
			continue
		_segments.append(
			{
				"from": centers[from_id],
				"to": centers[to_id],
			}
		)
	queue_redraw()


func _draw() -> void:
	for segment_variant in _segments:
		var segment: Dictionary = segment_variant
		var p0: Vector2 = segment.get("from", Vector2.ZERO)
		var p3: Vector2 = segment.get("to", Vector2.ZERO)
		var dx = absf(p3.x - p0.x) * 0.35
		var p1 = Vector2(p0.x + dx, p0.y)
		var p2 = Vector2(p3.x - dx, p3.y)

		var points: PackedVector2Array = []
		var steps = 20
		for i in range(steps + 1):
			var t = float(i) / float(steps)
			points.append(_bezier_point(p0, p1, p2, p3, t))
		draw_polyline(points, Color(0.45, 0.62, 0.95, 0.72), 3.0, true)


func _bezier_point(p0: Vector2, p1: Vector2, p2: Vector2, p3: Vector2, t: float) -> Vector2:
	var u = 1.0 - t
	return (u * u * u) * p0 + (3.0 * u * u * t) * p1 + (3.0 * u * t * t) * p2 + (t * t * t) * p3
