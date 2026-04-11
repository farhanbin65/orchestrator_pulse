from bangla_text_renderer import BanglaTextRenderer
from PIL import Image

# Create renderer with your Bangla font
renderer = BanglaTextRenderer(
    font_path="assets/NotoSansBengali-Regular.ttf",
    font_size=40
)

# Render text
text = "বাংলা লেখা সঠিকভাবে"
img = renderer.render_text(text, width=800)

# Save image
img.save('output.png')