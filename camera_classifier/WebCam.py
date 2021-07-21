import numpy as np
import logging as log
from collections import deque
from Classifier import InferenceEngineClassifier

#puts openvino to the PATH
import os
os.add_dll_directory("C:\\Program Files (x86)\\Intel\\openvino_2021.3.394\\deployment_tools\\ngraph\\lib")
os.add_dll_directory("C:\\Program Files (x86)\\Intel\\openvino_2021.3.394\\deployment_tools\\inference_engine\\external\\tbb\\bin")
os.add_dll_directory("C:\\Program Files (x86)\\Intel\\openvino_2021.3.394\\deployment_tools\\inference_engine\\bin\\intel64\\Release")
#os.add_dll_directory("C:\\Program Files (x86)\\Intel\\openvino_2021.3.394\\deployment_tools\\inference_engine\\external\\hddl\\bin")
os.add_dll_directory("C:\\Program Files (x86)\\Intel\\openvino_2021.3.394\\opencv\\bin")
import cv2

# Define the upper and lower boundaries for a color to be considered "Blue"
blueLower = np.array([100, 60, 60])
blueUpper = np.array([140, 255, 255])

# Define a 5x5 kernel for erosion and dilation
kernel = np.ones((5, 5), np.uint8)

# Setup deques to store separate colors in separate arrays
bpoints = [deque(maxlen=1000)]

bindex = 0

colors = [(255, 255, 255)]
colorIndex = 0

# Setup the Paint interface
paintWindow = np.zeros((720, 1280,3)) + 0

cv2.namedWindow('Paint', cv2.WINDOW_AUTOSIZE)
cv2.getWindowImageRect('Paint')

# Load the video
camera = cv2.VideoCapture(0)

# Switcher
l1 = 1
l2 = 1
# Counter of image
c = 0

while True:
    # Grab the current paintWindow
    (grabbed, frame) = camera.read()
    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    cv2.putText(frame, "CLEAR ALL - press the 'c' key", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "SENT - press the 's' key", (49, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "STOP DRAWING - press the 'h' key", (49, 99), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "{} sent".format(c) , (600, 33), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    if(l1==1):
        cv2.putText(frame, "Turn On" , (800, 33), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        cv2.putText(frame, "Turn Off" , (800, 33), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)



    # Check to see if we have reached the end of the video
    if not grabbed:
        break

    # Determine which pixels fall within the blue boundaries and then blur the binary image
    blueMask = cv2.inRange(hsv, blueLower, blueUpper)
    blueMask = cv2.erode(blueMask, kernel, iterations=2)
    blueMask = cv2.morphologyEx(blueMask, cv2.MORPH_OPEN, kernel)
    blueMask = cv2.dilate(blueMask, kernel, iterations=1)

    # Find contours in the image
    (cnts, _) = cv2.findContours(blueMask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = None

    # Check to see if any contours were found
    if len(cnts) > 0:
    	# Sort the contours and find the largest one -- we
    	# will assume this contour correspondes to the area
        cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[0]
        # Get the radius of the enclosing circle around the found contour
        ((x, y), radius) = cv2.minEnclosingCircle(cnt)
        # Draw the circle around the contour
        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
        # Get the moments to calculate the center of the contour (in this case Circle)
        M = cv2.moments(cnt)
        center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))

        # Clear paintWindow 
        if cv2.waitKey(1) & 0xFF == ord("c"):
            bpoints = [deque(maxlen=512)]
            bindex = 0
            paintWindow[67:,:,:] = 0

        # Sent key
        if cv2.waitKey(1) & 0xFF == ord("s"):
            # ..... modifying line for project .....
            cv2.imwrite("image_{}.jpg".format(c), paintWindow)
            # ..... modifying line for project .....
            
            
            
            log.info("Start IE classification sample")

            # Create InferenceEngineClassifier object
            ie_classifier = InferenceEngineClassifier(
                configPath='squeezenet1.1.xml', 
                weightsPath='squeezenet1.1.bin', 
                device='CPU', 
                extension="CPU", 
                classesPath='names.txt')
            
                
            # Classify image
            prob = ie_classifier.classify(paintWindow)
            
            # Get top 5 predictions
            predictions = ie_classifier.get_top(prob)
            
            labels = [ie_classifier.labels_map[x] for x in predictions]
            
            # print result
            log.info("Predictions: " + str(predictions) + str(labels))
            
            

            bpoints = [deque(maxlen=512)]
            bindex = 0
            paintWindow[67:,:,:] = 0
            c+=1

        # Change switcher for stop/start drawing
        if cv2.waitKey(1) & 0xFF == ord("h"):
            l1 = -l1
            l2 = 1

        # Create the next new deq for lines   
        if l1 == -1 and l2 == 1:
            bpoints.append(deque(maxlen=1000))
            bindex += 1
            l2 = -1

        # Append new points in currently deq
        if colorIndex == 0 and l1 == 1:
             bpoints[bindex].appendleft(center)


    # Append the next deque when no contours are detected
    else:
        bpoints.append(deque(maxlen=1000))
        bindex += 1


    # Draw lines of all the colors
    # points = [bpoints]
    points = [bpoints]
    for i in range(len(points)):
        for j in range(len(points[i])):
            for k in range(1, len(points[i][j])):
                if points[i][j][k - 1] is None or points[i][j][k] is None:
                    continue
                cv2.line(frame, points[i][j][k - 1], points[i][j][k], colors[i], 10)
                cv2.line(paintWindow, points[i][j][k - 1], points[i][j][k], colors[i], 10)

    # Show the frame and the paintWindow image
    cv2.imshow("Tracking", frame)
    cv2.imshow("Paint", paintWindow)

	# If the 'q' key is pressed, stop the loop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()