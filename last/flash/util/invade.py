# 基本的运动物体检测
# 计算帧之间的差异，或考虑“背景”帧与其他帧之间的差异
import cv2
import pymysql
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from openpyxl import load_workbook

class face_detection:

    def __init__(self):
        self.months_s = []
        self.days_s = []
        self.hours_s = []
        self.minutes_s = []
        self.alarmtimes = []
        self.filenames = []

        self.alarmNum = 0
        self.work = load_workbook(filename="data_face_detection.xlsx")
        self.sheet = self.work.active  # 默认为第一张表格
        if self.sheet['A1'].value != 'time':
            self.sheet['A1'].value = 'time'
            self.sheet['B1'].value = 'facenum_cur'
            print('已添加')

        self.conn = pymysql.connect(host='127.0.0.1', user='root', passwd='010421', db='xhkdb', port=3306,
                               charset='utf8')
        self.cur = self.conn.cursor()

        # 入侵截图保存路径
        self.save_path = 'img/'
        self.choosedArea = None
        self.faceNum = 0

        self.path = 'venv/Lib/site-packages/cv2/data/'
        self.face_cascade = cv2.CascadeClassifier(self.path + 'haarcascade_frontalface_default.xml')

        # 设置为默认摄像头
        self.camera = cv2.VideoCapture(0)

        # 背景移除
        self.fgbg = cv2.createBackgroundSubtractorMOG2()

        # 存储视频
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('output.avi',self.fourcc, 30.0, (640, 480))

        self.point1 = None
        self.point2 = None
        self.isNew = False
    # 发送邮件

    def __del__(self):
        self.saveInSql(self.alarmNum, self.conn, self.cur)
        self.work.save("data_face_detection.xlsx")
        cv2.destroyAllWindows()
        self.camera.release()

    def mail(self,peoplenum,filename):
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
            <p>出现目标，请求核实</p >
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

    def saveInSql(self,alarmNum, conn, cur):
        for i in range(0,alarmNum-1):
            newmonth = self.months_s[i]
            newday = self.days_s[i]
            newhours = self.hours_s[i]
            newmin = self.minutes_s[i]
            newTime = self.alarmtimes[i]
            newFileName = self.filenames[i]
            # 添加数据
            sql = """
                            insert into stranger(month,day,hour,minute,time,screenshot) value(%s,%s,%s,%s,%s,%s)
                            """
            try:
                # 执行sql语句
                self.cur.execute(sql, (newmonth,newday,newhours,newmin,newTime, newFileName))
                # #提交到数据库执行
                self.conn.commit()
                print("数据库保存成功")
            except:
                # 发生错误时回滚
                self.conn.rollback()
                print("数据库保存失败")


    def detection(self):
        ret, original = self.camera.read()
        self.fgmask = self.fgbg.apply(original)
        # 警戒区域点坐标
        conn = pymysql.connect(host='127.0.0.1', user='root', passwd='yourpassword', db='mydata', port=3306,
                                    charset='utf8')
        cur = conn.cursor()
        cur.execute("select * from shows")
        for id,username,password,email,juris,x1,x2,y1,y2 in cur:
            point1=(x1,y1)
            point2=(x2,y2)
            print(x1,x2,y1,y2)
        # 画警戒区域
        # def on_mouse(event, x, y, flags, param):
        #     if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
        #         self.isNew = True
        #         if self.point1 != None:
        #             self.point1 = None
        #             self.point2 = None
        #         self.point1 = (x, y)
        #         cv2.circle(original, self.point1, 10, (0, 255, 0), 2)
        #         cv2.imshow("contours", original)
        #     elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):  # 按住左键拖曳
        #         cv2.rectangle(original, self.point1, (x, y), (255, 0, 0), 2)
        #         cv2.imshow("contours", original)
        #     elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
        #         self.point2 = (x, y)
        #         cv2.rectangle(original, self.point1,self. point2, (0, 0, 255), 2)
        #         cv2.imshow("contours", original)

       # while True:


        #有选中区域
        if point1 != None and point2 != None:
            cv2.rectangle(original, (point1[0], point1[1]), (point2[0], point2[1]), (0, 0, 255), 2)
            choosedArea = original[point1[1]:point2[1], point1[0]:point2[0]]
            # if self.isNew:
            #     self.isNew = False
        else:
            choosedArea = original


        #左上角时间显示
        now = datetime.now()
        month = now.strftime('%b')
        day = now.strftime('%d')
        hour = now.strftime('%H')
        minute = now.strftime('%M')
        time = now.strftime('%b %d %H %M %S %p')
        cv2.putText(original, "now time: {}".format(time),
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)



        # 人脸检测
        if ret:
            gray_img = cv2.cvtColor(choosedArea, cv2.COLOR_BGR2GRAY)
            # 人脸检测
            faces = self.face_cascade.detectMultiScale(gray_img, 1.3, 5)
            facenum_cur = len(faces)
            if facenum_cur==0:
                self.faceNum = 0
            # 场景中人数变化且不为0 -----发送警报-----
            if facenum_cur != self.faceNum and facenum_cur != 0:
                self.alarmNum += 1
                self.faceNum = facenum_cur
                # 保存图片
                filename = self.save_path + str(time) + '.jpg'
                cv2.imwrite(filename, original)
                #保存到excel
                don = [[time, facenum_cur]]
                for x in don:
                    self.sheet.append(x)
                # 发送邮件
                ret1 = self.mail(facenum_cur, filename)
                if ret1:
                    print("邮件发送成功")
                else:
                    print("邮件发送失败")
                self.months_s.append(str(month))
                self.days_s.append(str(day))
                self.hours_s.append(str(hour))
                self.minutes_s.append(str(minute))
                self.alarmtimes.append(str(time))
                self.filenames.append(filename)


            for (x, y, w, h) in faces:
                # 在原图像上绘制矩形
                cv2.rectangle(choosedArea, (x, y), (x + w, y + h), (255, 0, 0), 2)


        # cv2.imshow("contours", original)  ##显示轮廓的图像
        # cv2.setMouseCallback('contours', on_mouse)

        self.out.write(original)
        # cv2.imshow("seg", fgmask)
        rett, jpeg = cv2.imencode('.jpg', original)
        return jpeg.tobytes()









