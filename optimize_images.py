import os
from PIL import Image

src_dir = "website/public/art/renders"
# We'll save them back to the same place, but with a backup first? 
# No, let's just overwrite them to save space and simplify deployment.

files = [f for f in os.listdir(src_dir) if f.endswith(".png")]
print(f"Found {len(files)} images to optimize.")

for i, filename in enumerate(files):
    path = os.path.join(src_dir, filename)
    try:
        with Image.open(path) as img:
            # Calculate new height to maintain aspect ratio
            width = 500 # Sufficient for gallery and divination display
            w_percent = (width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            
            # Resize and convert to optimized PNG (or JPEG if we wanted even smaller)
            img = img.resize((width, h_size), Image.Resampling.LANCZOS)
            img.save(path, optimize=True)
            
            if i % 10 == 0:
                print(f"Optimized {i}/{len(files)}...")
    except Exception as e:
        print(f"Error optimizing {filename}: {e}")

print("Optimization complete!")
