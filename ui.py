"""
ui.py - a simple window for the fantasy draft helper.

Put this next to sleeper.py, DraftInfo.py, gemini.py and the data/ folder, then run:

    python ui.py

This file only handles the window. Draft data comes from SleeperData, your pick
slots come from DraftInfo, and the suggestions come from Gemini.
"""
import os
import queue
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# gemini.py opens "data/..." relative to the current folder, so run from this file's folder
HERE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir("data") and os.path.isdir(os.path.join(HERE, "data")):
    os.chdir(HERE)

from sleeper import SleeperData  # noqa: E402
from DraftInfo import DraftInfo  # noqa: E402
from gemini import Gemini  # noqa: E402

REFRESH_SECONDS = 5

BG = "#f4f5f7"
CARD = "#ffffff"
BORDER = "#e1e4e8"
TEXT = "#1f2328"
MUTED = "#6a737d"
GREEN = "#1a7f37"
GREEN_DARK = "#156a2e"
GREEN_LIGHT = "#e9f7ee"
AMBER = "#b35900"
RED = "#cf222e"


class DraftHelperUI:
    def __init__(self, root):
        self.root = root
        self.sleeper = None      # SleeperData, once connected
        self.draft_info = None   # DraftInfo, once connected
        self.gemini = None       # created on first use (it uploads the data files)
        self.gemini_lock = threading.Lock()
        self.results = queue.Queue()
        self.refresh_job = None
        self.refreshing = False
        self.thinking = False
        self.was_my_turn = False
        self.draft_over = False
        self.shown_pick_count = -1

        self.setup_style()
        self.build_header()
        self.build_banner()
        self.build_footer()
        self.build_main()
        self.root.after(100, self.check_results)

    # ------------------------------------------------------------------ layout
    def setup_style(self):
        self.root.title("Draft Helper")
        self.root.geometry("1100x720")
        self.root.minsize(940, 600)
        self.root.configure(bg=BG)

        families = tkfont.families(self.root)
        family = next((f for f in ("Segoe UI", "Helvetica Neue", "Inter", "DejaVu Sans") if f in families), "Arial")
        self.font = (family, 10)
        self.font_bold = (family, 10, "bold")
        self.font_small = (family, 9)
        self.font_title = (family, 15, "bold")
        self.font_headline = (family, 18, "bold")
        self.font_answer = (family, 11)
        self.font_answer_bold = (family, 11, "bold")
        scale = self.root.winfo_fpixels("1i") / 96  # bigger table rows on high-DPI screens

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=self.font)
        style.configure("TButton", background=CARD, bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD,
                        padding=(14, 6), relief="flat")
        style.map("TButton", background=[("disabled", BG), ("active", "#eef0f2")],
                  foreground=[("disabled", MUTED)])
        style.configure("Accent.TButton", background=GREEN, foreground="white", bordercolor=GREEN,
                        lightcolor=GREEN, darkcolor=GREEN, font=self.font_bold)
        accent_states = [("disabled", "#8cc59d"), ("active", GREEN_DARK)]
        style.map("Accent.TButton", background=accent_states, lightcolor=accent_states,
                  darkcolor=accent_states, bordercolor=accent_states, foreground=[("disabled", "white")])
        style.configure("TEntry", fieldbackground=CARD, bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD, padding=6)
        style.map("TEntry", bordercolor=[("focus", GREEN)], lightcolor=[("focus", GREEN)])
        style.configure("TCheckbutton", background=BG, foreground=MUTED, font=self.font_small,
                        indicatorforeground=GREEN)
        style.map("TCheckbutton", background=[("active", BG)])
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, borderwidth=0,
                        bordercolor=CARD, lightcolor=CARD, darkcolor=CARD, rowheight=int(26 * scale))
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Treeview.Heading", background=CARD, foreground=MUTED, font=self.font_small,
                        relief="flat", bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD)
        style.map("Treeview.Heading", background=[("active", CARD)])
        style.map("Treeview", background=[("selected", CARD)], foreground=[("selected", TEXT)])
        style.layout("Vertical.TScrollbar", [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        style.configure("Vertical.TScrollbar", background="#d0d4d9", troughcolor=CARD, bordercolor=CARD,
                        lightcolor="#d0d4d9", darkcolor="#d0d4d9", gripcount=0)

    def build_header(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(16, 12))
        tk.Label(header, text="Draft Helper", font=self.font_title, bg=BG, fg=TEXT).pack(side="left")

        # packed right-to-left: [Sleeper username ___] [Draft ID ___] [Connect]
        self.connect_button = ttk.Button(header, text="Connect", style="Accent.TButton", command=self.connect)
        self.connect_button.pack(side="right")
        self.draft_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.add_field(header, "Draft ID or link", self.draft_var, 21)
        self.add_field(header, "Sleeper username", self.username_var, 15)

    def add_field(self, parent, label, variable, width):
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.pack(side="right", padx=(0, 14))
        entry.bind("<Return>", lambda event: self.connect())
        tk.Label(parent, text=label, font=self.font_small, bg=BG, fg=MUTED).pack(side="right", padx=(0, 6))

    def build_banner(self):
        self.banner = tk.Frame(self.root, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        self.banner.pack(fill="x", padx=20, pady=(0, 12))
        self.headline = tk.Label(self.banner, font=self.font_headline, bg=CARD, anchor="w")
        self.headline.pack(fill="x", padx=18, pady=(12, 0))
        self.details = tk.Label(self.banner, font=self.font, bg=CARD, fg=MUTED, anchor="w")
        self.details.pack(fill="x", padx=18, pady=(2, 12))
        self.set_banner("Not connected", "Enter your draft ID above and press Connect.")

    def build_footer(self):
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(side="bottom", fill="x", padx=20, pady=(0, 14))
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.auto_suggest_var = tk.BooleanVar(value=False)
        ttk.Button(footer, text="Refresh", command=self.refresh).pack(side="right")
        ttk.Checkbutton(footer, text="Auto-suggest on my turn",
                        variable=self.auto_suggest_var).pack(side="right", padx=(0, 18))
        ttk.Checkbutton(footer, text=f"Auto-refresh every {REFRESH_SECONDS}s",
                        variable=self.auto_refresh_var).pack(side="right", padx=(0, 18))
        self.status = tk.Label(footer, font=self.font_small, bg=BG, fg=MUTED, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)

    def build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, minsize=330)
        main.rowconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # AI suggestion: left column, full height
        card, body, _ = self.card(main, "AI suggestion")
        card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        ask_row = tk.Frame(body, bg=CARD)
        ask_row.pack(fill="x")
        self.prompt_var = tk.StringVar()
        prompt = ttk.Entry(ask_row, textvariable=self.prompt_var)
        prompt.pack(side="left", fill="x", expand=True)
        prompt.bind("<Return>", lambda event: self.suggest())
        self.suggest_button = ttk.Button(ask_row, text="Suggest pick", style="Accent.TButton", command=self.suggest)
        self.suggest_button.pack(side="left", padx=(8, 0))
        tk.Label(body, text="Optional: anything Gemini should consider, like \"PPR league\" or \"I need a WR\".",
                 font=self.font_small, bg=CARD, fg=MUTED).pack(anchor="w", pady=(5, 10))

        text_frame = tk.Frame(body, bg=CARD)
        text_frame.pack(fill="both", expand=True)
        self.answer = tk.Text(text_frame, wrap="word", font=self.font_answer, bg=CARD, fg=TEXT, relief="flat",
                              highlightthickness=0, padx=2, pady=4, spacing1=2, spacing3=4, cursor="arrow",
                              width=40, height=10)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.answer.yview)

        def show_scrollbar_if_needed(first, last):
            if float(first) <= 0 and float(last) >= 1:
                scrollbar.pack_forget()
            elif not scrollbar.winfo_ismapped():
                scrollbar.pack(side="right", fill="y", before=self.answer)
            scrollbar.set(first, last)

        self.answer.configure(yscrollcommand=show_scrollbar_if_needed)
        self.answer.pack(side="left", fill="both", expand=True)
        self.answer.tag_configure("bold", font=self.font_answer_bold)
        self.answer.tag_configure("muted", foreground=MUTED)
        self.answer.tag_configure("error", foreground=RED)
        self.answer.tag_configure("bullet", lmargin1=10, lmargin2=27)
        self.answer.tag_configure("subbullet", lmargin1=32, lmargin2=49)
        self.show_message("Connect to your draft, then press Suggest pick.", "muted")

        # My team: top of the right column
        card, body, self.team_title = self.card(main, "My team")
        card.grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        self.team_table = self.make_table(body, [("pos", "POS", 50), ("player", "PLAYER", 180), ("team", "TEAM", 55)])

        # Recent picks: bottom of the right column
        card, body, _ = self.card(main, "Recent picks")
        card.grid(row=1, column=1, sticky="nsew")
        self.picks_table = self.make_table(body, [("pick", "#", 40), ("player", "PLAYER", 160),
                                                  ("pos", "POS", 45), ("team", "TEAM", 45)])
        self.picks_table.tag_configure("mine", background=GREEN_LIGHT, font=self.font_bold)

    def card(self, parent, title):
        frame = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        title_label = tk.Label(frame, text=title, font=self.font_bold, bg=CARD, fg=TEXT)
        title_label.pack(anchor="w", padx=16, pady=(12, 8))
        body = tk.Frame(frame, bg=CARD)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return frame, body, title_label

    def make_table(self, parent, columns):
        table = ttk.Treeview(parent, columns=[key for key, _, _ in columns], show="headings",
                             selectmode="none", height=5)
        for key, heading, width in columns:
            table.heading(key, text=heading, anchor="w")
            table.column(key, width=width, minwidth=width, anchor="w", stretch=(key == "player"))
        table.pack(fill="both", expand=True)
        return table

    # ------------------------------------------------------------------ small helpers
    def set_status(self, text, color=MUTED):
        self.status.config(text=text, fg=color)

    def set_banner(self, headline, details, color=TEXT, background=CARD):
        for widget in (self.banner, self.headline, self.details):
            widget.config(bg=background)
        self.headline.config(text=headline, fg=color)
        self.details.config(text=details)

    def fill_table(self, table, rows, tags=None):
        table.delete(*table.get_children())
        for i, row in enumerate(rows):
            table.insert("", "end", values=row, tags=tags[i] if tags else ())

    def show_message(self, text, tag):
        self.answer.config(state="normal")
        self.answer.delete("1.0", "end")
        self.answer.insert("end", text, tag)
        self.answer.config(state="disabled")

    def show_answer(self, text, pick):
        """Show Gemini's reply, turning its markdown (**bold**, * bullets, # headings) into plain formatting."""
        box = self.answer
        box.config(state="normal")
        box.delete("1.0", "end")
        box.insert("end", f"Suggestion for pick {pick}  ·  {time.strftime('%I:%M %p').lstrip('0')}\n\n", "muted")
        for line in text.strip().splitlines():
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            tags = ()
            if stripped.startswith("#"):
                stripped = "**" + stripped.lstrip("#").strip() + "**"
            elif stripped[:2] in ("* ", "- "):
                tags = ("subbullet",) if indent >= 2 else ("bullet",)
                stripped = "•  " + stripped[2:].strip()
            for i, part in enumerate(stripped.split("**")):  # every other piece sits between ** marks
                box.insert("end", part, tags + (("bold",) if i % 2 else ()))
            box.insert("end", "\n", tags)
        box.config(state="disabled")
        box.see("1.0")

    # ------------------------------------------------------------------ background work
    # Sleeper and Gemini calls take a moment, so they run on a separate thread and hand
    # their result back through a queue. Tkinter widgets are only touched on the main thread.
    def run_in_background(self, work, when_done):
        def worker():
            try:
                result = work()
            except Exception as error:
                result = error
            self.results.put((when_done, result))
        threading.Thread(target=worker, daemon=True).start()

    def check_results(self):
        while not self.results.empty():
            when_done, result = self.results.get()
            when_done(result)
        self.root.after(100, self.check_results)

    def get_latest(self, sleeper, draft_info):
        """Background thread: fetch the newest picks and update DraftInfo."""
        drafted = sleeper.getDraftedPlayers()
        draft_info.setCurrentPickNumber(sleeper.getPickNumber())
        draft_info.setCurrentRound(sleeper.getCurrentRound())
        draft_info.determineDraftStatus()
        return {"drafted": drafted,
                "pick": draft_info.getCurrentPickNumber(),
                "round": draft_info.getCurrentRound(),
                "my_turn": draft_info.getUserCanDraft(),
                "status": sleeper.getDraftData().get("status", "drafting")}

    def get_gemini(self):
        with self.gemini_lock:
            if self.gemini is None:
                for path in ("data/football.csv", "data/updated_current_player_info.txt"):
                    if not os.path.exists(path):
                        raise FileNotFoundError(f"Gemini needs {path}, but it isn't in {os.getcwd()}")
                self.gemini = Gemini()
            return self.gemini

    # ------------------------------------------------------------------ connecting
    def connect(self):
        draft_id = self.draft_var.get().strip().rstrip("/").split("/")[-1]  # also accepts a pasted link
        username = self.username_var.get().strip()
        if not username or not draft_id:
            self.set_status("Enter your Sleeper username and draft ID first.", RED)
            return
        self.connect_button.config(state="disabled")
        self.set_status("Connecting…")
        self.run_in_background(lambda: self.load_draft(username, draft_id), self.on_connected)

    def load_draft(self, username, draft_id):
        """Background thread: set up SleeperData and DraftInfo for this draft."""
        sleeper = SleeperData(username, "", draft_id)
        # check the IDs first so a typo gets a clear message instead of a KeyError
        draft = sleeper.getDraftData()
        if not draft:
            raise ValueError("Sleeper couldn't find that draft. Check the draft ID.")
        if not draft.get("draft_order"):
            raise ValueError("The draft order hasn't been set on Sleeper yet.")
        user = sleeper.getUserData()
        if not user:
            raise ValueError(f"Sleeper couldn't find the username \"{username}\".")
        if user["user_id"] not in draft["draft_order"]:
            raise ValueError(f"{username} isn't in this draft.")
        if draft.get("league_id"):
            sleeper.setLeagueId(draft["league_id"])  # the draft knows which league it belongs to
        roster_positions = sleeper.getRosterPositions() if sleeper.getLeagueId() else []  # mock drafts have none

        draft_info = DraftInfo(roster_positions=roster_positions,
                               users_draft_order=sleeper.getDraftOrder(),
                               rounds=sleeper.getRounds(),
                               teams=sleeper.getTeams())
        draft_info.determineUsersDraftSlots()
        return sleeper, draft_info, self.get_latest(sleeper, draft_info)

    def on_connected(self, result):
        self.connect_button.config(state="normal")
        if isinstance(result, Exception):
            if self.sleeper is None:
                self.set_banner("Couldn't connect", str(result), RED)
                self.set_status("")
            else:  # keep following the draft you were already connected to
                self.set_status(f"Couldn't connect: {result}", RED)
            return
        self.sleeper, self.draft_info, latest = result
        self.draft_var.set(self.sleeper.getDraftId())
        self.was_my_turn = False
        self.shown_pick_count = -1
        self.show_draft(latest)
        self.schedule_refresh()
        if self.gemini is None:  # load the AI data files now so the first suggestion is quicker
            self.run_in_background(self.get_gemini, self.on_gemini_loaded)

    def on_gemini_loaded(self, result):
        if isinstance(result, Exception) and not self.thinking:
            self.show_message(f"Couldn't start Gemini: {result}", "error")

    # ------------------------------------------------------------------ refreshing
    def schedule_refresh(self):
        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
            self.refresh_job = None
        if self.sleeper and not self.draft_over:
            self.refresh_job = self.root.after(REFRESH_SECONDS * 1000, self.auto_refresh)

    def auto_refresh(self):
        self.refresh_job = None
        if self.auto_refresh_var.get():
            self.refresh()
        else:
            self.schedule_refresh()

    def refresh(self):
        if self.sleeper is None or self.refreshing:
            return
        self.refreshing = True
        sleeper, draft_info = self.sleeper, self.draft_info
        self.run_in_background(lambda: self.get_latest(sleeper, draft_info),
                               lambda result: self.on_refreshed(result, sleeper))

    def on_refreshed(self, result, sleeper):
        self.refreshing = False
        if sleeper is self.sleeper:  # ignore it if you connected to a different draft meanwhile
            if isinstance(result, Exception):
                self.set_status(f"Refresh failed: {result}. Trying again…", RED)
            else:
                self.show_draft(result)
        self.schedule_refresh()

    def show_draft(self, latest):
        pick, status, drafted = latest["pick"], latest["status"], latest["drafted"]
        my_turn = latest["my_turn"] and status not in ("pre_draft", "complete")
        upcoming = [slot for slot in self.draft_info.getUsersDraftSlots() if slot >= pick]
        rounds = self.draft_info.getRounds()
        where = f"Round {min(latest['round'], rounds)} of {rounds}  ·  Pick {pick}"
        self.draft_over = status == "complete"

        if status == "complete":
            self.set_banner("Draft complete", "Good luck this season!")
        elif status == "pre_draft":
            self.set_banner("Waiting for the draft to start",
                            f"Your first pick is #{upcoming[0]}." if upcoming else "")
        elif my_turn:
            self.set_banner("You're on the clock", where, GREEN, GREEN_LIGHT)
        elif upcoming:
            away = upcoming[0] - pick
            self.set_banner(f"You're up in {away} pick{'s' if away != 1 else ''}",
                            f"{where}  ·  Your next pick is #{upcoming[0]}", AMBER if away <= 2 else TEXT)
        else:
            self.set_banner("All your picks are in", where)

        if len(drafted) != self.shown_pick_count:  # only redraw the tables when a pick was made
            self.shown_pick_count = len(drafted)
            mine = [p for p in drafted if p["is_mine"]]
            self.fill_table(self.team_table, [(p["position"], p["name"], p["team"]) for p in mine])
            roster_size = len(self.draft_info.getRosterPositions() or [])
            self.team_title.config(text=f"My team  ({len(mine)}/{roster_size})" if roster_size else "My team")
            newest_first = list(reversed(drafted))
            self.fill_table(self.picks_table,
                            [(p["pick_no"], p["name"], p["position"], p["team"]) for p in newest_first],
                            [("mine",) if p["is_mine"] else () for p in newest_first])

        self.set_status(f"Updated {time.strftime('%I:%M:%S %p').lstrip('0')}  ·  {len(drafted)} picks made")
        if my_turn and not self.was_my_turn:
            self.root.bell()
            if self.auto_suggest_var.get():
                self.suggest()
        self.was_my_turn = my_turn

    # ------------------------------------------------------------------ suggestions
    def suggest(self):
        if self.sleeper is None:
            self.set_status("Connect to a draft first.", RED)
            return
        if self.thinking:
            return
        self.thinking = True
        self.suggest_button.config(state="disabled", text="Thinking…")
        self.show_message("Checking the latest picks and asking Gemini…", "muted")
        prompt = self.prompt_var.get().strip()
        sleeper, draft_info = self.sleeper, self.draft_info
        self.run_in_background(lambda: self.ask_gemini(sleeper, draft_info, prompt), self.on_suggestion)

    def ask_gemini(self, sleeper, draft_info, prompt):
        """Background thread: get the newest picks, then ask Gemini."""
        drafted = sleeper.getDraftedPlayers()  # fresh, so Gemini never suggests someone just taken
        pick = sleeper.getPickNumber()
        answer = self.get_gemini().suggest_pick(user_prompt=prompt, drafted_players=drafted,
                                                roster_positions=draft_info.getRosterPositions())
        return pick, answer or ""

    def on_suggestion(self, result):
        self.thinking = False
        self.suggest_button.config(state="normal", text="Suggest pick")
        if isinstance(result, Exception):
            self.show_message(f"Something went wrong: {result}", "error")
        else:
            pick, text = result
            if text.strip():
                self.show_answer(text, pick)
            else:
                self.show_message("Gemini didn't send back any text.", "error")


def main():
    try:  # sharper text on Windows screens that use display scaling
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    DraftHelperUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
