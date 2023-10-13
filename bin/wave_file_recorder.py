import wave
import os

def _get_random_temp_filename():
    """ファイル名として適切な8文字のランダムな文字列を生成する
    https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits
    """
    import random
    import string
    return ".{}.bin".format(''.join(random.choices(string.ascii_uppercase + string.digits, k=8)))

class WaveFileRecorder:
    def __init__(self):
        self._filename = None

    def start(self, filename, channels, sample_width, sample_rate):
        if self._filename is not None:
            raise Exception("Recording is already started.")

        self._filename = filename
        self._channels = channels
        self._sample_width = sample_width
        self._sample_rate = sample_rate

        self._temp_fielname = _get_random_temp_filename()
        self._filehandle = open(self._temp_fielname, 'wb')
        
    def put(self, data):
        if self._filename is None:
            raise Exception("Recording is not started.")
    
        self._filehandle.write(data)

    def terminate(self):
        if self._filename is None:
            raise Exception("Recording is not started.")
        
        self._filehandle.close()
        self._filehandle = None

        with wave.open(self._filename, 'wb') as wf, open(self._temp_fielname, 'rb') as rf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(self._sample_width)
            wf.setframerate(self._sample_rate)
            wf.writeframes(rf.read())

        os.remove(self._temp_fielname)

if __name__ == "__main__":
    print(_get_random_temp_filename())