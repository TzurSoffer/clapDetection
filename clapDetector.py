import pyaudio
import numpy as np
import time
from datetime import datetime
import requests
from scipy.signal import butter, lfilter, find_peaks

class ClapDetector():
    def __init__(self, inputDeviceIndex=8,
                 volumeThreshold=9000,
                 rate=48000,
                 buffer=1024,
                 debounceTime=0.15,
                 resetTime=0.25, #< seconds to reset the clap pattern
                 clapInterval=0.08,
                 secondsPerTimePeriod=10
                 ):
        self.inputDeviceIndex = inputDeviceIndex
        self.volumeThreshold = volumeThreshold

        self.rate = rate
        self.buffer = buffer
        self.debounceTimeSamples = int(debounceTime * rate)
        self.resetTimeSamples = int(resetTime * rate)
        self.clapInterval = clapInterval #< seconds
        self.clapIntervalSamples = int(clapInterval * rate)

        self.samplesPerTimePeriod = secondsPerTimePeriod * rate

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.buffer,
                        input_device_index=self.inputDeviceIndex)
        # Clap detection variables
        self.lastClapSample = 0
        self.currentSample = 0 + self.debounceTimeSamples
        self.clapTimes = []
        self.doubleClapTimes = [] #< the times that a double clap occurred

    def subSample(self, a, b):
        result = a - b
        if b > a:
            result = self.samplesPerTimePeriod + a - b
        return result

    def addSample(self, a, b):
        return (a + b) % self.samplesPerTimePeriod

    def bandpassFilter(self, data, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        filteredData = lfilter(b, a, data)
        return filteredData

    def detectClap(self, audioData):
        clapDetected = False
        # Apply bandpass filter to focus on clap frequencies
        filteredAudio = self.bandpassFilter(audioData, lowcut=1600, highcut=2300, fs=self.rate)
        # (1700, 1900)
        # Find peaks in the audio signal
        peaks, _ = find_peaks(filteredAudio, height=self.volumeThreshold)

        # If peaks are found and debounce time has passed
        if len(peaks) > 0 and (self.subSample(self.currentSample, self.lastClapSample) >= self.debounceTimeSamples):
            print(f"Clap detected! {len(peaks)} peaks found")
            clapDetected = True

        return(clapDetected)

    def patternDetect(self):
        # Check for pattern reset
        if self.clapTimes and (self.subSample(self.currentSample, self.clapTimes[-1]) >= self.resetTimeSamples):
            pattern = []
            intervals = [self.subSample(self.clapTimes[i], self.clapTimes[i-1]) for i in range(1, len(self.clapTimes))]

            # Initialize variables
            shortIntervalCount = 0

            # Loop through each interval and update shortIntervalCount
            # and pattern accordingly.
            for interval in intervals:
                if interval < self.clapIntervalSamples:  # Short interval detected
                    shortIntervalCount += 1
                else:  # Long interval or end of pattern detected
                    pattern.append(shortIntervalCount)
                    shortIntervalCount = 0  # Reset shortIntervalCount for the next group

            # Handle the case where the pattern ends with a short interval
            # or if it ends with a long interval but no short interval followed before
            pattern.append(shortIntervalCount)

            print("Pattern:", pattern)
            return pattern
        return ''

    def printDeviceInfo(self):
        info = self.p.get_host_api_info_by_index(0)
        numDevices = info.get('deviceCount')

        print("Available audio devices:")
        for i in range(0, numDevices):
            deviceInfo = self.p.get_device_info_by_host_api_device_index(0, i)
            print(f"Device {i}: {deviceInfo['name']}")

    def ntty(self, msg):
        url = f"http://192.168.0.121:81/testing"
        try:
            res = requests.post(url, data=msg)
        except:
            res = None
        return(res)
    
    def run(self):
        self.printDeviceInfo()
        try:
            print("ready")
            while True:
                try:
                    audioData = np.frombuffer(self.stream.read(self.buffer), dtype=np.int16)
                except Exception as e:
                    print(f"error in reading stream: {e}")
                    time.sleep(1)
                    continue
                self.currentSample = self.addSample(self.currentSample, self.buffer)

                if self.detectClap(audioData):
                    self.lastClapSample = self.currentSample
                    self.clapTimes.append(self.currentSample)

                result = self.patternDetect()
                if len(result) == 2:
                    timeNow = datetime.now()
                    timeNowFormated = f"{timeNow.hour}:{timeNow.minute}"
                    self.doubleClapTimes.append(timeNowFormated)
                    listTimes = str("\n".join(self.doubleClapTimes))
                    print(listTimes)

                    with open("counter.dat", "w") as f:
                        f.write(listTimes)

                    self.ntty(timeNowFormated)

                if result != '':
                    self.clapTimes = []  # Reset clapTimes

        except KeyboardInterrupt:
            print("Exited gracefully")
        except Exception as e:
            print(e)
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

if __name__ == '__main__':
    clapDetection = ClapDetector()
    clapDetection.run()
