# import the necessary packages
from __future__ import print_function  # 确保代码同时在Python2.7和Python3上兼容

import pymysql
from imutils.object_detection import non_max_suppression
import numpy as np
import argparse
import imutils  # 安装库pip install imutils ；pip install --upgrade imutils更新版本大于v0.3.1
import cv2
from openpyxl import load_workbook
from datetime import datetime


class peopledetection:

    def __init__(self):

        self.point1 = None
        self.point2 = None
        self.isNew = False

        self.months_s = []
        self.days_s = []
        self.hours_s = []
        self.minutes_s = []
        self.alarmtimes = []
        self.filenames = []

        self.work = load_workbook(filename="data_people_detection.xlsx")
        self.sheet = self.work.active  # 默认为第一张表格
        if self.sheet['A1'].value != 'time':
            self.sheet['A1'].value = 'time'
            self.sheet['B1'].value = 'facenum_cur'
            print('已添加')

        self.conn = pymysql.connect(host='127.0.0.1', user='root', passwd='010421', db='xhkdb', port=3306,
                               charset='utf8')
        self.cur = self.conn.cursor()
        self.alarmNum = 0
        # construct the argument parse and parse the arguments
        self.ap = argparse.ArgumentParser()
        self.ap.add_argument("-i", "--images", required=True, help="path to images directory")
        # args = vars(ap.parse_args())

        # 初始化我们的行人检测器
        self.hog = cv2.HOGDescriptor()  # 初始化方向梯度直方图描述子
        self.hog.setSVMDetector(
            cv2.HOGDescriptor_getDefaultPeopleDetector())  # 设置支持向量机(Support Vector Machine)使得它成为一个预先训练好了的行人检测器
        # hog.load('myHogDector3.bin')
        # 到这里，我们的OpenCV行人检测器已经完全载入了，我们只需要把它应用到一些图像上
        # ---------------------------------------------------------------------------------------------------------
        self.srcTest = 'D:/pycharm/07221407/test1.wmv'
        self.cap = cv2.VideoCapture(0)  # Open video file
        self.savepath = 'D:/pycharm/07221407/img/'
        self.peoplenum = 0
        # 背景移除
        self.fgbg = cv2.createBackgroundSubtractorMOG2()

    def __del__(self):
        self.work.save("data_people_detection.xlsx")
        self.cap.release()
        cv2.destroyAllWindows()

    def peopledetection(self):
        # 警戒区域点坐标

        # 画警戒区域
        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
                self.isNew = True
                if self.point1 != None:
                    self.point1 = None
                    self.point2 = None
                self.point1 = (x, y)
                cv2.circle(original, self.point1, 10, (0, 255, 0), 2)
                cv2.imshow("contours", original)
            elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):  # 按住左键拖曳
                cv2.rectangle(original, self.point1, (x, y), (255, 0, 0), 2)
                cv2.imshow("contours", original)
            elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
                self.point2 = (x, y)
                cv2.rectangle(original, self.point1, self.point2, (0, 0, 255), 2)
                cv2.imshow("contours", original)

        # loop over the image paths
        #while (self.cap.isOpened()):  # args["images"]
        # load the image and resize it to (1) reduce detection time
        # and (2) improve detection accuracy
        ret, original = self.cap.read()
        fgmask = self.fgbg.apply(original)
        original = imutils.resize(original, width=min(800, original.shape[1]))
        self.frameForView = original.copy()
        # 有选中区域
        if self.point1 != None and self.point2 != None:
            cv2.rectangle(original, (self.point1[0], self.point1[1]), (self.point2[0],self. point2[1]), (0, 0, 255), 2)
            choosedArea = original[self.point1[1]:self.point2[1], self.point1[0]:self.point2[0]]
            if self.isNew:
                self.isNew = False
        else:
            choosedArea = original
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
        # detect people in the image：
        (rects, weights) = self.hog.detectMultiScale(choosedArea, winStride=(4, 4), padding=(8, 8), scale=1.05)
        # 应用非极大抑制方法，通过设置一个阈值来抑制那些重叠的边框
        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)
        if ret:
            # draw the final bounding boxes
            for (xA, yA, xB, yB) in pick:
                cv2.rectangle(choosedArea, (xA, yA), (xB, yB), (0, 255, 0), 2)
            num = len(pick)
            if (num == 0):
                self.peoplenum = 0
            if num != self.peoplenum and num != 0:
                self.alarmNum += 1
                self.pnum = num
                # 保存图片
                filename = self.savepath + str(time) + '.jpg'
                cv2.imwrite(filename, original)
                # 保存到excel
                don = [[time, num]]
                for x in don:
                    self.sheet.append(x)
                self.months_s.append(str(month))
                self.days_s.append(str(day))
                self.hours_s.append(str(hour))
                self.minutes_s.append(str(minute))
                self.alarmtimes.append(str(time))
                self.filenames.append(filename)

        rett, jpeg = cv2.imencode('.jpg', original)
        return jpeg.tobytes()
            # try:
            #     # cv2.imshow('contours', original)
            #     # cv2.setMouseCallback('contours', on_mouse)
            #
            #     # cv2.imshow("seg", fgmask)
            #     # cv2.imshow('Frame', frame)
            #
            # except Exception as e:
            #     print(e)
            #     break

            # Abort and exit with 'Q' or ESC
            # k = cv2.waitKey(5) & 0xff
            # if k == 27:
            #     break
