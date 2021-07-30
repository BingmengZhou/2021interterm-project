import datetime

import dlib
import numpy as np
import cv2
import os
import shutil
import time
import logging
import csv

class Face_Register:

    def return_128d_features(self,path_img):
        self.img_rd = cv2.imread(path_img)
        self.faces = self.detector(self.img_rd, 1)

        logging.info("%-40s %-20s", "检测到人脸的图像 / Image with faces detected:", path_img)

        # 因为有可能截下来的人脸再去检测，检测不出来人脸了, 所以要确保是 检测到人脸的人脸图像拿去算特征
        # For photos of faces saved, we need to make sure that we can detect faces from the cropped images
        if len(self.faces) != 0:
            self.shape = self.predictor(self.img_rd, self.faces[0])
            self.face_descriptor = self.face_reco_model.compute_face_descriptor(self.img_rd, self.shape)
        else:
            self.face_descriptor = 0
            logging.warning("no face")
        return self.face_descriptor

    # 返回 personX 的 128D 特征均值 / Return the mean value of 128D face descriptor for person X
    # Input:    path_face_personX        <class 'str'>
    # Output:   features_mean_personX    <class 'numpy.ndarray'>
    def return_features_mean_personX(self,path_face_personX):
        self.features_list_personX = []
        self.photos_list = os.listdir(path_face_personX)
        if self.photos_list:
            for i in range(len(self.photos_list)):
                # 调用 return_128d_features() 得到 128D 特征 / Get 128D features for single image of personX
                logging.info("%-40s %-20s", "正在读的人脸图像 / Reading image:", path_face_personX + "/" + self.photos_list[i])
                self.features_128d = self.return_128d_features(path_face_personX + "/" + self.photos_list[i])
                # 遇到没有检测出人脸的图片跳过 / Jump if no face detected from image
                if self.features_128d == 0:
                    i += 1
                else:
                    self.features_list_personX.append(self.features_128d)
        else:
            logging.warning("文件夹内图像文件为空 / Warning: No images in%s/", path_face_personX)

        # 计算 128D 特征的均值 / Compute the mean
        # personX 的 N 张图像 x 128D -> 1 x 128D
        if self.features_list_personX:
            self.features_mean_personX = np.array(self.features_list_personX).mean(axis=0)
        else:
            self.features_mean_personX = np.zeros(128, dtype=int, order='C')
        return self.features_mean_personX

    def csv(self):
        logging.basicConfig(level=logging.INFO)
        # 获取已录入的最后一个人脸序号 / Get the order of latest person
        self.person_list = os.listdir("data/data_faces_from_camera/")
        self.person_num_list = []
        for person in self.person_list:
            self.person_num_list.append(int(person.split('_')[-1]))
        self.person_cnt = max(self.person_num_list)

        with open("data/features_all.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for person in range(self.person_cnt):
                # Get the mean/average features of face/personX, it will be a list with a length of 128D
                logging.info("%sperson_%s", self.path_images_from_camera, str(person + 1))
                features_mean_personX = self.return_features_mean_personX(
                    self.path_images_from_camera + "person_" + str(person + 1))
                writer.writerow(features_mean_personX)
                logging.info('\n')
            logging.info("所有录入人脸数据存入 / Save all the features of faces registered into: data/features_all.csv")

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.detector = dlib.get_frontal_face_detector()
        # 要读取人脸图像文件的路径 / Path of cropped faces
        self.path_images_from_camera = "data/data_faces_from_camera/"

        # Dlib 人脸 landmark 特征点检测器 / Get face landmarks
        self.predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

        # Dlib Resnet 人脸识别模型，提取 128D 的特征矢量 / Use Dlib resnet50 model to get 128D face descriptor
        self.face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

        self.path_photos_from_camera = "data/data_faces_from_camera/"
        self.font = cv2.FONT_ITALIC

        self.existing_faces_cnt = 0         # 已录入的人脸计数器 / cnt for counting saved faces
        self.ss_cnt = 0                     # 录入 personX 人脸时图片计数器 / cnt for screen shots
        self.current_frame_faces_cnt = 0    # 录入人脸计数器 / cnt for counting faces in current frame

        self.save_flag = 1                  # 之后用来控制是否保存图像的 flag / The flag to control if save
        self.press_n_flag = 0               # 之后用来检查是否先按 'n' 再按 's' / The flag to check if press 'n' before 's'
        self.lock_n = False
        self.new_face = False
        self.name = None

        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.start = datetime.datetime.now()

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.csv()

    def pre_work_mkdir(self):
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)

    # 删除之前存的人脸数据文件夹 / Delete the old data of faces
    def pre_work_del_old_face_folders(self):
        # 删除之前存的人脸数据文件夹, 删除 "/data_faces_from_camera/person_x/"...
        folders_rd = os.listdir(self.path_photos_from_camera)
        for i in range(len(folders_rd)):
            shutil.rmtree(self.path_photos_from_camera+folders_rd[i])
        if os.path.isfile("data/features_all.csv"):
            os.remove("data/features_all.csv")

    # 如果有之前录入的人脸, 在之前 person_x 的序号按照 person_x+1 开始录入 / Start from person_x+1
    def check_existing_faces_cnt(self):
        if os.listdir("data/data_faces_from_camera/"):
            # 获取已录入的最后一个人脸序号 / Get the order of latest person
            person_list = os.listdir("data/data_faces_from_camera/")
            person_num_list = []
            for person in person_list:
                person_num_list.append(int(person.split('_')[-1]))
            self.existing_faces_cnt = max(person_num_list)

        # 如果第一次存储或者没有之前录入的人脸, 按照 person_1 开始录入 / Start from person_1
        else:
            self.existing_faces_cnt = 0

    # 获取处理之后 stream 的帧数 / Update FPS of video stream
    def update_fps(self):
        now = time.time()
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

    # 生成的 cv2 window 上面添加说明文字 / PutText on cv2 window
    def draw_note(self, img_rd):
        # 添加说明 / Add some notes
        cv2.putText(img_rd, "Face Register", (20, 40), self.font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img_rd, "N: Create new face", (20, 400), self.font, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img_rd, "Q: Quit", (20, 450), self.font, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

    # 获取人脸 / Main process of face detection and saving
    def processin(self):
        stream = self.cap
        # 1. 新建储存人脸图像文件目录 / Create folders to save photos
        self.pre_work_mkdir()

        # # 2. 删除 "/data/data_faces_from_camera" 中已有人脸图像文件 / Uncomment if want to delete the saved faces and start from person_1
        # if os.path.isdir(self.path_photos_from_camera):
        #     self.pre_work_del_old_face_folders()

        # 3. 检查 "/data/data_faces_from_camera" 中已有人脸文件
        self.check_existing_faces_cnt()

        while stream.isOpened():
            flag, img_rd = stream.read()        # Get camera video stream
            kk = cv2.waitKey(1)
            faces = self.detector(img_rd, 0)         # Use Dlib face detector
            end=datetime.datetime.now()
            if int((end-self.start).seconds)>=10 and not self.lock_n:
            # 4. 按下 'n' 新建存储人脸的文件夹 / Press 'n' to create the folders for saving faces
            # if kk == ord('n') and not self.lock_n:
                self.name = "die"
                self.new_face = True
                self.existing_faces_cnt += 1
                current_face_dir = self.path_photos_from_camera + "person" + "_" + str(self.existing_faces_cnt)
                os.makedirs(current_face_dir)
                print('\n')
                print("新建的人脸文件夹 / Create folders: ", current_face_dir)

                self.ss_cnt = 0                 # 将人脸计数器清零 / Clear the cnt of screen shots
                self.press_n_flag = 1           # 已经按下 'n' / Pressed 'n' already
                self.lock_n = True

            # 5. 检测到人脸 / Face detected
            if len(faces) != 0:
                # 矩形框 / Show the ROI of faces
                for k, d in enumerate(faces):
                    # 计算矩形框大小 / Compute the size of rectangle box
                    height = (d.bottom() - d.top())
                    width = (d.right() - d.left())
                    hh = int(height/2)
                    ww = int(width/2)

                    # 6. 判断人脸矩形框是否超出 480x640 / If the size of ROI > 480x640
                    if (d.right()+ww) > 640 or (d.bottom()+hh > 480) or (d.left()-ww < 0) or (d.top()-hh < 0):
                        cv2.putText(img_rd, "OUT OF RANGE", (20, 300), self.font, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
                        color_rectangle = (0, 0, 255)
                        save_flag = 0
                        if self.press_n_flag:
                            print("请调整位置 / Please adjust your position")
                    else:
                        color_rectangle = (255, 255, 255)
                        save_flag = 1

                    cv2.rectangle(img_rd,
                                  tuple([d.left() - ww, d.top() - hh]),
                                  tuple([d.right() + ww, d.bottom() + hh]),
                                  color_rectangle, 2)

                    # 7. 根据人脸大小生成空的图像 / Create blank image according to the size of face detected
                    img_blank = np.zeros((int(height*2), width*2, 3), np.uint8)

                    if self.press_n_flag:
                        # 8. 按下 's' 保存摄像头中的人脸到本地 / Press 's' to save faces into local images
                        # 检查有没有先按'n'新建文件夹 / Check if you have pressed 'n'
                        if self.save_flag:
                            self.ss_cnt += 1
                            for ii in range(height * 2):
                                for jj in range(width * 2):
                                    img_blank[ii][jj] = img_rd[d.top() - hh + ii][d.left() - ww + jj]  # 截取人脸
                            cv2.imwrite(current_face_dir + "/"+self.name+"_" + str(self.ss_cnt) + ".jpg", img_blank)
                            print("写入本地 / Save into：", str(current_face_dir) + "/"+self.name+"_" + str(self.ss_cnt) + ".jpg")
                        else:
                            print("请先按 'N' 来建文件夹, 按 'S' / Please press 'N' and press 'S'")

            if self.ss_cnt >= 10 and self.new_face:
                self.press_n_flag = 0
                self.new_face = False
                print(self.name + " has saved")
                break

            self.current_frame_faces_cnt = len(faces)

            # 9. 生成的窗口添加说明文字 / Add note on cv2 window
            self.draw_note(img_rd)



            # 11. Update FPS
            self.update_fps()

            # cv2.namedWindow("camera", 1)
            # cv2.imshow("camera", img_rd)


            rett, jpeg = cv2.imencode('.jpg', img_rd)
            return jpeg.tobytes()
