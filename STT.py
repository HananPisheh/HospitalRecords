import json
from os.path import join, dirname
from watson_developer_cloud import SpeechToTextV1


def concatJsonText(text_data):
	num = len(text_data)
	print(num)


speech_to_text = SpeechToTextV1(
    username='4fe69ee8-af2c-43d0-952d-00f777d66e71',
    password='T25LaJAYsuwK',
    x_watson_learning_opt_out=False
)

print(json.dumps(speech_to_text.models(), indent=2))

print(json.dumps(speech_to_text.get_model('en-US_BroadbandModel'), indent=2))

with open(join(dirname(__file__), 'demo.wav'),
          'rb') as audio_file:
    text_data = json.dumps(speech_to_text.recognize(
        audio_file, content_type='audio/wav', timestamps=True,
        word_confidence=True),
        indent=2)

print(text_data)
text_data_json = json.loads(text_data)
my_transcript = text_data_json['results'][0]['alternatives'][0]['transcript']
print(my_transcript)

worked = False
word = ""

if "weaning failure" in my_transcript or "winning failure" in my_transcript:
	print("Working")
else:
	print("No")

# Insert brute force code

# for char in my_transcript:
# 	# form words from characters
# 	if char != " ":
# 		word += char

# 	#if word == 'weaning':
# 	if "weaning" in word:
# 		print("Working!!")
# 		worked = True
# if not worked:
# 	print("Didn't work :(")






	