[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)

# Devicehive Audio Analysis
Audio classification feature demo\
Detailed description can be found [here](https://www.iotforall.com/tensorflow-sound-classification-machine-learning-applications/)

## Installation
* Get a copy of this repo
* Install system packages
```bash
sudo apt-get install libportaudio2 portaudio19-dev
```
* Install python requirements
```bash
pip install -r requirements.txt
```

* Download and extract saved models to source directory
```bash
wget https://s3.amazonaws.com/audioanalysis/models.tar.gz
tar -xzf models.tar.gz
```

## Running
#### To process prerecorded wav file
run
```bash
python parse_file.py path_to_your_file.wav
```
_Note: file should have 16000 rate_

#### To capture and process audio from mic
run
```bash
python capture.py
```
It will capture and process samples in a loop.\
To get info about parameters run
```bash
python capture.py --help
```

#### To start web server
run
```bash
python daemon.py
```
By default you can reach it on http://127.0.0.1:8000 \
It will:
* Capture data form your mic
* Process data
* Send predictions to web interface
* Send predictions to devicehive

Also you can configure your devicehive connection though this web interface.

## Useful info
To train classification model next resources have been used:
* [Google AudioSet](https://research.google.com/audioset/)
* [YouTube-8M model](https://github.com/google/youtube-8m)
* [Tensorflow vggish model](https://github.com/tensorflow/models/tree/master/research/audioset)

You can try to train model with more steps/samples to get more accuracy.
