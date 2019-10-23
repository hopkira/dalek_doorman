# dalek-doorman

## Description
A talking dalek doorman with face recognition and attitude that will welcome you home or say goodbye.  The context of whether to say hello or goodbye is dependent upon whether the dalek has seen your mobile phone recently.  Of course, if he doesn't recognise you, he will threaten you with extermination!

## Key program files
The doorman is based on six key files:

Filename | Language | Description
--------|--------|-----------
dalek-doorman.py | Python 3 | The main program that uses face recognition to identify who is in front of the dalek and uses the Cloudant DB to determine the context (i.e. inferring whether you are leaving or arriving)
whosin.py | Python 3 | A Scapy based program that scans your home network an IP address at a time and retrieves the MAC address of active devices.  This information is used to infer whether a household member is at home or not and this information is stored in Cloudant DB on IBM Cloud.
whosin.json | Node-RED | A simple flow that reads the data from the Cloudant DB and provides a a web page dashboard that shows who is in the house and who is out
dalek_db.py | Python 3 | Provides a very thin abstraction layer on top of the Cloudant APIs enabling the database implementation to be changed without impacting the other programs
db_init.py | Python 3 | Initializes the Cloudant DB with information such as family names and the MAC addresses of their mobile phones (generally only run once)
tts | bash script | A very simple script that turns text into a dalek voice via espeak and sox

## Installation and execution
The dalek-doorman and whosin programs can be installed on separate Linux or MacOS machines, or can happily co-exist.  Although the programs work on Raspberry Pi, the face recognition is probably better done on a low end laptop or PC.  I am currently executing both simultaneously on an aged two core IBM Thinkpad T420 dual core 2.5GHz machine.

whosin.py assumes an IBM Cloud and Python environment that is described in detail in [this post](https://k9-build.blogspot.com/2019/10/whos-in-house.html).

dalek-doorman and the Cloudant programs will require the installation of a number of Python packages, the most significant installation is face_recognition which is described [here](https://github.com/ageitgey/face_recognition).  You will need to create a "training" directory under the directory from where you run dalek-doorman.  In the training directory you can then create a separate directory for each person you wish to recognise.  Inside each of those directories you can store different photos of that person.  The program assumes the file names are sequential e.g. 0.png, 1.png, 2.png etc.

