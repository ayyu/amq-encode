"""AMQ Encoding

Entry point for batch encoding of source files into valid AMQ webms and mp3s.
Also has functions for muxing clean audio with video files (to be split into
separate module).
"""


__all__ = [
    'encode_all',
    'mux_clean_directory',
]


from typing import Union
import os

from . import audio, common, mux, video


def mux_clean_directory(
        input_dir: str,
        input_audio: str,
        output_dir: str = './clean/',
        norm: bool = False) -> None:
    """
    Muxes all webm/mp3 files in the input directory with a clean audio file.

    Args:
        input_dir (str): Path containing webm and/or mp3 files to be muxed.
        input_audio (str): Path to clean audio file to mux.
        output_dir (str): Path to output muxed files. Defaults to `./clean/`.
        norm (bool): Whether to normalize audio level of the outputs.
    """
    for file in os.listdir(input_dir):
        if file.endswith(('.webm', '.mp3')):
            mux.mux_clean(
                os.path.join(input_dir, file),
                input_audio,
                os.path.join(output_dir, file),
                norm)


mux_folder = mux_clean_directory


def encode_all(
        input_file: str,
        output_dir: str = './source/',
        norm: bool = False,
        skip_resolutions: Union[str, list] = '360',
        **kwargs) -> None:
    """
    Encodes a video in all requested resolutions.

    Args:
        input_file (str): Path to video file to encode from.
        output_dir (str, optional): Path to output encoded files.
            Defaults to `./source/`.
        norm (bool): Whether to normalize audio level of the output.
        skip_resolutions (list of int): List of resolutions to skip.
            Use this if you want to use the default list of resolutions and
            skip a specific one. Defaults to including 360.
        **kwargs: Arbitrary keyword arguments. Includes arguments specific to
            this package, as well as any native ffmpeg parameters you wish to
            pass.

    Keyword Args:
        resolutions (list of int): List of resolutions to be encoded,
            in terms of video height. Include 0 to encode an mp3.
            Defaults to `[0, 360, 480, 720]`.
        vp9_settings (dict of str: str/int/None):
            Dictionary of settings to override default VP9 parameters.
        force_dimensions (dict of str: int/Fraction):
            Dictionary of dimensional data to force, ignoring dimensions probed
            using ffprobe on the source video.
            Valid keys are `width`, `height`, `sar`, and `dar`.
        vf (str or dict of str: str/None):
            String or dictionary of video filters to apply.
        af (str or dict of str: str/None):
            String or dictionary of audio filters to apply.
            Normalization filter will be applied after these, if requested.
    """

    common.ensure_dir(output_dir + '/')

    if isinstance(skip_resolutions, str):
        skip_resolutions = [int(x) for x in skip_resolutions.split(',')]

    resolutions = sorted(
        {res for res
         in kwargs.pop('resolutions', video.RESOLUTIONS)
         if res not in skip_resolutions})
    first_video = next((
        i for i, x
        in enumerate(resolutions)
        if not x in (0, '0')), None)

    vp9_settings = dict(
        video.VP9_SETTINGS,
        **kwargs.pop('vp9_settings', {}))

    probe_data = dict(
        video.probe_dimensions(input_file),
        **kwargs.pop('override_dimensions', {}),
        **kwargs.pop('force_dimensions', {}))

    video_filters = dict(
        video.INIT_VIDEO_FILTERS,
        **common.parse_filter_string(kwargs.pop('vf', {})))
    audio_filters = dict(
        common.parse_filter_string(kwargs.pop('af', {})),
        **(audio.get_norm_filter(input_file, **kwargs) if norm else {}))

    common_settings = dict(
        common.MAP_SETTINGS,
        **audio.AUDIO_SETTINGS,
        **kwargs)

    for resolution in resolutions:

        resolution = int(resolution)

        if resolution == 0:  # 0 = mp3
            output_file = os.path.join(output_dir, f"{resolution}.mp3")
            audio.encode_mp3(
                input_file, output_file,
                af=audio_filters,
                **audio.MP3_SETTINGS,
                **common_settings)
            continue

        if (resolution > probe_data['height']+16 and
            resolution > resolutions[first_video]):
            print(f"Skipping {resolution}p due to insufficient video height")
            continue

        output_file = os.path.join(output_dir, f"{resolution}.webm")
        width = round(probe_data['dar'] * resolution)
        height = resolution
        video_filters.update(scale=f"{width}x{height}")
        video.encode_webm(
            input_file, output_file,
            vf=video_filters, af=audio_filters,
            **vp9_settings,
            **audio.OPUS_SETTINGS,
            **common_settings)
