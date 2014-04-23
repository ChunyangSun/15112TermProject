import numpy as np
import cv2
import cv
import os


class BackgroundSubstraction(object):
    def main(self):
        self.ksize = 5
        self.sigma = 0.3*(self.ksize-1)*0.5 - 1 + 0.8
        self.fgbg = cv2.BackgroundSubtractorMOG()
        self.fgmask_last = [[0]*640 for row in xrange(480)]
        f = open("data.txt", "w")
        
        # get the video stream 
        cap = cv2.VideoCapture(0)
        # keep catching the frames 
        while(1):
            ret, self.frame = cap.read() 
            self.frame = self.erode(self.frame)
            self.frame = self.dilate(self.frame)
            self.fgmask = self.fgbg.apply(self.frame)
            
            self.diff = self.fgmask - self.fgmask_last
        
            #self.diff = self.erode(self.diff)
            #self.diff = self.dilate(self.diff)
            #self.getConnectedComponent()
            
            cv2.imshow('frame',self.diff)
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                break
        
            self.fgmask_last = self.fgmask 
        #f.close()
        cap.release()
        cv2.destroyAllWindows()
        
 #   def getConnectedComponent(self):
 #           
 #       # L = morphology.label(self.diff)
 #       # print "Number of components:", np.max(L)
 #       storage = cv2.cvCreateMemStorage(0)
 #       nb_contours, contours = cv2.findContours(self.diff,
 #       storage, cv2.CV_RETR_EXTERNAL,cv2.CV_CHAIN_APPROX_NONE, cv2.cvPoint(0,0))
	## comment this out if you do not want approximation
	#contours = cv.cvApproxPoly (contours, cv.sizeof_CvContour,
	#                                cv.CV_POLY_APPROX_DP, 3, 1)
 #       
 #       self.contours = contours
        
        
        
    def erode(self, frame):
        gaussion = cv2.getGaussianKernel(self.ksize, self.sigma) 
        frame = cv2.erode(frame, gaussion)
        return frame
        
    def dilate(self, frame):
        gaussion = cv2.getGaussianKernel(self.ksize, self.sigma) 
        frame = cv2.dilate(frame, gaussion)
        return frame
    

bgd = BackgroundSubstraction()
bgd.main()