extends Control

var _segments: Array[Dictionary] = []
var _line_color: Color = Color(0.45, 0.62, 0.95, 0.72)
var _line_width: float = 3.0
var _arrow_size: float = 10.0


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


func set_line_theme(line_color: Color, width: float, arrow_scale: float = 1.0) -> void:
	_line_color = line_color
	_line_width = width
	_arrow_size = clampf(10.0 * arrow_scale, 7.0, 18.0)
	queue_redraw()


func _draw() -> void:
	for segment_variant in _segments:
		var segment: Dictionary = segment_variant
		var p0: Vector2 = segment.get("from", Vector2.ZERO)
		var p3: Vector2 = segment.get("to", Vector2.ZERO)
		_draw_branch(p0, p3)


func _bezier_point(p0: Vector2, p1: Vector2, p2: Vector2, p3: Vector2, t: float) -> Vector2:
	var u = 1.0 - t
	return (u * u * u) * p0 + (3.0 * u * u * t) * p1 + (3.0 * u * t * t) * p2 + (t * t * t) * p3


func _draw_branch(p0: Vector2, p3: Vector2) -> void:
	var dy := absf(p3.y - p0.y) * 0.42
	var p1 := Vector2(p0.x, p0.y + dy)
	var p2 := Vector2(p3.x, p3.y - dy)

	var points: Array[Vector2] = []
	var steps := 22
	for i in range(steps + 1):
		var t := float(i) / float(steps)
		points.append(_bezier_point(p0, p1, p2, p3, t))

	# Branch trunk
	for i in range(points.size() - 1):
		var a := points[i]
		var b := points[i + 1]
		draw_line(a, b, _line_color, _line_width, true)

	# Sub branches
	_draw_twig(points, 0.34, 20.0, -0.62)
	_draw_twig(points, 0.68, 15.0, 0.58)

	# Small bud at endpoint
	draw_circle(p3, 2.6, Color(_line_color.r, _line_color.g, _line_color.b, 0.95))


func _draw_twig(points: Array[Vector2], ratio: float, length: float, side_sign: float) -> void:
	if points.size() < 3:
		return
	var idx := clampi(int(points.size() * ratio), 1, points.size() - 2)
	var center := points[idx]
	var tangent := (points[idx + 1] - points[idx - 1]).normalized()
	if tangent == Vector2.ZERO:
		return
	var normal := Vector2(-tangent.y, tangent.x) * side_sign
	var tip := center + tangent * (length * 0.55) + normal * (length * 0.8)
	draw_line(center, tip, Color(_line_color.r, _line_color.g, _line_color.b, 0.74), maxf(_line_width * 0.54, 1.2), true)
	draw_circle(tip, 1.8, Color(_line_color.r, _line_color.g, _line_color.b, 0.8))
