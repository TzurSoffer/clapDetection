import pyaudio
import numpy as np
import time
from datetime import datetime
import requests
from scipy.signal import butter, lfilter, find_peaks
from scipy.io.wavfile import write as writeAudioFile
import logging
from collections import deque

class ClapDetector():
    """TBR
    """
    def __init__(self, inputDeviceIndex=8, #< 8
                 initialVolumeThreshold=7000,
                 rate=48000,
                 bufferLength=1024,
                 debounceTimeFactor=0.15,
                 resetTime=0.25,                                       #< seconds to reset the clap pattern
                 clapInterval=0.08,
                 secondsPerTimePeriod=10,
                 volumeAverageFactor=0.9,                              #< Factor to control the influence of the new threshold on the average
                 logger=None,
                 logLevel = logging.INFO,
                 audioBufferLength=3.1                                 #< legth of audio to save in buffer in seconds (for saving audio to file only. not used in calculations)
                 ):
        self.inputDeviceIndex = inputDeviceIndex
        self.volumeThreshold = initialVolumeThreshold
        self.rate = rate
        self.bufferLength = bufferLength
        self.debounceTimeFactor = debounceTimeFactor
        self.resetTimeSamples = int(resetTime * rate)
        self.clapIntervalSamples = int(clapInterval * rate)
        self.samplesPerTimePeriod = secondsPerTimePeriod * rate
        self.volumeAverageFactor = volumeAverageFactor
        
        print((rate*audioBufferLength)/bufferLength)
        self.audioBuffer = deque(maxlen=int((rate*audioBufferLength)/bufferLength))

        # Clap detection variables
        self.currentSampleTime = 0 + int(debounceTimeFactor * rate)
        self._resetClapTimes()                                        #< initialize the clapTimes with a zero for the debounce to have an init value to use for calculations
        
        #initialize the logger if a logger was not provided
        self.logger = logger
        if self.logger == None:
            self.initLogger(logLevel=logLevel)
    
    def _resetClapTimes(self):
        self.clapTimes = [0]  #< Reset clapTimes
    
    def initLogger(self, logLevel=logging.INFO) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logLevel)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Add a file handler
        fileHandler = logging.FileHandler('clapDetection.log')
        fileHandler.setLevel(logLevel)
        fileHandler.setFormatter(formatter)
        self.logger.addHandler(fileHandler)

        # Stream handler (to print log messages to the console)
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logLevel)
        streamHandler.setFormatter(formatter)
        self.logger.addHandler(streamHandler)

    def initAudio(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.bufferLength,
                                  input_device_index=self.inputDeviceIndex)
        self.logger.debug("audio has been initialized")
        return(self)
        
    def restartAudio(self):
        try:
            self.stop()
        except:
            self.logger.warning("audio stream failed to stop")
        self.initAudio()
        self.logger.debug("sucsesfully restarted audio stream")
        return(self)

    def calculateTimeDifference(self, timeA, timeB) -> float:
        """
        Calculate the time difference between two timestamps, considering a circular time scale([97,98,99,0,1,2,3,4]).

        Args:
        - timeA (float): The first timestamp.
        - timeB (float): The second timestamp.

        Returns:
        - float: The time difference between timeA and timeB.
        """

        timeDifference = timeA - timeB

        # If timeB is greater than timeA, it means we've crossed the circular boundary.
        # In such cases, consider the time period to complete the circle.
        if timeB > timeA:
            timeDifference += self.samplesPerTimePeriod

        return(timeDifference)

    def convertToCircularTime(self, timestamp) -> float:
        """
        Convert the timestamp to a circular time scale.

        Args:
        - timestamp (float): The timestamp.

        Returns:
        - float: The result of timestamp, modulo self.samplesPerTimePeriod.
        """
        circularTimeResult = timestamp % self.samplesPerTimePeriod
        return(circularTimeResult)

    def bandpassFilter(self, data, lowcut, highcut, fs, order=5):
        """
        Apply a bandpass filter to the input data.

        Args:
        - data (array): Input data to be filtered.
        - lowcut (float): Low cutoff frequency of the bandpass filter.
        - highcut (float): High cutoff frequency of the bandpass filter.
        - fs (float): Sampling frequency of the input data.
        - order (int): Order of the Butterworth filter (default is 5).

        Returns:
        - array: Filtered data after applying the bandpass filter.
        """
        # Calculate Nyquist frequency
        nyq = 0.5 * fs

        # Normalize cutoff frequencies
        low = lowcut / nyq
        high = highcut / nyq

        # Design a Butterworth bandpass filter
        b, a = butter(order, [low, high], btype='band')

        # Apply the bandpass filter to the input data
        filteredData = lfilter(b, a, data)

        return filteredData

    def updateDynamicThreshold(self, newValue) -> None:
        """
        Update the volume threshold using a running average with a weighted change.

        This method adjusts the volume threshold based on a running average calculation.
        The running average is updated by incorporating a new dynamic threshold, taking into account
        the influence of the existing threshold and the new value. The change is weighted to be
        only half of the difference, making the threshold adjustment more robust.

        Args:
        - newValue (float): The new dynamic threshold to be incorporated into the running average.

        Returns:
        - None
        """
        # Update the volume threshold as a running average
        self.volumeThreshold = (self.volumeAverageFactor * self.volumeThreshold) + \
                            ((1 - self.volumeAverageFactor) * newValue) * 0.5

    def isClap(self, thresholdBias=6000, lowcut=1600, highcut=2300):
        """
        Detect the occurrence of a clap in the input audio data using a dynamic threshold.

        This method applies a bandpass filter to focus on clap frequencies, calculates a dynamic threshold
        based on the maximum amplitude in the last second, and detects peaks in the filtered audio signal
        that exceed the adjusted volume threshold. The occurrence of a clap is determined by the presence
        of peaks and the debounce time condition.

        Args:
        - thresholdBias (float): Bias added to the volume threshold to account for variations (default is 6000).
        - lowcut (float): Low cutoff frequency for the bandpass filter (default is 1600).
        - highcut (float): High cutoff frequency for the bandpass filter (default is 2300).

        Returns:
        - bool: True if a clap is detected, False otherwise.
        """
        clapDetected = False

        # Apply bandpass filter to focus on clap frequencies
        filteredAudio = self.bandpassFilter(self.audioData, lowcut=lowcut, highcut=highcut, fs=self.rate)

        # Calculate dynamic threshold based on the maximum amplitude in the last second
        dynamicThreshold = np.max(np.abs(self.audioData[-self.rate:]))

        # Update the dynamic threshold
        self.updateDynamicThreshold(dynamicThreshold)

        # Find peaks in the filtered audio signal
        peaks, _ = find_peaks(self, currentSampleTime, filteredAudio, height=self.volumeThreshold + thresholdBias)

        # If peaks are found and debounce time has passed
        if len(peaks) > 0 and (self.calculateTimeDifference(currentSampleTime, self.clapTimes[-1]) >= int(self.debounceTimeFactor * self.rate)):
            clapDetected = True
            self.clapTimes.append(currentSampleTime)
            self.logger.debug(f"Clap detected! {len(peaks)} peaks found")

        return(clapDetected)

    def detectClapPattern(self) -> list:
        """
        Detect and extract clap patterns based on recorded clap times.

        Returns:
        - list: A list representing the detected clap pattern, where each element corresponds to the number of short
                intervals before a long interval or the end of the pattern.
        """
        pattern = []

        # Check for pattern reset
        lastClapTime = self.clapTimes[-1]
        if self.calculateTimeDifference(self.currentSampleTime, lastClapTime) >= self.resetTimeSamples:
            pattern = self.extractPattern()
            # Uncomment the following line for debugging or logging the detected pattern
            # print("Clap Pattern:", pattern)

        return(pattern)

    def extractPattern(self) -> list:
        """
        Extract clap pattern based on the time intervals between recorded clap times.

        Returns:
        - list: A list representing the extracted clap pattern, where each element corresponds to the number of short
                intervals before a long interval or the end of the pattern.
        """

        intervals = [self.calculateTimeDifference(self.clapTimes[i], self.clapTimes[i - 1]) for i in range(1, len(self.clapTimes))] #< get the list of all the time differences between the claps
        pattern = []
        consecutiveClaps = 1                         #< the amount of claps within the self.clapIntervalSamples time period

        for interval in intervals:
            if interval < self.clapIntervalSamples:
                consecutiveClaps += 1                #< add 1 to consecutiveClaps
            else:
                pattern.append(consecutiveClaps)     #< append the amount of claps to the pattern
                consecutiveClaps = 1                 #< reset consecutiveClaps
        
        if consecutiveClaps > 1:                     #< if there are more than one consecutaive clap that was recorder but not appended to the pattern
            pattern.append(consecutiveClaps)
        return(pattern)

    def printDeviceInfo(self) -> None:
        """
        Print information about available audio devices.

        This method retrieves information about audio devices and prints details for each device,
        including its index and name.

        Returns:
        - None
        """
        info = self.p.get_host_api_info_by_index(0)
        numDevices = info.get('deviceCount')

        print("Available audio devices:")
        for i in range(0, numDevices):
            deviceInfo = self.p.get_device_info_by_host_api_device_index(0, i)
            print(f"Device {i}: {deviceInfo['name']}")
    
    def getAudio(self, audio=-1) -> np.ndarray:
        """
        Continuously retrieve audio data from the input stream.

        This method attempts to read audio data from the input stream and returns the data as a NumPy array.
        If a recording error occurs, it waits for one second, prints an error message, resets the audio stream,
        and retries to obtain the audio data.

        Returns:
        - numpy.ndarray: NumPy array containing the retrieved audio data.
        """
        while True:
            try:
                self.audioData = audio
                if type(audio) == int:
                    self.audioData = np.frombuffer(self.stream.read(self.bufferLength), dtype=np.int16) #< Convert the raw audio data to a NumPy array of 16-bit integers
                
                self.audioBuffer.append(self.audioData)
                return(self.audioData)
            except:
                time.sleep(1)
                print("Recording error, resetting stream and trying again")
                self.restartAudio()
                continue
    
    def saveAudio(self, folder="./claps", fileName=None, audio=-1):
        if type(audio) == int:
            audio = np.array(self.audioBuffer, dtype=np.int16).reshape(-1,)
        if fileName == None:
            fileName = f"{datetime.now().strftime('%Y-%m-%d:%H:%M')}.wav"
        
        writeAudioFile(f"{folder}/{fileName}", self.rate, audio)

    def run(self, thresholdBias=6000, lowcut=1600, highcut=2300, audioData=-1) -> list:
        """
        Run the clap detection process and return the result.

        This method orchestrates the clap detection process. It updates the clap times,
        and returns the clap patterns.

        Args:
        - thresholdBias (float): Bias added to the volume threshold to account for variations (default is 6000).
        - lowcut (float): Low cutoff frequency for the bandpass filter (default is 1600).
        - highcut (float): High cutoff frequency for the bandpass filter (default is 2300).
        - audioData (array or int): Input audio data for clap detection or an indicator to retrieve audio data using self.getAudio().

        Returns:
        - list: The clap pattern.
        """

        self.getAudio(audioData)

        self.currentSampleTime = self.convertToCircularTime(self.currentSampleTime + self.bufferLength) #< Convert the current sample time to a circular time scale

        self.isClap(thresholdBias=thresholdBias, lowcut=lowcut, highcut=highcut)
        pattern = self.detectClapPattern()

        if pattern:              
            self._resetClapTimes()

        return(pattern)

    def stop(self):
        """gracefully stops the audio stream"""
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.logger.info("audio stream stoped")

