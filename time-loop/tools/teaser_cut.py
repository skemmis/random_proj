# Builds the teaser rough cut from the edit list below: an MP4 to watch and an FCP 7 XML timeline
# (DaVinci Resolve: File > Import > Timeline) that places every clip, so Sam only retimes.
# Event kinds:  ("v", clip, in, out)            full-screen shot on V1, its own sound on A1
#               ("v", clip, in, out, {"mute":1}) picture only
#               ("gap", seconds)                black and silence
#               ("hold", clip, at, seconds)      freeze one frame (written to the bin as a still clip)
#               ("grid", seconds, [(clip, in), x4])  four shots at once, sound from all four
#               ("a", clip, in, out, at, gain_db, fade_in[, fade_out]) extra sound on A2-A4; at "@" = under the shot before it
# Times in clip-relative seconds (see media/teaser-bin/BIN.json for what each clip holds).
import json, subprocess, pathlib, shutil, sys
TL = pathlib.Path("/mnt/project-files/time-loop"); BIN = TL / "media/teaser-bin"; GFX = TL / "media/teaser-gfx"
OUT = TL / "00-teaser/roughcut"; OUT.mkdir(parents=True, exist_ok=True)
WORK = pathlib.Path("/tmp/claude-0/tb/cut"); shutil.rmtree(WORK, ignore_errors=True); WORK.mkdir(parents=True)
FPS = 30
GFX_NAMES = {"sight-shots", "turn-fire", "margin-path", "whiteout-cut", "flyover", "crowd-beat", "skull-path", "close-gap", "head-turn", "word-bullet", "word-ear", "word-head", "word-990", "chart-scrub"}

