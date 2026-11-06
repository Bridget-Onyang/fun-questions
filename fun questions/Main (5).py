import sys



ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
IV, JS = 1789, 1838


def build():
    rows = TABLE.split("|")
    n = len(rows)
    W, D, N = [0] * (2 * n), [0] * (2 * n), [-1] * (2 * n)
    for s, r in enumerate(rows):
        f = r.split()
        for b in range(2):
            w, d, t = f[3 * b:3 * b + 3]
            ns = ALPHA.index(t[0]) * 52 + ALPHA.index(t[1])
            W[2 * s + b] = int(w)
            D[2 * s + b] = 1 if d == "R" else -1
            N[2 * s + b] = ns if ns < n else -1
    return W, D, N


W, D, N = build()


def run(nums, cap=50_000_000):
    s = "0".join("1" * c for c in nums)
    off = 4 * len(s) + 100000
    tape = bytearray(2 * off + len(s))
    for i, ch in enumerate(s):
        if ch == "1":
            tape[off + i] = 1
    pos, st = off, 0
    for _ in range(cap):
        if st == IV:
            q = pos
            while not tape[q]:
                q += 1
            if q - pos <= 30 and not any(tape[q - 30:q]):
                pos, st = q - 29, JS
                continue
        i = 2 * st + tape[pos]
        if N[i] < 0:
            break
        tape[pos] = W[i]
        pos += D[i]
        st = N[i]
        if st == 0:
            if not tape[pos]:
                return 0
            j = tape.find(1)
            k = tape.find(0, j)
            return k - j
    return 0


def main():
    data = sys.stdin.buffer.read().decode("utf-8-sig", "ignore").splitlines()
    n = int(data[0])
    out = []
    for line in data[1:n + 1]:
        out.append(str(run([int(x) for x in line.split()])))
    print("\n".join(out))


main()