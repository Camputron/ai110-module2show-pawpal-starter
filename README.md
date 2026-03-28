# PawPal+

A smart pet care scheduling assistant built with Python and Streamlit. PawPal+ helps busy pet owners plan daily care tasks across multiple pets, prioritizing what matters most and explaining every scheduling decision.

## Features

- **Multi-pet support** — Manage multiple pets, each with their own task list and special needs
- **Smart scheduling** — Greedy algorithm sorts by scheduled time, then priority, fitting tasks into available minutes
- **Time-based sorting** — Tasks with a specific time (HH:MM) are ordered chronologically; unscheduled tasks go last
- **Priority system** — High/medium/low priority via enum; high-priority tasks always come first
- **Conflict detection** — Warns when two or more tasks are booked at the same time
- **Recurring tasks** — Daily and weekly tasks auto-generate their next occurrence when completed
- **Filtering** — Filter tasks by pet name, task type, or completion status
- **Transparent reasoning** — Every scheduled or skipped task includes an explanation of why
- **Data persistence** — Owner, pets, and tasks are saved to `data.json` and auto-loaded on startup
- **Visual UI** — Color-coded priorities (🔴 high, 🟡 medium, 🟢 low) and task-type emojis (🚶 walk, 🍽️ feeding, 💊 meds, ✂️ grooming, 🧸 enrichment)

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the app

```bash
streamlit run app.py
```

### Project structure

| File | Purpose |
|---|---|
| `pawpal_system.py` | Core logic — Task, Pet, Owner, Scheduler, ScheduledPlan |
| `app.py` | Streamlit UI wired to the logic layer |
| `main.py` | CLI demo script for verifying features |
| `tests/test_pawpal.py` | Automated test suite (27 tests) |
| `reflection.md` | Design decisions, tradeoffs, and project reflection |

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest tests/ -v
```

The suite includes 27 tests covering:

- **Task basics** — completion status, priority checks
- **Pet management** — adding tasks, summary output
- **Owner logic** — time fitting, filtering completed tasks
- **Scheduling** — priority ordering, time-based sorting, skipping overflows
- **Filtering** — by pet name and task type
- **Conflict detection** — same-time warnings, three-way conflicts
- **Recurring tasks** — daily, weekly, and one-time task behavior
- **Edge cases** — no pets, no tasks, zero available time, exact time fit, all tasks completed

**Confidence level: 4/5** — All happy paths and key edge cases are covered. The main gap is overlap-based conflict detection (we only check exact time matches, not overlapping durations).