# v2 (Sam, Oct 15 22:29): a teaser, not a piece: faster start, no Ned, no charts (motion graphics only),
# "I Got You Babe" over the fist raise.
# v5 order of every loop (Sam 22:55): clock (and Phil up), Trump's joke, the train scene ("their rules") with the
# shove, no consequences, "shoot somebody", Edge of Tomorrow, Butler. Every loop starts on the clock (22:39).
PASS1 = [  # long takes, clean sound
 ("v", "alarm-day1", 4.0, 9.0, {"mute": 1}),  # the clock at 5:59; the song bed starts here (22:31)
 ("v", "wake-1", 2.5, 7.0, {"mute": 1}),       # Phil gets up
 ("v", "electro-anaheim", 0.0, 2.45),          # the joke, dead air cut out (jump cuts)
 ("v", "electro-anaheim", 8.1, 11.3),
 ("v", "electro-anaheim", 12.85, 16.3),
 ("v", "own-rules", 2.6, 8.4),                 # the train: "I'm not going to live by their rules anymore!" (22:51)
 ("v", "shove", 0.6, 5.0),                     # Trump shoves past Montenegro's prime minister (22:51)
 ("v", "no-tomorrow", 2.0, 12.0),              # "What if there were no tomorrow? ... whatever we wanted"
 ("v", "fifth-avenue", 8.2, 13.0),             # "shoot somebody and I wouldn't lose any voters"
 ("v", "find-me", 5.0, 9.0),                   # "Find me when you wake up!"
 ("v", "find-me", 11.6, 13.5),                 # and Cage wakes
 ("v", "butler-speech", 28.5, 38.0),           # "take a look at what happened" ... the shots ... agents cover him
]
PASS2 = [  # tighter; motion graphics cut in; sound runs over the cuts
 ("v", "clock-flip-b", 1.5, 4.6, {"mute": 1}), # 5:59 to 6:00: loop two
 ("v", "wake-4", 2.6, 5.6, {"mute": 1}),       # Phil sits up
 ("v", "electro-grandrapids", 9.2, 12.3),      # punchline only: "I will take electrocution all day long"
 ("v", "own-rules", 3.2, 6.6),
 ("v", "shove", 1.4, 3.0),
 ("v", "head-turn", 1.0, 3.0, {"mute": 1}), ("a", "no-tomorrow", 4.0, 6.0, "@", -3, 0),
 ("v", "no-tomorrow", 6.0, 8.0),               # "there would be no consequences"
 ("v", "fifth-avenue", 9.6, 11.6),             # "Fifth Avenue and shoot somebody"
 ("v", "find-me", 5.0, 7.0),
 ("v", "butler-speech", 30.0, 33.5),
 ("v", "whiteout-cut", 1.6, 4.0, {"mute": 1}), ("a", "butler-speech", 33.5, 35.9, "@", -6, 0),
 ("v", "flyover", 1.5, 4.5, {"mute": 1}), ("a", "butler-speech", 35.9, 38.9, "@", -9, 0),  # up and over to the shooter's roof
 ("v", "skull-path", 1.5, 4.0, {"mute": 1}), ("a", "butler-speech", 38.9, 41.4, "@", -12, 0),
 ("v", "margin-path", 1.5, 3.5, {"mute": 1}), ("a", "never-seen", 13.0, 14.8, "@", -3, 0),
 ("v", "never-seen", 14.8, 16.9),              # "There's never been anything like this"
 ("v", "close-gap", 1.0, 3.0, {"mute": 1}),
 ("v", "daze-cabinet", 12.0, 14.5),            # Trump jerks awake, into the next loop
]
PASS3 = [  # manic: half-second shots in the same order, sound piling up
 ("v", "alarm-day2", 5.5, 6.3, {"mute": 1}),  # the flip again: loop three
 ("v", "wake-2", 2.4, 3.1, {"mute": 1}),
 ("v", "electro-ankeny", 10.0, 10.9), ("v", "own-rules", 6.0, 6.7), ("v", "shove", 1.2, 1.8),
 ("v", "no-tomorrow", 16.5, 17.2), ("v", "fifth-avenue", 9.8, 10.4), ("v", "find-me", 5.0, 5.6),
 ("v", "butler-speech", 30.9, 31.5), ("v", "flyover", 5.0, 5.5, {"mute": 1}), ("v", "sight-shots", 1.5, 2.1, {"mute": 1}), ("v", "skull-path", 2.0, 2.5, {"mute": 1}),
 ("v", "turn-fire", 2.0, 2.5, {"mute": 1}), ("v", "daze-coal", 11.6, 12.2), ("v", "never-seen", 1.1, 1.7),
 ("v", "head-turn", 2.5, 3.0, {"mute": 1}), ("v", "close-gap", 1.5, 1.9, {"mute": 1}), ("v", "butler-speech", 31.0, 31.4),
 ("v", "margin-path", 3.0, 3.4, {"mute": 1}), ("v", "electro-vegas", 11.6, 12.0), ("v", "didnt-sleep", 3.0, 3.4),
 ("grid", 1.6, [("butler-speech", 31.0), ("sight-shots", 2.0), ("electro-vegas", 11.3), ("find-me", 5.0)]),
 ("v", "alarm-smash", 3.8, 5.0),               # Phil smashes the clock: the loop breaks
]
# "I Got You Babe" runs under the whole teaser on A4 (song-bed: the film's clock-radio song, stitched to one take
# until Sam sends a clean MP3): full over the opening clock, ducked by BED_DUCK dB, back up for the fist raise.
BED_DUCK = -16
ENDING = [ ("gap", 1.0),
 ("v", "butler-fist", 4.0, 10.0, {"mute": 1}), ("a", "butler-fist", 4.0, 10.0, "@", -14, 0),
 ("hold", "butler-fist", 10.0, 4.5) ]
# Placeholder end card (Sam 22:58): the title over the fist, then the subtitle; the page sets the real one as text.
TITLE = [("title-1.png", 0.6), ("title-2.png", 2.0)]  # fist highest at 10.0 (rsbn 580)

# The bin was recut on Oct 15 22:55 with about 10 s more at each end (Sam: "some of them need to be extended").
# Times in the edit list are relative to the OLD cuts; SHIFT moves them onto the new files.
SHIFT = {'electro-anaheim': 10, 'electro-grandrapids': 10, 'fifth-avenue': 10, 'no-tomorrow': 8, 'own-rules': 10, 'find-me': 10, 'alarm-day1': 4, 'alarm-day2': 10, 'alarm-smash': 10, 'alarm-late': 10, 'wake-1': 10, 'wake-2': 10, 'wake-3': 10, 'wake-4': 10, 'wake-5': 10, 'clock-flip-b': 10, 'daze-cabinet': 10, 'daze-coal': 10, 'didnt-sleep': 10, 'never-seen': 10}

