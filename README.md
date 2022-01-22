# ffmpeg scripts for handicaps

This Python 3 package simplifies 2-pass VP9/Opus encoding for AMQ using `ffmpeg`.
It's basically a wrapper with presets for [ffmpeg-python](https://github.com/kkroening/ffmpeg-python),
with some hacky stuff to get 2-pass encodes working.

You can use it to encode every resolution of a video with a single command.

You can override a lot of the presets.
Passing `norm=True` automatically adjusts volume levels for you.

I'll write up documentation later.

## Install it with `pip`

First, install Python 3 if you haven't already. Then,

```bash
pip install amqencode
```

or maybe this on Windows

```cmd
py -3 -m pip install amqencode
```

Also make sure that `ffmpeg` is on your PATH.

## Usage

`import amqencode` in your python scripts.

See `sample_encode.py` for an example of a script that encodes a video into
mp3 and webms, then muxes those outputs with clean audio.

### CLI

If you just want to encode a file without writing a standalone script,
you can call the package directly from a terminal.

*nix

```bash
python3 -m amqencode
```

Windows

```cmd
py -3 -m amqencode
```

However, this is incapable of muxing clean audio into an encode.
