import amqencode

encode_dir = './source/'

amqencode.encode.encode_all(
  input_file='YOURFILE',
  output_dir=encode_dir,
  norm=True,
  ss="1:39", to="5:20")

amqencode.encode.mux_clean_directory(
  input_dir=encode_dir,
  input_audio='clean.wav',
  output_dir='./clean/',
  norm=True)