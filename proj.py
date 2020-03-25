import cv2
import numpy as np
import math
from pynput.mouse import Button, Controller
import time

######################## MOUSE CONTROL SECTION ########################
wait_time = 1000

class mouse_control:
    cool_down = int(round(time.time() * 1000))
    mousec = Controller()

    def init(self):
        mousec = Controller()
        cool_down = int(round(time.time() * 1000))
        (cord_x, cord_y) = mousec.position

    def move_mouse(self, x, y):
        self.mousec.move(x, y)

    def gesture(self, kind):

        if kind == "right_click" and (int(round(time.time() * 1000)) - int(self.cool_down)) > wait_time:
            self.mousec.click(Button.right, 1)
            self.cool_down = int(round(time.time() * 1000))
            print("right")
        elif kind == "left_click" and (int(round(time.time() * 1000)) - int(self.cool_down)) > wait_time:
            self.cool_down = int(round(time.time() * 1000))
            self.mousec.click(Button.left, 1)
            print("left")
        else:
            pass
    def control_mouse(self, kind, x, y):
        if kind == 'move':

            self.move_mouse(x, y)
        else:
            self.gesture(kind)

#################### HELPER FUNCTIONS SECTION ####################

def draw_pad(roi, pad_center, pad_radius, neutral_radius, primary_directions_angle):
    color = [255, 102, 51]
    thickness = 3
    cv2.circle(roi, pad_center, pad_radius, color, thickness)
    cv2.circle(roi, pad_center, neutral_radius, color, thickness)

    for i in range(0, 4):
        primary_direction = i * np.pi/2
        angle = np.deg2rad(primary_directions_angle)
        direction = np.array([math.cos(primary_direction + angle / 2), math.sin(primary_direction + angle / 2)])
        center = np.array([pad_center[0], pad_center[1]])
        line_start = center + direction * neutral_radius
        line_end = center + direction * pad_radius
        cv2.line(roi, (int(line_start[0]), int(line_start[1])), (int(line_end[0]), int(line_end[1])), color, thickness)

        direction = np.array([math.cos(primary_direction - angle / 2), math.sin(primary_direction - angle / 2)])
        center = np.array([pad_center[0], pad_center[1]])
        line_start = center + direction * neutral_radius
        line_end = center + direction * pad_radius
        cv2.line(roi, (int(line_start[0]), int(line_start[1])), (int(line_end[0]), int(line_end[1])), color, thickness)


def normalize_and_clamp(magnitude, pad_radius, neutral_radius, min_speed, max_speed):
    normalize_by_radius = (magnitude - neutral_radius)/(pad_radius-neutral_radius)
    # check if center of mass is in the cursor pad
    if normalize_by_radius < 0 or normalize_by_radius > 1:
        return 0

    normalize_by_speed = min_speed + normalize_by_radius * (max_speed - min_speed)
    return normalize_by_speed


# IN DEGREES, NOT RADIANS!!!!!!!
def calc_angle(origin, dest, primary_directions_angle):
    angle = 0
    norm = np.linalg.norm((dest-origin))
    if norm != 0:
        angle = math.acos((dest-origin)[0]/norm)
    if dest[1] > origin[1]:
        angle *= -1

    angle = np.rad2deg(angle)

    # constrain angle to primary directions when in the appropriate area
    if -primary_directions_angle/2 < angle < primary_directions_angle/2:
        angle = 0
    elif 90 - primary_directions_angle/2 < angle < 90 + primary_directions_angle/2:
        angle = 90
    elif 180 - primary_directions_angle/2 < angle < 180 or -180 < angle < -180 + primary_directions_angle/2:
        angle = 180
    elif -90 - primary_directions_angle/2 < angle < -90 + primary_directions_angle/2:
        angle = -90

    return angle;


def calc_cursor_velocity(pad_center, center_of_mass, pad_radius, neutral_radius,
                            primary_directions_angle, min_speed, max_speed):

    xspeed = 0
    yspeed = 0

    origin = np.array([pad_center[0], pad_center[1]])
    dest = np.array([center_of_mass[0], center_of_mass[1]])

    magnitude = np.linalg.norm(dest-origin)
    # normalize the magnitude according to pad and neutral radius and min and max cursor speed
    normalized_magnitude = normalize_and_clamp(magnitude, pad_radius, neutral_radius, min_speed, max_speed)
    if normalized_magnitude == 0:
        return 0, 0

    angle = calc_angle(origin, dest, primary_directions_angle)

    xspeed = normalized_magnitude * math.cos(np.deg2rad(angle))
    yspeed = normalized_magnitude * math.sin(np.deg2rad(angle))

    return int(xspeed), int(yspeed)

