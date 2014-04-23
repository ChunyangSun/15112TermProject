#!/usr/bin/env python
from numpy import *
import numpy as np
import cv2
import cv
# import video
from matplotlib import pyplot as plt

help_message = '''
USAGE: motion_saliency.py [<camera_index>] [<mode>]
<mode>: 1: optical flow, 2: grabcut 
'''

# A function to draw the optical flow
def draw_flow(img, flow, step=16):
    h, w = img.shape[:2]
    y, x = np.mgrid[step/2:h:step, step/2:w:step].reshape(2,-1)
    fx, fy = flow[y,x].T
    lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.polylines(vis, lines, 0, (0, 255, 0))
    for (x1, y1), (x2, y2) in lines:
        cv2.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
    return vis

# A function to calculate the mask by thresholding the optical flow
def calc_mask(flow):
    h, w = flow.shape[:2]
    fx, fy = flow[:,:,0], flow[:,:,1]
    ang = np.arctan2(fy, fx) + np.pi
    v = np.sqrt(fx*fx+fy*fy)
    
    mask = np.zeros((h,w), np.uint8)
    
    # Use simple threshold to make the mask binary
    threshold = 0.2*v.max()
    mask[ v<threshold ] = 0
    mask[ v>threshold ] = 1

    # Alleviate the noise by image morphology, open and close
    kernel = np.ones((10,10),np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    kernel = np.ones((10,10),np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask

# A function to find contours and convex hull, used to get the tracking box
def process_mask(mask):
    # Find Contours
    contours, hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    hull = 0
    for i in xrange(len(contours)):
        temp_hull = cv2.convexHull(contours[i])
        if i == 0:
            hull = temp_hull
        else:
            hull = np.concatenate((hull,temp_hull))

    hull = cv2.convexHull(hull)
    return hull
    
# The main function 
if __name__ == '__main__':
    import sys
    print help_message
    try:
        # camera_index = sys.argv[1]
        fn = sys.argv[2]
        #mode_flag = sys.argv[2] 
    except:
        fn = 0

    cap = cv2.VideoCapture(0)
    ret, prev = cap.read()
    if not ret:
        print "cannot open the camera"
    else:
        prevgray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        show_hsv = True
        cur_glitch = prev.copy()
        first_time = True
        iteration_1 = 20
        iteration_2 = 50
        running_time_1 = 0
        running_time_2 = 0

        delta_c = 20
        is_stablizing = False
        stable_count = 0
        stable_thld = 10
        stable_time = 15
        frame_h, frame_w = prev.shape[:2]
        has_result = False
        while True:
            ret, img = cap.read()
            if not ret:
                break
            else:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                flow = cv2.calcOpticalFlowFarneback(prevgray, gray, 0.5, 3, 40, 1, 5, 1.2, 1)

                mask = calc_mask(flow)
                hull = process_mask(mask)
                M = cv2.moments(hull)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                area = cv2.contourArea(hull)
                x,y,w,h = cv2.boundingRect(hull)
                rect = (x,y,w,h)

                running_time_1 = running_time_1%iteration_1 + 1
                running_time_2 = running_time_2%iteration_2 + 1
                if first_time:
                    prev_rect = rect
                    first_time = False

                if running_time_2 == 1 and not is_stablizing:
                    stable_count = 0

                if running_time_1 == 1:
                    avg_cx = cx
                    avg_cy = cy
                    avg_area = area

                else:
                    avg_cx = (avg_cx*(running_time_1-1)+cx)/running_time_1
                    avg_cy = (avg_cy*(running_time_1-1)+cy)/running_time_1
                    avg_area = (avg_area*(running_time_1-1)+area)/running_time_1
                    #if is_stablizing:
                        #rect = prev_rect
                    if np.sqrt((avg_cx-cx)**2+(avg_cy-cy)**2) < 20 and abs(float(area-avg_area))/avg_area < 0.5:
                        # avg_cx = (avg_cx*(running_time-1)+cx)/running_time
                        # avg_cy = (avg_cy*(running_time-1)+cy)/running_time
                        # avg_area = (avg_area*(running_time-1)+area)/running_time
                        prev_rect = rect
                        #print "(area,w*h) = (%f,%f)" %(area,frame_w*frame_h)
                        if area < frame_h*frame_w*0.5 and not is_stablizing:
                            stable_count = stable_count + 1
                    else:
                        rect = prev_rect
                        
                
                if not has_result:
                    result = np.copy(img)

                if stable_count >= stable_thld + stable_time:

                    has_result = True
                    result = np.copy(img)
                    # Take picture
                    bgdModel = np.zeros((1,65),np.float64)
                    fgdModel = np.zeros((1,65),np.float64)
                    mask2 = np.zeros(img.shape[:2],np.uint8)    
                    cv2.grabCut(img,mask2,rect,bgdModel,fgdModel,10,cv2.GC_INIT_WITH_RECT)
                    
                    mask3 = np.zeros(img.shape[:2],np.uint8)
                    mask3[prev_rect[1]:prev_rect[1]+prev_rect[3],prev_rect[0]:prev_rect[0]+prev_rect[2]] = mask2[prev_rect[1]:prev_rect[1]+prev_rect[3],prev_rect[0]:prev_rect[0]+prev_rect[2]]
                    mask4 = np.where((mask3==2)|(mask3==0),0,1).astype('uint8')
                    result = result*mask4[:,:,np.newaxis]
                    crop_img = result[prev_rect[1]:prev_rect[1]+prev_rect[3],prev_rect[0]:prev_rect[0]+prev_rect[2]]
                    
                    is_stablizing = False
                    stable_count = 0
                    color = (0,255,0)

                elif stable_count > stable_thld: # and stable_count < stable_thld + stable_time:
                    # Prepare to take picture
                    is_stablizing = True
                    stable_count = stable_count + 1
                    rect = prev_rect
                    color = (255,0,0)
                else:
                    color = (0,255,0)

                print stable_count

                cv2.drawContours(img, hull, -1, (0,0,255), 3)
                
                cv2.imshow('with contours', img)
                cv2.waitKey(5)

            prevgray = gray

    cv2.destroyAllWindows()