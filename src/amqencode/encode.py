__all__ = [
  'encode_all',
  'mux_clean_directory',
  'mux_clean',
]


import os
from typing import Union

import ffmpeg

from . import audio, common, video


def mux_clean_directory(
    input_dir: str,
    input_audio: str,
    output_dir: str = './clean/',
    norm: bool = False) -> None:
  """Muxes all mp3 and webm files in the input directory with a clean audio input file"""
  for file in os.listdir(input_dir):
    if file.endswith(('.webm', '.mp3')):
      mux_clean(
        os.path.join(input_dir, file),
        input_audio,
        os.path.join(output_dir, file),
        norm)


mux_folder = mux_clean_directory


def mux_clean(
    input_video: str,
    input_audio: str,
    output_file: str,
    norm: bool = False) -> None:
  """Muxes a given video input file with a clean audio input file"""
  output_dir = os.path.dirname(output_file)
  audio_s = ffmpeg.input(input_audio).audio
  args = dict(audio.audio_settings)
  if not os.path.exists(output_dir): os.makedirs(output_dir)
  if norm: audio_s = common.apply_filters(audio_s, audio.get_norm_filter(input_audio))
  if input_video.endswith('.mp3'):
    args = dict(
      {'vn': None, 'shortest': None},
      **args, **audio.mp3_settings)
    stream = ffmpeg.output(audio_s, output_file, **args)
  else:
    video_s = ffmpeg.input(input_video).video
    args = dict(
      {'c:v': 'copy', 'shortest': None},
      **args, **audio.opus_settings)
    stream = ffmpeg.output(video_s, audio_s, output_file, **args)
  stream.run(overwrite_output=True)


def encode_all(
    input_file: str,
    output_dir: str,
    norm: bool = False,
    **kwargs) -> None:
  """Encodes a video in all requested resolutions and an mp3."""
  resolutions = sorted({res for res
    in kwargs.pop('resolutions', video.resolutions)
    if res not in kwargs.pop('skip_resolutions', [])})
  first_video = next((
    i for i, x
    in enumerate(resolutions)
    if not (x == 0 or x == '0')), None)
  vp9_settings = dict(
    video.vp9_settings,
    **kwargs.pop('vp9_settings', {}))
  if not os.path.exists(output_dir): os.makedirs(output_dir)
  probe_data = dict(
    video.probe_dimensions(input_file),
    **kwargs.pop('override_dimensions', {}),
    **kwargs.pop('force_dimensions', {}))
  vf = dict(
    video.init_vf,
    **common.parse_filter_string(kwargs.pop('vf', {})))
  af = dict(
    common.parse_filter_string(kwargs.pop('af', {})),
    **(audio.get_norm_filter(input_file, **kwargs) if norm else {}))
  common_settings = dict(
    common.map_settings,
    **audio.audio_settings,
    **kwargs)
  for resolution in resolutions:
    output_file = os.path.join(output_dir, '{res}.{ext}'.format(
      res=resolution,
      ext='mp3' if resolution == 0 else 'webm'))
    if resolution == 0:
      audio.encode_mp3(
        input_file, output_file,
        af=af,
        **audio.mp3_settings,
        **common_settings)
    else:
      if (resolution > probe_data['height']+16 and
          resolution > resolutions[first_video]):
        print('Skipping {}p due to insufficient input dimensions'.format(resolution))
        continue
      vf.update(scale='{w}x{h}'.format(
        w=round(probe_data['dar']*resolution),
        h=resolution))
      video.encode_webm(
        input_file, output_file,
        vf=vf, af=af,
        **vp9_settings,
        **audio.opus_settings,
        **common_settings)

