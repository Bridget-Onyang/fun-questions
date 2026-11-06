"""Types a file into Notepad at a human-ish pace while a big on-screen keyboard lights up each key.

Usage:  python typer.py [file] [chars_per_minute]
        python typer.py solution.py 400
If you leave out the speed and have run speedtest.py, it types at 90% of your measured speed.

1. Open Notepad and turn OFF word wrap (View > Word wrap, or Format > Word Wrap),
   because the script uses the Up arrow to go back and fix earlier lines.
2. Run this. A keyboard window appears at the bottom of the screen.
3. You get 5 seconds to click into Notepad. Then it types.
Hold ESC to stop at any time. Windows only, no extra packages needed.
"""
import ctypes
import json
import os
import queue
import random
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x2
KEYEVENTF_UNICODE = 0x4
VK_RETURN, VK_BACK, VK_ESCAPE = 0x0D, 0x08, 0x1B


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def _send(vk, scan, flags):
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_char(ch):
    if ch == "\n":
        _send(VK_RETURN, 0, 0); _send(VK_RETURN, 0, KEYEVENTF_KEYUP)
    else:
        _send(0, ord(ch), KEYEVENTF_UNICODE); _send(0, ord(ch), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)


def send_vk(vk, ctrl=False, shift=False):
    # Arrows/Home/End/Delete must be sent as "extended" keys, or Num Lock can turn them into digits.
    ext = 0x1 if vk in (0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2E) else 0
    mods = ([VK["Ctrl"]] if ctrl else []) + ([0x10] if shift else [])
    for m in mods:
        _send(m, 0, 0)
    _send(vk, 0, ext); _send(vk, 0, ext | KEYEVENTF_KEYUP)
    for m in reversed(mods):
        _send(m, 0, KEYEVENTF_KEYUP)


def esc_held():
    return user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000


# ---------------- on-screen keyboard ----------------

ROWS = [
    ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
    ["Tab", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\"],
    ["Caps", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "Enter"],
    ["LShift", "z", "x", "c", "v", "b", "n", "m", ",", ".", "/", "RShift"],
    ["Ctrl", "Space", "End", "Left", "Up", "Down", "Right"],
]
WIDE = {"Backspace": 2, "Tab": 1.5, "\\": 1.5, "Caps": 1.8, "Enter": 2.2, "LShift": 2.4, "RShift": 2.6,
        "Ctrl": 1.6, "Space": 7, "End": 1.4}
ARROWS = {"Left": "←", "Up": "↑", "Down": "↓", "Right": "→"}
VK = {"Backspace": 0x08, "Ctrl": 0x11, "End": 0x23, "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
      "Esc": 0x1B, "Home": 0x24, "Delete": 0x2E}
SHIFTED = dict(zip('~!@#$%^&*()_+{}|:"<>?', "`1234567890-=[]\\;',./"))


def keys_for(ch):
    """Which on-screen keys to light up for a character: (key, needs_shift)."""
    if ch == "\n":
        return "Enter", False
    if ch == " ":
        return "Space", False
    if ch.isalpha() and ch.isupper():
        return ch.lower(), True
    if ch in SHIFTED:
        return SHIFTED[ch], True
    return ch, False


class Keyboard:
    BG, KEY, LIT, TXT = "#1e1e1e", "#3a3a3a", "#4fc3f7", "#ffffff"

    def __init__(self, root):
        self.root = root
        self.labels = {}
        root.title("Keyboard")
        root.configure(bg=self.BG)
        root.attributes("-topmost", True)
        self.status = tk.Label(root, text="", bg=self.BG, fg="#aaaaaa", font=("Segoe UI", 11))
        self.status.pack(pady=(6, 0))
        unit = 46
        for row in ROWS:
            fr = tk.Frame(root, bg=self.BG)
            fr.pack(pady=3)
            for k in row:
                text = {"LShift": "Shift", "RShift": "Shift", **ARROWS}.get(k, k)
                w = int(unit * WIDE.get(k, 1))
                cell = tk.Frame(fr, width=w, height=unit, bg=self.BG)
                cell.pack_propagate(False)
                cell.pack(side="left", padx=3)
                lab = tk.Label(cell, text=text, bg=self.KEY, fg=self.TXT, font=("Segoe UI", 12, "bold"))
                lab.pack(fill="both", expand=True)
                self.labels[k] = lab
        root.update_idletasks()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = root.winfo_width(), root.winfo_height()
        root.geometry(f"+{(sw - w) // 2}+{sh - h - 80}")

    def no_activate(self):
        # Make the window never take keyboard focus, so typing keeps going into Notepad.
        hwnd = int(self.root.wm_frame(), 16)
        GWL_EXSTYLE, WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW = -20, 0x08000000, 0x80
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)

    def light(self, key, on):
        lab = self.labels.get(key)
        if lab:
            lab.configure(bg=self.LIT if on else self.KEY, fg="#000000" if on else self.TXT)


