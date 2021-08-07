# ffmpeg scripts for handicaps

These scripts expedite 2-pass VP9/Opus encoding for AMQ using `ffmpeg`. They are basically all wrappers for ffmpeg.

Windows versions will probably never exist.

## Requirements

- `bash`
  - if you're on Windows 10, you can use [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10).
  - if you're on older Windows versions, it might be time to upgrade.
  - OS X/Linux users know what they're doing.
- `ffmpeg` and `ffprobe`
  - in bash, do `sudo apt update && sudo apt install ffmpeg`
- some level of comfort using a terminal
  - This might be a tall ask.

## Installing

Probably the easiest way to do this would be to put the scripts in a folder under your home folder (e.g. `/home/amq_scripts/`), then do:

```bash
sudo install /home/amq_scripts/*.sh /usr/local/bin/
```

You should be able to run the scripts from any directory after doing that.
Make sure all the scripts are in the same folder as several of them depend on each other.

## Included scripts

### `amq_encode.sh`

2-pass VP9 encoding with CRF 20. Generates output files named `720.webm`, `480.webm`, and `0.mp3`.
You may need to specify additional video filters if your source file is inadequate.

Options:

- `-vf`: will prepend your desired filters before the `scale` and `setsar` filters
- `-crf`: will override the default CRF of 20
- any other ffmpeg options should also get passed if specified

Outputs to directory `./source/`

### `amq_mux.sh`

Muxes a clean audio track to all files in the specified input directory.
Make sure your clean audio file is synced to and already about the same length as the video files.

This will ignore an existing MP3 file in the input directory and instead encode directly from your clean file to a new MP3.
The drawback is that it won't truncate the clean to the same length as the existing MP3, so it's best to make sure your clean is the same duration as your video.

Options:

- `-a`: path to clean audio file
- `-i`: path to folder containing videos to be muxed. Usually, you want to choose `source` to use the outputs from `amq_mux.sh`

Outputs to directory `./clean/`

### `amq_volume_norm.sh`

Adjusts audio levels to -18 dB and -1 dB peak.
`norm` is a misnomer as it doesn't actually normalize audio, but just applies gain to each file as needed.
However, I am an ape and won't rename it at this point.
Depends on `amq_volume_detect.sh`.

Options:

- `-i`: path to input file

Outputs to directory `./norm/`

### `amq_volume_auto.sh`

Applies `amq_volume_norm.sh` to all files in the specified directory.

Options:

- `-i`: path to folder containing videos to be adjusted

Outputs to directory `./norm/`

### `amq_volume_detect.sh`

Wrapper for the `-af volumedetect` filter in ffmpeg. Extracts values for `mean_volume` and `max_volume` into shell variables and calculates the difference between `mean_volume` and `target_mean` as specified in `amq_settings.sh`.

Options:

- `-i`: path to input file

Does not produce any output besides assigning some shell variables.

### `amq_settings.sh`

Shared settings between the scripts, including things like desired audio levels and audio bitrates.
Place this in the same directory as the other scripts or none of them will work.

## Usage

### 1. Encoding video

The `amq_encode.sh` mostly gets called the same way that you would call an ffmpeg command, and will pass parameters as needed.
This is usually the first thing you will use.

First, pick your start and end timestamps from your source video, ideally to the millisecond level. You can use a player capable of frame advancing and millisecond display to do this. [mpv](https://mpv.io/) works quite well. You can also use an audio editor to do this.

Pass them to `amq_encode.sh` with the `-ss` and `-to` options, respectively.

```bash
amq_encode.sh -i "[LowPower-Raws] Tokyo 7th Sisters (Bluray-1080p).mkv" -ss 58:05.679 -to 1:00:48.491
```

Once this is done, your (unclean) outputs will be in the `source` folder.

I would recommend saving your command in a `.sh` file for future reference, perhaps making it a bit more readable:

```bash
amq_encode.sh \
  -i "[LowPower-Raws] Tokyo 7th Sisters (Bluray-1080p).mkv" \
  -ss 58:05.679 -to 1:00:48.491
```

I've lost timestamps in the past for uploads that needed corrections, and cba finding them again.

### 2. Audio levels

If the audio plays cleanly enough from the source and you are content, you can adjust the audio levels automatically to -18 dB LUFS and -1 dB peak with this script, pointing it to the `source` folder like so:

```bash
amq_volume_auto.sh -i "source"
```

which will produce outputs in a `norm` folder that you can then upload.

### 3. Muxing clean audio

However, if your source video has SFX/talking/whatever and needs to be muxed with a clean version of the audio, you'll have some more work to do.

First, sync your clean audio to the video. This may take some editing in the software of your choice. If you're poor/not a pirate you can use Audacity and line up the waveforms/spectrograms as best as you can.

Once you have your clean audio, you can mux it with your previously encoded output video with this script:

```bash
amq_mux.sh -i "source" -a "clean.wav"
```

where the options `-i` points to your video folder and `-a` points to your clean audio file.
This generates outputs in a `clean` folder.

Then apply the same audio adjustment as in step 2, but pointing to your `clean` folder instead of `source`:

```bash
amq_volume_auto.sh -i "clean"
```

You can now upload the contents of your `norm` folder.
Yes I am aware that this introduces generation loss but it's minimal at the prescribed bitrate.

## Tips

### Don't use MP3/FLAC for your final cleans to be muxed

They add some amount of silence to the beginning and end of the file,
so your audio will be slightly out of sync with the video if they were originally synced properly in your editing software.

Once you've finished editing your clean, export it as some other format. WAV works fine.
You can of course still use MP3/FLAC for your sources to be edited (as long as they are of acceptable quality).

### Audio quality

Generally, lossy codecs save space by discarding information that's humanly inaudible. The more compression, the lower the cutoff frequency gets.
MP3 @ 320K CBR usually cuts off at 20-22 kHz, so it's *usually* safe to use it as a source, but anything at lower bitrates gets worse rapidly. YMMV.
Lossless files do not have this limitation.

People will hate on you for using a 320K source for a 320K encode, but the differences are inaudible to human ears so you can safely dismiss them as mindless Redditors. However, using audio sources with clear degradation in quality (e.g. 128K YouTube rips) is noticeably worse, so avoid this at all costs unless you are encoding an obscure web-only release with no released OSTs.

You can use [Spek](http://spek.cc/) to visualize this.

### Fixing 3:2 pulldown, 30 FPS > 24 FPS

If your source file is 29.97 fps and has a duplicated frame once every 6 frames, you can fix it in your encode by adding the following argument to your encode command:

```bash
-vf "fps=30000/1001,fieldmatch,decimate"
```

If you require deinterlacing as well, do this instead:

```bash
-vf "fps=30000/1001,fieldmatch,yadif,decimate"
```

See this [Wikipedia entry](https://en.wikipedia.org/wiki/Three-two_pull_down) if you're a nerd.

I will cover more corner cases and corrections as they come up or I remember them, which won't be very often due to my feeble arthritic brain.
