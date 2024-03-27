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

import argparse
import cv2
import os
import requests


def manageArgs() -> argparse.Namespace:
    """
    Manage Arguments.
    :return:
    """
    if os.name == 'nt':
        sourcePath = os.path.join(os.environ["TEMP"], "BHP")
    else:
        sourcePath = '/tmp/BHP'
    defaultSourceDir = os.path.join(sourcePath, 'images')
    defaultoutputDir = os.path.join(sourcePath, 'output')
    defaultTrainingDir = os.path.join(sourcePath, 'training')
    parser = argparse.ArgumentParser(
        description='BHP detector find faces in all jpg or jpeg in a directory.\n'
                    'Training file for openCv is found here '
                    'http://eclecti.cc/files/2008/03/haarcascade_frontalface_alt.xml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python3 detector.py -s /tmp/BHP/images -o /tmp/BHP/outPut -t /tmp/BHP/training\n')
    parser.add_argument(
        '-s',
        '--sourceDir',
        default=defaultSourceDir,
        help=f'The directory with jpeg or jpg. Default is {defaultSourceDir}'
    )
    parser.add_argument(
        '-o',
        '--outputDir',
        default=defaultoutputDir,
        help=f'The directory where we put images with faces. Default is {defaultoutputDir}'
    )
    parser.add_argument(
        '-t',
        '--trainingDir',
        default=defaultTrainingDir,
        help=f'The directory containing haarcascade_frontalface_alt.xml training file. Default is {defaultTrainingDir}'
    )
    parser.add_argument('-f', '--forceDlTrain', action='store_true', help='Force the download of training file.')
    return parser.parse_args()


def detect(sourceDir: str, targetDir: str, train_dir: str) -> None:
    print(f'List of files found: {", ".join(os.listdir(sourceDir))}')
    for fileName in os.listdir(sourceDir):
        if not fileName.upper().endswith('.JPEG') and not fileName.upper().endswith('.JPG'):
            continue
        fullname = os.path.join(sourceDir, fileName)
        newname = os.path.join(targetDir, fileName)
        img = cv2.imread(fullname)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        training = os.path.join(train_dir, 'haarcascade_frontalface_alt.xml')
        cascade = cv2.CascadeClassifier(training)
        rects = cascade.detectMultiScale(gray, 1.3, 5)
        try:
            if rects.any():
                print(f'Got a face in {fileName}')
                rects[:, 2:] += rects[:, 2:]
        except AttributeError:
            print(f'No face found in {fileName}.')
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
    myArgs = manageArgs()
    try:
        if not os.path.exists(myArgs.sourceDir):
            os.makedirs(myArgs.sourceDir)
        if not os.path.exists(myArgs.outputDir):
            os.makedirs(myArgs.outputDir)
        if not os.path.exists(myArgs.trainingDir):
            os.makedirs(myArgs.trainingDir)
    except PermissionError as Perr:
        print(f'You are not allowed to create {Perr.filename}!')
        exit(1)

    trainingUrl = 'http://eclecti.cc/files/2008/03/haarcascade_frontalface_alt.xml'
    if not os.path.exists(os.path.join(myArgs.trainingDir, 'haarcascade_frontalface_alt.xml')) or myArgs.forceDlTrain:
        print(downloadTraining(trainingUrl, myArgs.trainingDir))
    detect(myArgs.sourceDir, myArgs.outputDir, myArgs.trainingDir)