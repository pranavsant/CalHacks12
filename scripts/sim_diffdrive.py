# scripts/sim_diffdrive.py
# Minimal viewer/simulator for relative_program output.
# Usage:
#   python scripts/sim_diffdrive.py --run_id <your_run_id>
#   (or) python scripts/sim_diffdrive.py --file exports/relative_program_<run_id>.json

import json, math, argparse, sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_id", type=str, default=None,
                    help="Run ID (loads exports/relative_program_<run_id>.json)")
    ap.add_argument("--file", type=str, default=None,
                    help="Path to a relative_program_*.json file (overrides --run_id)")
    ap.add_argument("--samples_per_segment", type=int, default=400,
                    help="Geometric samples per segment")
    ap.add_argument("--fps", type=int, default=60, help="Animation FPS")
    ap.add_argument("--robot_len", type=float, default=0.12, help="Robot body length (m) for drawing")
    return ap.parse_args()

# --- Safe eval context for math expressions in t ---
SAFE = {
    k: getattr(math, k)
    for k in ["sin","cos","tan","asin","acos","atan","atan2","sqrt","exp","log","log10","pi","e"]
}
# NB: atan2(y,x) not typically in user expressions; we keep for completeness.
SAFE.update({"abs": abs, "min": min, "max": max})

def eval_xy(expr_x, expr_y, t_values):
    """Evaluate x(t), y(t) expressions over t_values safely."""
    xs, ys = [], []
    for t in t_values:
        local = dict(SAFE)
        local["t"] = float(t)
        x = eval(expr_x, {"__builtins__": None}, local)
        y = eval(expr_y, {"__builtins__": None}, local)
        xs.append(float(x)); ys.append(float(y))
    return np.array(xs), np.array(ys)

def transform_points_local_to_global(xs, ys, gx, gy, gtheta):
    """Apply global pose (gx,gy,gtheta) to local points."""
    c, s = math.cos(gtheta), math.sin(gtheta)
    X = gx + c*xs - s*ys
    Y = gy + s*xs + c*ys
    return X, Y

def heading_from_polyline(X, Y):
    """Tangent heading along polyline; finite-diff with clamped ends."""
    dX = np.gradient(X); dY = np.gradient(Y)
    theta = np.arctan2(dY, dX)
    # unwrap for smoothness
    theta = np.unwrap(theta)
    return theta

def load_relative_program(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rp = data["relative_program"]
    segs = rp["segments"]
    return segs, data.get("run_id", None)

def main():
    args = parse_args()
    if args.file:
        path = Path(args.file)
    else:
        if not args.run_id:
            print("ERROR: Provide --run_id or --file", file=sys.stderr)
            sys.exit(1)
        path = Path("exports") / f"relative_program_{args.run_id}.json"
    if not path.is_file():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    segments, run_id = load_relative_program(path)

    # Global pose accumulator (robot “thinks” it resets each segment to local, but we visualize globally)
    gx = 0.0; gy = 0.0; gtheta = 0.0

    # Store full drawing for animation frames
    frames = []         # list of (X, Y, theta, color, pen_down) for each polyline vertex in order
    drawn_paths = []    # per segment: (X, Y, color, pen_down)

    for seg in segments:
        name = seg.get("name", "")
        x_rel = seg["x_rel"]; y_rel = seg["y_rel"]
        tmin = float(seg["t_min"]); tmax = float(seg["t_max"])
        color = (seg.get("pen") or {}).get("color", "#000000")
        pen_down = (color != "none")

        # Sample the local curve uniformly in t
        t = np.linspace(tmin, tmax, num=args.samples_per_segment)
        xs, ys = eval_xy(x_rel, y_rel, t)

        # Transform to global frame for visualization using current global pose
        X, Y = transform_points_local_to_global(xs, ys, gx, gy, gtheta)
        TH = heading_from_polyline(X, Y)

        drawn_paths.append((X, Y, color, pen_down))

        # The endpoint pose becomes the next segment's origin (relative frame logic)
        # End tangent heading = last TH
        gx, gy, gtheta = float(X[-1]), float(Y[-1]), float(TH[-1])

        # Accumulate per-vertex frames (so we can animate smoothly)
        for i in range(len(X)):
            frames.append((X[i], Y[i], TH[i], color, pen_down))

    # Build figure
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect("equal", adjustable="box")
    # Compute bounds
    allX = np.concatenate([p[0] for p in drawn_paths if len(p[0]) > 0])
    allY = np.concatenate([p[1] for p in drawn_paths if len(p[1]) > 0])
    if allX.size == 0 or allY.size == 0:
        print("No points to draw.", file=sys.stderr)
        sys.exit(1)
    margin = 0.1 * max(allX.max()-allX.min(), allY.max()-allY.min())
    ax.set_xlim(allX.min()-margin, allX.max()+margin)
    ax.set_ylim(allY.min()-margin, allY.max()+margin)
    ax.set_title(f"Relative Program Simulation (run_id={run_id or 'N/A'})")

    # Pre-plot background path (for context)
    for (X, Y, color, pen_down) in drawn_paths:
        if pen_down:
            ax.plot(X, Y, linewidth=2, alpha=0.3, color=color)
        else:
            ax.plot(X, Y, linewidth=1, alpha=0.2, color="gray", linestyle="--")

    # Dynamic artist: the “ink” and the robot body
    ink_line, = ax.plot([], [], linewidth=3, color="#000000")  # will recolor as we draw
    robot_patch = ax.fill([], [], alpha=0.8, color="#222222")[0]  # single Polygon artist


    # Keep growing “drawn” path
    drawn_X = []
    drawn_Y = []
    current_color = None

    def robot_triangle(x, y, theta, L):
        # Simple isosceles triangle footprint pointing along theta
        w = 0.6 * L
        p_front = np.array([ L/2, 0.0 ])
        p_bl = np.array([-L/2, -w/2])
        p_br = np.array([-L/2,  w/2])
        R = np.array([[math.cos(theta), -math.sin(theta)],
                      [math.sin(theta),  math.cos(theta)]])
        P = np.vstack([p_front, p_br, p_bl]) @ R.T
        P[:,0] += x; P[:,1] += y
        return P

    # Build per-frame function
    def init():
        ink_line.set_data([], [])
        robot_patch.set_xy(np.zeros((3, 2)))
        return ink_line, robot_patch

    def update(frame_idx):
        nonlocal current_color
        x, y, th, color, pen_down = frames[frame_idx]

        # Update robot body
        tri = robot_triangle(x, y, th, args.robot_len)
        robot_patch.set_xy(tri)

        # Update ink trace (only when pen_down)
        if pen_down:
            if current_color != color:
                # flush previous color: start a new stroke
                current_color = color
                ink_line.set_color(color)
            drawn_X.append(x); drawn_Y.append(y)
        else:
            # Pen up: don't add to drawn path; optionally lift (gap)
            pass

        ink_line.set_data(drawn_X, drawn_Y)
        return ink_line, robot_patch

    frames_total = len(frames)
    interval_ms = 1000.0 / args.fps
    anim = FuncAnimation(fig, update, init_func=init,
                         frames=frames_total, interval=interval_ms,
                         blit=True, repeat=False)
    plt.show()

if __name__ == "__main__":
    main()
