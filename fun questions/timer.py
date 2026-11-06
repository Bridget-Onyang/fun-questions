"""A countdown timer that stays on top of the screen and pops up big when time is up.

Usage:  python timer.py [time] [label]
        python timer.py 15              -> 15 seconds (demo)
        python timer.py 45:00           -> 45 minutes
        python timer.py 1:30:00 Contest -> 1 hour 30 minutes, with a label

It never takes keyboard focus, so typer.py can keep typing into the editor while it runs.
Drag it with the mouse to move it. Right-click it to close it.
"""
import ctypes
import sys
import time
import tkinter as tk
import winsound

user32 = ctypes.WinDLL("user32")


def parse(s):
    secs = 0
    for part in s.split(":"):
        secs = secs * 60 + int(part)
    return secs


def fmt(secs):
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"


def no_activate(win):
    # Never steal focus, so keystrokes keep going into the editor.
    hwnd = int(win.wm_frame(), 16)
    style = user32.GetWindowLongW(hwnd, -20)
    user32.SetWindowLongW(hwnd, -20, style | 0x08000000 | 0x80)   # WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW


def main():
    total = parse(sys.argv[1]) if len(sys.argv) > 1 else 15
    label = " ".join(sys.argv[2:]) or "Time left"
    end = time.time() + total

    root = tk.Tk()
    root.overrideredirect(True)            # no title bar
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.92)
    BG = "#1e1e1e"
    root.configure(bg=BG)
    title = tk.Label(root, text=label, bg=BG, fg="#aaaaaa", font=("Segoe UI", 10))
    title.pack(padx=14, pady=(8, 0))
    clock = tk.Label(root, text=fmt(total), bg=BG, fg="#4fc3f7", font=("Consolas", 28, "bold"))
    clock.pack(padx=14, pady=(0, 10))
    root.update_idletasks()
    root.geometry(f"+{root.winfo_screenwidth() - root.winfo_width() - 30}+30")   # top-right corner
    root.after(100, lambda: no_activate(root))

    # drag to move, right-click to close
    drag = {}
    def start(e): drag.update(x=e.x, y=e.y)
    def move(e): root.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")
    for w in (root, title, clock):
        w.bind("<Button-1>", start)
        w.bind("<B1-Motion>", move)
        w.bind("<Button-3>", lambda e: root.destroy())

    beeped = set()

    def times_up():
        clock.configure(text="00:00")
        pop = tk.Toplevel(root)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg="#c62828")
        tk.Label(pop, text="TIME'S UP!", bg="#c62828", fg="white",
                 font=("Segoe UI", 64, "bold")).pack(padx=60, pady=(40, 0))
        tk.Label(pop, text=label, bg="#c62828", fg="white", font=("Segoe UI", 18)).pack()
        tk.Label(pop, text="click to close", bg="#c62828", fg="#ffcdd2",
                 font=("Segoe UI", 12)).pack(pady=(10, 30))
        pop.update_idletasks()
        sw, sh = pop.winfo_screenwidth(), pop.winfo_screenheight()
        pop.geometry(f"+{(sw - pop.winfo_width()) // 2}+{(sh - pop.winfo_height()) // 2}")
        pop.after(50, lambda: no_activate(pop))
        for w in [pop] + pop.winfo_children():
            w.bind("<Button-1>", lambda e: root.destroy())

        flash = [0]
        def blink():
            if flash[0] < 20:
                c = "#c62828" if flash[0] % 2 else "#ff5252"
                pop.configure(bg=c)
                for w in pop.winfo_children():
                    w.configure(bg=c)
                flash[0] += 1
                pop.after(400, blink)
        blink()
        for _ in range(3):
            winsound.Beep(1000, 300)
            time.sleep(0.1)

    def tick():
        left = end - time.time()
        if left <= 0:
            times_up()
            return
        clock.configure(text=fmt(left + 0.999))
        # colour warnings: yellow in the last 25% (or last 5 min), red in the last 10 seconds
        if left <= 10:
            clock.configure(fg="#ff5252")
            s = int(left)
            if s not in beeped and s <= 5:      # short tick beeps for the last 5 seconds
                beeped.add(s)
                winsound.Beep(700, 80)
        elif left <= min(300, total * 0.25):
            clock.configure(fg="#ffd54f")
        root.after(200, tick)

    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
