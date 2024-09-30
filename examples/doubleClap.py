import time

import sys
sys.path.append("..")
from src.clapDetector import ClapDetector, printDeviceInfo

print("""
      --------------------------------
      The application initially attempts to use the system's default audio device. If this doesn't work or if you prefer to use a different device, you can change it. Below are the available audio devices. Find the one you are using and change the 'inputDevice' variable to the name or index of your preferred audio device. Then, restart the program, and it should properly capture audio.
      --------------------------------
      """)
printDeviceInfo()

thresholdBias = 6000
lowcut=200               #< increase this to make claps detection more strict 
highcut=3200             #< decrease this to make claps detection more strict
clapDetector = ClapDetector(inputDevice=-1, logLevel=10)
clapDetector.initAudio()

try:
   while True:
      audioData = clapDetector.getAudio()

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
