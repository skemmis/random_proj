# Builds index.html from template.html. (The YouTube preview frames in frames.json are no longer used:
# each clip now shows its first frame from posters/ while it loads.)
import pathlib
here = pathlib.Path(__file__).parent
html = (here / "template.html").read_text()
(here / "index.html").write_text(html)
print("index.html", len(html) // 1024, "KB")
