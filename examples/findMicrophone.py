from clapDetector import ClapDetector

clapDetector = ClapDetector(logLevel=10, inputDeviceIndex="")
clapDetector.printDeviceInfo()
print("""
These are all the audio devices found, find the one you want to use, then copy the name of the microphone or its index and paste it into the "inputDeviceIndex" variable.
An example of an input device will look something like this:
      
Device 0: Microphone (Yeti Stereo Microph

If this is the device you want to use, then you can either copy its device number(0, in this case) and paste it into the inputDeviceIndex as an integer, or copy its name("Microphone (Yeti Stereo Microph", in this case), or a section of its name("Microphone (Yeti", in this case) and paste it into the inputDeviceIndex as a string.
The resulting inputDeviceIndex in this case should then either look like:
inputDeviceIndex=0
or
inputDeviceIndex="Microphone (Yeti Stereo Microph"
""")