# ---------------- typing worker ----------------

def typer(text, cpm, events, typo=0.012, insert=False):
    # insert=True: type the text into the middle of existing code (no pasting, nothing deleted after it).
    base = 60.0 / cpm
    # At high speeds, shrink the key-hold time and the "thinking" pauses so the speed is actually reached.
    pf = min(1.0, base / 0.2)                       # pause factor: 1 at normal speeds, small when very fast
    hold_lo, hold_hi = (0.04, 0.09) if base > 0.15 else (base * 0.3, base * 0.4)
    for s in range(10, 0, -1):
        events.put(("status", f"Click into Notepad now! Starting in {s}...   (hold ESC to stop)"))
        time.sleep(1)
    events.put(("status", f"Typing {len(text)} characters...   (hold ESC to stop)"))

    class Stop(Exception):
        pass

    def lit(keys):
        for k in keys:
            events.put(("on", k))
        time.sleep(random.uniform(hold_lo, hold_hi))   # keep the keys lit briefly
        for k in keys:
            events.put(("off", k))

    def press(ch):
        if esc_held():
            raise Stop
        key, shift = keys_for(ch)
        if shift:
            events.put(("on", "LShift"))
        events.put(("on", key))
        send_char(ch)
        time.sleep(random.uniform(hold_lo, hold_hi))
        events.put(("off", key))
        if shift:
            events.put(("off", "LShift"))

    def press_key(name, ctrl=False, shift=False):
        if esc_held():
            raise Stop
        send_vk(VK[name], ctrl, shift)
        lit((["Ctrl"] if ctrl else []) + (["LShift"] if shift else []) + [name])

    def close_popups():
        # VS Code-style editors pop up suggestions; Esc closes them so Enter/Up/brackets don't pick one.
        send_vk(VK["Esc"])
        time.sleep(0.03)

    def new_line():
        close_popups()
        # Editors that auto-close brackets/quotes can leave a leftover ")" or "]" right of the cursor.
        # Select to the end of the line and delete it, so Enter doesn't push it onto the next line.
        # (In Notepad the cursor is already at the very end, so this does nothing.)
        send_vk(VK["End"], shift=True)
        send_vk(VK["Delete"])
        press("\n")
        time.sleep(0.05)
        # Code editors auto-indent the new line. Select that indentation and delete it, so only the
        # script's own spaces end up there. (In plain Notepad this selects nothing and does nothing.)
        send_vk(VK["Home"], shift=True)
        send_vk(VK["Delete"])

    def wait(lo, hi):
        time.sleep(max(0.0, base * random.uniform(lo, hi) - (hold_lo + hold_hi) / 2))

    def type_line(line):
        i = 0
        while i < len(line):
            ch = line[i]
            if i and (line[i - 1].isalnum() or line[i - 1] == "_") and not (ch.isalnum() or ch == "_"):
                close_popups()                                # end of a word: dismiss suggestions
            if ch.isalpha() and random.random() < typo:
                # Typo: hit a wrong key, type on a few letters, notice, backspace and redo.
                # Only letters are typed ahead, so auto-closing brackets/quotes never get involved.
                ahead = ""
                for c in line[i + 1:i + 1 + random.randint(0, 3)]:
                    if not c.isalpha():
                        break
                    ahead += c
                press(random.choice("asdfghjklqwertyuiop".replace(ch.lower(), "")))
                for c in ahead:
                    press(c); wait(0.5, 1.2)
                time.sleep(random.uniform(0.3, 1.0) * pf)     # "wait, that's wrong"
                for _ in range(len(ahead) + 1):
                    press_key("Backspace"); wait(0.4, 0.8)
            press(ch)
            wait(0.5, 1.5)
            if random.random() < 0.004:
                time.sleep(random.uniform(1, 3) * pf)         # rare thinking pause
            i += 1

    def fix_forgotten(pending, cur_line):
        # Go back up to the line where a closing character was forgotten, add it, return to the end.
        char, line_no = pending
        time.sleep(random.uniform(0.8, 2.0))
        close_popups()
        for _ in range(cur_line - line_no):
            press_key("Up"); wait(0.8, 1.6)
        press_key("End"); wait(1, 2)
        press(char); wait(1, 3)
        press_key("End", ctrl=True)                           # Ctrl+End: back to the end of the file
        time.sleep(random.uniform(0.5, 1.2))

    def paste(s):
        # Put the text on the clipboard (done by the window thread), then press Ctrl+V.
        done = threading.Event()
        events.put(("clip", (s, done)))
        done.wait()
        time.sleep(random.uniform(0.5, 1.5))
        if esc_held():
            raise Stop
        send_vk(0x56, ctrl=True)
        lit(["Ctrl", "v"])
        time.sleep(random.uniform(1.0, 2.0))

    lines = []
    for line in text.split("\n"):
        if line.lstrip().startswith("#"):
            continue                                          # skip comment-only lines
        if not line.startswith("TABLE = ") and "  # " in line:
            line = line[:line.index("  # ")]                  # drop end-of-line comments
        lines.append(line)
    while lines and not lines[-1]:
        lines.pop()
    pending, fix_after = None, 0
    try:
        for n, line in enumerate(lines):
            last = n == len(lines) - 1
            # Only a forgotten ":" gets fixed later: editors auto-close brackets/quotes, so "forgetting"
            # one of those wouldn't really leave it out.
            forget = (pending is None and not last and 3 < len(line) < 200
                      and line[-1] == ":" and random.random() < 0.3)
            if len(line) > 1000 and not insert:
                paste(line)                                  # the giant table line: paste it
            elif forget:
                type_line(line[:-1])
                pending, fix_after = (line[-1], n), n + random.randint(1, 2)
            else:
                type_line(line)
            if not last:
                new_line()
                wait(3, 10)                                   # pause between lines
            if pending and (n >= fix_after or last):
                # Cursor is at the start of line n+1 (or the end of the last line).
                fix_forgotten(pending, n if last else n + 1)
                pending = None
        close_popups()
        send_vk(VK["End"], shift=True)                        # clear any leftover auto-closed character
        if insert:
            # Code continues below, so Delete could join the next line on. Instead type a space over
            # the selection (or after the cursor if nothing is selected), then backspace it away.
            send_char(" ")
            send_vk(VK["Backspace"])
        else:
            send_vk(VK["Delete"])
    except Stop:
        events.put(("status", "Stopped (ESC)."))
        events.put(("done", None))
        return
    events.put(("status", "Done!"))
    events.put(("done", None))


