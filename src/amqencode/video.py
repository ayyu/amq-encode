__all__ = [
  'vp9_settings',
  'resolutions',
  'probe_dimensions',
  'encode_webm'
]

from os import devnull

from fractions import Fraction
import subprocess
from typing import Dict, Union

import ffmpeg

from . import common

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

init_vf = {
  'scale': 1,
  'setsar': 1
}

def probe_dimensions(input_file: str) -> Dict[str, any]:
  """Returns a dict of dimensional info for the input"""
  metadata = ffmpeg.probe(input_file, select_streams='v')['streams'][0]
  return {
    'width': int(metadata['width']),
    'height': int(metadata['height']),
    'sar': Fraction(metadata['sample_aspect_ratio'].replace(':', '/')),
    'dar': Fraction(metadata['display_aspect_ratio'].replace(':', '/'))}


def encode_webm(
    input_file: str,
    output_file: str,
    **kwargs) -> None:
  """Encodes a webm from the supplied inputs"""
  seek = common.extract_seek(kwargs)
  input = ffmpeg.input(input_file)
  audio = common.apply_filters(input.audio,
    common.parse_filter_string(kwargs.pop('af', {})))
  video = common.apply_filters(input.video,
    common.parse_filter_string(kwargs.pop('vf', {})))
  pass_1_cmd = ffmpeg.output(
    video,
    devnull, format='null',
    **dict({'pass': 1}, **kwargs)).compile()
  pass_2_cmd = ffmpeg.output(
    audio, video,
    output_file, format='webm',
    **dict({'pass': 2}, **kwargs)).compile()
  if not len(seek) == 0:
    pass_1_cmd[1:1] = seek
    pass_2_cmd[1:1] = seek
  subprocess.run(pass_1_cmd)
  subprocess.run(pass_2_cmd)