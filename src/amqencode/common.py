import os

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

def parse_filter_string(input_string):
  return dict([x.split('=') if '=' in x else [x, None] for x in input_string.split(',')])


__all__ = [
  'get_null_output',
  'dict_filter_stream',
  'parse_filter_string'
]