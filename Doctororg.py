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
import datetime


# Global variables for recording function
THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 30100

global_recommendation = ""
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
    if len(text_data_json['results']) > 0:
        my_transcript = text_data_json['results'][0]['alternatives'][0]['transcript']
    else:
        my_transcript = "Dummy"
    print(my_transcript)
    return my_transcript





# image = Image.open('deep vein thrombosis.jpeg')
# image.show()
# image = Image.open('Myocardial Infarction.jpeg')
# image.show()
# image = Image.open('Septic shockI.jpeg')
# image.show()
# image = Image.open('Wound dehiscence.jpeg')
# image.show()


def getDiagnosis(transcript):
    diagnosis = ""
    Alexa_predict = "Patient is likely to develop " # first few words when Alexa predicts complication0000
    Alexa_rec = "Treatments for " # first few words when Alexa gives recommendation
    # Insert brute force code

    if "recommend" in transcript or "recommendations" in transcript:
        return global_recommendation, "", ""
    elif "yes" in transcript:
        return "yes", "", ""

    elif "weaning failure" in transcript or "winning failure" in transcript or "renamed failure" in transcript or "failure" in transcript:
        diagnosis = Alexa_predict + " deep vein thrombosis and septic shock"
        '''***Then connect Alexa to printer/big screen (Shoudn't be hard!) so doctor can point to the picture of weaning failure, 
        deep vein thrombosis, and septic shock to explain to patient what the complication is'''
        # Show picture of weaning failure
        image = Image.open('Weaning Failure.jpg')
        image.show()

      #  return diagnosis
    #elif "recommend" in transcript or "recommendations" in transcript:
        global_recommendation = Alexa_rec + "deep vein thrombosis include: blood thinners and use of compression stockings. "
        ''' Can we make it more like an interaction between doctor, patient, and Alexa?'''
        global_recommendation += Alexa_rec + "septic shock consists of fluids and blood pressure support. Warning: Septic shock is a life-threatening condition"
        return diagnosis, global_recommendation, ""
    elif "pulmonary embolism" in transcript:
        diagnosis = Alexa_predict + "deep vein thrombosis"
        global_recommendation = Alexa_rec + "deep vein thrombosis include: blood thinners and use of compression stockings"
        image = Image.open('Pulmonary Embolism.jpeg')
        image.show()
        return diagnosis, global_recommendation, ""
    elif "progressive renal dysfunction" in transcript:
        diagnosis = Alexa_predict + "septic shock"
        global_recommendation = Alexa_rec + "septic shock consist of fluids and blood pressure support. Warning: Septic shock is a life-threatening condition"
        return diagnosis, global_recommendation, ""
    elif "reintubation" in transcript:
        diagnosis = Alexa_predict + "weaning failure and myocardial infarction"
        global_recommendation = "General treatments are not applicable. Weaning failure treatment requires tailored treatment strategy from surgeonss. "
        global_recommendation += Alexa_rec + "myocardial infarction ranges from lifestyle changes and cardiac rehabilitation to medications, stens, and bypass surgery"
        return diagnosis, global_recommendation, ""
    elif "cardiac arrest" in transcript:
        diagnosis = Alexa_predict + "reintubation"
        global_recommendation = "General treatments are not applicable. Reintubation treatment requires tailored treatment strategy from surgeons"
        image = Image.open('Cardiac Arrest.jpeg')
        image.show()
        return diagnosis, global_recommendation, ""
    elif "acute renal failure" in transcript:
        diagnosis = Alexa_predict + "weaning failure"
        global_recommendation = "General treatments are not applicable. Weaning failure treatment requires tailored treatment strategy from surgeons"
        image = Image.open('Acute Renal Failure.jpeg')
        image.show()
        return diagnosis, global_recommendation, ""
    elif "pneumonia" in transcript:
        diagnosis = Alexa_predict + "weaning failure"
        global_recommendation = "General treatments are not applicable. Weaning failure treatment requires tailored treatment strategy from surgeons"
        image = Image.open('Pneumonia.jpeg')
        image.show()
        return diagnosis, global_recommendation, ""
    elif "sepsis" in transcript:
        diagnosis = Alexa_predict + "pneumonia"
        global_recommendation = "Antibiotics can treat many forms of pneumonia. Some forms of pneumonia can be prevented by vaccines"
        image = Image.open('Sepsis.jpeg')
        image.show()
        return diagnosis, global_recommendation, ""
    elif "urinary tract infection" in transcript:
        diagnosis = Alexa_predict + "sepsis"
        global_recommendation = Alexa_rec + "include: antibiotics and intravenous fluids"
        image = Image.open('Urinary Tract Infection.jpeg')
        image.show()
        return diagnosis, global_recommendation, ""
    elif "deep surgical site infection" in transcript or "did surgical" in transcript:
        diagnosis = Alexa_predict + "sepsis and wound dehiscence"
        global_recommendation = Alexa_rec + "include: antibiotics and intravenous fluids. "
        global_recommendation += "Any type of dehisced wound requires immediate medical attention. The treatment of a dehisced wound depends on its size and location, and the severity of any infections. Depending on the infection's depth, surgeons need to monitor patient's wound care or refer to a wound specialist"
        return diagnosis, global_recommendation, ""
    elif "organ space surgical site infection" in transcript:
        diagnosis = Alexa_predict + "sepsis"
        global_recommendation = Alexa_rec +  "include: antibiotics and intravenous fluids"
        image = Image.open('Organ space SSI.jpg')
        image.show()
        return diagnosis, global_recommendation, ""
    else:
        diagnosis = "I couldn't hear you"
    return diagnosis, "No recommendation needed", ""

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
    exit = False
    while not exit:
        # Listen to Doctor
        print("please speak a word into the microphone")
        record_to_file('demo.wav')
        print("done - result written to demo.wav")
        # Sleep to make sure wav file is written to correctly
        sleep(3)
        # Then determine diagnosis, and speak it back to Doctor
        my_transcript = speechToText()
        diagnosis, recommendation1, recommendation2 = getDiagnosis(my_transcript)
        # If the diagnosis wasn't error, speak the outcome
        if diagnosis != "I couldn't hear you":
            speak(diagnosis)
            # Speak here in python
            speakWithPython()
            exit = True
        # Else, ask Doctor to repeat him/herself
        else:
            speak("Could you repeat that please?")
            speakWithPython()
    
    # Write info to text file
    f= open("index.html","a")
    f.write("Patient's History\n")
    f.write("Patients Name: Hanan Pisheh")
    f.write('Timestamp: {:%Y-%b-%d %H:%M:%S}'.format(datetime.datetime.now()) + "\n")
    f.write("Diagnosis:  ")
    f.write(diagnosis + "\n")
    f.write("recommendation:  ")
    f.write(recommendation1 + "\n")

    f.close()

    #print("Ask for recommendation")
    # Ask Alexa for recommendation, act on response
    #record_to_file('demo.wav')
    sleep(3)
    #new_transcript = speechToText()
    #recommendation, dummy, dummy2 = getDiagnosis(new_transcript)
    #if recommendation == "":
    speak("Would you like a recommendation?")
    speakWithPython()
    record_to_file('demo.wav')
    answer_transcript = speechToText()
    answer, dumm, dumm2 = getDiagnosis(answer_transcript)
    if "yes" in answer:
        speak(recommendation1)
        speakWithPython()
    else:
        speak("Empty")

        #speak(recommendation)
    #speak("My recommendation is: " + global_recommendation)
    #speakWithPython()



	
