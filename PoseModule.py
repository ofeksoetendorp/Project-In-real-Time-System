import cv2
import mediapipe as mp
import numpy as np


class PoseDetector:
    #MODEL_COMPLEXITY = 0

    # these are the id's of the relevant points
    LANDMARKS = [0, 11, 12, 13, 14, 15, 16, 23, 24]
    # 0:nose, 11:left_shoulder, 12:right_shoulder, 13:left_elbow, 14:right_elbow, 15:left_wrist, 16:right_wrist, 23:left_hip, 24:right_hip

    def __init__(self, mode=False, model_complexity=0):
        self.MODEL_COMPLEXITY = model_complexity
        self.mode = mode
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.mode, model_complexity=self.MODEL_COMPLEXITY)

    def calculate_neck(self, nose, left_shoulder, right_shoulder):
        return (nose + left_shoulder + right_shoulder) / 3

    def center(self, points, neck):
        centered_points = points
        for point in centered_points:
            point[0] = point[0] - neck[0]
            point[1] = point[1] - neck[1]
            #point[2] = point[2] - neck[2]
        return centered_points

    def calculate_furthest_shoulder(self, neck, left_shoulder, right_shoulder):
        dist_to_left_shoulder = np.linalg.norm(neck - left_shoulder)
        dist_to_right_shoulder = np.linalg.norm(neck - right_shoulder)
        furthest_shoulder = 0
        if (dist_to_left_shoulder > dist_to_right_shoulder):
            furthest_shoulder = left_shoulder
        else:
            furthest_shoulder = right_shoulder
        return furthest_shoulder

    def calculate_angle(self, neck, furthest_shoulder):
        temp = (furthest_shoulder[1] - neck[1]) / (furthest_shoulder[0] - neck[0])
        alpha = np.arctan([temp])
        alpha = alpha[0]
        return alpha

    def rotate(self, points, alpha):
        rotated_points = points
        # we want only to rotate around the z axis and we do not want the "depth" of the point to change
        for point in rotated_points:
            x = point[0]
            y = point[1]
            point[0] = x * np.cos(alpha) - y * np.sin(alpha)
            point[1] = x * np.sin(alpha) + y * np.cos(alpha)
        return rotated_points

    def normalize(self, points, neck, furthest_shoulder):
        normalized_points = points
        for point in normalized_points:
            point[0] = point[0] / np.linalg.norm(neck - furthest_shoulder)
            point[1] = point[1] / np.linalg.norm(neck - furthest_shoulder)
            #point[2] = point[2] / np.linalg.norm(neck - furthest_shoulder)
        return normalized_points

    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)
        return img

    def getPosition(self, img, draw=True):

        #lmList = np.empty((0, 3))
        lmList = np.empty((0, 2))
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                if id in self.LANDMARKS:
                    h, w, c = img.shape

                    """cx, cy, cz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                    lmList = np.append(lmList, [[cx, cy, cz]], axis=0)"""

                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList = np.append(lmList, [[cx, cy]], axis=0)

                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)

            nose = lmList[0]
            left_shoulder = lmList[1]
            right_shoulder = lmList[2]
            neck = self.calculate_neck(nose, left_shoulder, right_shoulder)
            lmList = self.center(lmList, neck)
            furthest_shoulder = self.calculate_furthest_shoulder(neck, left_shoulder, right_shoulder)
            alpha = self.calculate_angle(neck, furthest_shoulder)
            lmList = self.rotate(lmList, alpha)
            lmList = self.normalize(lmList, neck, furthest_shoulder)

            # THE Y AXIS GOES DOONWARDS, SO THE Y OF THE NOSE IS ACTUALLY < THE Y OF THE SHOULDERS, FOR EXAMPLE.

        return lmList
