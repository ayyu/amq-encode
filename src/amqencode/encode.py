# -*- coding: utf-8 -*-

__all__ = [
  'encode_all',
  'mux_clean_directory',
  'mux_clean',
]


import os

import ffmpeg

from . import audio, common, video


def mux_clean_directory(
    input_dir: str,
    input_audio: str,
    output_dir: str = './clean/',
    norm: bool = False) -> None:
  r"""
  Muxes all webm and mp3 files in the input directory with a clean audio file.

  Args:
    input_dir (str): Path containing webm and/or mp3 files to be muxed.
    input_audio (str): Path to clean audio file to mux.
    output_dir (str): Path to output muxed files. Defaults to `./clean/`.
    norm (bool): Whether to normalize audio level of the outputs.
  """
  for file in os.listdir(input_dir):
    if file.endswith(('.webm', '.mp3')):
      mux_clean(
        os.path.join(input_dir, file), input_audio,
        os.path.join(output_dir, file),
        norm)


mux_folder = mux_clean_directory


def mux_clean(
    input_video: str,
    input_audio: str,
    output_file: str,
    norm: bool = False) -> None:
  r"""
  Muxes an input file with a clean audio file.

  Args:
    input_video (str): Path to video file to mux.
    input_audio (str): Path to clean audio file to mux.
    output_file (str): Path to output muxed file.
    norm (bool): Whether to normalize audio level of the output.
  """

  output_dir = os.path.dirname(output_file)
  if not os.path.exists(output_dir): os.makedirs(output_dir)

  audio_s = ffmpeg.input(input_audio).audio
  args = dict(audio.audio_settings)
  if norm:
    audio_s = common.apply_filters(audio_s, audio.get_norm_filter(input_audio))

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
    output_dir: str = './source/',
    norm: bool = False,
    **kwargs) -> None:
  r"""
  Encodes a video in all requested resolutions.

  Args:
    input_file (str): Path to video file to encode from.
    output_dir (str, optional): Path to output encoded files.
      Defaults to `./source/`.
    norm (bool): Whether to normalize audio level of the output.
    **kwargs: Arbitrary keyword arguments. Includes arguments specific to this
      package, as well as any native ffmpeg parameters you wish to pass.
    
  Keyword Args:
    resolutions (list of int): List of resolutions to be encoded,
      in terms of video height. Include 0 to encode an mp3.
      Defaults to `[0, 360, 480, 720]`.
    skip_resolutions (list): List of resolutions to skip. Use this if you want
      to use the default list of resolutions and skip a specific one.
    vp9_settings (dict of str: str/int/None):
      Dictionary of settings to override default VP9 parameters.
    force_dimensions (dict of str: int/Fraction):
      Dictionary of dimensional data to force, ignoring dimensions probed using
      ffprobe on the source video.
      Valid keys are `width`, `height`, `sar`, and `dar`.
    vf (str or dict of str: str/None):
      String or dictionary of video filters to apply.
    af (str or dict of str: str/None):
      String or dictionary of audio filters to apply.
      Normalization filter will be applied after these, if requested.
  """

  if not os.path.exists(output_dir): os.makedirs(output_dir)
  skip_resolutions = kwargs.pop('skip_resolutions', [])
  resolutions = sorted({res for res
    in kwargs.pop('resolutions', video.resolutions)
    if res not in skip_resolutions})
  first_video = next((
    i for i, x
    in enumerate(resolutions)
    if not (x == 0 or x == '0')), None)

  vp9_settings = dict(
    video.vp9_settings,
    **kwargs.pop('vp9_settings', {}))
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

    if resolution == 0: # 0 = mp3
      audio.encode_mp3(
        input_file, output_file,
        af=af,
        **audio.mp3_settings,
        **common_settings)

    else:
      if (resolution > probe_data['height']+16 and
          resolution > resolutions[first_video]):
        print('Skipping {}p due to insufficient input dimensions'
          .format(resolution))
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
