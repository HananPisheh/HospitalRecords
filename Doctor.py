import json
from os.path import join, dirname
from watson_developer_cloud import SpeechToTextV1
from watson_developer_cloud import TextToSpeechV1
from sys import byteorder
from array import array
from struct import pack
import pyaudio
import wave
from time import sleep
from PIL import Image


# Global variables for recording function
THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100


############################## Recording Section ####################################
def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in xrange(int(seconds*RATE))])
    r.extend(snd_data)
    r.extend([0 for i in xrange(int(seconds*RATE))])
    return r

def record():
    """
    Record a word or words from the microphone and 
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the 
    start and end, and pads with 0.5 seconds of 
    blank sound to make sure VLC et al can play 
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()


############################## IBM Watson ####################################
def speechToText():
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
    return my_transcript


def getDiagnosis(transcript):
    worked = False
    diagnosis = ""
    Alexa_predict = "Patient is likely to develop " # first few words when Alexa predicts complication0000
    Alexa_rec = "Treatments for " # first few words when Alexa gives recommendation
    # Insert brute force code
    if "weaning failure" in transcript or "winning failure" in transcript or "renamed failure" in transcript:
        diagnosis = Alexa_predict + " deep vein thrombosis and septic shock"
        '''***Then connect Alexa to printer/big screen (Shoudn't be hard!) so doctor can point to the picture of weaning failure, 
        deep vein thrombosis, and septic shock to explain to patient what the complication is'''
        # Show picture of weaning failure
        image = Image.open('septic.jpeg')
        image.show()

      #  return diagnosis
    #elif "recommend" in transcript or "recommendations" in transcript:
        recommendation_comp1_DVT = Alexa_rec + "deep vein thrombosis include: blood thinners and use of compression stockings. "
        ''' Can we make it more like an interaction between doctor, patient, and Alexa?'''
        recommendation_comp2_SS = Alexa_rec + "septic shock consists of fluids and blood pressure support. Warning: Septic shock is a life-threatening condition"
        return diagnosis, recommendation_comp1_DVT, recommendation_comp2_SS
    elif "Pulmonary embolism" in transcript:
        diagnosis = Alexa_predict + "deep vein thrombosis"
        recommendation_comp2_DVT = Alexa_rec + "deep vein thrombosis include: blood thinners and use of compression stockings"
        return diagnosis, recommendation_comp2_DVT, ""
    elif "Progressive renal dysfunction" in transcript:
        diagnosis = Alexa_predict + "septic shock"
        recommendation_comp3_SS = Alexa_rec + "septic shock consist of fluids and blood pressure support. Warning: Septic shock is a life-threatening condition"
        return diagnosis, recommendation_comp3_SS, ""
    elif "Reintubation" in transcript:
        diagnosis = Alexa_predict + "weaning failure and myocardial infarction"
        recommendation_comp4_WF = "General treatments are not applicable. Weaning failure treatment requires tailored treatment strategy from surgeonss. "
        recommendation_comp4_MI = Alexa_rec + "myocardial infarction ranges from lifestyle changes and cardiac rehabilitation to medications, stens, and bypass surgery"
        return diagnosis, recommendation_comp4_WF, recommendation_comp4_MI
    elif "Cardiac Arrest" in transcript:
        diagnosis = Alexa_predict + "reintubation"
        recommendation_comp5_Reintubate = "General treatments are not applicable. Reintubation treatment requires tailored treatment strategy from surgeons"
        return diagnosis, recommendation_comp5_Reintubate, ""
    elif "Acute renal failure" in transcript:
        diagnosis = Alexa_predict + "weaning failure"
        recommendation_comp6_WF = "General treatments are not applicable. Weaning failure treatment requires tailored treatment strategy from surgeons"
        return diagnosis, recommendation_comp6_WF, ""
    elif "Pneumonia" in transcript:
        diagnosis = Alexa_predict + "weaning failure"
        recommendation_comp7_WF = "General treatments are not applicable. Weaning failure treatment requires tailored treatment strategy from surgeons"
        return diagnosis, recommendation_comp7_WF, ""
    elif "Sepsis" in transcript:
        diagnosis = Alexa_predict + "pneumonia"
        recommendation_comp8_Pneumonia = "Antibiotics can treat many forms of pneumonia. Some forms of pneumonia can be prevented by vaccines"
        return diagnosis, recommendation_comp8_Pneumonia, ""
    elif "Urinary tract Infection" in transcript:
        diagnosis = Alexa_predict + "sepsis"
        recommendation_comp9_Sepsis = Alexa_rec + "include: antibiotics and intravenous fluids"
        return diagnosis, recommendation_comp9_Sepsis, ""
    elif "Deep surgical site infection" in transcript:
        diagnosis = Alexa_predict + "sepsis and wound dehiscence"
        recommendation_comp10_Sepsis = Alexa_rec + "include: antibiotics and intravenous fluids. "
        recommendation_comp10_Dehis = "Any type of dehisced wound requires immediate medical attention. The treatment of a dehisced wound depends on its size and location, and the severity of any infections. Depending on the infection's depth, surgeons need to monitor patient's wound care or refer to a wound specialist"
        return diagnosis, recommendation_comp10_Sepsis, recommendation_comp10_Dehis
    elif "Organ space surgical site infection" in transcript:
        diagnosis = Alexa_predict + "sepsis"
        recommendation_comp11_Sepsis = Alexa_rec +  "include: antibiotics and intravenous fluids"
        return diagnosis, recommendation_comp11_Sepsis, ""
    else:
        diagnosis = "Error"
    return diagnosis, "", ""

def speakWithPython():
    #open a wav format music
    f = wave.open(r"output6.wav","rb")  
    #instantiate PyAudio  
    p = pyaudio.PyAudio()  
    #open stream  
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                    channels = f.getnchannels(),  
                    rate = f.getframerate(),  
                    output = True)  
    #read data  
    data = f.readframes(CHUNK_SIZE)  

    #play stream  
    while data:  
        stream.write(data)  
        data = f.readframes(CHUNK_SIZE)  

    #stop stream  
    stream.stop_stream()  
    stream.close()  

    #close PyAudio  
    p.terminate()


def speak(text_to_speak):
    text_to_speech = TextToSpeechV1(
        username='e2341c61-9e0e-4448-933d-83e5db3e822e',
        password='FKoUtY56nE0a',
        x_watson_learning_opt_out=True)  # Optional flag

    print(json.dumps(text_to_speech.voices(), indent=2))

    with open(join(dirname(__file__), 'output6.wav'),
              'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(text_to_speak, accept='audio/wav',
                                      voice="en-US_AllisonVoice"))

    print(
        json.dumps(text_to_speech.pronunciation(
            'Watson', pronunciation_format='spr'), indent=2))

    print(json.dumps(text_to_speech.customizations(), indent=2))


if __name__ == "__main__":
    # Listen to Doctor
    print("please speak a word into the microphone")
    record_to_file('demo.wav')
    print("done - result written to demo.wav")
    # Sleep to make sure wav file is written to correctly
    sleep(3)
    # Then determine diagnosis, and speak it back to Doctor
    my_transcript = speechToText()
    diagnosis, recommendation1, recommendation2 = getDiagnosis(my_transcript)
    speak(diagnosis)
    # Speak here in python
    speakWithPython()
    
    sleep(5)
    
    f= open("Medical Record.txt","w+")
    f.write("Patient's History/n ")
    f.write("Diagnosis:  ")
    f.write(diagnosis)
    f.write("recommendation:  ")
    f.write(recommendation1)
    f.close()
    print("Speak Now")
    # Ask Alexa for recommendation, act on response
    record_to_file('demo.wav')
    sleep(3)
    #new_transcript = speechToText()
    #recommendation = getDiagnosis(new_transcript)
    speak(recommendation1+recommendation2)
    speakWithPython()



	