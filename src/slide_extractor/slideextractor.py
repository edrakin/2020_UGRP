import time
import os
import argparse
import cv2
import imutils
import changedetection
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--video", dest="video", required=True,
                    help="the path to your video file to be analyzed")
parser.add_argument("-o", "--output", dest="output", default="slides.pdf",
                    help="the output pdf file where the extracted slides will be saved")
parser.add_argument("-s", "--step-size", dest="step-size", default=20,
                    help="the amount of frames skipped in every iteration")
parser.add_argument("-p", "--progress-interval", dest="progress-interval", default=1,
                    help="how many percent should be skipped between each progress output")
parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true",
                    help="the path to your video file to be analyzed")
args = vars(parser.parse_args())



class SlideExtractor:
    slideCounter = 10
    result = []

    def __init__(self, debug, vidpath, output, stepSize, progressInterval):
        self.vidpath = vidpath
        self.output = output
        self.detection = changedetection.ChangeDetection(
            stepSize, progressInterval, debug)
        # self.dupeHandler = duplicatehandler.DuplicateHandler(1)

    # crop image to slide size
    def cropImage(self, frame):
        min_area = (frame.shape[0] * frame.shape[1]) * (2 / 3)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)#회색으로 만들고
        thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]#이미지 이진화(흑백)
        contours = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)#가장 큰 컨투어 찾기
        contours = contours[0] if imutils.is_cv2() else contours[1]#cv버전에 따라 컨투어 변환
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                crop = frame[y:y+h, x:x+w]
                return crop

    def onTrigger(self, frame):
        frame = self.cropImage(frame)
        if frame is not None:
            self.saveSlide(frame)

#save slide in directory
    def saveSlide(self, slide):
        print("Saving slide " + str(self.slideCounter - 10) + "...")
        cv2.imwrite(os.path.join(
            "img", str(self.slideCounter) + ".jpg"), slide)
        self.slideCounter += 1
#list img after deduplication
    def listImg(self):
        path = "./img"
        file_names = os.listdir(path)

        i = 0
        for name in file_names:
            src = os.path.join(path, name)
            dst = str(i) + '.jpg'
            dst = os.path.join(path, dst)
            os.rename(src, dst)
            i += 1

    def clearImg(self):
        if not os.path.exists("./img"):
            os.makedirs("./img")
        file_names = os.listdir("./img")
        for name in file_names:
            os.remove(os.path.join("./img", name))

    def start(self):
        now = time.localtime()
        print("%04d/%02d/%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
        self.clearImg()
        self.detection.onTrigger += self.onTrigger

        self.detection.start(cv2.VideoCapture(self.vidpath.strip()))

        subprocess.call('python sort.py', shell=True)
        self.listImg()
        print("SlideExtractor Done.")


main = SlideExtractor(args['debug'], args['video'], args['output'],
                      args['step-size'], args['progress-interval'])
main.start()
