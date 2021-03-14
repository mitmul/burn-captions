#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import math
import pprint
import shlex

import imageio
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pycaption import SRTReader
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--srt", type=str, required=True)
    parser.add_argument("--font", type=str, default="/System/Library/Fonts/HelveticaNeue.ttc")
    parser.add_argument("--font-size", type=int, default=36)
    parser.add_argument("--font-index", type=int, default=10)
    parser.add_argument("--font-italic-index", type=int, default=11)
    parser.add_argument("--secondary-font-index", type=int, default=10)
    parser.add_argument("--secondary-font-italic-index", type=int, default=11)
    parser.add_argument("--secondary-font-size", type=int, default=52)
    parser.add_argument("--secondary-font-start", type=int, default=432)
    parser.add_argument("--secondary-font-end", type=int, default=448)
    parser.add_argument("--bottom-space", type=int, default=36)

    parser.add_argument("--blueback", action="store_true", default=False)
    parser.add_argument("--pixelformat", type=str, default="yuv422p10le")
    parser.add_argument(
        "--quality", type=int, default=10, help="The quality measure of the output video. It should be within 0 to 10."
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=None,
        help="The bitrate in b/s of the output video. The default is None (--quality is used).",
    )
    parser.add_argument(
        "--skip-first", action="store_true", default=False, help="If it is True, the first caption will be skipped."
    )
    parser.add_argument(
        "--break-after", type=float, default=0, help="Enable test mode to finish after the given seconds."
    )
    parser.add_argument("--output-params", type=str)
    args = parser.parse_args()

    srt_text = open(args.srt).read()
    srt = SRTReader().read(srt_text, lang="en")
    captions = srt.get_captions("en")

    reader = imageio.get_reader(args.video)
    meta_data = reader.get_meta_data()
    pprint.pprint(meta_data)
    fps = meta_data["fps"]

    if args.output_params:
        output_params = shlex.split(args.output_params)
    else:
        output_params = []

    print("save to:", args.out)
    writer = imageio.get_writer(
        args.out,
        codec=meta_data["codec"],
        fps=fps,
        pixelformat=args.pixelformat,
        macro_block_size=20,
        quality=args.quality,
        bitrate=args.bitrate,
        output_params=output_params,
    )

    caption_data = []
    for caption in captions:
        if len(caption_data) == 0 and args.skip_first:
            args.skip_first = False
            continue
        start_sec = caption.start / 1000 / 1000
        end_sec = caption.end / 1000 / 1000
        start_frame_num = int(start_sec * fps)
        end_frame_num = int(end_sec * fps)
        text = caption.get_text()

        italic = False
        if "<i>" in text:
            text = text.replace("<i>", "")
            text = text.replace("</i>", "")
            italic = True

        caption_data.append(
            {
                "text": text,
                "start_frame_num": start_frame_num,
                "end_frame_num": end_frame_num,
                "italic": italic,
            }
        )

    caption_i = 0
    pbar = tqdm(total=reader.count_frames())

    for frame_i, frame in enumerate(reader):
        if args.blueback:
            frame = np.ones((1080, 1920, 3), dtype=np.uint8)
            frame = frame * np.array([[[0, 0, 255]]], dtype=np.uint8)

        if caption_i < len(caption_data):
            caption = caption_data[caption_i]
        if caption["start_frame_num"] <= frame_i <= caption["end_frame_num"]:
            image = Image.fromarray(frame)
            draw = ImageDraw.Draw(image)
            if args.secondary_font_start <= caption_i <= args.secondary_font_end:
                if caption["italic"]:
                    font_i = args.secondary_font_italic_index
                else:
                    font_i = args.secondary_font_index

                draw.font = ImageFont.truetype(
                    args.font,
                    args.secondary_font_size,
                    font_i,
                    layout_engine=ImageFont.LAYOUT_BASIC,
                )
            else:
                if caption["italic"]:
                    font_i = args.font_italic_index
                else:
                    font_i = args.font_index

                draw.font = ImageFont.truetype(
                    args.font,
                    args.font_size,
                    font_i,
                    layout_engine=ImageFont.LAYOUT_BASIC,
                )

            h, w, _ = frame.shape
            wt, ht = draw.font.getsize_multiline(caption["text"])

            # fmt: off
            pos = [
                int(w / 2 - wt / 2),  # center
                h - ht - args.bottom_space  # bottom
            ]
            # fmt: on
            color = (255, 255, 255)
            draw.text(
                pos,
                caption["text"],
                color,
                align="center",
                stroke_width=2,
                stroke_fill=(0, 0, 0),
            )
            writer.append_data(np.array(image))
        elif frame_i > caption["end_frame_num"]:
            caption_i += 1
            writer.append_data(frame)
        else:
            writer.append_data(frame)
        pbar.update(1)

        if args.break_after > 0 and (frame_i / fps) > args.break_after:
            break

        frame_i += 1

    reader.close()
    writer.close()
