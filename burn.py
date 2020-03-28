#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import math
import os
import pprint

import imageio
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pycaption import SRTReader
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('--video', type=str)
parser.add_argument('--srt', type=str)
parser.add_argument('--font', type=str,
                    default='/System/Library/Fonts/HelveticaNeue.ttc')
parser.add_argument('--font-size', type=int, default=36)
parser.add_argument('--bottom-space', type=int, default=36)
parser.add_argument('--skip-first', action='store_true', default=False)
args = parser.parse_args()

srt_text = open(args.srt).read()
srt = SRTReader().read(srt_text, lang='en')
captions = srt.get_captions('en')

reader = imageio.get_reader(args.video)
meta_data = reader.get_meta_data()
pprint.pprint(meta_data)
fps = meta_data['fps']

out_fn = os.path.splitext(args.video)[0] + '_sub.mp4'
print('out_fn:', out_fn)
writer = imageio.get_writer(
    out_fn, fps=fps, pixelformat='yuv420p', macro_block_size=8, quality=10)

caption_data = []
for caption in captions:
    if len(caption_data) == 0 and args.skip_first:
        args.skip_first = False
        continue
    start_sec = caption.start / 1000 / 1000
    end_sec = caption.end / 1000 / 1000
    start_frame_num = start_sec * fps
    end_frame_num = end_sec * fps
    text = caption.get_text()

    indent = False
    if '<i>' in text:
        text = text.replace('<i>', '')
        text = text.replace('</i>', '')
        indent = True

    start_frame_num = int(math.floor(start_frame_num))
    end_frame_num = int(math.ceil(end_frame_num))

    caption_data.append({
        'text': text,
        'start_frame_num': start_frame_num,
        'end_frame_num': end_frame_num,
        'italic': True,
    })


caption_i = 0
pbar = tqdm(total=reader.count_frames())
for frame_i, frame in enumerate(reader):
    caption = caption_data[caption_i]
    if caption['start_frame_num'] <= frame_i <= caption['end_frame_num']:
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image)
        draw.font = ImageFont.truetype(
            args.font, args.font_size, 13 if caption['italic'] else 0,
            layout_engine=ImageFont.LAYOUT_BASIC)

        h, w, _ = frame.shape
        wt, ht = draw.font.getsize_multiline(caption['text'])

        pos = [
            int(w / 2 - wt / 2),  # center
            h - ht - args.bottom_space  # bottom
        ]
        color = (255, 255, 255)
        draw.text(pos, caption['text'], color, align='center', stroke_width=2, stroke_fill=(0, 0, 0))
        writer.append_data(np.array(image))
    elif frame_i > caption['end_frame_num']:
        caption_i += 1
    else:
        writer.append_data(frame)

    pbar.update(1)

reader.close()
writer.close()
