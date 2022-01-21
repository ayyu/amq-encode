__all__ = [
  'map_settings',
  'apply_filters',
  'extract_seek',
  'parse_filter_string'
]

from typing import Dict, Union


map_settings = {
  'dn': None,
  'sn': None,
  'map_chapters': -1}
"""(dict of str: None): Streams to deselect for ffmpeg output mapping."""


def apply_filters(
    stream: object,
    filters: Union[str, dict]) -> object:
  """
  Returns the supplied ffmpeg-python Stream with filters applied.

  Args:
    stream (ffmpeg.Stream): ffmpeg-python stream to be filtered.
    filters (str or dict of str: str/int/None):
      String or dictionary of filters to be applied to stream.
  
  Returns:
    ffmpeg.Stream: Filtered stream.
  """
  filters = parse_filter_string(filters)
  for k, v in filters.items():
    if v == None: stream = stream.filter(k)
    else: stream = stream.filter(k, v)
  return stream


def parse_filter_string(input_filters: Union[str, dict]) -> Dict[str, any]:
  """
  Converts a filter string into a filter dictionary.
  If a filter dictionary is supplied, it will be returned unchanged.

  Args:
    input_filters (str or dict of str: str/int/None):
      String to be converted to filter dictionary.

  Returns:
    (dict of str: str/int/None): Filter dictionary.
  """
  if len(input_filters) == 0: return {}
  if isinstance(input_filters, str):
    return dict(
      [x.split('=') if '=' in x else [x, None]
      for x in input_filters.split(',')])
  return input_filters


def extract_seek(kwargs: Dict[str, any]) -> list:
  """
  Pops ffmpeg seeking parameters from the input kwargs and returns them in
  a separate list. Use this to reposition seeking parameters in a command list,
  e.g. to force input seeking.
  `t` will override `to`, as ffmpeg normally does anyway.
  Note that this modifies the supplied dictionary in place.

  Args:
    kwargs (dict of str: any): Keyword arguments containing seeking params.
  
  Returns:
    list of str: List of seeking parameters.
  """
  seek = []
  if 'ss' in kwargs:
    seek.extend(['-ss', kwargs.pop('ss'), '-accurate_seek'])
  if 't' in kwargs:
    seek.extend(['-t', kwargs.pop('t')])
    kwargs.pop('to', None)
  elif 'to' in kwargs:
    seek.extend(['-to', kwargs.pop('to')])
  return seek
