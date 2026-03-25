from PIL import Image
import os

base = "/home/gg/Documents/FG-ToolWatcher/GUI/__ASSETS/icons"

for filename in os.listdir(base):
    if filename.lower().endswith(('.ico', '.png')):
        path = os.path.join(base, filename)
        try:
            img = Image.open(path).convert("RGBA")
            w, h = img.size
            if w != 256 or h != 256:
                img = img.resize((256, 256), Image.LANCZOS)
                img.save(path)
                print(f"{filename}: {w}x{h} → 256x256")
            else:
                print(f"{filename}: already 256x256, skipped")
        except Exception as e:
            print(f"{filename}: ERROR — {e}")
