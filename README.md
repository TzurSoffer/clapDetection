![PyPI - Downloads](https://img.shields.io/pypi/dw/clap-detector) ![Downloads](https://static.pepy.tech/badge/clap-detector)
# Clap Detection System

## Overview

This project implements a clap detection system using an a mic or raw audio data as input. It can detect clap patterns including single and double claps.

### If you found [this repository](https://github.com/TzurSoffer/clapDetection) useful, please give it a ⭐!.

## Features

- Clap pattern detection.
- Dynamic threshold adjustment for robust clap detection.
- Bandpass filtering to focus on clap frequencies.
- Audio recording and saving capabilities.
![Live Visualization Failed to load](examples/videos/liveVisualization.gif)
## Troubleshooting

### PyAudio
   - #### Option A
      If clap-detector fails to install due to pyaudio issues, try to install ``` portaudio19 ``` using ``` sudo apt install portaudio19-dev ```, then install clap-detector normally using ``` pip install clap-detector ```.
   - #### Option B
      If pyaudio still fails to install after trying option A, try to install it using ``` sudo apt install python3-pyaudio ```, then install clap-detector normally ``` pip install clap-detector```.

### Input
   - If there are issues with audio input, check the inputDevice in the `ClapDetector` constructor.

### Accuracy
- Adjust the bandpass filter parameters for better clap detection in different environments.

## Requirements

- Python3
- PyAudio
- NumPy
- SciPy

## Installation

### option A:
1. install from the official pypi package:
   ```bash
   pip install clap-detector
   ```

### option B:
1. Install the required Python packages:

   ```bash
   pip install pyaudio numpy scipy
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/TzurSoffer/clapDetection/
   cd clapDetection/src/clapDetector
   ```

3. Run the clap detection script:

   ```bash
   python clapDetector.py
   ```

## Configuration

- Adjust parameters in the `ClapDetector` class constructor to fine-tune the clap detection system.
  ### Choosing microphone (input device)
   The application initially attempts to use the system's default audio device. If this doesn't work or if you prefer to use a different device, you can change it.
   First, find your input devices using `clapDetector.printDeviceInfo()`, this will print something along the lines of:
   ```
   Available audio devices:
   Device 0: Microsoft Sound Mapper - Input
   Device 1: Microphone (Yeti Stereo Microph
   Device 2: Microsoft Sound Mapper - Output
   Device 3: YX Display (NVIDIA High Definit
   Device 4: Speakers (Realtek(R) Audio)
   Device 5: Speakers (Yeti Stereo Microphon
   Device 6: ES-G34C5 (NVIDIA High Definitio
   ```

   once you found your desired input device, copy either it id or name, eg: `1` or `Microphone (Yeti Stereo Microph`, note that it's almost always better to use the name and not the id as it is more robust.

   Once you have your input device, simply tell the constructor to use it like so: </br>
   ```clapDetector.ClapDetector(inputDevice="Microphone (Yeti Stereo Microph")``` </br>
   or </br>
   ```clapDetector.ClapDetector(inputDevice=1)```

## Usage

### option A:
1. clone the repository, if you have not already using ```git clone https://github.com/TzurSoffer/clapDetection/```

2. go into the examples folder and choose one of the scripts you would like to run.

   The `examples/` folder contains small runnable scripts demonstrating common flows:
   - `findMicrophone.py` — list audio devices and indexes
   - `singleClap.py` — detects single claps
   - `doubleClap.py` — detects double claps and saves audio when detected
   - `liveVisualization.py` — live plot of audio levels (may require matplotlib)
   - `externalAudioSource.py` — shows how to feed audio into the detector without using the module's built-in tools (Note that this is an advanced example showing the tools versatility, but I do not recommend doing this in most cases)

   To run an example (PowerShell):

   ```powershell
   python .\examples\doubleClap.py
   ```

### option B:
1. Create a script that uses this library 
   ```python
   import time
   from clapDetector import ClapDetector, printDeviceInfo

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
         resultLength = len(result)    #< amount of claps detected (1 is single-clap, 2 is double-clap, etc)
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
   ```

2. The system will continuously monitor audio input and detect claps.

## License

This project is licensed under the MIT License — see the `LICENSE.txt` file for details.
