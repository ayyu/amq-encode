"""Audio encoding

Functions and settings for encoding valid AMQ mp3s, as well as detecting volume
using ffprobe.
"""


__all__ = [
    'AUDIO_SETTINGS',
    'MP3_SETTINGS',
    'OPUS_SETTINGS',
    'detect_volume',
    'get_norm_filter',
    'probe_duration',
    'encode_mp3',
]


import re
import subprocess
from os import devnull
from typing import Dict, Union

import ffmpeg

from . import common
from .video import VP9_SETTINGS


_MEAN_DB_RE = re.compile(r' mean_volume: (?P<mean>-?[0-9]+\.?[0-9]*)')
_PEAK_DB_RE = re.compile(r' max_volume: (?P<peak>-?[0-9]+\.?[0-9]*)')

_IGNORE_STREAMS = {'vn': None, 'sn': None, 'dn': None}
"""(dict of str: None): Streams to ignore when encoding audio."""

AUDIO_SETTINGS = {
    'b:a': '320k',
    'ac': 2}
"""(dict of str: str): audio encoding parameters for both codecs."""

MP3_SETTINGS = {'c:a': 'libmp3lame'}
"""(dict of str: str): MP3 encoding parameters."""

OPUS_SETTINGS = {'c:a': 'libopus'}
"""(dict of str: str): Opus encoding parameters."""

DEFAULT_PEAK_DB = -0.5
"""(float): Target normalization peak volume in decibels."""

DEFAULT_MEAN_DB = -18.5
"""(float): Target normalization mean volume in decibels."""


def detect_volume(
        input_file: str,
        **kwargs) -> Dict[str, Union[float, None]]:
    """
    Returns the peak and mean dB for the input file.

    Args:
        input_file (str): Path to audio file to detect.
        **kwargs: Arbitrary keyword arguments. Includes arguments specific to
        this package, as well as any native ffmpeg parameters you wish to pass.

    Returns:
        (dict of str: float): Dictionary with keys `peak_db` and `mean_db`.
    """

    seek = common.extract_seek(kwargs)
    cmd =  (ffmpeg.input(input_file)
            .filter('volumedetect')
            .output(devnull, format='null', **_IGNORE_STREAMS, **kwargs)
            .compile())
    if len(seek) != 0:
        cmd[1:1] = seek

    proc = subprocess.run(
        cmd, check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output = proc.stdout.decode('utf-8').splitlines()

    mean_db = None
    peak_db = None
    for line in output:
        mean_db_match = _MEAN_DB_RE.search(line)
        peak_db_match = _PEAK_DB_RE.search(line)
        if mean_db_match:
            mean_db = float(mean_db_match.group('mean'))
        if peak_db_match:
            peak_db = float(peak_db_match.group('peak'))
    return {
        'peak_db': peak_db,
        'mean_db': mean_db}


def get_norm_filter(
        input_file: str,
        target_peak_db: float = DEFAULT_PEAK_DB,
        target_mean_db: float = DEFAULT_MEAN_DB,
        **kwargs) -> Dict[str, str]:
    """
    Returns a filter dictionary for applying gain based on peak and mean dB.
    Will avoid exceeding either of the targeted peak or mean.
    Does not apply any filtering to the file.

    Args:
        input_file (str): Path to audio file to be filtered.
        target_peak_db (float, optional): Defaults to -0.5 dB.
        target_mean_db (float, optional): Defaults to -18.5 dB.
        **kwargs: Arbitrary keyword arguments. Includes arguments specific to
            this package, as well as any native ffmpeg parameters you wish to
            pass.

    Returns:
        (dict of str: str): Filter dictionary for volume adjustment.
    """
    input_levels = detect_volume(input_file, **kwargs)
    diff_peak = target_peak_db - input_levels['peak_db']
    diff_mean = target_mean_db - input_levels['mean_db']
    return {'volume': f"{min(diff_peak, diff_mean):.1f}dB"}


def probe_duration(input_file: str) -> float:
    """
    Returns the duration of the first audio stream of an input file.

    Args:
        input_file (str): Path to media file to probe.

    Returns:
        (float): Duration of audio stream in seconds.
    """
    metadata = ffmpeg.probe(input_file, select_streams='a')['streams'][0]
    return float(metadata['duration'])


def encode_mp3(
        input_file: str,
        output_file: str,
        **kwargs) -> None:
    """
    Encodes an mp3 from the supplied input file.

    Args:
        input_file (str): Path to video file to encode from.
        output_file (str): Path to output encoded file.
        **kwargs: Arbitrary keyword arguments. Includes arguments specific to
            this package, as well as any native ffmpeg parameters you wish to
            pass.

    Keyword Args:
        af (str or dict of str: str/None):
            String or dictionary of audio filters to apply.
    """

    common.ensure_dir(output_file)

    audio = common.apply_filters(
        ffmpeg.input(input_file).audio,
        common.parse_filter_string(kwargs.pop('af', {})))

    kwargs.pop('vf', None)
    for key in VP9_SETTINGS:
        kwargs.pop(key, None)
    kwargs.update(_IGNORE_STREAMS)

    seek = common.extract_seek(kwargs)
    cmd = ffmpeg.output(
        audio, output_file,
        format='mp3', **kwargs).compile()
    if len(seek) != 0:
        cmd[1:1] = seek

    subprocess.run(cmd, check=False)
