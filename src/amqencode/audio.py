__all__ = [
  'audio_settings',
  'mp3_settings',
  'opus_settings',
  'detect_volume',
  'get_norm_filter',
  'encode_mp3'
]


import re
import subprocess
from os import devnull
from typing import Dict, Union

import ffmpeg

from . import common
from .video import vp9_settings


_mean_dB_re = re.compile(r' mean_volume: (?P<mean>-?[0-9]+\.?[0-9]*)')
_peak_dB_re = re.compile(r' max_volume: (?P<peak>-?[0-9]+\.?[0-9]*)')

_ignore_streams = {'vn': None, 'sn': None, 'dn': None}
"""(dict of str: None): Streams to ignore when encoding audio."""

audio_settings = {
  'b:a': '320k',
  'ac': 2 }
"""(dict of str: str): audio encoding parameters for both codecs."""

mp3_settings = { 'c:a': 'libmp3lame' }
"""(dict of str: str): MP3 encoding parameters."""

opus_settings = { 'c:a': 'libopus' }
"""(dict of str: str): Opus encoding parameters."""

target_peak_dB = -0.5
"""(float): Target normalization peak volume in decibels."""

target_mean_dB = -18.5
"""(float): Target normalization mean volume in decibels."""


def detect_volume(
    input_file: str,
    **kwargs) -> Dict[str, Union[float, None]]:
  """
  Returns the peak and mean dB for the input file.

  Args:
    input_file (str): Path to audio file to detect.
    **kwargs: Arbitrary keyword arguments. Includes arguments specific to this
      package, as well as any native ffmpeg parameters you wish to pass.
  
  Returns:
    (dict of str: float): Dictionary with keys `peak_dB` and `mean_dB`.
  """
  seek = common.extract_seek(kwargs)
  cmd = (ffmpeg
    .input(input_file)
    .filter('volumedetect')
    .output(devnull, format='null', **_ignore_streams, **kwargs)
    .compile())
  if not len(seek) == 0: cmd[1:1] = seek
  p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  output = p.stdout.decode('utf-8').splitlines()

  mean_dB = None
  peak_dB = None
  for line in output:
    mean_dB_match = _mean_dB_re.search(line)
    peak_dB_match = _peak_dB_re.search(line)
    if mean_dB_match: mean_dB = float(mean_dB_match.group('mean'))
    if peak_dB_match: peak_dB = float(peak_dB_match.group('peak'))
  return {
    'peak_dB': peak_dB,
    'mean_dB': mean_dB}


def get_norm_filter(
    input_file: str,
    target_peak_dB: float = target_peak_dB,
    target_mean_dB: float = target_mean_dB,
    **kwargs) -> Dict[str, str]:
  """
  Returns a filter dictionary for applying gain based on peak and mean dB.
  Will avoid exceeding either of the targeted peak or mean.
  Does not apply any filtering to the file.

  Args:
    input_file (str): Path to audio file to be filtered.
    target_peak_dB (float, optional): Defaults to -0.5 dB.
    target_mean_dB (float, optional): Defaults to -18.5 dB.
    **kwargs: Arbitrary keyword arguments. Includes arguments specific to this
      package, as well as any native ffmpeg parameters you wish to pass.
  
  Returns:
    (dict of str: str): Filter dictionary for volume adjustment.
  """
  input_levels = detect_volume(input_file, **kwargs)
  diff_peak = target_peak_dB - input_levels['peak_dB']
  diff_mean = target_mean_dB - input_levels['mean_dB']
  return {'volume': '{:.1f}dB'.format(min(diff_peak, diff_mean))}


def encode_mp3(
    input_file: str,
    output_file: str,
    **kwargs) -> None:
  """
  Encodes an mp3 from the supplied input file.

  Args:
    input_file (str): Path to video file to encode from.
    output_file (str): Path to output encoded file.
    **kwargs: Arbitrary keyword arguments. Includes arguments specific to this
      package, as well as any native ffmpeg parameters you wish to pass.

  Keyword Args:
    af (str or dict of str: str/None):
      String or dictionary of audio filters to apply.
  """

  audio = common.apply_filters(
    ffmpeg.input(input_file).audio,
    common.parse_filter_string(kwargs.pop('af', {})))

  kwargs.pop('vf', None)
  for key in vp9_settings: kwargs.pop(key, None)
  kwargs.update(_ignore_streams)

  seek = common.extract_seek(kwargs)
  cmd = ffmpeg.output(
    audio, output_file,
    format='mp3', **kwargs).compile()
  if not len(seek) == 0: cmd[1:1] = seek
  subprocess.run(cmd)
