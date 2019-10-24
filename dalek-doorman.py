import face_recognition
import cv2
import numpy as np
import os
import time
import subprocess
import random
import dalek_db as db
from os import listdir
from os.path import isfile, join

DEAD_TIME = 30 # minimum time in seconds between doorman annoucemnents
EVENT_GAP = 3 # maximum time window in seconds for valid detection events
THRESHOLD = 3 # no. of recognition events needed with less than EVENT_GAP between them to hit threshold
UNKNOWN_THRESHOLD = 4 # numer of unknown events to hit threshold
SAMPLES = 8 # number of training photos per person (limit 50 in total)

known_face_encodings = [] # a list of all the face encodings
known_face_names = [] # a list of the unique people that have been trained on
known_people = [] # the list of the people in each trained image

unknown_count = 0 # number of times an unknown face has been seen
unknown_seen = round(time.time())

video_capture = cv2.VideoCapture(0) # opens default video capture stream

# connect to the Cloudant "dalek" database
my_connection = db.get_connection()
my_db = db.db_read(my_connection,"dalek")

class Person:
    '''The Person class represents the people known to the Dalek'''

    def __init__(self,name):
        '''Each Person instance has attributes persistently stored in Cloudant
        
        Attributes
        ----------
        name : str
            the name of the person (used as document index on Cloudant)
        last_seen : int
            time since last greeting, stored in Cloudant
        detected: int
            time of last detection event
        detected_events: int
            number of detection events within EVENT_GAP
        detection_time: int
            time of last detection event

        Methods
        -------

        just_seen :
            records a sighting of the person by the robot
        '''
        self.name = name
        self.detection_events = 0 # number of detection events at init is zero
        self.doc = db.read_doc(my_db,self.name) # retrieve Person details from Cloudant
        self.last_seen = self.doc['last_seen'] # time of last announcement
        self.detected = self.last_seen # time of last know detection event

    def just_seen(self):
        '''Record sighting of person in Cloudant'''

        global unknown_count
        unknown_count = 0
        self.now = round(time.time()) # record the time of the detection event
        self.doc = db.read_doc(my_db,self.name) # retrieve the relevant Cloudant document
        self.duration = self.now - self.doc['last_seen'] # work out how long since last greeting
        print("Just seen " + str(self.name) + " after " + str(self.duration) + "s")
        if (self.duration > DEAD_TIME) : # tests if an announcment is allowed
            self.gap = self.now - self.detected # gap = how long since last sighting
            self.detected = self.now # record the time of the sighting
            self.detection_events += 1 # increment the sightings counter
            print("Seen " + str(self.name) + " " + str(self.detection_events) + " times.  Last time " + str(self.gap) + "s ago")
            if (self.gap < EVENT_GAP) : # is the gap shorter than the allowed gap?
                "I will remember this."
                if (self.detection_events >= THRESHOLD) : # has the threshold been met?
                    print("I have seen " + self.name + " too many times for it to be a false postive.")
                    # as we are outside the dead time and the threshold has
                    # been met, then we make an annoucement by
                    # upadating the Cloudant db with the current time,
                    # resetting the detection events counter to zero and
                    # initiating the dalek greeting
                    self.doc = db.read_doc(my_db,self.name) # re-retrieve the relevant Cloudant document
                    try:
                        db.update_doc(self.doc, "last_seen", self.now)
                        db.save_doc(self.doc)
                    except:
                        print("ERROR: Write error to database")
                    self.detection_events = 0
                    dalek_greeting(self.name, self.doc['in_house'])
                else:
                    print("Back to watching, detection events for " + str(self.name) + " stands at " + str(self.detection_events))
                    return
            else :
                # as the event is outside the window, but a sighting
                # has happened then reset the counter to 1
                self.detection_events = 1
                print("Reset counter. Detection events for " + str(self.name) + " is set to " + str(self.detection_events)) 
                return
        else :
            print("I've seen " + str(self.name) +", but recently shouted at them.")
            return

def dalek_greeting(name, in_house):
    '''Dalek will issue an appropriate greeting depending upon context'''
    
    response = ""
    leaving = ("Have a nice day name","Goodbye name","Come back soon name","See you later name")
    arriving = ("Welcome back name","Hello name, you are a friend of the Darleks","Greetings name")
    if in_house :
        response = random_msg(leaving)
    else:
        response = random_msg(arriving)
    response = response.replace('name',name)
    print(response)
    dalek_speak(response)

def dalek_warning():
    '''Dalek will issue a random threat to unidentified faces'''
    global unknown_count
    global unknown_seen
    global UNKNOWN_THRESHOLD
    now = round(time.time())
    unknown_count += 1
    if ((now - unknown_seen) > 300) :
        unknown_count = 1
    if (unknown_count < UNKNOWN_THRESHOLD) :
        print("Unknown count: " + str(unknown_count))
        return
    else :
        warning = ("You are unrecognized. Do not move!","Halt. You are an enemy of the Darleks."," You are unknown. You will be exterminated!")
        response = random_msg(warning)
        unknown_count = 0
        dalek_speak(response)

def dalek_speak(speech):
    '''Assemble the command line argument and execute as subprocess'''
    
    command = './tts ' + speech
    subprocess.call(command, shell=True)

def random_msg(phrase_dict):
    '''Choose a random phrase from a list'''
    
    length = len(phrase_dict)
    index = random.randint(0,length-1)
    message = phrase_dict[index]
    return message

# This routine iterates across all files and directories in the training directory.
# Each person has their own directory, with the photos being stored as .png files.
# The files should be called '0.png', '1.png' etc.
for root, dirs, files in os.walk('/your_path/dalek-doorman/training'):
    for dir in dirs:
        print('Training subject: ' + dir) # announce who is being trained
        # create an instance of person based on directory name
        known_people.append(Person(dir)) 
        for num in range (0,SAMPLES): # iterate over this number of photo samples for each person
            # create a fully described path for each training image
            file_name = str(num)+'.png'
            train_filename = (os.path.join(root,dir,file_name))
            print('Training ' + dir + ' with ' + train_filename)
            # load the image into the face recognition module and train
            training_image = face_recognition.load_image_file(train_filename)
            known_face_encodings.append(face_recognition.face_encodings(training_image)[0])
            known_face_names.append(dir)

def detect_face():
    '''Returns a list of names for all the faces detected in the video stream'''

    face_locations = [] # list of all face locations in video image
    face_encodings = [] # list of all face encodings from face locations
    face_names = [] # list of people in the video image
    ret, frame = video_capture.read() # read a frame of the video stream
    rgb_frame = frame[:, :, ::-1] # convert to rgb colour
    # get a list of where all the faces are in the frame
    face_locations = face_recognition.face_locations(rgb_frame)
    # encode all the faces that have been detected for recognition
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    # for each of the encoded faces, try and work out who it is...
    for face_encoding in face_encodings:
        name = "unknown" # default return if the face(s) are unrecognised
        # see if the face is a match for the previously trained faces
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        # best match is the face from all the trained images with the smallest delta
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            # retrieve the name of the best match
            name = known_face_names[best_match_index]
        face_names.append(name) # add 'unknown' or the name to the return list
    return face_names

while True:
    try:
        faces = detect_face()
        if len(faces)>0:
            print ("======DETECTED=======")
            for face in faces:
                for search_face in known_people : 
                    if search_face.name == face :
                        search_face.just_seen()
                if face == "unknown" :
                    dalek_warning()
            print ("=====================")
    except KeyboardInterrupt:
        video_capture.release()
        print("\nProgram stopped by user")
        quit()
