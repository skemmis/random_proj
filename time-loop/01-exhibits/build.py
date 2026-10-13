# Builds index.html from template.html and frames.json (four YouTube preview frames per clip, as data URIs).
import json, pathlib
here = pathlib.Path(__file__).parent
frames = json.loads((here / "frames.json").read_text())
html = (here / "template.html").read_text().replace("__FRAMES__", json.dumps(frames))
(here / "index.html").write_text(html)
print("index.html", len(html) // 1024, "KB")