mouse = mouse_control()


def get_state_name(num_of_fingers):

    if num_of_fingers >= 3:
        return "move"
    elif num_of_fingers == 1:
        return "left_click"
    elif num_of_fingers == 2:
        return "right_click"

####################    MAIN PROGRAM SECTION ####################

# define region of interest
roi_width = 300
roi_height = 300
roi_origin = (0, 0)


# define cursor pad regions
pad_center = (int(roi_origin[0]+roi_width/2), int(roi_origin[1]+roi_height/2))
pad_radius = 100
neutral_radius = 30
primary_directions_angle = 20
# define cursor attributes
min_speed = 1
max_speed = 20

# define range of skin color in HSV
lower_skin = np.array([2,32,67], dtype=np.uint8)
upper_skin = np.array([12,255,220], dtype=np.uint8)

cap = cv2.VideoCapture(0)
while 1:

    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    kernel = np.ones((3, 3), np.uint8)

    roi_clear = True
    # draw region of interest
    roi = frame[roi_origin[1]:roi_origin[1] + roi_height, roi_origin[0]:roi_origin[0] + roi_width]
    cv2.rectangle(frame, (roi_origin[0], roi_origin[1]), (roi_origin[0] + roi_width, roi_origin[1] + roi_height),
                  (0, 255, 0), 0)
    # draw pad
    draw_pad(roi, pad_center, pad_radius, neutral_radius, primary_directions_angle)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)


    # make binary image according to skin color
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # fill dark spots within the hand region
    mask = cv2.dilate(mask, kernel, iterations=4)

    # blur the image
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    # find contours
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:   # make sure contours were found

        # find contour of the hand (the contour with maximum arc length from contours)
        hand_contour = max(contours, key=lambda x: cv2.contourArea(x))

        # approximate the contour
        epsilon = 0.0005 * cv2.arcLength(hand_contour, True)
        approx = cv2.approxPolyDP(hand_contour, epsilon, True)

        # calc convex hull of the approximated curve of the hand
        hull = cv2.convexHull(hand_contour)

        # find the defects in convex hull with respect to hand
        hull = cv2.convexHull(approx, returnPoints=False)
        defects = cv2.convexityDefects(approx, hull)
        if not defects is None:
            roi_clear = False
            num_of_defects = 0
            center_of_mass = (0, 0)

            # code for finding no. of defects due to fingers
            for i in range(defects.shape[0]):
                s, e, f, distance = defects[i, 0]
                start = tuple(approx[s][0])
                end = tuple(approx[e][0])
                far = tuple(approx[f][0])
                pt = (100, 180)

                # find length of all sides of triangle
                a = math.sqrt((start[0] - far[0]) ** 2 + (start[1] - far[1]) ** 2)
                b = math.sqrt((far[0] - end[0]) ** 2 + (far[1] - end[1]) ** 2)
                c = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

                # apply cosine rule here
                defect_angle = np.rad2deg(math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b)))

                middle = (int((start[0]+end[0])/2), int((start[1]+end[1])/2))

                # ignore angles > 90 and ignore points very close to convex hull(they generally come due to noise)
                # and directions of defects not facing upwards
                if defect_angle <= 90 and distance > 7700 and middle[1] < far[1]:
                    num_of_defects += 1
                    cv2.circle(roi, far, 3, [255, 0, 0], -1)
                    center_of_mass = (center_of_mass[0] + far[0], center_of_mass[1] + far[1])

                # draw lines around hand
                cv2.line(roi, start, end, [0, 255, 0], 2)

            xspeed = 0
            yspeed = 0
            if num_of_defects > 0:
                center_of_mass = (int(center_of_mass[0] / num_of_defects), int(center_of_mass[1] / num_of_defects))
                cv2.circle(roi, center_of_mass, 7, (255, 255, 255), -1)
                xspeed, yspeed = calc_cursor_velocity(pad_center, center_of_mass, pad_radius, neutral_radius,
                                                        primary_directions_angle, min_speed, max_speed)
            # number of fingers
            if not roi_clear:
                num_of_fingers = num_of_defects + 1
                state = get_state_name(num_of_fingers)

                mouse.control_mouse(state, xspeed, -yspeed)

    cv2.imshow('mask', mask)
    cv2.imshow('frame', frame)

    # break at ESC key press
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()
cap.release()