def build_events():
    ev, t, last = [], 0.0, 0.0  # "@" in an extra-sound event = the start of the shot just before it
    beds = []
    for part, items in (("pass1", PASS1), ("pass2", PASS2), ("pass3", PASS3), ("end", ENDING)):
        if part == "pass3": p3 = t
        if part == "end": fist_at = t + 1.0
        for it in items:
            k = it[0]
            if k == "a":
                c, i, o, at, g, fi = it[1:7]; fo = it[7] if len(it) > 7 else 0
                ev.append(dict(kind="a", clip=c, i=i, o=o, at=last if at == "@" else at, gain=g, fade=fi, fadeout=fo, part=part)); continue
            if k == "v":
                c, i, o = it[1:4]; d = round((o - i) * FPS) / FPS; last = t
                ev.append(dict(kind="v", clip=c, i=i, o=i + d, at=t, mute=bool(len(it) > 4 and it[4].get("mute")), part=part)); t += d
            elif k == "gap": ev.append(dict(kind="gap", d=it[1], at=t, part=part)); t += it[1]
            elif k == "hold": ev.append(dict(kind="hold", clip=it[1], i=it[2], d=it[3], at=t, part=part)); t += it[3]
            elif k == "grid": ev.append(dict(kind="grid", d=it[1], src=it[2], at=t, part=part)); t += it[1]
        if part == "pass3":
            # the crescendo: the clock-radio song and the Butler screams rise under the whole pass
            ev.append(dict(kind="a", clip="butler-speech", i=31.3, o=31.3 + (t - p3), at=p3, gain=-8, fade=(t - p3) * .7, part=part))
    for e in ev:
        if e.get("clip") in SHIFT and e["kind"] in ("v", "a", "hold"):
            e["i"] += SHIFT[e["clip"]]
            if "o" in e: e["o"] += SHIFT[e["clip"]]
        if e["kind"] == "grid": e["src"] = [(c, i + SHIFT.get(c, 0)) for c, i in e["src"]]
    first = ev[0]["o"] - ev[0]["i"]
    ev.append(dict(kind="bed", clip="song-bed", up1=first, up2=fist_at, total=t, duck=BED_DUCK, part="all"))
    return ev, t

def path(c):
    if c.endswith(".png"): return BIN / c
    if c in GFX_NAMES:
        g = GFX / f"{c}.mp4"
        if g.exists(): return g
        ph = BIN / "placeholders" / f"{c}.mp4"
        if not ph.exists():
            ph.parent.mkdir(exist_ok=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0b0d10:s=1920x1080:r=30:d=8", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                "-vf", f"drawtext=text='{c} (graphic on its way)':fontcolor=0x8a8a8a:fontsize=54:x=(w-tw)/2:y=(h-th)/2", "-t", "8", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(ph)], check=True)
        return ph
    return BIN / f"{c}.mp4"

def ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True)

