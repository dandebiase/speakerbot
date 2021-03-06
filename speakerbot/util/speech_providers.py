import os
import re
import subprocess

from config import config
from hashlib import sha256
import requests
from urllib import quote_plus

from text_manipulators import split_text
from sounds import SoundPlayer

from speaker_db import SpeakerDB


class IBMTextToSpeech(object):

    PHRASE_LENGTH = 1000

    def __init__(self):
        self._db = SpeakerDB()
        self._voice = config['ibm_speech']['voice']
        self._voice_prefix = '<voice-transformation type="Custom" glottal_tension="-10%" breathiness="-10%" pitch="10%" pitch_range="15%" rate="-99%" strength="5%">'

    def say(self, text):
        phrases = [text]
        filenames = []
        text = text.lower()
        if len(text) > self.PHRASE_LENGTH:
            phrases = split_text(text, self.PHRASE_LENGTH)

        voice = self._voice
        voice_prefix = self._voice_prefix
        if 'kyle' in text:
            phrases = [r'Kyle is a programmer god.']
            voice_prefix = '<voice-transformation type="Custom" strength="100%" breathiness="-100%" glottal_tension="100%" rate="-100%">'
        elif re.search(r'debia(s|cc)e', text):
            voice = 'it-IT_FrancescaVoice'
            voice_prefix = ''
        elif re.search(r'(volkswagen|audi|porsche|bmw|mercedes|benz)', text):
            voice = 'de-DE_DieterVoice'
            voice_prefix = ''
        elif 'godzilla' in text:
            voice = 'ja-JP_EmiVoice'
            voice_prefix = ''
        elif re.search(r'(hola|gracias|amigo)', text):
            voice = 'es-US_SofiaVoice'
            voice_prefix = ''
        elif re.search(r'ja(ke|cob)', text):
            voice = 'en-US_LisaVoice'
            voice_prefix = '<voice-transformation type="Custom" glottal_tension="60%" breathiness="-30%" pitch="-50%" pitch_range="35%" rate="-30%">'
        elif 'dan' in text:
            voice_prefix = '<voice-transformation type="Custom" strength="100%" pitch="-100%" pitch_range="20%" breathiness="20%" glottal_tension="-100%" rate="-100%">'
        elif 'johnny' in text:
            voice_prefix = '<voice-transformation type="Custom" strength="-30%" pitch="100%" pitch_range="100%" breathiness="-30%" glottal_tension="70%" rate="-30%" timbre="Breeze" timbre_extent="50%">'
        elif 'accounts payable' in text:
            voice_prefix = '<voice-transformation type="Custom" pitch="65%" pitch_range="99%" rate="20%">'

        for phrase in phrases:
            hsh = sha256('{}{}{}'.format(phrase.lower(), voice, voice_prefix)).hexdigest()
            filename = 'speech/%s.wav' % hsh
            if voice_prefix:
                phrase = '{}{}</voice-transformation>'.format(voice_prefix, phrase)
            self.create_sound_file(filename, phrase, voice)
            filenames.append(filename)

        for filename in filenames:
            SoundPlayer(config['wav_player']).play_sound(filename)

    def create_sound_file(self, filename, text, voice):
        if os.path.isfile(filename) and os.path.getsize(filename):
            return

        headers = {
            'Content-Type': 'text/plain',
            'Accept': 'audio/wav'
        }

        params = {
            'text': text,
            'voice': voice
        }

        response = requests.get('https://stream.watsonplatform.net/text-to-speech/api/v1/synthesize',
                                headers=headers,
                                auth=(config['ibm_speech']['user'], config['ibm_speech']['pw']),
                                params=params)

        with open(filename, 'wb') as f:
            f.write(response.content)


class GoogleTextToSpeech(object):

    def __init__(self, url_string=None):

        self.url_string = url_string
        if not url_string:
            self.url_string = u"http://translate.google.com/translate_tts?tl=en_gb&ie=UTF-8&q=%s"

    def say(self, text):

        if len(text) > 100:
            phrases = split_text(text, 100)
            for phrase in phrases:
                self.say(phrase)

            return

        text = quote_plus(text.encode("utf-8"))

        hsh = sha256()
        hsh.update(text.lower())

        filename = "speech/%s.mp3" % hsh.hexdigest()

        self.get_file(filename, self.url_string % (text))

        s = SoundPlayer()
        s.play_sound(filename)

    def get_file(self, filename, url, retries=3):

        if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
            f = open(filename, "w")
            subprocess.call(
                    ['curl','-A Mozilla', url],
                    stdout=f)
        if os.path.getsize(filename) == 0 and retries > 0:
            self.get_file(filename, url, retries=retries-1)


class EspeakTextToSpeech(object):

    def __init__(self, speak_path="espeak", wpm=150):

        self.speak_path = speak_path
        self.wpm_string = "-s %s" % wpm

    def say(self, text):

        subprocess.call([self.speak_path, text, self.wpm_string])
