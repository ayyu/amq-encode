# ffmpeg scripts for handicaps

This Python 3 module simplifies 2-pass VP9/Opus encoding for AMQ using `ffmpeg`.
It's basically a wrapper with presets for [ffmpeg-python](https://github.com/kkroening/ffmpeg-python),
with some hacky stuff to get 2-pass encodes working.

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

Also make sure that ffmpeg is on your PATH.

## Usage

`import amqencode` in your python scripts.

### CLI

If you just want to encode a file without writing a standalone script, you can call it directly.

*nix

```bash
python3 -m amqencode
```

Windows

```cmd
py -3 -m amqencode
```

However, this is incapable of muxing clean audio into an encode.
