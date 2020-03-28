#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import math
import pprint

import imageio
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pycaption import SRTReader
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', type=str)
    parser.add_argument('--out', type=str)
    parser.add_argument('--srt', type=str)
    parser.add_argument('--font', type=str,
                        default='/System/Library/Fonts/HelveticaNeue.ttc')
    parser.add_argument('--font-size', type=int, default=36)
    parser.add_argument('--font-index', type=int, default=10)
    parser.add_argument('--font-italic-index', type=int, default=11)
    parser.add_argument('--secondary-font-index', type=int, default=11)
    parser.add_argument('--secondary-font-start', type=int, default=433)
    parser.add_argument('--secondary-font-end', type=int, default=449)
    parser.add_argument('--bottom-space', type=int, default=36)

    parser.add_argument('--codec', type=str, default='prores_ks')
    parser.add_argument('--pixelformat', type=str, default='yuv444p10le')
    parser.add_argument(
        '--quality', type=int, default=10,
        help='The quality measure of the output video. It should be within 0 to 10.')
    parser.add_argument(
        '--skip-first', action='store_true', default=False,
        help='If it is True, the first caption will be skipped.')
    parser.add_argument(
        '--break-after', type=float, default=0,
        help='Enable test mode to finish after the given seconds.')
    args = parser.parse_args()

    srt_text = open(args.srt).read()
    srt = SRTReader().read(srt_text, lang='en')
    captions = srt.get_captions('en')

    reader = imageio.get_reader(args.video)
    meta_data = reader.get_meta_data()
    pprint.pprint(meta_data)
    fps = meta_data['fps']

    print('save to:', args.out)
    writer = imageio.get_writer(
        args.out,
        codec=args.codec,
        fps=fps,
        pixelformat=args.pixelformat,
        macro_block_size=8,
        quality=args.quality,
    )

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

        italic = False
        if '<i>' in text:
            text = text.replace('<i>', '')
            text = text.replace('</i>', '')
            italic = True

        caption_data.append({
            'text': text,
            'start_frame_num': start_frame_num,
            'end_frame_num': end_frame_num,
            'italic': italic,
        })

    caption_i = 0
    pbar = tqdm(total=reader.count_frames())
    for frame_i, frame in enumerate(reader):
        if caption_i < len(caption_data):
            caption = caption_data[caption_i]
        if caption['start_frame_num'] <= frame_i <= caption['end_frame_num']:
            image = Image.fromarray(frame)
            draw = ImageDraw.Draw(image)
            if caption['italic']:
                font_i = args.font_italic_index
            else:
                font_i = args.font_index
            draw.font = ImageFont.truetype(
                args.font, args.font_size, font_i,
                layout_engine=ImageFont.LAYOUT_BASIC
            )

            h, w, _ = frame.shape
            wt, ht = draw.font.getsize_multiline(caption['text'])

            pos = [
                int(w / 2 - wt / 2),  # center
                h - ht - args.bottom_space  # bottom
            ]
            color = (255, 255, 255)
            draw.text(pos, caption['text'], color, align='center',
                      stroke_width=2, stroke_fill=(0, 0, 0))
            writer.append_data(np.array(image))
        elif frame_i > caption['end_frame_num']:
            caption_i += 1
            writer.append_data(frame)
        else:
            writer.append_data(frame)
        pbar.update(1)

        if args.break_after > 0 and (frame_i / fps) > args.break_after:
            break

    reader.close()
    writer.close()
