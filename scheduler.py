"""Conflict-free examination timetable generation using graph coloring + backtracking."""
from datetime import date, timedelta


def students_overlap(group_a, group_b):
    """Student groups are comma-separated IDs/tags. Blank means unknown/no overlap constraint."""
    a = {x.strip().lower() for x in (group_a or "").split(",") if x.strip()}
    b = {x.strip().lower() for x in (group_b or "").split(",") if x.strip()}
    return bool(a & b)


def build_conflict_graph(subjects):
    """
    Each subject is a vertex. An edge joins subjects that cannot be held simultaneously:
    - same semester (conservative default: students are assumed to take all subjects in it)
    - or overlapping student-group tags
    """
    graph = {s["id"]: set() for s in subjects}
    for i, a in enumerate(subjects):
        for b in subjects[i + 1:]:
            same_semester = str(a["semester"]).strip().lower() == str(b["semester"]).strip().lower()
            overlap = students_overlap(a.get("students", ""), b.get("students", ""))
            if same_semester or overlap:
                graph[a["id"]].add(b["id"])
                graph[b["id"]].add(a["id"])
    return graph


def color_graph_backtracking(graph, available_colors):
    """DSATUR-style vertex selection with recursive backtracking."""
    colors = {}

    def choose_vertex():
        uncolored = [v for v in graph if v not in colors]
        if not uncolored:
            return None
        # Highest saturation, then highest degree
        return max(
            uncolored,
            key=lambda v: (
                len({colors[n] for n in graph[v] if n in colors}),
                len(graph[v])
            )
        )

    def solve():
        if len(colors) == len(graph):
            return True
        vertex = choose_vertex()
        forbidden = {colors[n] for n in graph[vertex] if n in colors}
        for color in range(available_colors):
            if color in forbidden:
                continue
            colors[vertex] = color
            if solve():
                return True
            del colors[vertex]
        return False

    if solve():
        return colors
    return None


def generate_schedule(subjects, start_date, slots, rooms, gap_days=0):
    """Return a schedule or an explanatory error. Slots are reusable across exam dates."""
    if not subjects:
        return {"ok": False, "message": "No subjects were supplied."}
    if not slots or not rooms:
        return {"ok": False, "message": "At least one time slot and one room are required."}

    graph = build_conflict_graph(subjects)
    # A color represents a day/slot pair. Rooms are assigned after coloring.
    # More than one room allows non-conflicting subjects to run at the same time.
    max_colors = len(slots) * len(subjects)
    colors = color_graph_backtracking(graph, max_colors)
    if colors is None:
        return {"ok": False, "message": "Could not find a schedule. Try adding time slots or reviewing constraints."}

    # Assign each color to a day and slot. Colors are ordered by color index.
    # If several subjects have the same color, they do not conflict and use separate rooms.
    start = date.fromisoformat(start_date)
    schedule = []
    by_color = {}
    for subject in subjects:
        by_color.setdefault(colors[subject["id"]], []).append(subject)

    for color in sorted(by_color):
        day_offset = color // len(slots)
        slot_index = color % len(slots)
        exam_day = start + timedelta(days=day_offset * (gap_days + 1))
        group = by_color[color]
        if len(group) > len(rooms):
            return {
                "ok": False,
                "message": (
                    f"Not enough rooms for {exam_day.isoformat()} {slots[slot_index]}. "
                    f"{len(group)} non-conflicting subjects need rooms, but only {len(rooms)} room(s) were provided."
                )
            }
        for index, subject in enumerate(sorted(group, key=lambda s: s["code"])):
            schedule.append({
                "subject_id": subject["id"],
                "code": subject["code"],
                "name": subject["name"],
                "semester": subject["semester"],
                "date": exam_day.isoformat(),
                "slot": slots[slot_index],
                "room": rooms[index]
            })

    schedule.sort(key=lambda x: (x["date"], x["slot"], x["room"], x["code"]))
    return {"ok": True, "schedule": schedule, "graph": graph}
