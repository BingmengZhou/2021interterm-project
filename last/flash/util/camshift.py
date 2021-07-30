import cv2
import pymysql
import numpy as np
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header


class camshift(object):
    def __init__(self):
        # 通过opencv获取实时视频流
        # global conn, cur, alarmNum, save_path, choosedArea, faceNum, r, h, c, w, track_window, cap
        # global x, y, isNewTar, ret, frame, roi, hsv_roi, mask, roi_hist, term_crit, fourcc, out
        self.conn = pymysql.connect(host='127.0.0.1', user='root', passwd='010421', db='xhkdb', port=3306,
                               charset='utf8')
        self.cur = self.conn.cursor()
        self.alarmNum = 0
        self.months_s = []
        self.days_s = []
        self.hours_s = []
        self.minutes_s = []
        self.alarmtimes = []
        self.filenames = []
        # 入侵截图保存路径
        self.save_path = 'img/'
        self.choosedArea = None
        self.faceNum = 0

        # 设置初始化的窗口位置
        self.r, self.h, self.c, self.w = 200, 100, 200, 100  # 设置初试窗口位置和大小
        self.track_window = (self.c, self.r, self.w, self.h)
        self.x = self.c
        self.y = self.r
        self.isNewTar = True
        self.cap = cv2.VideoCapture(0)
        self.ret, self.frame = self.cap.read()

        # 设置追踪的区域
        self.roi = self.frame[self.r:self.r + self.h, self.c:self.c + self.w]
        # roi区域的hsv图像
        self.hsv_roi = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        # 取值hsv值在(0,60,32)到(180,255,255)之间的部分
        self.mask = cv2.inRange(self.hsv_roi, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
        # 计算直方图,参数为 图片(可多)，通道数，蒙板区域，直方图长度，范围
        self.roi_hist = cv2.calcHist([self.hsv_roi], [0], self.mask, [180], [0, 180])
        # 归一化
        cv2.normalize(self.roi_hist, self.roi_hist, 0, 255, cv2.NORM_MINMAX)
        # 设置终止条件，迭代10次或者至少移动1次
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        # 存储视频
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('output.avi', self.fourcc, 30.0, (640, 480))

        # 警戒区域点坐标
        self.point1 = None
        self.point2 = None
        self.isNew = False

    def __del__(self):
        self.saveInSql(self.alarmNum, self.conn, self.cur)
        self.cap.release()
        cv2.destroyAllWindows()

    # 发送邮件
    def mail(self,filename):
        self.ret = True
        try:
            # 发送方接收方邮件设置
            self.mail_host = "smtp.qq.com"  # 设置主机
            self.mail_user = "1972611792@qq.com"  # 发送方账号名
            self.mail_pass = "dpzzaecxtolnedef"  # 授权码，而非我们设置的登录密码
            self.sender = "1972611792@qq.com"  # 发送方
            self.receivers = ["19301148@bjtu.edu.cn"]  # 接收方成员列表

            # 发件人昵称
            self.sendername = "入侵检测系统"
            # 收件人昵称
            self.receiversname = 'manager'
            # 设置信息头
            self.message = MIMEMultipart()
            self.message["From"] = Header(self.sendername, "utf-8")
            self.message["To"] = Header(self.receiversname, "utf-8")

            # 信件主题
            self.subject = "入侵检测系统"
            self.message["Subject"] = Header(self.subject, "utf-8")

            # 信件内容
            self.mail_message = """
            <p>当前出现目标，请求核实</p >
            """
            self.message.attach(MIMEText(self.mail_message, "html", "utf-8"))

            # 发送入侵截图附件
            self.att = MIMEText(open(self.filename, 'rb').read(), 'base64', 'utf-8')
            self.att["Content-Type"] = 'application/octet-stream'
            self.att["Content-Disposition"] = 'attachment; filename="screenshot.jpg"'
            self.message.attach(self.att)

            # 发送邮件
            self.smtpObj = self.smtplib.SMTP()
            self.smtpObj.connect(self.mail_host, 25)
            self.smtpObj.login(self.mail_user, self.mail_pass)
            self.smtpObj.sendmail(self.sender, self.receivers, self.message.as_string())
            self.smtpObj.quit()
        except Exception:
            self.ret = False
        return self.ret

    # 入侵记录存储到数据库
    def saveInSql(self,alarmNum, conn, cur):
        for i in range(0, alarmNum - 1):
            self.newmonth = self.months_s[i]
            self.newday = self.days_s[i]
            self.newhours = self.hours_s[i]
            self.newmin = self.minutes_s[i]
            self.newTime = self.alarmtimes[i]
            self.newFileName = self.filenames[i]
                # 添加数据
            sql = """
                            insert into stranger(month,day,hour,minute,time,screenshot) value(%s,%s,%s,%s,%s,%s)
                            """
            try:
                # 执行sql语句
                cur.execute(sql, (self.newmonth, self.newday,self.newhours, self.newmin, self.newTime, self.newFileName))
                # #提交到数据库执行
                self.conn.commit()
                print("数据库保存成功")
            except:
                # 发生错误时回滚
                self.conn.rollback()
                print("数据库保存失败")

    def trace(self):
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
                point2 = (x, y)
                cv2.rectangle(original, self.point1, point2, (0, 0, 255), 2)

        #while(1):
        ret, original = self.cap.read()

        # 有选中区域
        if self.point1 != None and self.point2 != None:
            cv2.rectangle(original, (self.point1[0], self.point1[1]), (self.point2[0], self.point2[1]), (0, 0, 255), 2)
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

        if ret == True:
            # 计算每一帧的hsv图像
            self.hsv = cv2.cvtColor(choosedArea, cv2.COLOR_BGR2HSV)
            # 计算反向投影
            self.dst = cv2.calcBackProject([self.hsv],[0],self.roi_hist,[0,180],1)
            # 调用meanShift算法在dst中寻找目标窗口，找到后返回目标窗口
            ret, self.track_window = cv2.CamShift(self.dst, self.track_window, self.term_crit)

            tmp_x = int(self.track_window[0])
            tmp_y = int(self.track_window[1])

            if abs(tmp_x - self.x)<20 and abs(tmp_y - self.y)<20:
                self.isNewTar = True
            # --------发送警报----------
            if self.isNewTar and abs(tmp_x - self.x)>20 and abs(tmp_y - self.y)>20:
                self.alarmNum += 1
                print(1111)
                # 保存图片
                filename = self.save_path + str(time) + '.jpg'
                cv2.imwrite(filename, original)
                # 发送邮件
                ret1 = self.mail(filename)
                if ret1:
                    print("邮件发送成功")
                else:
                    print("邮件发送失败")
                self.isNewTar = False
                self.months_s.append(str(month))
                self.days_s.append(str(day))
                self.hours_s.append(str(hour))
                self.minutes_s.append(str(minute))
                self.alarmtimes.append(str(time))
                self.filenames.append(filename)

            x = tmp_x
            y = tmp_y
            # Draw it on image
            pts = cv2.boxPoints(ret)
            pts = np.int0(pts)
            self.img2 = cv2.polylines(choosedArea,[pts],True, 255,2)


            # cv2.imshow('contours',original)
            # cv2.setMouseCallback('contours', on_mouse)

        self.out.write(original)
        rett, jpeg = cv2.imencode('.jpg', original)
        return jpeg.tobytes()

        # 后面都不要
        #k = cv2.waitKey(5) & 0xFF
        #if k == 27:
            #break


