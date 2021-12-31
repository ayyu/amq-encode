import argparse
import os

from . import encode, video

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', type=str, required=True, help='input video')
  parser.add_argument('-crf', type=int, help='constant rate factor')
  parser.add_argument('-g', type=int, help='interval between keyframes')
  parser.add_argument('-vf', '-filter:v', type=str, default='', help='video filter string')
  parser.add_argument('-af', '-filter:a', type=str, default='', help='audio filter string')
  parser.add_argument('-ss', type=str, help='start time')
  parser.add_argument('-to', type=str, help='end time')
  parser.add_argument('-t', type=str, help='encode duration')
  parser.add_argument('-norm', action='store_true', help='normalize output volume')
  parser.add_argument('-outdir', type=str, help='output path')
  parser.add_argument('-skip', type=int, nargs='+', help='resolutions to skip')
  parser.set_defaults(
    norm=False,
    outdir='./source/',
    skip=[]
  )
  args = parser.parse_args()

  if not os.path.isfile(args.i):
    print('invalid input file provided')
    exit()
  
  kwargs = {k: v for k, v in {
    'ss': args.ss,
    'to': args.to,
    't': args.t}.items() if not v == None}

  vp9_settings = {k: v for k, v in {
    'crf': args.crf,
    'g': args.g}.items() if not v == None}

  resolutions = [res for res in video.resolutions if res not in args.skip]

  encode.encode_all(
    args.i, args.outdir,
    vf=args.vf, af=args.af,
    norm=args.norm,
    vp9_settings=vp9_settings,
    **kwargs)
