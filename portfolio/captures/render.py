"""Cut list -> looping clips. Each segment: (src, start, dur, cw, ch, x0, y0, x1, y1).
Crop window cw x ch (16:9) pans linearly from (x0,y0) to (x1,y1) over the segment, then scales to 1280x720."""
import subprocess, sys, os, json
import imageio_ffmpeg as f
FF = f.get_ffmpeg_exe()
OUT = '/home/user/random_proj/portfolio/site/public/shots'
TMP = '/tmp/claude-0/-home-user-random-proj/18377e1a-98ff-502b-99e1-e66b3b05e846/scratchpad/seg'
os.makedirs(TMP, exist_ok=True)

PX = 434  # x for a 640-wide crop centred on the phone column (538..971)
PLAN = {
  'fantasy-reality': [
    ('fr-leaderboard.mov', 3.6, 3.5, 640, 360, PX, 60, PX, 330),
    ('fr-markets.mov',     4.0, 4.0, 800, 450, 354, 320, 354, 320),
    ('fr-markets.mov',     9.5, 2.2, 640, 360, PX, 380, PX, 380),
    ('fr-graphs.mov',      3.9, 4.1, 800, 450, 352, 139, 352, 404),
  ],
  'degenbench': [
    ('dgb-overview.mov',    0.5, 3.5, 640, 360, PX, 250, PX, 420),
    ('dgb-user-detail.mov', 3.9, 4.0, 800, 450, 352, 73, 352, 469),
    ('dgb-overview.mov',    9.0, 3.5, 640, 360, PX, 250, PX, 500),
    ('dgb-overview.mov',   14.0, 3.0, 640, 360, PX, 100, PX, 300),
  ],
  'mention-tracker': [
    ('mt-overview.mov', 0.5, 4.5, 960, 540, 262, 40, 262, 40),
    ('mt-overview.mov', 5.0, 3.5, 960, 540, 262, 250, 262, 420),
    ('mt-overview.mov', 8.5, 3.2, 1484, 835, 0, 100, 0, 100),
  ],
  'emberfall': [
    ('ef-static.mov', 0.3, 3.7, 1488, 837, 0, 60, 0, 60),
    ('ef-static.mov', 4.0, 2.6, 744, 418, 200, 250, 400, 250),
    ('ef-travel.mov', 5.5, 4.0, 800, 450, 520, 300, 520, 300),
    ('ef-travel.mov', 12.0, 4.0, 800, 450, 688, 0, 688, 400),
  ],
  'music-for-parking': [
    ('mfp-static.mov', 0.5, 7.0, 744, 418, 480, 250, 580, 280),
    ('mfp-static.mov', 8.0, 6.5, 900, 506, 580, 30, 560, 120),
  ],
  'gizzard-hours': [
    ('gizzard-hours.webm', 0.6, 3.4, 800, 450, 240, 0, 240, 60),
    ('gizzard-hours.webm', 5.0, 4.5, 800, 450, 240, 90, 240, 130),
    ('gizzard-hours.webm', 11.0, 3.0, 800, 450, 240, 100, 240, 100),
    ('gizzard-hours.webm', 15.2, 3.0, 800, 450, 240, 60, 240, 60),
  ],
  'pre-speech-odds': [
    ('pre-speech-odds.webm', 1.2, 3.3, 960, 540, 160, 0, 160, 60),
    ('pre-speech-odds.webm', 7.8, 3.6, 800, 450, 240, 120, 240, 120),
    ('pre-speech-odds.webm', 12.8, 3.4, 960, 540, 160, 80, 160, 120),
    ('pre-speech-odds.webm', 17.4, 3.5, 960, 540, 160, 100, 160, 140),
  ],
  'adaptive-resume': [
    ('adaptive-resume.webm', 1.0, 3.0, 960, 540, 160, 0, 160, 0),
    ('adaptive-resume.webm', 71.0, 10.5, 1280, 720, 0, 0, 0, 0),
  ],
  'fr-newsletter': [
    ('fr-newsletter.webm', 10.2, 4.0, 960, 540, 160, 40, 160, 40),
    ('/home/user/random_proj/portfolio/site/public/art/newsletter-chart-meme.webp', 0, 4.0, 'IMG', 0, 0, 0, 0, 'PAN'),
    ('fr-newsletter.webm', 14.5, 4.0, 1280, 720, 0, 0, 0, 0),
    ('/home/user/random_proj/portfolio/site/public/art/newsletter-chart-editorial.webp', 0, 3.5, 'IMG', 0, 0, 0, 0, 'PAN'),
  ],
  'sex-house-island': [
    ('shi-new-game.mov', 0.5, 2.5, 1391, 782, 0, 100, 0, 100),
    ('shi-new-game.mov', 4.5, 3.5, 1391, 782, 0, 0, 0, 212),
    ('shi-gameplay.mov', 3.0, 3.0, 1391, 782, 0, 150, 0, 150),
    ('shi-new-game.mov', 16.0, 3.5, 1391, 782, 0, 150, 0, 150),
    ('shi-gameplay.mov', 16.5, 2.3, 1391, 782, 0, 0, 0, 0),
  ],
}

def run(a): subprocess.run(a, check=True, capture_output=True)
def render(slug):
  segs = PLAN[slug]; files = []
  for i, (src, st, du, cw, ch, x0, y0, x1, y1) in enumerate(segs):
    p = f'{TMP}/{slug}-{i}.mp4'
    if cw == 'IMG':  # still image: crop a 16:9 window the full width and pan it top to bottom
      from PIL import Image
      W, H = Image.open(src).size; ch = int(W * 9 / 16); cw = W; x0 = x1 = 0; y0 = 0; y1 = max(0, H - ch)
      pre = ['-loop', '1', '-t', str(du), '-i', src]
    else:
      pre = ['-ss', str(st), '-t', str(du), '-i', src]
    vf = f"crop={cw}:{ch}:'{x0}+({x1}-{x0})*t/{du}':'{y0}+({y1}-{y0})*t/{du}',scale=1280:720:flags=lanczos,fps=24,format=yuv420p"
    run([FF, '-y', '-loglevel', 'error', *pre, '-vf', vf, '-an', '-c:v', 'libx264', '-crf', '16', '-preset', 'fast', p])
    files.append(p)
  lst = f'{TMP}/{slug}.txt'; open(lst, 'w').write(''.join(f"file '{p}'\n" for p in files))
  cat = f'{TMP}/{slug}-all.mp4'
  run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', cat])
  run([FF, '-y', '-loglevel', 'error', '-i', cat, '-an', '-c:v', 'libvpx-vp9', '-crf', '33', '-b:v', '0', '-deadline', 'good', '-cpu-used', '2', '-row-mt', '1', f'{OUT}/{slug}.webm'])
  run([FF, '-y', '-loglevel', 'error', '-i', cat, '-an', '-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{OUT}/{slug}.mp4'])
  run([FF, '-y', '-loglevel', 'error', '-i', cat, '-frames:v', '1', '-vf', 'scale=1280:720', '-c:v', 'libwebp', '-quality', '82', f'{OUT}/{slug}-poster.webp'])
  total = sum(s[2] for s in segs)
  print(f"{slug}: {len(segs)} cuts, {total:.1f}s, webm {os.path.getsize(f'{OUT}/{slug}.webm')//1024} KB, mp4 {os.path.getsize(f'{OUT}/{slug}.mp4')//1024} KB")

for slug in (sys.argv[1:] or PLAN): render(slug)
