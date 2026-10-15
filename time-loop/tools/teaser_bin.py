# Cuts the teaser media bin: each source moment with handles, all 1920x1080, 30 fps, H.264 + AAC 48 kHz stereo,
# loudness near -18 LUFS (silent sources get a silent track so every clip behaves the same in an editor).
import subprocess, sys, json, pathlib
TL = pathlib.Path("/mnt/project-files/time-loop"); S = TL / "sources"; IA = pathlib.Path("/tmp/claude-0/tl/ia"); IA2 = pathlib.Path("/tmp/claude-0/dl/ia2"); TB = pathlib.Path("/tmp/claude-0/tb")
RSBN = "/tmp/claude-0/tl/rsbn/rsbn.webm"
OUT = TL / "media/teaser-bin"; OUT.mkdir(parents=True, exist_ok=True)
# name: (source, start, end, has_audio, note)
BIN = {
 "butler-speech":    (RSBN, 470, 530, True,  "Butler, July 13, 2024: the chart, the shots at 31.3 s, agents cover him"),
 "butler-fist":      (RSBN, 570, 592, True,  "Butler: Trump rises and raises his fist, about 7 s in"),
 "ned-day1":         (S/"ned.mp4", 12, 42, False, "Groundhog Day: Ned Ryerson greets Phil (NO AUDIO yet)"),
 "ned-day2":         (S/"ned.mp4", 80, 117, False, "Groundhog Day: Ned again; Phil steps in the puddle about 28 s in (NO AUDIO yet)"),
 "electro-anaheim":  (IA2/"ana.mp4", 17.47, 54.47, True, "Shark or electrocution, Anaheim, Sept. 29, 2023 (C-SPAN)"),
 "electro-ankeny":   (IA/"a2.mp4", 0, 12.0, True, "Shark or electrocution, Ankeny, Dec. 2, 2023 (C-SPAN)"),
 "electro-vegas":    (IA/"a3.mp4", 0, 14.0, True, "Shark or electrocution, Las Vegas, June 9, 2024 (C-SPAN)"),
 "electro-grandrapids": (IA2/"gr.mp4", 18.01, 51.51, True, "Shark or electrocution, Grand Rapids, July 20, 2024: punchline at 8.5 s"),
 "no-tomorrow":      (TB/"cons-av.mp4", 0, 40, True, "Groundhog Day: 'What if there were no tomorrow? ... no consequences'"),
 "own-rules":        (TB/"cons-av.mp4", 100, 124, True, "Groundhog Day: 'I'm not going to live by their rules anymore'"),
 "fifth-avenue":     (IA2/"fifth.mp4", 14.06, 48.56, True, "Sioux Center, Jan. 23, 2016: 'shoot somebody and I wouldn't lose any voters' (CNN)"),
 "find-me":          (TB/"wake-av.mp4", 66, 102, True, "Edge of Tomorrow: 'Find me when you wake up', then Cage wakes"),
 "alarm-day1":       (S/"clock-av.mp4", 26, 60, True, "Groundhog Day: 5:59 to 6:00, 'I Got You Babe', Phil wakes"),
 "alarm-day2":       (S/"clock-av.mp4", 98, 135, True, "Groundhog Day: close-up flip from 5:59 to 6:00 at 5-6 s"),
 "alarm-smash":      (S/"clock-av.mp4", 116, 152, True, "Groundhog Day: Phil smashes the clock radio"),
 "alarm-late":       (S/"clock-av.mp4", 158, 201, True, "Groundhog Day: a later 6:00, 'Oh, please, not again'"),
 "wake-1":           (S/"clock-av.mp4", 47, 76, True, "Groundhog Day: Phil asleep, then up and across to the window (rises about 3 s in)"),
 "wake-2":           (S/"clock-av.mp4", 59, 86, True, "Groundhog Day: Phil sits bolt upright, about 2.5 s in"),
 "wake-3":           (S/"clock-av.mp4", 78, 109, True, "Groundhog Day: Phil sits up, then throws himself back down about 7 s in"),
 "wake-4":           (S/"clock-av.mp4", 134, 162, True, "Groundhog Day: Phil's eyes pop open and he sits up, about 3 s in"),
 "wake-5":           (S/"clock-av.mp4", 157, 186, True, "Groundhog Day: Phil wakes, sits up and heads for the window, about 3 s in"),
 "clock-flip-b":     (S/"clock-av.mp4", 129, 156, True, "Groundhog Day: close-up 5:59 at 2 s, flips to 6:00 at 4 s"),
 "shove":            (IA/"nato_src2.mp4", 0, 15.2, True, "NATO, Brussels, May 25, 2017: Trump pushes past Montenegro's prime minister (MSNBC)"),
 "daze-cabinet":     (S/"daze/cabinet-nod.mp4", 70, 114, True, "Cabinet meeting, Dec. 2, 2025: head jerks up about 13 s in"),
 "daze-coal":        (S/"daze/coal-nod.mp4", 25, 60, True, "Coal event, June 4, 2026: head snaps up about 12 s in"),
 "didnt-sleep":      (S/"daze/didnt-sleep.mp4", 8, 41, True, "Cabinet meeting, Jan. 29, 2026: 'I didn't sleep, I just closed them'"),
 "never-seen":       (S/"daze/never-seen.mp4", 9, 45, True, "Nov. 6, 2025: 'There's never been anything like this', three times"),
 "forecast":         (TB/"fore-av.mp4", 0, 17.7, True, "Groundhog Day: Phil's forecast"),
 "tarmac-wake":      (TB/"train-av.mp4", 172, 186, True, "Edge of Tomorrow: Cage wakes on the tarmac"),
}
LB = "crop=528:360:0:60,scale=1920:1080,"  # C-SPAN archive files: a 16:9 picture letterboxed in 528x480 anamorphic
CROP = {"butler-fist": "crop=1600:900:280:0,", "electro-anaheim": LB, "electro-grandrapids": LB,
        "daze-cabinet": LB, "daze-coal": LB, "didnt-sleep": LB, "never-seen": LB}  # the network banner cropped off the closing shot
VF = "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30"
names = sys.argv[1:] or list(BIN)
for n in names:
    src, a, b, au, note = BIN[n]; o = OUT / f"{n}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", str(src)]
    if au: cmd += ["-map", "0:v:0", "-map", "0:a:0", "-af", "loudnorm=I=-18:TP=-1.5:LRA=11,aresample=48000", "-ac", "2"]
    else: cmd += ["-f", "lavfi", "-t", str(b - a), "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-vf", CROP.get(n, "") + VF, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-g", "30",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(o)]
    subprocess.run(cmd, check=True); print(n, o.stat().st_size // 1024, "KB", flush=True)
(OUT / "BIN.json").write_text(json.dumps({k: {"source": str(v[0]).replace("/tmp/claude-0/tl/rsbn/rsbn.webm", "RSBN broadcast, full HD").replace("/tmp/claude-0/", "(work copy) "), "from": v[1], "to": v[2], "audio": v[3], "note": v[4]} for k, v in BIN.items()}, indent=1))
