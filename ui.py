"""
ui.py - basic Tkinter front-end for the Fantasy Draft Helper.

Run it from the project folder (driver.py uploads football.csv and
updated_current_player_info.txt relative to the working directory):

    python ui.py

It reuses the `sleeper` and `gemini` objects created in driver.py, polls Sleeper
in the background, and only calls Gemini when you press the button.
Don't run driver.py's main() at the same time - this replaces its loop.
"""

import contextlib
import io
import queue
import re
import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

POLL_SECONDS = 3          # how often to check Sleeper for new picks
REQUIRE_MY_TURN = True    # False = allow suggestions any time the draft is live
ROUND_NOTE_SECONDS = 6    # how long the "Round updated" note stays visible

BADGE_COLORS = {
    "idle": "#6b7280",
    "waiting": "#b45309",
    "ready": "#15803d",
    "busy": "#1d4ed8",
    "error": "#b91c1c",
}


def slot_for_pick(draft, pick_no):
    """Draft slot that is on the clock for an overall pick number (1-based)."""
    settings = draft.get("settings") or {}
    teams = settings["teams"]
    rnd = (pick_no - 1) // teams + 1
    pos = (pick_no - 1) % teams + 1

    if draft.get("type") == "snake":
        reversal = settings.get("reversal_round") or 0
        # third-round reversal: from that round on, direction flips one round earlier
        effective = rnd - 1 if reversal and rnd >= reversal else rnd
        if effective % 2 == 0:
            return teams - pos + 1
    return pos


class DraftApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fantasy Draft Helper")
        self.minsize(600, 560)

        self.sleeper = None
        self.gemini = None
        self.events = queue.Queue()
        self.stop = threading.Event()

        self.state_kind = "idle"
        self.headline = "Starting up..."
        self.detail = "Connecting to Sleeper and Gemini"
        self.drafting = False   # draft is live
        self.ready = False      # it's the user's pick
        self.busy = False       # waiting on Gemini
        self.round_no = None
        self.round_note_job = None

        self._build()
        self._render()
        self.protocol("WM_DELETE_WINDOW", self._close)

        threading.Thread(target=self._boot, daemon=True).start()
        self.after(100, self._pump)

    # ---------- layout ----------
    def _build(self):
        header = ttk.Frame(self, padding=(16, 14, 16, 4))
        header.pack(fill="x")
        self.round_var = tk.StringVar(value="Round -")
        ttk.Label(header, textvariable=self.round_var,
                  font=("Helvetica", 28, "bold")).pack(side="left")
        self.note_var = tk.StringVar()
        ttk.Label(header, textvariable=self.note_var, foreground="#1d4ed8",
                  font=("Helvetica", 11, "bold")).pack(side="left", padx=12)
        self.badge = tk.Label(header, font=("Helvetica", 11, "bold"),
                              fg="white", padx=12, pady=4)
        self.badge.pack(side="right")

        info = ttk.Frame(self, padding=(16, 0, 16, 10))
        info.pack(fill="x")
        self.detail_var = tk.StringVar()
        ttk.Label(info, textvariable=self.detail_var).pack(side="left")
        self.sync_var = tk.StringVar(value="Not synced yet")
        ttk.Label(info, textvariable=self.sync_var,
                  foreground="#6b7280").pack(side="right")

        ttk.Separator(self).pack(fill="x")

        controls = ttk.Frame(self, padding=16)
        controls.pack(fill="x")
        ttk.Label(controls, text="Extra instructions (optional):").pack(side="left")
        self.extra = ttk.Entry(controls)
        self.extra.pack(side="left", fill="x", expand=True, padx=8)
        self.extra.bind("<Return>", lambda _e: self._on_suggest())
        self.button = ttk.Button(controls, text="Get Suggestion",
                                 command=self._on_suggest)
        self.button.pack(side="right")

        self.output = ScrolledText(self, wrap="word", font=("Helvetica", 12),
                                   padx=14, pady=12, borderwidth=0,
                                   relief="flat", spacing1=2, spacing3=2)
        self.output.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        o = self.output
        o.tag_configure("title", font=("Helvetica", 14, "bold"),
                        foreground="#1d4ed8", spacing3=8)
        o.tag_configure("h", font=("Helvetica", 13, "bold"), spacing1=10)
        o.tag_configure("bold", font=("Helvetica", 12, "bold"))
        o.tag_configure("item1", lmargin1=14, lmargin2=30)
        o.tag_configure("item2", lmargin1=36, lmargin2=52)
        o.tag_configure("muted", foreground="#6b7280")
        o.tag_configure("error", foreground="#b91c1c")

        o.insert("end", "Suggestions will show up here.", "muted")
        o.configure(state="disabled")

    # ---------- background work ----------
    def _boot(self):
        try:
            import driver  # creates the Sleeper and Gemini objects (uploads data files)
            self.sleeper, self.gemini = driver.sleeper, driver.gemini
        except Exception as exc:
            self.events.put(("fatal", f"Startup failed: {exc}"))
            return
        self.events.put(("booted",))
        self._poll_loop()

    def _poll_loop(self):
        while not self.stop.is_set():
            try:
                draft = self.sleeper.getDraftData()
                picks = self.sleeper.getDraftPicks()
                self.events.put(("state", draft, picks))
            except Exception as exc:
                self.events.put(("poll_error", str(exc)))
            self.stop.wait(POLL_SECONDS)

    def _suggest_worker(self, user_prompt):
        try:
            draft = self.sleeper.getDraftData()
            picks = self.sleeper.getDraftPicks()
            drafted = self.sleeper.getDraftedPlayers(picks)
            # The drafted-player blacklist replaces the raw pick dump in the context.
            context = (str(self.sleeper.getUserData())
                       + str(self.sleeper.getLeagueData())
                       + str(draft))

            teams = draft["settings"]["teams"]
            made = len(picks)
            label = f"Suggestion for pick #{made + 1} (round {made // teams + 1})"

            # suggest_pick currently prints instead of returning; capture the print
            # as a fallback so this works without touching gemini.py.
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                result = self.gemini.suggest_pick(
                    context, user_prompt=user_prompt, drafted_players=drafted)
            text = result if isinstance(result, str) and result else buf.getvalue()
            self.events.put(("suggestion", label, text.strip()))
        except Exception as exc:
            self.events.put(("suggestion_error", str(exc)))

    # ---------- main-thread event handling ----------
    def _pump(self):
        try:
            while True:
                event = self.events.get_nowait()
                try:
                    self._handle(event)
                except Exception as exc:
                    self._set_state("error", "UI error", str(exc))
        except queue.Empty:
            pass
        self.after(100, self._pump)

    def _handle(self, event):
        kind = event[0]
        if kind == "booted":
            self._set_state("idle", "Connected", "Waiting for the first update from Sleeper")
        elif kind == "state":
            self._on_state(event[1], event[2])
        elif kind == "poll_error":
            self.drafting = self.ready = False
            self._set_state("error", "Can't reach Sleeper", event[1])
        elif kind == "fatal":
            self.drafting = self.ready = False
            self._set_state("error", "Startup failed", event[1])
            self._show_error(event[1])
        elif kind == "suggestion":
            self.busy = False
            self._show_suggestion(event[1], event[2])
            self._render()
        elif kind == "suggestion_error":
            self.busy = False
            self._show_error(event[1])
            self._render()

    def _on_state(self, draft, picks):
        self.sync_var.set(time.strftime("Last synced %H:%M:%S"))
        settings = draft.get("settings") or {}
        teams, rounds = settings["teams"], settings["rounds"]
        total = teams * rounds
        made = len(picks)
        status = draft.get("status", "")

        if status == "pre_draft":
            self.drafting = self.ready = False
            self.round_var.set("Round -")
            self._set_state("idle", "Draft hasn't started", "Waiting for the draft to begin")
            return
        if status == "complete" or made >= total:
            self.drafting = self.ready = False
            self.round_var.set("Draft complete")
            self._set_state("idle", "Draft complete", f"{made} picks made")
            return

        next_pick = made + 1
        rnd = (next_pick - 1) // teams + 1
        self.round_var.set(f"Round {rnd}")
        if self.round_no is not None and rnd != self.round_no:
            self._flash_round_note()
        self.round_no = rnd
        self.drafting = True

        my_slot = self.sleeper.getDraftOrder()
        away = next((p - next_pick for p in range(next_pick, total + 1)
                     if slot_for_pick(draft, p) == my_slot), None)
        self.ready = away == 0

        if away is None:
            self._set_state("idle", "No picks left", "You've made your last pick")
        elif away == 0:
            self._set_state("ready", "Your pick is up - ready",
                            f"Pick #{next_pick} (round {rnd}). Press Get Suggestion.")
        else:
            plural = "" if away == 1 else "s"
            self._set_state("waiting", "Waiting for your turn",
                            f"You pick in {away} pick{plural} (pick #{next_pick + away})")

    def _flash_round_note(self):
        self.note_var.set("Round updated")
        if self.round_note_job:
            self.after_cancel(self.round_note_job)
        self.round_note_job = self.after(ROUND_NOTE_SECONDS * 1000,
                                         lambda: self.note_var.set(""))

    # ---------- state -> widgets ----------
    def _set_state(self, kind, headline, detail=""):
        self.state_kind, self.headline, self.detail = kind, headline, detail
        self._render()

    def _render(self):
        if self.busy:
            kind, headline = "busy", "Getting suggestion..."
            detail = "Asking Gemini, this can take a few seconds"
        else:
            kind, headline, detail = self.state_kind, self.headline, self.detail

        self.badge.config(text=headline, bg=BADGE_COLORS[kind])
        self.detail_var.set(detail)

        can_ask = self.drafting and not self.busy and (self.ready or not REQUIRE_MY_TURN)
        self.button.state(["!disabled"] if can_ask else ["disabled"])

    def _on_suggest(self):
        if self.busy or self.button.instate(["disabled"]):
            return
        self.busy = True
        self._render()
        extra = self.extra.get().strip() or None
        threading.Thread(target=self._suggest_worker, args=(extra,), daemon=True).start()

    # ---------- output pane ----------
    def _show_suggestion(self, label, text):
        o = self.output
        o.configure(state="normal")
        o.delete("1.0", "end")
        o.insert("end", label + "\n", "title")
        self._insert_markdown(text or "(Gemini returned an empty response)")
        o.configure(state="disabled")
        o.see("1.0")

    def _show_error(self, message):
        o = self.output
        o.configure(state="normal")
        o.delete("1.0", "end")
        o.insert("end", "Something went wrong\n", ("title", "error"))
        o.insert("end", message, "error")
        o.configure(state="disabled")

    def _insert_markdown(self, text):
        """Tiny markdown renderer: headings, bullets, **bold**."""
        o = self.output
        for raw in text.splitlines():
            line = raw.rstrip()
            stripped = line.lstrip()

            if stripped.startswith("#"):
                o.insert("end", stripped.lstrip("#").strip() + "\n", "h")
                continue

            tag = None
            bullet = re.match(r"^(\s*)[*\-\u2022]\s+(.*)", line)
            if bullet:
                tag = "item2" if len(bullet.group(1)) >= 2 else "item1"
                o.insert("end", "\u2022 ", tag)
                line = bullet.group(2)

            base = (tag,) if tag else ()
            for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", line)):
                o.insert("end", part, base + ("bold",) if i % 2 else base)
            o.insert("end", "\n")

    def _close(self):
        self.stop.set()
        self.destroy()


if __name__ == "__main__":
    DraftApp().mainloop()
