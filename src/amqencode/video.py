from fractions import Fraction
from typing import Dict, Union

import ffmpeg

from .common import apply_filters, get_null_output, parse_filter_string

vp9_settings = {
  'c:v': 'libvpx-vp9',
  'b:v': 0,
  'g': 119,
  'crf': 20,
  'pix_fmt': 'yuv420p',
  'deadline': 'good',
  'cpu-used': 1,
  'row-mt': 1,
  'frame-parallel': 0,
  'tile-columns': 2,
  'tile-rows': 0,
  'threads': 4
}

resolutions = [0, 360, 480, 720]


def probe_dimensions(input_file: str) -> Dict[str, any]:
  """Returns a dict of dimensional info for the input"""
  metadata = ffmpeg.probe(input_file, select_streams='v')['streams'][0]
  return {
    'width': int(metadata['width']),
    'height': int(metadata['height']),
    'sar': Fraction(metadata['sample_aspect_ratio'].replace(':', '/')),
    'dar': Fraction(metadata['display_aspect_ratio'].replace(':', '/'))
  }


def encode_webm(
  input_file: str,
  output_file: str,
  vf: Union[str, dict]={},
  af: Union[str, dict]={},
  **kwargs) -> None:
  input = ffmpeg.input(input_file)
  audio = apply_filters(input.audio, parse_filter_string(af))
  video = apply_filters(input.video, parse_filter_string(vf))
  ffmpeg.output(video, get_null_output(), format='null', **dict({'pass': 1}, **kwargs)).run()
  ffmpeg.output(audio, video, output_file, format='webm', **dict({'pass': 2}, **kwargs)).run(overwrite_output=True)


__all__ = [
  'vp9_settings',
  'resolutions',
  'probe_dimensions'
]
