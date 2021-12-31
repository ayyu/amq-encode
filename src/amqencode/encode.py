__all__ = [
  'encode_all',
  'encode_webm',
  'encode_mp3',
  'mux_folder',
  'mux_clean',
]


import argparse
import os
from typing import Union

import ffmpeg

from . import audio, common, video


def mux_folder(
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
    vf: Union[str, dict] = {},
    af: Union[str, dict] = {},
    norm: bool = False,
    vp9_settings: dict = {},
    resolutions: list = video.resolutions,
    override_dimensions: dict = {},
    **kwargs) -> None:
  """Encodes a video in all requested resolutions and an mp3."""
  vp9_settings = dict(video.vp9_settings, **vp9_settings)
  if not os.path.exists(output_dir): os.makedirs(output_dir)
  # turn filters into dicts
  vf = common.parse_filter_string(vf)
  af = common.parse_filter_string(af)
  vf.update(video.init_vf)
  if norm:
    print('Detecting input volume')
    af = dict(af, **audio.get_norm_filter(input_file, **kwargs))
  probe_data = video.probe_dimensions(input_file).update(override_dimensions)
  # common settings
  common_settings = dict(
    common.map_settings,
    **audio.audio_settings,
    **kwargs)
  # sort unique resolutions
  resolutions = sorted(list(set(resolutions)))
  smallest_resolution = next((i for i, x in enumerate(resolutions) if x), None)
  for resolution in resolutions:
    output_file = os.path.join(output_dir, '{res}.{ext}'.format(
      res=resolution,
      ext='mp3' if resolution == 0 else '.webm'))
    if resolution == 0:
      audio.encode_mp3(
        input_file, output_file,
        af=af,
        **audio.mp3_settings,
        **common_settings)
    else:
      if (resolution > probe_data['height']+16 and
          resolution > smallest_resolution):
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


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', type=str, required=True, help='input video')
  parser.add_argument('-crf', type=int, help='constant rate factor')
  parser.add_argument('-g', type=int, help='interval between keyframes')
  parser.add_argument('-vf', '-filter:v', type=str, default='', help='video filter string')
  parser.add_argument('-af', '-filter:a', type=str, default='', help='audio filter string')
  parser.add_argument('-ss', type=str, help='start time')
  parser.add_argument('-to', type=str, help='end time')
  parser.add_argument('-t', type=str, help='encode duration')
  parser.add_argument('-norm', action='store_true', help='normalize output volume')
  parser.add_argument('-outdir', type=str, help='output path')
  parser.add_argument('-skip', type=int, nargs='+', help='resolutions to skip')
  parser.set_defaults(
    norm=False,
    outdir='./source/',
    skip=[]
  )
  args = parser.parse_args()

  if not os.path.isfile(args.i):
    print('invalid input file provided')
    exit()
  
  kwargs = {k: v for k, v in {
    'ss': args.ss,
    'to': args.to,
    't': args.t}.items() if not v == None}

  vp9_settings = {k: v for k, v in {
    'crf': args.crf,
    'g': args.g}.items() if not v == None}

  resolutions = [res for res in video.resolutions if res not in args.skip]

  encode_all(
    args.i, args.outdir,
    vf=args.vf, af=args.af,
    norm=args.norm,
    vp9_settings=vp9_settings,
    **kwargs)
