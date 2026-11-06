"""Measures your typing speed on code, so typer.py can type a bit slower than you.

Usage:  python speedtest.py
Type each line shown, press Enter after each. Your result is saved to my_speed.json.
"""
import json
import os
import random
import time
import tkinter as tk

SAMPLES = [
    "The quick brown fox jumps over the lazy dog while the farmer watches from the porch, sipping his coffee slowly.",
    "Every morning I walk to the corner shop, buy a fresh loaf of bread, and chat with the old man who runs the place.",
    "My friend thinks he is the best at solving puzzles, but today I finished the hardest one before he even started.",
    "When the rain finally stopped, the kids ran outside to splash in the puddles and chase each other around the yard.",
    "Learning to code takes patience, practice, and a lot of coffee, but the feeling of seeing it work is worth it.",
    "The football match went into extra time, and the whole stadium held its breath as the striker stepped up to shoot.",
    "She packed her bags the night before the trip, double checking the tickets, the passport, and the phone charger.",
    "If you leave the window open during a storm, do not be surprised when your homework ends up soaking wet on the floor.",
    "We ordered two large pizzas, a bottle of soda, and some garlic bread, then argued about which movie to watch first.",
    "The old computer in the corner still works perfectly, even though it is slower than a snail climbing up a wall.",
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_speed.json")


def main():
    lines = random.sample(SAMPLES, 5)
    st = {"i": 0, "start": None, "typed": 0, "backspaces": 0, "time": 0.0}

    root = tk.Tk()
    root.title("Typing speed test")
    root.configure(bg="#1e1e1e", padx=20, pady=20)
    info = tk.Label(root, text="Type the line below exactly, then press Enter.", bg="#1e1e1e", fg="#aaaaaa",
                    font=("Segoe UI", 11))
    info.pack(anchor="w")
    target = tk.Label(root, text="", bg="#1e1e1e", fg="#4fc3f7", font=("Segoe UI", 16),
                      wraplength=900, justify="left")
    target.pack(anchor="w", pady=10)
    entry = tk.Entry(root, font=("Segoe UI", 14), width=95, bg="#2d2d2d", fg="white", insertbackground="white")
    entry.pack(anchor="w")
    result = tk.Label(root, text="", bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 12))
    result.pack(anchor="w", pady=10)

    def show():
        target.configure(text=lines[st["i"]])
        info.configure(text=f"Line {st['i'] + 1} of {len(lines)}: type it exactly, then press Enter.")
        entry.delete(0, "end")
        st["start"] = None

    def on_key(ev):
        if ev.keysym == "BackSpace":
            st["backspaces"] += 1
        if st["start"] is None and ev.char and ev.char.isprintable():
            st["start"] = time.time()   # timer starts at your first key, not when the line appears

    def on_enter(ev):
        line = lines[st["i"]]
        if entry.get() != line:
            info.configure(text="Not quite the same, fix it and press Enter again.")
            return
        if st["start"] is not None:
            st["time"] += time.time() - st["start"]
            st["typed"] += len(line)
        st["i"] += 1
        cpm = st["typed"] / max(st["time"], 0.001) * 60
        typo_rate = st["backspaces"] / max(1, st["typed"])
        with open(OUT, "w") as f:   # save after every sentence, so a partial run still counts
            json.dump({"cpm": round(cpm), "typo_rate": round(typo_rate, 4)}, f)
        if st["i"] < len(lines):
            show()
            return
        entry.configure(state="disabled")
        target.configure(text="")
        info.configure(text="Done!")
        result.configure(text=f"Your speed: {cpm:.0f} characters/min (about {cpm / 5:.0f} words/min)\n"
                              f"Backspaces: {st['backspaces']} over {st['typed']} characters\n"
                              f"typer.py will now type at {cpm * 0.9:.0f}/min (90% of you).")

    entry.bind("<Key>", on_key)
    entry.bind("<Return>", on_enter)
    show()
    entry.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
