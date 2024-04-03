# Clap Detection System

## Overview

This project implements a clap detection system using an a mic or raw audio data as input. It can detect calp patterns including single and double claps.

## Features

- Clap pattern detection.
- Dynamic threshold adjustment for robust clap detection.
- Bandpass filtering to focus on clap frequencies.
- Audio recording and saving capabilities.

## Requirements

- Python3
- PyAudio
- NumPy
- SciPy

## Installation

### option A:
1. install from the official pypi package (might be outdated):
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
   cd clapDetection
   ```

3. Run the clap detection script:

   ```bash
   python clapDetector.py
   ```

## Configuration

- Adjust parameters in the `ClapDetector` class constructor to fine-tune the clap detection system.

## Usage

1. Run the script using ```bash python clapDetector.py```.

2. The system will continuously monitor audio input and detect claps.

## Troubleshooting

- If there are issues with audio input, check the device index in the `ClapDetector` constructor.

- Adjust the bandpass filter parameters for better clap detection in different environments.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