def render(ev, total):
    segs = []
    VF = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b0d10,setsar=1,fps=30"
    for n, e in enumerate(ev):
        s = WORK / f"s{n:03d}.mp4"
        enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2"]
        if e["kind"] == "v":
            d = e["o"] - e["i"]
            if e["mute"]: ff("-ss", e["i"], "-t", d, "-i", path(e["clip"]), "-f", "lavfi", "-t", d, "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-vf", VF, "-t", d, *enc, s)
            else: ff("-ss", e["i"], "-t", d, "-i", path(e["clip"]), "-vf", VF, "-af", "apad", "-t", d, *enc, s)
        elif e["kind"] == "gap": ff("-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=30:d={e['d']}", "-f", "lavfi", "-t", e["d"], "-i", "anullsrc=r=48000:cl=stereo", "-t", e["d"], *enc, s)
        elif e["kind"] == "hold":
            t1, t2 = (BIN / TITLE[0][0]), (BIN / TITLE[1][0])
            fc = (f"[0:v]{VF},trim=end_frame=1,tpad=stop_mode=clone:stop_duration={e['d']}[b];"
                  f"[b][2:v]overlay=enable='between(t,{TITLE[0][1]},{TITLE[1][1]})'[b1];[b1][3:v]overlay=enable='gte(t,{TITLE[1][1]})'[v]")
            ff("-ss", e["i"] - 1 / FPS, "-i", path(e["clip"]), "-f", "lavfi", "-t", e["d"], "-i", "anullsrc=r=48000:cl=stereo", "-loop", "1", "-i", t1, "-loop", "1", "-i", t2,
               "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-t", e["d"], *enc, s)
        elif e["kind"] == "grid":
            d = e["d"]; ins = []
            for c, i in e["src"]: ins += ["-ss", i, "-t", d, "-i", path(c)]
            fc = ";".join(f"[{k}:v]scale=960:540:force_original_aspect_ratio=increase,crop=960:540,setsar=1,fps=30[g{k}]" for k in range(4))
            snd = [k for k, (c, i) in enumerate(e["src"]) if c not in GFX_NAMES]
            fc += ";[g0][g1][g2][g3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v];" + "".join(f"[{k}:a]" for k in snd) + f"amix=inputs={len(snd)}:normalize=0,volume=0.8[a]"
            ff(*ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", d, *enc, s)
        else: continue
        segs.append(s)
    (WORK / "list.txt").write_text("".join(f"file '{s}'\n" for s in segs))
    ff("-f", "concat", "-safe", "0", "-i", WORK / "list.txt", "-c", "copy", WORK / "v1.mp4")
    extras = [e for e in ev if e["kind"] == "a"]; ins = ["-i", WORK / "v1.mp4"]; fc = []
    bed = next((e for e in ev if e["kind"] == "bed"), None)
    if bed:
        d = 10 ** (bed["duck"] / 20); a, b = bed["up1"], bed["up2"]
        env = f"if(lt(t,{a}),1,if(lt(t,{a}+1.5),1-(1-{d})*(t-{a})/1.5,if(lt(t,{b}),{d},min(1,{d}+(1-{d})*(t-{b})/0.8))))"
        extras.append(dict(clip="song-bed", i=0, o=bed["total"], at=0, gain=0, fade=0, fadeout=1.5, env=env))
    for k, e in enumerate(extras, 1):
        ins += ["-ss", e["i"], "-t", e["o"] - e["i"], "-i", path(e["clip"])]
        f = f"[{k}:a]volume={e['gain']}dB" + (f",volume='{e['env']}':eval=frame" if e.get("env") else "") + (f",afade=t=in:d={e['fade']:.2f}:curve=exp" if e["fade"] else "") + (f",afade=t=out:st={e['o'] - e['i'] - e['fadeout']:.2f}:d={e['fadeout']}" if e.get("fadeout") else "") + f",adelay={int(e['at'] * 1000)}:all=1[x{k}]"
        fc.append(f)
    mix = "[0:a]" + "".join(f"[x{k}]" for k in range(1, len(extras) + 1))
    fc.append(f"{mix}amix=inputs={len(extras) + 1}:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5[a]")
    ff(*ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT / "teaser-roughcut.mp4")

# ---- FCP 7 XML (xmeml v5) for Resolve ----
def xml(ev, total):
    fr = lambda s: int(round(s * FPS))
    files, fid = {}, 0
    def fileref(c, dur_s):
        nonlocal fid
        p = path(c)
        if c in files: return f'<file id="{files[c]}"/>'
        fid += 1; files[c] = f"file-{fid}"
        return (f'<file id="file-{fid}"><name>{p.name}</name><pathurl>file://localhost/teaser-kit/{p.name}</pathurl>'
                f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><duration>{fr(dur_s)}</duration>'
                f'<media><video><samplecharacteristics><width>1920</width><height>1080</height></samplecharacteristics></video><audio><channelcount>2</channelcount></audio></media></file>')
    def dur(c):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path(c))], capture_output=True, text=True)
        return float(r.stdout.strip() or 30)
    D = {}
    def clip(cid, c, i, o, at, track_kind, motion=None, gain=0):
        if c not in D: D[c] = dur(c)
        rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"
        filt = ""
        if motion: filt = ('<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>'
                           f'<parameter><parameterid>scale</parameterid><name>Scale</name><value>50</value></parameter>'
                           f'<parameter><parameterid>center</parameterid><name>Center</name><value><horiz>{motion[0]}</horiz><vert>{motion[1]}</vert></value></parameter></effect></filter>')
        if gain: filt += f'<filter><effect><name>Audio Levels</name><effectid>audiolevels</effectid><effecttype>audiolevels</effecttype><mediatype>audio</mediatype><parameter><parameterid>level</parameterid><name>Level</name><value>{10 ** (gain / 20):.3f}</value></parameter></effect></filter>'
        return (f'<clipitem id="{cid}"><name>{c}</name><duration>{fr(D[c])}</duration>{rate}<start>{fr(at)}</start><end>{fr(at) + fr(o - i)}</end>'
                f'<in>{fr(i)}</in><out>{fr(i) + fr(o - i)}</out>{fileref(c, D[c])}' + (f"<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>" if track_kind == "a" else "") + f"{filt}</clipitem>")
    V = {1: [], 2: [], 3: [], 4: [], 5: []}; A = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}; n = 0
    holdnames = {}
    for e in ev:
        n += 1
        if e["kind"] == "v":
            V[1].append(clip(f"v{n}", e["clip"], e["i"], e["o"], e["at"], "v"))
            if not e["mute"]: A[1].append(clip(f"a{n}", e["clip"], e["i"], e["o"], e["at"], "a"))
        elif e["kind"] == "hold":
            still = BIN / f"{e['clip']}-hold.mp4"
            ff("-ss", e["i"] - 1 / FPS, "-i", path(e["clip"]), "-f", "lavfi", "-t", 10, "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a",
               "-vf", "trim=end_frame=1,tpad=stop_mode=clone:stop_duration=10", "-t", 10, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", still)
            V[1].append(clip(f"v{n}", f"{e['clip']}-hold", 0, e["d"], e["at"], "v"))
            D["title-1.png"] = D["title-2.png"] = 60
            V[2].append(clip(f"t{n}a", "title-1.png", 0, TITLE[1][1] - TITLE[0][1], e["at"] + TITLE[0][1], "v"))
            V[2].append(clip(f"t{n}b", "title-2.png", 0, e["d"] - TITLE[1][1], e["at"] + TITLE[1][1], "v"))
        elif e["kind"] == "grid":
            for k, (c, i) in enumerate(e["src"]):
                pos = [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)][k]
                V[2 + k].append(clip(f"g{n}{k}", c, i, i + e["d"], e["at"], "v", motion=pos))
                if c not in GFX_NAMES: A[1 if k == 0 else 4 + k].append(clip(f"ga{n}{k}", c, i, i + e["d"], e["at"], "a", gain=-3))
        elif e["kind"] == "bed":
            A[4].append(clip(f"b{n}a", "song-bed", 0, e["up1"], 0, "a"))
            A[4].append(clip(f"b{n}b", "song-bed", e["up1"], e["up2"], e["up1"], "a", gain=e["duck"]))
            A[4].append(clip(f"b{n}c", "song-bed", e["up2"], e["total"], e["up2"], "a"))
        elif e["kind"] == "a":
            tr = 2
            if e["clip"] == "butler-speech" and e["fade"] > 2: tr = 3
            A[tr].append(clip(f"x{n}", e["clip"], e["i"], e["o"], e["at"], "a", gain=e["gain"]))
    tr = lambda items: "<track>" + "".join(items) + "</track>"
    body = (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5"><sequence id="seq-1"><name>Teaser rough cut</name><duration>{fr(total)}</duration>'
            f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate><media><video><format><samplecharacteristics><width>1920</width><height>1080</height>'
            f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate></samplecharacteristics></format>' + "".join(tr(V[k]) for k in V) +
            '</video><audio>' + "".join(tr(A[k]) for k in A) + '</audio></media></sequence></xmeml>\n')
    (OUT / "teaser-roughcut.xml").write_text(body)

if __name__ == "__main__":
    ev, total = build_events()
    (OUT / "edl.json").write_text(json.dumps(ev, indent=1))
    print("timeline", round(total, 1), "s,", sum(e["kind"] != "a" for e in ev), "shots")
    if "--xml-only" not in sys.argv: render(ev, total)
    xml(ev, total)
    print("done")
