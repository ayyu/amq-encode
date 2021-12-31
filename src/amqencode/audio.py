import ffmpeg
import re, subprocess
from .common import get_null_output

mean_dB_re = re.compile(r' mean_volume: (?P<mean>-?[0-9]+\.?[0-9]*)')
peak_dB_re = re.compile(r' max_volume: (?P<peak>-?[0-9]+\.?[0-9]*)') 

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


def get_norm_filter(filename, target_peak_dB=-0.5, target_mean_dB=-18.5, **kwargs):
  input_levels = detect_volume(filename, **kwargs)
  diff_peak = target_peak_dB - input_levels['peak_dB']
  diff_mean = target_mean_dB - input_levels['mean_dB']
  return {
    'volume': '{}dB'.format(min(diff_peak, diff_mean))
  }


__all__ = [
  'audio_settings',
  'mp3_settings',
  'opus_settings',
  'detect_volume',
  'get_norm_filter'
]