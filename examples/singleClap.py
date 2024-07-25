from clapDetector import ClapDetector

thresholdBias = 6000
lowcut=200               #< increase this to make claps detection more strict
highcut=3200             #< decrease this to make claps detection more strict
clapDetector = ClapDetector(logLevel=10, inputDeviceIndex="USB Audio Device")
clapDetector.printDeviceInfo()
print("""
      -----------------------------
      These are the audio devices, find the one you are using and change the variable "inputDeviceIndex" to the the name or index of your audio device. Then restart the program and it should properly get audio data.
      -----------------------------
      """)
clapDetector.initAudio()

try:
   while True:
      audioData = clapDetector.getAudio()

      result = clapDetector.run(thresholdBias=thresholdBias, lowcut=lowcut, highcut=highcut, audioData=audioData)
      resultLength = len(result)
      if resultLength == 1:
            print(f"Single clap detected! bias {thresholdBias}, lowcut {lowcut}, and highcut {highcut}")
            clapDetector.saveAudio(folder="./")

except KeyboardInterrupt:
   print("Exited gracefully")
except Exception as e:
   print(f"error: {e}")
   clapDetector.stop()
