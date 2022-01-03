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

audio_settings = {
  'b:a': '320k',
  'ac': 2
}

mp3_settings = {
  'c:a': 'libmp3lame'
}

opus_settings = {
  'c:a': 'libopus'
}

target_peak_dB = -0.5
target_mean_dB = -18.5


def detect_volume(
    input_file: str,
    **kwargs) -> Dict[str, Union[float, None]]:
  """Return peak and mean dB for the input file"""
  ignore_streams = {'vn': None, 'sn': None, 'dn': None}
  seek = common.extract_seek(kwargs)
  cmd = (ffmpeg
    .input(input_file)
    .filter('volumedetect')
    .output(devnull, format='null', **ignore_streams, **kwargs)
    .compile())
  # force fast seek or else volume detection won't respect seeking
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
  """Returns a filter dictionary for applying gain based on peak and mean dB"""
  input_levels = detect_volume(input_file, **kwargs)
  diff_peak = target_peak_dB - input_levels['peak_dB']
  diff_mean = target_mean_dB - input_levels['mean_dB']
  return {'volume': '{:.1f}dB'.format(min(diff_peak, diff_mean))}


def encode_mp3(
    input_file: str,
    output_file: str,
    af: Union[str, dict] = {},
    **kwargs) -> None:
  """Encodes an MP3 from the input file"""
  audio = common.apply_filters(
    ffmpeg.input(input_file).audio,
    common.parse_filter_string(af))
  seek = common.extract_seek(kwargs)
  for key in vp9_settings: kwargs.pop(key, None)
  cmd = ffmpeg.output(
    audio, output_file,
    format='mp3', **kwargs).compile(overwrite_output=True)
  if not len(seek) == 0: cmd[1:1] = seek
  subprocess.run(cmd)
  