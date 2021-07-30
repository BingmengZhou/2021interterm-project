import cv2
from datetime import datetime

class shishi(object):
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

    def __del__(self):
        self.cap.release()

    def trace(self):
        #while(1):
        ret, original = self.cap.read()

        # 左上角时间显示
        now = datetime.now()
        month = now.strftime('%b')
        day = now.strftime('%d')
        hour = now.strftime('%H')
        minute = now.strftime('%M')
        time = now.strftime('%b %d %H %M %S %p')
        cv2.putText(original, "now time: {}".format(time),
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if ret == True:

            rett, jpeg = cv2.imencode('.jpg', original)
            return jpeg.tobytes()