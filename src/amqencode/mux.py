"""Muxing

Functions for muxing clean audio with video files.
"""

__all__ = [
    'mux_clean',
]


import ffmpeg

from . import audio, common


def mux_clean(
        input_video: str,
        input_audio: str,
        output_file: str,
        norm: bool = False) -> None:
    """
    Muxes an input file with a clean audio file.

    Args:
        input_video (str): Path to video file to mux.
        input_audio (str): Path to clean audio file to mux.
        output_file (str): Path to output muxed file.
        norm (bool): Whether to normalize audio level of the output.
    """

    common.ensure_dir(output_file)

    audio_stream = ffmpeg.input(input_audio).audio
    args = dict(audio.AUDIO_SETTINGS)

    if norm:
        audio_stream = common.apply_filters(
            audio_stream,
            audio.get_norm_filter(input_audio))

    if input_video.endswith('.mp3'):
        duration = audio.probe_duration(input_video)
        args = dict(
            {'vn': None, 't': f"{duration:.3f}"},
            **args, **audio.MP3_SETTINGS)
        stream = ffmpeg.output(audio_stream, output_file, **args)

    else:
        video_stream = ffmpeg.input(input_video).video
        args = dict(
            {'c:v': 'copy', 'shortest': None},
            **args, **audio.OPUS_SETTINGS)
        stream = ffmpeg.output(video_stream, audio_stream, output_file, **args)

    stream.run(overwrite_output=True)
