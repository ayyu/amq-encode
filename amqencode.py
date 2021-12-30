#!/usr/bin/env python3

"""
requires ffmpeg-python
"""

import os, subprocess
import argparse, re
import ffmpeg
from fractions import Fraction

map_settings = {
  'map_metadata': -1,
  'map_chapters': -1,
  'sn': 1
}

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

mean_dB_re = re.compile(r' mean_volume: (?P<mean>-?[0-9]+\.?[0-9]*)')
peak_dB_re = re.compile(r' max_volume: (?P<peak>-?[0-9]+\.?[0-9]*)') 


def probe_video(filename):
  metadata = ffmpeg.probe(filename, select_streams='v')['streams'][0]
  return {
    'width': int(metadata['width']),
    'height': int(metadata['height']),
    'sar': Fraction(metadata['sample_aspect_ratio'].replace(':', '/')),
    'dar': Fraction(metadata['display_aspect_ratio'].replace(':', '/'))
  }


def detect_volume(filename, **kwargs):
  cmd = (ffmpeg
    .input(filename)
    .filter('volumedetect')
    .output(get_null_output(), format='null', **kwargs)
    .compile()
  )
  p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  output = p.stdout.decode('utf-8').splitlines()
  mean_dB = None
  peak_dB = None
  for line in output:
    mean_dB_match = mean_dB_re.search(line)
    peak_dB_match = peak_dB_re.search(line)
    if mean_dB_match:
      mean_dB = mean_dB_match.group('mean')
    elif peak_dB_match:
      peak_dB = peak_dB_match.group('peak')
  return {
    'peak_dB': float(peak_dB),
    'mean_dB': float(mean_dB)
  }


def get_null_output():
  if os.name == 'nt':
    return 'NUL'
  return '/dev/null/'


def dict_filter_stream(stream, filters):
  for k, v in filters.items():
    if v == None:
      stream = stream.filter(k)
    else:
      stream = stream.filter(k, v)
  return stream


def get_norm_filter(filename, target_peak_dB=-0.5, target_mean_dB=-18.5, **kwargs):
  input_levels = detect_volume(filename, **kwargs)
  diff_peak = target_peak_dB - input_levels['peak_dB']
  diff_mean = target_mean_dB - input_levels['mean_dB']
  return {
    'volume': '{}dB'.format(min(diff_peak, diff_mean))
  }


def encode_webm(input_name, output_name, vf={}, af={}, **kwargs):
  input = ffmpeg.input(input_name)
  audio = dict_filter_stream(input.audio, af)
  video = dict_filter_stream(input.video, vf)
  ffmpeg.output(video, get_null_output(), format='null', **dict({'pass': 1}, **kwargs)).run()
  ffmpeg.output(audio, video, output_name, format='webm', **dict({'pass': 2}, **kwargs)).run(overwrite_output=True)
  

def encode_mp3(input_name, output_name, af={}, **kwargs):
  input = ffmpeg.input(input_name)
  audio = dict_filter_stream(input.audio, af)
  stream = ffmpeg.output(audio, output_name, format='mp3', **kwargs)
  stream.run(overwrite_output=True)


def parse_filter_string(input_string):
  return dict([x.split('=') if '=' in x else [x, None] for x in input_string.split(',')])


def mux_folder(input_dir, input_audio, output_dir, norm=False):
  for file in os.listdir(input_dir):
    if file.endswith(('.webm', '.mp3')):
      mux_clean(os.path.join(input_dir, file), input_audio, os.path.join(output_dir, file), norm)


def mux_clean(input_video, input_audio, output_file, norm=False):
  audio = ffmpeg.input(input_audio).audio
  video = ffmpeg.input(input_video).video
  if norm:
    audio = dict_filter_stream(audio, get_norm_filter(input_audio))
  if not os.path.exists(os.path.dirname(output_file)):
    os.makedirs(os.path.dirname(output_file))
  if input_video.endswith('.mp3'):
    args = dict({'shortest': '-vn'}, **mp3_settings, **audio_settings)
    stream = ffmpeg.output(audio, output_file, **args)
  else:
    args = dict({'c:v': 'copy', 'shortest': '-shortest'}, **opus_settings, **audio_settings)
    stream = ffmpeg.output(video, audio, output_file, **args)
  stream.run(overwrite_output=True)


def encode_all(
  input_name, output_dir,
  vf={}, af={},
  norm=False,
  crf=vp9_settings['crf'], g=vp9_settings['g'],
  skip=[],
  resolutions=resolutions,
  **kwargs):
  global vp9_settings
  vp9_settings.update(crf=crf)
  vp9_settings.update(g=g)
  probe_data = probe_video(input_name)
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  if norm:
    print('Detecting input volume')
    af.update(get_norm_filter(input_name, **kwargs))
  for resolution in resolutions:
    if resolution in skip:
      print('Skipping {}p due to passed -skip argument'.format(resolution))
      continue
    output_stem = os.path.join(output_dir,str(resolution))
    if resolution == 0:
      print('Encoding mp3')
      settings = dict(kwargs, **mp3_settings, **audio_settings)
      encode_mp3(input_name, output_stem+'.mp3', af, **settings)
    else:
      if probe_data['height']+10 < resolution and resolution > resolutions[1]:
        print('Skipping {}p due to insufficient input dimensions'.format(resolution))
        continue
      settings = dict(kwargs, **vp9_settings, **opus_settings, **audio_settings)
      vf.update(scale='{w}x{h}'.format(w=round(probe_data['dar']*resolution),h=resolution))
      print('Encoding {}p webm'.format(resolution))
      encode_webm(input_name, output_stem+'.webm', vf, af, **settings)


def main(args):
  if not os.path.isfile(args.i):
    print('invalid input provided')
    return
  vf = {'scale': 1,'setsar': 1}
  af = {}
  kwargs = {}
  if args.vf:
    vf.update(parse_filter_string(args.vf))
  if args.af:
    af.update(parse_filter_string(args.af))
  if args.ss:
    kwargs.update(ss=args.ss)
  if args.to:
    kwargs.update(to=args.to)
  if args.t:
    kwargs.update(t=args.t)
  encode_all(args.i, args.out, vf=vf, af=af, norm=args.norm, crf=args.crf, g=args.g, skip=args.skip, **kwargs)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', type=str, required=True, help='input video')
  parser.add_argument('-crf', type=int, help='constant rate factor')
  parser.add_argument('-g', type=int, help='interval between keyframes')
  parser.add_argument('-vf', '-filter:v', type=str, help='video filter string')
  parser.add_argument('-af', '-filter:a', type=str, help='audio filter string')
  parser.add_argument('-ss', type=str, help='start time')
  parser.add_argument('-to', type=str, help='end time')
  parser.add_argument('-t', type=str, help='encode duration')
  parser.add_argument('-norm', action='store_true', help='normalize output volume')
  parser.add_argument('-out', type=str, help='output path')
  parser.add_argument('-skip', type=int, nargs='+', help='resolutions to skip')
  parser.set_defaults(
    crf=vp9_settings['crf'],
    g=vp9_settings['g'],
    norm=False,
    out='./source/',
    skip=[]
  )
  args = parser.parse_args()
  main(args)