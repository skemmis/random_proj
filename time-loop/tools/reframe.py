"""Crop a landscape clip to a tall frame that follows one person, like social-media auto-reframe tools.

Usage: python3 reframe.py IN.mp4 OUT.mp4 --seed X [--aspect 4:5] [--keys "t:x,t:x"] [--start S --dur D]
  --seed  horizontal position (0-1) of the person to follow in the first frame.
  --keys  optional manual centres (seconds:fraction) that override the tracker near those times.
The tracker detects faces with OpenCV's YuNet model, follows the face nearest the last position,
holds its place when the face is lost, and smooths the path so the virtual camera pans gently.
"""
import argparse, subprocess, pathlib, numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--seed", type=float, default=0.5); ap.add_argument("--aspect", default="4:5")
ap.add_argument("--keys", default=""); ap.add_argument("--start", type=float, default=0); ap.add_argument("--dur", type=float, default=0)
ap.add_argument("--height", type=int, default=960); ap.add_argument("--crf", type=int, default=24)
a = ap.parse_args()
model = str(pathlib.Path(__file__).with_name("face_detection_yunet_2023mar.onnx"))

cap = cv2.VideoCapture(a.inp); fps = cap.get(cv2.CAP_PROP_FPS) or 30
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.set(cv2.CAP_PROP_POS_MSEC, a.start * 1000)
n_max = int(a.dur * fps) if a.dur else 10**9
aw, ah = map(int, a.aspect.split(":")); cw = min(W, int(round(H * aw / ah / 2) * 2))
scale = 640 / W; det = cv2.FaceDetectorYN.create(model, "", (640, int(H * scale)), 0.6)

frames, xs = [], []; x = a.seed * W
while len(frames) < n_max:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
    if len(frames) % 2 == 1:  # detect on every other frame
        _, faces = det.detect(cv2.resize(f, (640, int(H * scale))))
        if faces is not None and len(faces):
            cx = (faces[:, 0] + faces[:, 2] / 2) / scale; size = faces[:, 2] / scale
            near = np.abs(cx - x) < np.maximum(0.18 * W, 3 * size)
            if near.any():
                i = np.argmax(np.where(near, size - 0.002 * np.abs(cx - x), -1e9)); x = 0.7 * x + 0.3 * cx[i]
    xs.append(x)
xs = np.array(xs, float)
for k in filter(None, a.keys.split(",")):  # manual centres win within half a second
    t, fx = map(float, k.split(":")); i = int(t * fps)
    lo, hi = max(0, i - int(fps / 2)), min(len(xs), i + int(fps / 2)); xs[lo:hi] = fx * W
win = int(fps * 0.8) | 1; pad = np.pad(xs, win, mode="edge")
sm = np.convolve(pad, np.ones(win) / win, mode="same")[win:-win]
left = np.clip(sm - cw / 2, 0, W - cw).astype(int)

oh = min(a.height, H); ow = int(round(oh * aw / ah / 2) * 2)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{cw}x{H}", "-r", str(fps), "-i", "-",
    "-ss", str(a.start), "-t", str(len(frames) / fps), "-i", a.inp, "-map", "0:v", "-map", "1:a?", "-vf", f"scale={ow}:{oh}",
    "-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "96k", "-shortest", a.out], stdin=subprocess.PIPE)
for f, l in zip(frames, left): enc.stdin.write(np.ascontiguousarray(f[:, l:l + cw]).tobytes())
enc.stdin.close(); enc.wait()
print(f"{a.out}: {len(frames)} frames, crop {cw}x{H} -> {ow}x{oh}, camera x from {left.min()} to {left.max()}")
