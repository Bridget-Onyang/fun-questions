
import sys
from collections import deque

def main():
    inp = sys.stdin
    out = sys.stdout
    line = inp.readline()
    while line and not any(ch.isdigit() for ch in line):
        line = inp.readline()
    ints = [int(x) for x in line.replace(',', ' ').split() if x.lstrip('-').isdigit()]
    R, C, U, V, T = ints[0], ints[1], ints[2], ints[3], ints[4]
    known = ints[5] if len(ints) > 5 else 0

    wall = [[-1] * C for _ in range(R)]   # -1 unknown, 0 open, 1 wall
    paint = [[0] * C for _ in range(R)]   # 0 none/unknown, 1 mine, 2 opponent

    if known:
        line = inp.readline()          # "MAP"
        for r in range(R):
            row = inp.readline().strip()
            for c in range(C):
                wall[r][c] = 1 if row[c] == '#' else 0

    DIRS = [('N', -1, 0), ('E', 0, 1), ('S', 1, 0), ('W', 0, -1)]

    while True:
        line = inp.readline()
        if not line:
            return
        line = line.strip()
        if line.startswith("GAME_END"):
            return
        if not line.startswith("ROUND"):
            continue
        units = []
        enemies = set()
        for _ in range(U):
            parts = inp.readline().split()
            i, r, c = int(parts[1]), int(parts[2]), int(parts[3])
            units.append((i, r, c))
            for dr in range(-V, V + 1):
                row = inp.readline().rstrip('\n')
                rr = r + dr
                for dc in range(-V, V + 1):
                    cc = c + dc
                    if not (0 <= rr < R and 0 <= cc < C):
                        continue
                    ch = row[dc + V]
                    if ch == '#':
                        wall[rr][cc] = 1
                        continue
                    wall[rr][cc] = 0
                    if ch in '+M':
                        paint[rr][cc] = 1
                    elif ch in '-E':
                        paint[rr][cc] = 2
                    else:
                        paint[rr][cc] = 0
                    if ch == 'E':
                        enemies.add((rr, cc))

        cur = {(r, c) for _, r, c in units}
        planned = set()
        claimed = set()
        orders = ['H'] * U
        for (i, r, c) in units:
            blocked = (cur - {(r, c)}) | planned | enemies
            dist = {(r, c): 0}
            first = {}
            dq = deque([(r, c)])
            best = None
            bestcost = 1e9
            while dq:
                x, y = dq.popleft()
                d = dist[(x, y)]
                if d - 0.5 >= bestcost:
                    break
                if d > 0 and paint[x][y] != 1 and (x, y) not in claimed:
                    cost = d - (0.5 if paint[x][y] == 2 else 0)
                    if cost < bestcost:
                        bestcost = cost
                        best = (x, y)
                for k, (nm, dr, dc) in enumerate(DIRS):
                    nx, ny = x + dr, y + dc
                    if not (0 <= nx < R and 0 <= ny < C):
                        continue
                    if wall[nx][ny] == 1 or (nx, ny) in dist:
                        continue
                    if d == 0 and (nx, ny) in blocked:
                        continue
                    dist[(nx, ny)] = d + 1
                    first[(nx, ny)] = first[(x, y)] if d > 0 else k
                    dq.append((nx, ny))
            if best is not None:
                k = first[best]
                nm, dr, dc = DIRS[k]
                orders[i] = nm
                planned.add((r + dr, c + dc))
                claimed.add(best)
            else:
                planned.add((r, c))
        out.write("ORDERS " + " ".join(orders) + "\n")
        out.flush()

main()