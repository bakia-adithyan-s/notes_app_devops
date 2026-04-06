from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from uuid import uuid4

from flask import Flask, abort, flash, redirect, render_template, request, url_for


app = Flask(__name__)
app.secret_key = "notes-reminders-secret-key"


@dataclass
class Note:
    id: str
    title: str
    content: str
    status: str
    reminder_at: Optional[str]
    created_at: str
    updated_at: str

    def to_context(self) -> dict:
        reminder_dt = None
        overdue = False

        if self.reminder_at:
            reminder_dt = datetime.fromisoformat(self.reminder_at)
            overdue = reminder_dt < datetime.now() and self.status != "completed"

        return {
            **asdict(self),
            "reminder_display": reminder_dt.strftime("%Y-%m-%d %H:%M") if reminder_dt else None,
            "created_display": datetime.fromisoformat(self.created_at).strftime("%Y-%m-%d %H:%M"),
            "updated_display": datetime.fromisoformat(self.updated_at).strftime("%Y-%m-%d %H:%M"),
            "is_overdue": overdue,
            "is_completed": self.status == "completed",
        }


notes: list[Note] = []


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_reminder(value: str | None) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M").isoformat(timespec="seconds")
    except ValueError:
        return None


@app.route("/", methods=["GET"])
def index():
    sorted_notes = sorted(notes, key=lambda note: note.updated_at, reverse=True)
    return render_template("index.html", notes=[note.to_context() for note in sorted_notes])


@app.route("/add", methods=["POST"])
def add_note():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    status = request.form.get("status", "pending")
    reminder_at = parse_reminder(request.form.get("reminder_at"))

    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("index"))

    timestamp = now_iso()
    notes.append(
        Note(
            id=str(uuid4()),
            title=title,
            content=content,
            status=status if status in {"pending", "completed"} else "pending",
            reminder_at=reminder_at,
            created_at=timestamp,
            updated_at=timestamp,
        )
    )
    flash("Note added.", "success")
    return redirect(url_for("index"))


@app.route("/edit/<note_id>", methods=["POST"])
def edit_note(note_id: str):
    note = next((item for item in notes if item.id == note_id), None)
    if note is None:
        abort(404)

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    status = request.form.get("status", "pending")
    reminder_at = parse_reminder(request.form.get("reminder_at"))

    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("index"))

    note.title = title
    note.content = content
    note.status = status if status in {"pending", "completed"} else "pending"
    note.reminder_at = reminder_at
    note.updated_at = now_iso()

    flash("Note updated.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<note_id>", methods=["POST"])
def delete_note(note_id: str):
    global notes
    before_count = len(notes)
    notes = [note for note in notes if note.id != note_id]
    if len(notes) == before_count:
        abort(404)

    flash("Note deleted.", "success")
    return redirect(url_for("index"))


@app.template_filter("datetime_label")
def datetime_label(value: Optional[str]) -> str:
    if not value:
        return "No reminder set"
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