def main():
    insert = "--insert" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--insert"]
    path = args[0] if args else "solution.py"
    cpm, typo = 300.0, 0.012
    speed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_speed.json")
    if len(args) > 1:
        cpm = float(args[1])
    elif os.path.exists(speed_file):
        # Use your measured speed from speedtest.py: type at 90% of it, with a similar typo rate.
        me = json.load(open(speed_file))
        cpm = me["cpm"] * 0.9
        typo = min(0.05, max(0.003, me["typo_rate"] / 2.5))   # each typo costs ~2.5 backspaces
        print(f"Using your measured speed: {me['cpm']}/min -> typing at {cpm:.0f}/min.")
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    typed = sum(len(l) + 1 for l in text.split("\n")
                if (insert or len(l) <= 1000) and not l.lstrip().startswith("#"))
    print(f"About {typed} chars to type at ~{cpm:.0f}/min = roughly {typed / cpm:.0f} minutes "
          f"(the table line gets pasted).")

    root = tk.Tk()
    kb = Keyboard(root)
    root.after(200, kb.no_activate)
    events = queue.Queue()

    def pump():
        try:
            while True:
                kind, val = events.get_nowait()
                if kind == "on":
                    kb.light(val, True)
                elif kind == "off":
                    kb.light(val, False)
                elif kind == "clip":
                    s, done = val
                    root.clipboard_clear()
                    root.clipboard_append(s)
                    root.update()
                    done.set()
                elif kind == "status":
                    kb.status.configure(text=val)
                elif kind == "done":
                    root.after(3000, root.destroy)
        except queue.Empty:
            pass
        root.after(10, pump)

    threading.Thread(target=typer, args=(text, cpm, events, typo, insert), daemon=True).start()
    pump()
    root.mainloop()


if __name__ == "__main__":
    main()
