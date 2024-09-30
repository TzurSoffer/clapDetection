import time
import numpy as np
import pyaudio

import sys
sys.path.append("..")
from src.clapDetector import ClapDetector, printDeviceInfo

print("Warning: This is an advanced example demonstrating the module's ability to be passed audio instead of it using the microphone. For most cases, I recommend using the library's built-in audio tools instead of external sources.")

printDeviceInfo()
print("\n\n")
inputDeviceIndex=int(input("Input device index: "))

thresholdBias = 6000
lowcut=200               #< increase this to make claps detection more strict 
highcut=3200             #< decrease this to make claps detection more strict
clapDetector = ClapDetector(inputDevice=None, logLevel=10)    #< setting inputDevice to None in order to tell the program that it will not be recording the audio.

p = pyaudio.PyAudio()
input_device_info = p.get_device_info_by_index(inputDeviceIndex)
channels = input_device_info.get('maxInputChannels', 1)

stream = p.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=44100,
                        input=True,
                        frames_per_buffer=2048,
                        input_device_index=inputDeviceIndex)
try:
   while True:
      audioData = np.frombuffer(stream.read(2048), dtype=np.int16) #< Convert the raw audio data to a NumPy array of 16-bit integers

      result = clapDetector.run(thresholdBias=thresholdBias, lowcut=lowcut, highcut=highcut, audioData=audioData)
      resultLength = len(result)
      if resultLength == 2:
            print(f"Double clap detected! bias {thresholdBias}, lowcut {lowcut}, and highcut {highcut}")
            clapDetector.saveAudio(folder="./")
      time.sleep(1/60)

except KeyboardInterrupt:
   print("Exited gracefully")
except Exception as e:
   print(f"error: {e}")
finally:
   clapDetector.stop()