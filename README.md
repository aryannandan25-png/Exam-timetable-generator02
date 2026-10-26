# ExamFlow — Exam Timetable Generator

A college semester project that automatically generates examination schedules using **Graph Coloring** and **Backtracking**, built with Python, Flask, HTML, CSS, and SQLite.

## Features
- Add and delete subjects.
- Store subject code, name, semester, and student-group tags.
- Generate a timetable from a start date, time slots, rooms, and optional day gaps.
- Same-semester papers are treated as conflicting by default; shared student-group tags also create a conflict.
- SQLite persistence, demo dataset, responsive dashboard, and browser print / Save as PDF.
- Graph-coloring scheduler with recursive backtracking and a saturation/degree vertex-selection heuristic.

## Requirements
- Python 3.10+
- Flask 3.x

## Run locally
1. Extract the ZIP.
2. Open a terminal in the extracted `exam_timetable_generator` folder.
3. (Recommended) Create and activate a virtual environment:
   - Windows: `py -m venv .venv`
   - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
4. Install Flask:
   `pip install -r requirements.txt`
5. Start the app:
   `python app.py`
6. Open `http://127.0.0.1:5000` in your browser.
7. Click **Load demo data**, choose a first exam date, and click **Generate timetable**.

## DSA logic
1. Each subject is represented as a graph vertex.
2. Add an edge between subjects whose students must not sit exams simultaneously. This implementation assumes subjects in the same semester conflict, and also checks overlapping comma-separated student-group tags.
3. Each color represents a date/time-slot combination.
4. Backtracking assigns colors while ensuring adjacent vertices have different colors. It chooses the uncolored vertex with the highest saturation, then degree.
5. The color is converted to a date and time slot; separate rooms are assigned to non-conflicting papers that share a slot.

## Project structure
```text
exam_timetable_generator/
├── app.py
├── scheduler.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## Important assumptions / limitations
- This is a semester-project prototype, not a production university examination system.
- Same-semester papers are conservatively treated as conflicting; student-group tags add more conflict edges.
- The implementation checks available room count when placing multiple papers in a slot. If the room count is insufficient, it reports the issue.
- For real deployment, add authentication, input validation, audit logs, and more detailed student enrollment data.
- Flask debug mode is enabled for local development only. Turn it off before deployment.