if __name__ == '__main__':

    def sendNotification(msg):
        url = f"http://192.168.0.121:81/testing"
        try:
            res = requests.post(url, data=msg)
        except:
            res = None
        return res

    pyaudio.PyAudio()
    # clapDetection = ClapDetector()
    
    
    clapDetectorVars = ((6000, 1500, 2000), (6000, 2000, 2500), (6000, 2500, 3000))
    clapDetectors = [ClapDetector(logLevel=logging.DEBUG) for _ in range(len(clapDetectorVars))]
    clapDetectors[0].initAudio()
    print(clapDetectors[0].printDeviceInfo())
    
    # Run the clap detection in a loop
    try:
        while True:
            audioData = clapDetectors[0].getAudio()
            
            isClap = False
            for i in range(len(clapDetectorVars)):
                result = clapDetectors[i-1].run(thresholdBias=clapDetectorVars[i-1][0], lowcut=clapDetectorVars[i-1][1], highcut=clapDetectorVars[i-1][2], audioData=audioData)
                resultLength = len(result)
                # if resultLength >= 1:
                #     print(f"result is {result} for bias {clapDetectorVars[i-1][0]}, lowcut {clapDetectorVars[i-1][1]}, and highcut {clapDetectorVars[i-1][2]}")
                if resultLength == 2:
                    message = f"Double clap detected! bias {clapDetectorVars[i-1][0]}, lowcut {clapDetectorVars[i-1][1]}, and highcut {clapDetectorVars[i-1][2]}"
                    isClap = True
                    # print(message)
                    sendNotification(message)
                    # Add any additional actions you want to perform when a double clap is detected
            if isClap:
                clapDetectors[0].saveAudio()

    except KeyboardInterrupt:
        print("Exited gracefully")
    except Exception as e:
        print(f"error: {e}")
        for clapDetector in clapDetectors:
            clapDetector.stop()
