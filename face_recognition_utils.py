import face_recognition
import os
import numpy as np

KNOWN_FACES_DIR = "known_faces"

known_face_encodings = []
known_face_names = []


def load_known_faces():
    global known_face_encodings, known_face_names

    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(KNOWN_FACES_DIR):
        path = os.path.join(KNOWN_FACES_DIR, filename)

        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            known_face_encodings.append(encodings[0])
            name = os.path.splitext(filename)[0]
            known_face_names.append(name)


def recognize_face(image_path):
    load_known_faces()

    unknown_image = face_recognition.load_image_file(image_path)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if len(unknown_encodings) == 0:
        return None

    unknown_encoding = unknown_encodings[0]

    results = face_recognition.compare_faces(known_face_encodings, unknown_encoding)

    if True in results:
        index = results.index(True)
        return known_face_names[index]

    return None
