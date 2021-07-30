

# 利用 OT 人脸追踪, 实时人脸识别 / Real-time face detection and recognition via OT for single face
import pymysql
from openpyxl import load_workbook
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

import dlib
import numpy as np
import os
import pandas as pd
import time
import logging
import cv2

class Face_Recognizer:

    def saveInSql(self):
        for i in range(0, self.alarm_str - 1):
            newTime = self.alarmtimes_s[i]
            newFileName = self.filenames_s[i]
            # 添加数据
            sql = """
                            insert into stranger(time,screenshot) value(%s,%s)
                            """
            try:
                # 执行sql语句
                self.cur.execute(sql, (newTime, newFileName))
                # #提交到数据库执行
                self.conn.commit()
                print("数据库保存成功")
            except:
                # 发生错误时回滚
                self.conn.rollback()
                print("数据库保存失败")
        for i in range(0, self.alarmNum_a - 1):
            newTime = self.alarmtimes_a[i]
            newFileName = self.filenames_a[i]
            # 添加数据
            sql = """
                            insert into acquaintance(time,screenshot) value(%s,%s)
                            """
            try:
                # 执行sql语句
                self.cur.execute(sql, (newTime, newFileName))
                # #提交到数据库执行
                self.conn.commit()
                print("数据库保存成功")
            except:
                # 发生错误时回滚
                self.conn.rollback()
                print("数据库保存失败")

    # 发送邮件
    def mail(self,peoplenum, filename):
        ret = True
        try:
            # 发送方接收方邮件设置
            mail_host = "smtp.qq.com"  # 设置主机
            mail_user = "1972611792@qq.com"  # 发送方账号名
            mail_pass = "dpzzaecxtolnedef"  # 授权码，而非我们设置的登录密码
            sender = "1972611792@qq.com"  # 发送方
            receivers = ["19301148@bjtu.edu.cn"]  # 接收方成员列表

            # 发件人昵称
            sendername = "入侵检测系统"
            # 收件人昵称
            receiversname = 'manager'
            # 设置信息头
            message = MIMEMultipart()
            message["From"] = Header(sendername, "utf-8")
            message["To"] = Header(receiversname, "utf-8")

            # 信件主题
            subject = "入侵检测系统"
            message["Subject"] = Header(subject, "utf-8")

            # 信件内容
            mail_message = """
            <p>当前出现目标，请求核实</p >
            """
            message.attach(MIMEText(mail_message, "html", "utf-8"))

            # 发送入侵截图附件
            att = MIMEText(open(filename, 'rb').read(), 'base64', 'utf-8')
            att["Content-Type"] = 'application/octet-stream'
            att["Content-Disposition"] = 'attachment; filename="screenshot.jpg"'
            message.attach(att)

            # 发送邮件
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, 25)
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
        except Exception:
            ret = False
        return ret

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        # Dlib 正向人脸检测器 / Use frontal face detector of Dlib
        self.detector = dlib.get_frontal_face_detector()

        # Dlib 人脸 landmark 特征点检测器 / Get face landmarks
        self.predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

        # Dlib Resnet 人脸识别模型，提取 128D 的特征矢量 / Use Dlib resnet50 model to get 128D face descriptor
        self.face_reco_model = dlib.face_recognition_model_v1(
            "data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

        self.work = load_workbook(filename="data_face_recognition.xlsx")
        self.sheet = self.work.active  # 默认为第一张表格
        if self.sheet['A1'].value != 'time':
            self.sheet['A1'].value = 'time'
            self.sheet['B1'].value = 'facenum_cur'

        self.conn = pymysql.connect(host='127.0.0.1', user='root', passwd='010421', db='xhkdb', port=3306,
                               charset='utf8')
        self.cur = self.conn.cursor()

        self.point1 = None
        self.point2 = None

        # 陌生人
        self.alarm_str = 0
        self.alarmtimes_s = []
        self.filenames_s = []
        # 熟人
        self.alarmNum_a = 0
        self.alarmtimes_a = []
        self.filenames_a = []

        self.original = None
        self.choosedArea = None

        self.font = cv2.FONT_ITALIC

        self.time = None
        self.name = None
        # For FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.frame_start_time = 0

        # cnt for frame
        self.frame_cnt = 0

        # 用来存放所有录入人脸特征的数组 / Save the features of faces in the database
        self.face_features_known_list = []
        # 存储录入人脸名字 / Save the name of faces in the database
        self.face_name_known_list = []

        # 用来存储上一帧和当前帧 ROI 的质心坐标 / List to save centroid positions of ROI in frame N-1 and N
        self.last_frame_face_centroid_list = []
        self.current_frame_face_centroid_list = []

        # 用来存储上一帧和当前帧检测出目标的名字 / List to save names of objects in frame N-1 and N
        self.last_frame_face_name_list = []
        self.current_frame_face_name_list = []

        # 上一帧和当前帧中人脸数的计数器 / cnt for faces in frame N-1 and N
        self.last_frame_face_cnt = 0
        self.current_frame_face_cnt = 0

        # 用来存放进行识别时候对比的欧氏距离 / Save the e-distance for faceX when recognizing
        self.current_frame_face_X_e_distance_list = []

        # 存储当前摄像头中捕获到的所有人脸的坐标名字 / Save the positions and names of current faces captured
        self.current_frame_face_position_list = []
        # 存储当前摄像头中捕获到的人脸特征 / Save the features of people in current frame
        self.current_frame_face_feature_list = []

        # e distance between centroid of ROI in last and current frame
        self.last_current_frame_centroid_e_distance = 0

        # 控制再识别的后续帧数 / Reclassify after 'reclassify_interval' frames
        # 如果识别出 "unknown" 的脸, 将在 reclassify_interval_cnt 计数到 reclassify_interval 后, 对于人脸进行重新识别
        self.reclassify_interval_cnt = 0
        self.reclassify_interval = 10

    def __del__(self):
        self.saveInSql()
        self.work.save(filename="data_face_recognition.xlsx")
        self.cap.release()
        cv2.destroyAllWindows()

    # 从 "features_all.csv" 读取录入人脸特征 / Get known faces from "features_all.csv"
    def get_face_database(self):
        if os.path.exists("data/features_all.csv"):
            path_features_known_csv = "data/features_all.csv"
            csv_rd = pd.read_csv(path_features_known_csv, header=None)
            for i in range(csv_rd.shape[0]):
                features_someone_arr = []
                for j in range(0, 128):
                    if csv_rd.iloc[i][j] == '':
                        features_someone_arr.append('0')
                    else:
                        features_someone_arr.append(csv_rd.iloc[i][j])
                self.face_features_known_list.append(features_someone_arr)
                photo_list = os.listdir("data/data_faces_from_camera/" + "person_" + str(i+1))
                tmp_list = photo_list[0].split('.')
                self.name = tmp_list[0].split('_')[0]
                self.face_name_known_list.append(self.name)
            logging.info("Faces in Database： %d", len(self.face_features_known_list))
            return 1
        else:
            logging.warning("'features_all.csv' not found!")
            logging.warning("Please run 'get_faces_from_camera.py' "
                            "and 'features_extraction_to_csv.py' before 'face_reco_from_camera.py'")
            return 0

    # 获取处理之后 stream 的帧数 / Get the fps of video stream
    def update_fps(self):
        now = time.time()
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

    @staticmethod
    # 计算两个128D向量间的欧式距离 / Compute the e-distance between two 128D features
    def return_euclidean_distance(feature_1, feature_2):
        feature_1 = np.array(feature_1)
        feature_2 = np.array(feature_2)
        dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
        return dist

    # Use centroid tracker to link face_x in current frame with person_x in last frame
    def centroid_tracker(self):
        for i in range(len(self.current_frame_face_centroid_list)):
            e_distance_current_frame_person_x_list = []
            # For object 1 in current_frame, compute e-distance with object 1/2/3/4/... in last frame
            for j in range(len(self.last_frame_face_centroid_list)):
                self.last_current_frame_centroid_e_distance = self.return_euclidean_distance(
                    self.current_frame_face_centroid_list[i], self.last_frame_face_centroid_list[j])

                e_distance_current_frame_person_x_list.append(
                    self.last_current_frame_centroid_e_distance)

            last_frame_num = e_distance_current_frame_person_x_list.index(
                min(e_distance_current_frame_person_x_list))
            self.current_frame_face_name_list[i] = self.last_frame_face_name_list[last_frame_num]

    # 处理获取的视频流，进行人脸识别 / Face detection and recognition wit OT from input video stream
    def process(self):
        stream = self.cap
        # 画警戒区域
        def on_mouse(event, x, y, flags, para):
            if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
                if self.point1 != None:
                    self.point1 = None
                    self.point2 = None
                self.point1 = (x, y)
            elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
                self.point2 = (x, y)
                # cv2.rectangle(img_rd, point1, point2, (0, 0, 255), 2)
                # cv2.imshow("camera", img_rd)
        # 1. 读取存放所有人脸特征的 csv / Get faces known from "features.all.csv"
        if self.get_face_database():
            #while stream.isOpened():
            self.frame_cnt += 1
            logging.debug("Frame " + str(self.frame_cnt) + " starts")
            flag, original = stream.read()
            kk = cv2.waitKey(1)

            # 时间显示
            now = datetime.now()
            self.time = now.strftime('%b %d %H %M %S %p')
            cv2.putText(original, "now time: {}".format(self.time),
                        (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


            # 已设置警戒区域
            if self.point1 != None and self.point2 != None:
                original = cv2.rectangle(original, (self.point1[0], self.point1[1]), (self.point2[0], self.point2[1]), (0, 0, 255), 2)
                choosedArea = original[self.point1[1]:self.point2[1], self.point1[0]:self.point2[0]]
            else:
                choosedArea = original

            # 2. 检测人脸 / Detect faces for frame X
            faces = self.detector(choosedArea, 0)

            # Update cnt for faces in frames
            self.last_frame_face_cnt = self.current_frame_face_cnt
            self.current_frame_face_cnt = len(faces)

            # Update the face name list in last frame
            self.last_frame_face_name_list = self.current_frame_face_name_list[:]

            # update frame centroid list
            self.last_frame_face_centroid_list = self.current_frame_face_centroid_list
            self.current_frame_face_centroid_list = []

            # 2.1. if cnt not changes
            if (self.current_frame_face_cnt == self.last_frame_face_cnt) and (
                    self.reclassify_interval_cnt != self.reclassify_interval):
                logging.debug("scene 1: 当前帧和上一帧相比没有发生人脸数变化 / No face cnt changes in this frame!!!")

                self.current_frame_face_position_list = []

                if "unknown" in self.current_frame_face_name_list:
                    logging.debug("  有未知人脸, 开始进行 reclassify_interval_cnt 计数")
                    self.reclassify_interval_cnt += 1

                if self.current_frame_face_cnt != 0:
                    # 2.1.1 Get ROI positions
                    for k, d in enumerate(faces):
                        if self.point1 is None:
                            self.current_frame_face_position_list.append(tuple(
                                [faces[k].left(), int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4)]))
                        else:
                            self.current_frame_face_position_list.append(tuple(
                                [faces[k].left()+self.point1[0],
                                 int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4+self.point1[1])]))
                        self.current_frame_face_centroid_list.append(
                            [int(faces[k].left() + faces[k].right()) / 2,
                             int(faces[k].top() + faces[k].bottom()) / 2])

                        # 计算矩形框大小 / Compute the size of rectangle box
                        height = (d.bottom() - d.top())
                        width = (d.right() - d.left())
                        hh = int(height / 2)
                        ww = int(width / 2)
                        if self.point1 is not None:
                            original = cv2.rectangle(original,
                                               tuple([d.left() - ww+self.point1[0], d.top() - hh+self.point1[1]]),
                                               tuple([d.right() + ww+self.point1[0], d.bottom() + hh+self.point1[1]]),
                                               (255, 255, 255), 2)
                        else:
                            original = cv2.rectangle(original,
                                                     tuple([d.left() - ww , d.top() - hh]),
                                                     tuple(
                                                         [d.right() + ww , d.bottom() + hh]),
                                                     (255, 255, 255), 2)

                # Multi-faces in current frame, use centroid-tracker to track
                if self.current_frame_face_cnt != 1:
                    self.centroid_tracker()

                for i in range(self.current_frame_face_cnt):
                    if self.current_frame_face_name_list[i]== "unknown":
                        original = cv2.putText(original, self.current_frame_face_name_list[i],
                                         self.current_frame_face_position_list[i], self.font, 1.5, (0, 0, 255), 3,
                                         cv2.LINE_AA)
                    else:
                        original = cv2.putText(original, self.current_frame_face_name_list[i],
                                               self.current_frame_face_position_list[i], self.font, 1.5,
                                               (0,255, 0), 3,
                                               cv2.LINE_AA)

            # 2.2 If cnt of faces changes, 0->1 or 1->0 or ...
            else:
                logging.debug("scene 2: 当前帧和上一帧相比人脸数发生变化 / Faces cnt changes in this frame")
                self.current_frame_face_position_list = []
                self.current_frame_face_X_e_distance_list = []
                self.current_frame_face_feature_list = []
                self.reclassify_interval_cnt = 0

                # 2.2.1 Face cnt decreases: 1->0, 2->1, ...
                if self.current_frame_face_cnt == 0:
                    logging.debug("  scene 2.1 人脸消失, 当前帧中没有人脸 / No faces in this frame!!!")
                    # clear list of names and features
                    self.current_frame_face_name_list = []
                # 2.2.2 Face cnt increase: 0->1, 0->2, ..., 1->2, ...
                else:
                    logging.debug("  scene 2.2 出现人脸，进行人脸识别 / Get faces in this frame and do face recognition")

                    #---------发送警报---------
                    # 保存入侵截图
                    filename = "C:/python/face_dlib/pics/" + str(self.time) + '.jpg'
                    cv2.imwrite(filename, original)


                    self.current_frame_face_name_list = []
                    for i in range(len(faces)):
                        shape = self.predictor(choosedArea, faces[i])
                        self.current_frame_face_feature_list.append(
                            self.face_reco_model.compute_face_descriptor(choosedArea, shape))
                        self.current_frame_face_name_list.append("unknown")

                    # 2.2.2.1 遍历捕获到的图像中所有的人脸 / Traversal all the faces in the database
                    for k in range(len(faces)):
                        logging.debug("  For face %d in current frame:", k + 1)
                        self.current_frame_face_centroid_list.append(
                            [int(faces[k].left() + faces[k].right()) / 2,
                             int(faces[k].top() + faces[k].bottom()) / 2])

                        self.current_frame_face_X_e_distance_list = []

                        # 2.2.2.2 每个捕获人脸的名字坐标 / Positions of faces captured
                        if self.point1 is not None:
                            tmp_x = faces[k].left()+self.point1[0]
                            tmp_y = int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4 + self.point1[1])
                            self.current_frame_face_position_list.append(tuple([tmp_x,tmp_y]))
                        else:
                            self.current_frame_face_position_list.append(tuple(
                                [faces[k].left() , int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4 )]))
                        # 2.2.2.3 对于某张人脸，遍历所有存储的人脸特征
                        # For every faces detected, compare the faces in the database
                        for i in range(len(self.face_features_known_list)):
                            # 如果 q 数据不为空
                            if str(self.face_features_known_list[i][0]) != '0.0':
                                e_distance_tmp = self.return_euclidean_distance(
                                    self.current_frame_face_feature_list[k],
                                    self.face_features_known_list[i])
                                logging.debug("      with person %d, the e-distance: %f", i + 1, e_distance_tmp)
                                self.current_frame_face_X_e_distance_list.append(e_distance_tmp)
                            else:
                                # 空数据 person_X
                                self.current_frame_face_X_e_distance_list.append(999999999)

                        # 2.2.2.4 寻找出最小的欧式距离匹配 / Find the one with minimum e distance
                        similar_person_num = self.current_frame_face_X_e_distance_list.index(
                            min(self.current_frame_face_X_e_distance_list))

                        if min(self.current_frame_face_X_e_distance_list) < 0.4:
                            self.current_frame_face_name_list[k] = self.face_name_known_list[similar_person_num]
                            logging.debug("  Face recognition result: %s",
                                          self.face_name_known_list[similar_person_num])
                            self.alarmNum_a += 1
                            self.alarmtimes_a.append(str(self.time))
                            self.filenames_a.append(filename)

                        else:
                            logging.debug("  Face recognition result: Unknown person")
                            self.alarm_str += 1
                            self.alarmtimes_s.append(str(self.time))
                            self.filenames_s.append(filename)

                            # 保存到excel
                            don = [[self.time, self.current_frame_face_cnt]]
                            for x in don:
                                self.sheet.append(x)
                            # 发送邮件
                            ret1 = self.mail(self.current_frame_face_cnt, filename)
                            if ret1:
                                print("邮件发送成功")
                            else:
                                print("邮件发送失败")



            self.update_fps()
            cv2.namedWindow("camera", 1)
            # cv2.imshow("camera", original)
            # cv2.setMouseCallback('camera', on_mouse)
            logging.debug("Frame ends\n\n")
            rett, jpeg = cv2.imencode('.jpg', original)
            return jpeg.tobytes()



