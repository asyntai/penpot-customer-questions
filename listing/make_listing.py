"""Build the Penpot Hub images from the real captures in listing/raw.

    venv/Scripts/python.exe plugins/penpot/asyntai/listing/make_listing.py

Cover and plugin images are 1390x724, the icon is 400x400. Every picture is a
real capture of the plugin in Penpot, set on a white card with a headline.
The chats are a made-up outdoor shop (test/demo-sessions.json).
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
FONTS = r'C:\Windows\Fonts'

W, H = 1390, 724
INK = (17, 24, 39)
MUTED = (75, 85, 99)
GROUND = (255, 255, 255)
FRAME = (229, 231, 235)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


BOLD = font('segoeuib.ttf', 44)
BODY = font('segoeui.ttf', 22)
SMALL = font('seguisb.ttf', 18)


def fit(img, box_w, box_h):
    scale = min(box_w / img.width, box_h / img.height)
    return img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)


def framed(shot, box_w, box_h):
    """The capture, scaled to the box, with a thin frame and round corners."""
    shot = fit(shot, box_w, box_h)
    radius = 12
    mask = Image.new('L', shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.width - 1, shot.height - 1), radius, fill=255)
    out = Image.new('RGBA', (shot.width + 2, shot.height + 2), (0, 0, 0, 0))
    ImageDraw.Draw(out).rounded_rectangle((0, 0, out.width - 1, out.height - 1), radius + 1, fill=FRAME)
    out.paste(shot, (1, 1), mask)
    return out


def logo_line(draw, x, y):
    icon = Image.open(os.path.join(ROOT, 'static', 'images', 'icon-512.png')).convert('RGBA').resize((34, 34), Image.LANCZOS)
    return icon


def slide(headline, sub, shot, name, side=True):
    img = Image.new('RGB', (W, H), GROUND)
    draw = ImageDraw.Draw(img)
    icon = Image.open(os.path.join(ROOT, 'static', 'images', 'icon-512.png')).convert('RGBA').resize((34, 34), Image.LANCZOS)
    if side:
        # Text on the left, the capture on the right.
        img.paste(icon, (64, 64), icon)
        draw.text((110, 68), 'Asyntai for Penpot', font=SMALL, fill=INK)
        y = 200
        for line in headline:
            draw.text((64, y), line, font=BOLD, fill=INK)
            y += 58
        y += 20
        for line in sub:
            draw.text((64, y), line, font=BODY, fill=MUTED)
            y += 34
        pic = framed(shot, 800, 640)
        img.paste(pic, (W - pic.width - 42, (H - pic.height) // 2), pic)
    else:
        # Headline on top, the capture under it.
        img.paste(icon, (64, 40), icon)
        draw.text((110, 44), 'Asyntai for Penpot', font=SMALL, fill=INK)
        draw.text((64, 96), headline[0], font=BOLD, fill=INK)
        pic = framed(shot, W - 128, H - 190)
        img.paste(pic, ((W - pic.width) // 2, 170), pic)
    path = os.path.join(HERE, name)
    img.save(path, optimize=True)
    print('wrote', name, img.size)


def main():
    added = Image.open(os.path.join(RAW, 'c_added.png')).convert('RGB')
    canvas = Image.open(os.path.join(RAW, 'd_canvas.png')).convert('RGB')
    main_panel = Image.open(os.path.join(RAW, 'b_main.png')).convert('RGB')

    # Canvas area and panel, without the layer list on the left.
    hero = added.crop((690, 50, 3190, 2000))
    # The whole block of cards on the canvas.
    block = canvas.crop((830, 180, 2370, 1850))
    # A close look at the first two rows.
    close = canvas.crop((880, 210, 2320, 960))
    # The panel with its filters, and a little canvas beside it.
    panel = main_panel.crop((1896, 78, 2668, 1212))

    slide(['Real visitor questions,', 'on your canvas'],
          ['Every question people asked your', 'chatbot, as cards in Penpot.'],
          hero, 'cover.png')
    slide(['The most asked', 'question comes first'],
          ['The same question from many visitors', 'becomes one card with its count.'],
          block, 'image-1.png')
    slide(['Where and why', 'they asked'],
          ['Under each question: how often it was', 'asked, the page, the country and the topic.'],
          close, 'image-2.png')
    slide(['Pick a website', 'and a period'],
          ['One website or all of them. The last', '7, 30 or 90 days, or all time.'],
          panel, 'image-3.png')

    icon = Image.open(os.path.join(ROOT, 'static', 'images', 'icon-512.png')).convert('RGBA')
    ground = Image.new('RGBA', icon.size, (255, 255, 255, 255))
    ground.alpha_composite(icon)
    ground.convert('RGB').resize((400, 400), Image.LANCZOS).save(os.path.join(HERE, 'icon-400.png'))
    print('wrote icon-400.png')


if __name__ == '__main__':
    main()
