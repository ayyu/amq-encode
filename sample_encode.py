import amqencode

input_file = 'yourfile.mkv'
clean_audio = 'clean.wav'
source_dir = './source/'
clean_dir = './clean/'

amqencode.encode.encode_all(
  input_file, source_dir,
  norm=True,
  ss="1:39", to="5:20")
amqencode.encode.mux_clean_directory(
  source_dir, clean_audio,
  clean_dir, norm=True)