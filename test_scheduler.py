from scheduler import build_conflict_graph, color_graph_backtracking

subjects = [
    {"id": 1, "semester": "4", "students": "IT-A"},
    {"id": 2, "semester": "4", "students": "IT-A"},
    {"id": 3, "semester": "6", "students": "IT-B"},
]
graph = build_conflict_graph(subjects)
assert 2 in graph[1] and 1 in graph[2]
assert 3 not in graph[1]
colors = color_graph_backtracking(graph, 2)
assert colors is not None
assert colors[1] != colors[2]
print("Scheduler smoke test passed.")
