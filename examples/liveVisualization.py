try:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
except:
    print("You do not have matplotlib installed, please install matplotlib using ``` pip install matplotlib ```, then restart this script.")
import threading
import numpy as np
import sys
sys.path.append("..")
from src.clapDetector import ClapDetector, printDeviceInfo

class Visualizer():
    def __init__(self, rate = 44100) -> None:
        self.audioBuffer = []
        self.rate = rate

    def initLiveVisualization(self):
        """
        Initialize the live audio visualization.
        """
        self.fig, self.ax = plt.subplots(figsize=(15, 5))
        self.line, = self.ax.plot([], [], color='blue')
        self.ax.set_title("Live Audio Buffer Waveform")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid()

    def updateLiveVisualization(self, frame):
        """
        Update the live audio visualization.
        """
        if len(self.audioBuffer) == 0:
            return self.line,

        # Combine the audio data from the buffer into a single array
        audioData = np.concatenate(self.audioBuffer)
        
        # Create a time axis for the audio data
        timeAxis = np.linspace(0, len(audioData) / self.rate, num=len(audioData))

        # Update the plot data
        self.line.set_data(timeAxis, audioData)
        self.ax.set_xlim(0, timeAxis[-1])
        self.ax.set_ylim(np.min(audioData), np.max(audioData))

        return self.line,

    def startLiveVisualization(self):
        """
        Start the live audio visualization.
        """
        self.initLiveVisualization()
        self.ani = FuncAnimation(self.fig, self.updateLiveVisualization, blit=True, interval=100)
        plt.show()

if __name__ == '__main__':

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
    
    visualizer = Visualizer(rate = clapDetector.rate)
    threading.Thread(target=visualizer.startLiveVisualization).start()

    try:
        while True:
            audioData = clapDetector.getAudio()

            result = clapDetector.run(thresholdBias=thresholdBias, lowcut=lowcut, highcut=highcut, audioData=audioData)
            resultLength = len(result)
            if resultLength == 2:
                    print(f"Double clap detected! bias {thresholdBias}, lowcut {lowcut}, and highcut {highcut}")
            visualizer.audioBuffer = clapDetector.audioBuffer

    except KeyboardInterrupt:
        print("Exited gracefully")
    except Exception as e:
        print(f"error: {e}")
        clapDetector.stop()