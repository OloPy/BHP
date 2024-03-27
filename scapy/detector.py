# -*-coding:Utf-8 -*

"""
This is a face detector on image file from BHP book.

Need these packages:
libopencv-dev, python3-opencv, python3-numpy python3-scipy
training files:
http://eclecti.cc/files/2008/03/haarcascade_frontalface_alt.xml
Improvement done:
- auto download training files

Improvement to do:
- add argparse for folders

"""

import cv2
import os
import requests


def detect(srcdir: str, tgdir: str, train_dir: str) -> None:
    for fname in os.listdir(srcdir):
        if not fname.upper().endswith('.JPEG'):
            continue
        fullname = os.path.join(srcdir, fname)
        newname = os.path.join(tgdir, fname)
        img = cv2.imread(fullname)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        training = os.path.join(train_dir, 'haarcascade_frontalface_alt.xml')
        cascade = cv2.CascadeClassifier(training)
        rects = cascade.detectMultiScale(gray, 1.3, 5)
        try:
            if rects.any():
                print('Got a face')
                rects[:, 2:] += rects[:, 2:]
        except AttributeError:
            print(f'No face found in {fname}.')
            continue
        # hilight the faces in the image
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(img, (x1, y1), (x2, y2), (127, 255, 0), 2)
        cv2.imwrite(newname, img)


def downloadTraining(fileUrl: str, path: str) -> str:
    """
    This function will dl a file from URL and store it in path
    :param fileUrl: the url for file dl
    :param path: the path where we want to store file
    :return: log of operation
    """
    response = requests.get(fileUrl)
    destFile = os.path.join(path, fileUrl.split('/')[-1])
    log = f'We save data in {destFile}\n'
    with open(destFile, 'w') as f:
        f.write(response.content.decode())
    return log


if __name__ == '__main__':
    trainingUrl = 'http://eclecti.cc/files/2008/03/haarcascade_frontalface_alt.xml'
    if not os.path.exists('/tmp/BHP/training/haarcascade_frontalface_alt.xml'):
        print(downloadTraining(trainingUrl, '/tmp/BHP/training'))
    detect('/tmp/BHP/pictures', '/tmp/BHP/faces', '/tmp/BHP/training')