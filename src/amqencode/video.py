from fractions import Fraction
import ffmpeg

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

def probe_video(filename):
  metadata = ffmpeg.probe(filename, select_streams='v')['streams'][0]
  return {
    'width': int(metadata['width']),
    'height': int(metadata['height']),
    'sar': Fraction(metadata['sample_aspect_ratio'].replace(':', '/')),
    'dar': Fraction(metadata['display_aspect_ratio'].replace(':', '/'))
  }


__all__ = [
  'vp9_settings',
  'resolutions',
  'probe_video'
]