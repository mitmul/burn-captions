Burn Captions
=============

Burn a given SRT file into a video.

## Requirements

- Python 3.7+

Please install required packages by the following command:

```bash
pip install -r requirements.txt
```

## Usage

```bash
usage: burn.py [-h] [--video VIDEO] [--srt SRT] [--font FONT]
               [--font-size FONT_SIZE] [--bottom-space BOTTOM_SPACE]
               [--skip-first]

optional arguments:
  -h, --help            show this help message and exit
  --video VIDEO
  --srt SRT
  --font FONT
  --font-size FONT_SIZE
  --bottom-space BOTTOM_SPACE
  --skip-first
```

### Example

```bash
python burn.py \
--video sample.mp4 \
--srt sample.srt
```