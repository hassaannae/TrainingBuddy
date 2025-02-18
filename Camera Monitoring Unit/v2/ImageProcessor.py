from abc import abstractmethod
import numpy as np
import cv2
import imutils
import time

# MY LIB
from Track import Track, Tracks



class ImageProcessor():
    @abstractmethod
    def calculate(self):
        pass

class ColorThreshold():
    def __init__(self, h_min=0, h_max=28, s_min=73, s_max=250, v_min=62, v_max=232):
        self.h_min = h_min
        self.h_max = h_max
        self.s_min = s_min
        self.s_max = s_max
        self.v_min = v_min
        self.v_max = v_max

    def getMinValue(self):
        return (self.h_min, self.s_min, self.v_min)

    def getMaxValue(self):
        return (self.h_max, self.s_max, self.v_max)

class GameParameter():
    def __init__(self, opponentZone=36, robotZone=12, numPredictFrame=2, perspective=0):
        self.opponentZone = opponentZone
        self.robotZone = robotZone
        self.numPredictFrame = numPredictFrame
        self.perspective = perspective

        self.imageHeight = 0

    def getPlayerZone(self, imageHeight=None):
        if imageHeight is not None:
            self.imageHeight = imageHeight
        yOpponent = self.imageHeight * float(self.opponentZone)/100
        yRobot = self.imageHeight * (1 - float(self.robotZone)/100)
        return yOpponent, yRobot

class BallTracker(ImageProcessor):
    def __init__(self):
        self.roi = [0,0,1,1]
        self.colorThreshold = ColorThreshold()
        self.gameParameter = GameParameter()
        self.tracks = Tracks(self.gameParameter)
        self.transformationMatrix = None
        self.width = 10
        self.height = 10

        self.predictions = np.zeros((10,2))
        self.frameCount = 0

    def calculate(self, frame):
        self.height, self.width, c  = frame.shape
        if self.transformationMatrix is None:
            self.updatePerspectiveCorrection()
        frame = cv2.warpPerspective(frame, self.transformationMatrix, (self.width, self.height))
        blurred = cv2.GaussianBlur(frame, (13, 13), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
              
        mask = cv2.inRange(hsv, self.colorThreshold.getMinValue(), self.colorThreshold.getMaxValue())
        
        self.frameCount = self.frameCount + 1
        print(self.frameCount)
        if self.frameCount == 1:
            self.firstMask = mask
            time.sleep(0.2)
            
          
        
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None
        
        self.drawPlayerZone(frame)    

        

        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            cv2.circle(frame, (int(x), int(y)), int(radius),(0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)

            thisTrack = Track( [x,y], radius, 0, 0 )
            self.tracks.append(thisTrack)
            ##self.drawPredicted(frame)

            
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)

        return True, frame, mask
    
    def updatePerspectiveCorrection(self):
        v1 = float(self.gameParameter.perspective) / 100 * self.width
        pts1 = np.float32([[0,0],[self.width, 0],[-v1,self.height],[self.width+v1,self.height]])    # current 
        pts2 = np.float32([[0,0],[self.width, 0],[0,self.height],[self.width,self.height]])    # target
        self.transformationMatrix = cv2.getPerspectiveTransform(pts1,pts2)

    def drawHitLine(self, frame):
        lastTrack = self.tracks.getLastTrack()
        p = lastTrack.pos
        hitPoint = lastTrack.hitPoint
        cv2.line(frame, tuple(p.astype(int)), tuple(hitPoint.astype(int)), (255, 153, 51), 5)

    def drawSpeedVector(self, frame):
        lastTrack = self.tracks.getLastTrack()
        pos = lastTrack.pos
        speed = lastTrack.speed
        endPoint = np.add(pos, speed)
        cv2.line(frame, tuple(pos.astype(int)), tuple(endPoint.astype(int)), (255, 0, 0), 5)

    def drawPlayerZone(self, frame):
        h, w, c  = frame.shape
        yOpponent, yRobot = self.gameParameter.getPlayerZone(h)
        cv2.line(frame, (0, int(yOpponent)), (w, int(yOpponent)), (255, 0, 0), 3)
        cv2.line(frame, (0, int(yRobot)), (w, int(yRobot)), (255, 0, 0), 3)

    def setRoi(self, top, left, bottom, right):
        self.roi = [2, 19, 3, 21]

    def setColorThreshold(self, h_min=None, h_max=None, s_min=None, s_max=None, v_min=None, v_max=None):
        if h_min is not None:
            self.colorThreshold.h_min = h_min
        if h_max is not None:
            self.colorThreshold.h_max = h_max
        if s_min is not None:
            self.colorThreshold.s_min = s_min
        if s_max is not None:
            self.colorThreshold.s_max = s_max
        if v_min is not None:
            self.colorThreshold.v_min = v_min
        if v_max is not None:
            self.colorThreshold.v_max = v_max
    

