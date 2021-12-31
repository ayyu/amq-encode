import os
from typing import Union, Dict

from ffmpeg.nodes import stream_operator

map_settings = {
  'map_metadata': -1,
  'map_chapters': -1,
  'sn': '-sn'
}

def get_null_output() -> str:
  """Returns the name of the null output device based on OS"""
  if os.name == 'nt':
    return 'NUL'
  return '/dev/null/'


def apply_filters(stream: object, filters: Union[str, list]) -> object:
  """Returns the supplied ffmpeg-python input object with filters applied"""
  filters = parse_filter_string(filters)
  for k, v in filters.items():
    if v == None:
      stream = stream.filter(k)
    else:
      stream = stream.filter(k, v)
  return stream


def parse_filter_string(input_filters: Union[str, dict]) -> Dict[str, any]:
  """Converts a filter string into a filter dict"""
  if isinstance(input_filters, str):
    if len(input_filters) > 0:
      return dict([x.split('=') if '=' in x else [x, None] for x in input.split(',')])
    else:
      return {}
  return input_filters


__all__ = [
  'get_null_output',
  'dict_filter_stream',
  'parse_filter_string'
]
