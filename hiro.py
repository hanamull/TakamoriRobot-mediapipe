"""
MediaPipe gesture recognitions -> serial port demo.

Setup:
  pip install mediapipe opencv-python pyserial
  Download the model here and save it next to this script:
  https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
"""

# Imports
import time
import math
import cv2
import serial
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# Below is the serial port associated with this computer, but we aren't using it right now. (Updated)
#PORT = "loop://"  

# We want to send this data somewhere else (to the robot) instead of loop. 
# We need to find out what the PORT should be to do this
# Probably should be something like:
#PORT = "/dev/ttyUSB0"      # Windows: "COM3", macOS: "/dev/cu.usbmodem1101"
PORT = "COM3"

# These values have to do with how fast data is sent through the serial
# port. We probably won't want to mess with these unless something in the
# robot serial port docs/tutorial says otherwise.
BAUD = 115200
SEND_HZ = 30                # cap the serial update rate

MODEL = "gesture_recognizer.task"

def main():
    ser = serial.Serial(PORT, BAUD, timeout=0)
    #ser = serial.serial_for_url(PORT, BAUD, timeout=0)

    # many Arduinos reset when the port opens, so this sleep
    # command (2 seconds) gives them time to boot
    time.sleep(2)  

    # Standard stuff for setting up a vision model:
    options = vision.GestureRecognizerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL), # The model file
        running_mode=vision.RunningMode.VIDEO, # Set video mode
        num_hands=2, # Make it work for 2 hands
        min_hand_detection_confidence=0.5, # Minimum levels of confidence
        min_tracking_confidence=0.5,
    )

    # Set up video capture
    cap = cv2.VideoCapture(0)
    # set up time counters for vid capture 
    # and serial port sending
    last_send, last_ts = 0.0, -1

    # Measuring if hand is at top (Trying to debug the arm being stuck at the top)
    atTop = False

    # This is the video capture loop. Most of this is standard
    # stuff that we will use as is
    with vision.GestureRecognizer.create_from_options(options) as recognizer:
        while cap.isOpened():
            # ok is a boolean saying whether the next video frame was 
            # successfully captured. frame is the frame itself.
            ok, frame = cap.read()
            # Below might be best implemented later, but we want to know the errors we get for now.
            # if not ok:
            #     break
            frame = cv2.flip(frame, 1)  # mirroring the frame view for 'selfie' view

            # Convert cv2 capture frame to mediapipe image format
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # Keep track of the current and previous time stamp
            ts = max(int(time.monotonic() * 1000), last_ts + 1)  # must increase
            last_ts = ts

            # This is the result of the gesture recognizer at each
            # video frame. It takes the image and timestamp (number) as 
            # arguments
            result = recognizer.recognize_for_video(image, ts)

            # Another little bit trying to debug the hand at top issue. Just sets default msg to 0 if it's not 10
            if(not atTop):
                msg = "0\n"

            # This executes if the recognizer has identified hands
            # in the frame
            if result.hand_landmarks:
                #print(result.hand_landmarks)

                # Just some starter to get into mirroring, we will add 2 hands next
                # 1 - the hand_landmarks makes it so as your hand goes up, your percent of coverage on the screen does too
                y_coordinate = 1 - result.hand_landmarks[0][9].y
                #print("y coord ", y_coordinate)

                # Below we don't need right now. We want to use hand landmarker 
                # now that we've got everything set up, not gesture.

                # result.gestures includes all identified gestures
                # gestures:[[Category(index=-1, score=0.5465779900550842, display_name=None, category_name='Thumb_Up')]],  
                # Note this is a list of lists. To get "Thumb_Up" from above, for example, you'd do
                # result.gestures[0][0].category_name

                # result.handedness includs corresponding right or left hand info
                # handedness:[[Category(index=1, score=0.9954624176025391, display_name='Left', category_name='Left')]]
                # This is also a list of lists, and the index should correspond with the gesture. 
                # To grab, "Left", you'd do
                # result.handedness[0][0].category_name

                # In both of the cases above, the outside list has one element if there is one hand and
                # two elements if there are two hands. 

                # This is for gestures, sending messages based on which hand is up
                # gestures = result.gestures
                # handedness = result.handedness
                # #print(len(gestures))
                # if(len(gestures)==1):
                #     if(handedness[0][0].category_name == "Left"):
                #         msg = '01\n'
                #         #print(msg)
                #     else:
                #         msg = '10\n'
                # elif(len(gestures)==2):
                #     msg = '11\n'
                
                # The msg is the main thing we need to modify in this script
                # This message is what will be sent to the robot's serial port
                # Right now 11/21 - message is a whole number between 1 and 10, 180
                # is divided by 10. We want seamless transitions between numbers so we will have to
                # send more decimals to Hiro.
                #msg = f"'gestures':'{gestures}', 'handedness':'{handedness}'\n"
                # The rest of the work is done on the robot side, getting the input
                # from its serial port and making it respond to the message stream
                # For now Hiro is not doing the rounding, but that may change.

                # Sends y_coordinate to serial port 
                height = int(y_coordinate*10) # rounding
                msg = str(height)+'\n' 
                if height == 9 or msg == '10'+'\n':
                    atTop = True # Trying to debug the hand at top thing
                else:
                    atTop = False
            if (atTop and msg == '0'+'\n') or (msg == '10'+'\n'):
                msg = '10'+'\n'
            
            # Grabs current timestamp
            now = time.monotonic()
            # Makes sure time has passed before sending serial port message
            if now - last_send >= 1.0 / SEND_HZ:
                # Sends the msg we defined previously though 
                # the serial port in text form
                print(msg)
                ser.write(msg.encode("ascii"))
                
                # This prints out the serial port data received
                # by our loop PORT. This is what actually prints the data
                # to our command line. When we are sending the data to 
                # the robot, we can comment out this line, since our 
                # computer won't be receiving anything. 
                # print(ser.read(ser.in_waiting or 1).decode(errors="ignore"), end="")

                # Update the last_send timestamp to the current time
                last_send = now

            # Sets up the q to quit display and hotkey
            cv2.imshow("Hand -> Serial (q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                # Breaks out of this loop if user hits q
                break
    
    # This only happens when the user has broken out of the loop
    # stop the capture, close the serial port connection, close the window
    cap.release()
    ser.close()
    cv2.destroyAllWindows()


# Calling the main function
if __name__ == "__main__":
    main()