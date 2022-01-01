__all__ = [
  'map_settings',
  'dict_filter_stream',
  'parse_filter_string'
]

from typing import Dict, Union

map_settings = {
  'map_metadata': -1,
  'map_chapters': -1,
  'sn': None
}


def apply_filters(
    stream: object,
    filters: Union[str, list]) -> object:
  """Returns the supplied ffmpeg-python input object with filters applied"""
  filters = parse_filter_string(filters)
  for k, v in filters.items():
    if v == None: stream = stream.filter(k)
    else: stream = stream.filter(k, v)
  return stream


def parse_filter_string(input_filters: Union[str, dict]) -> Dict[str, any]:
  """Converts a filter string into a filter dict"""
  if len(input_filters) == 0: return {}
  if isinstance(input_filters, str):
    return dict(
      [x.split('=') if '=' in x else [x, None]
      for x in input.split(',')])
  return input_filters
