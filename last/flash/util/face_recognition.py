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

#陌生人
months_s=[]
days_s=[]
hours_s=[]
minutes_s=[]
alarmtimes_s = []
filenames_s = []
#熟人
months_a=[]
days_a=[]
hours_a=[]
minutes_a=[]
alarmtimes_a = []
filenames_a = []


# 发送邮件
def mail(peoplenum,filename):
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

def saveInSql(alarmNum_s, alarmNum_a, conn, cur):
    for i in range(0,alarmNum_s-1):
        newmonth = months_s[i]
        newday = days_s[i]
        newhours = hours_s[i]
        newmin = minutes_s[i]
        newTime = alarmtimes_s[i]
        newFileName = filenames_s[i]
        # 添加数据
        sql = """
                        insert into stranger(month,day,hour,minute,time,screenshot) value(%s,%s,%s,%s,%s,%s)
                        """
        try:
            # 执行sql语句
            cur.execute(sql, (newmonth,newday,newhours,newmin,newTime, newFileName))
            # #提交到数据库执行
            conn.commit()
            print("数据库保存成功")
        except:
            # 发生错误时回滚
            conn.rollback()
            print("数据库保存失败")
    for i in range(0,alarmNum_a-1):
        newmonth=months_a[i]
        newday=days_a[i]
        newhours=hours_a[i]
        newmin=minutes_a[i]
        newTime = alarmtimes_a[i]
        newFileName = filenames_a[i]
        # 添加数据
        sql = """
                        insert into acquaintance(month,day,hour,minute,time,screenshot) value(%s,%s,%s,%s,%s,%s)
                        """
        try:
            print(newmonth,newday,newhours,newmin,newTime, newFileName)
            # 执行sql语句
            cur.execute(sql, (newmonth,newday,newhours,newmin,newTime, newFileName))
            # #提交到数据库执行
            conn.commit()
            print("数据库保存成功")
        except:
            # 发生错误时回滚
            conn.rollback()
            print("数据库保存失败")


def recognition(rtmpaddr):
    alarmNum_s = 0
    alarmNum_a = 0
    work = load_workbook(filename="data_face_detection.xlsx")
    sheet = work.active  # 默认为第一张表格
    if sheet['A1'].value != 'time':
        sheet['A1'].value = 'time'
        sheet['B1'].value = 'facenum_cur'
        print('已添加')

    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='yourpassword', db='mydata', port=3306, charset='utf8')
    cur = conn.cursor()

    # 入侵截图保存路径
    save_path = 'img/'
    background = None
    choosedArea = None

    path = 'venv/Lib/site-packages/cv2/data/'
    face_cascade = cv2.CascadeClassifier(path+'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(path+'haarcascade_eye.xml')
    body_cascade = cv2.CascadeClassifier(path+'haarcascade_fullbody.xml')

    faceNum = 0

    #设置为默认摄像头
    camera = cv2.VideoCapture(rtmpaddr)
    ret, original1 = camera.read()
    # 背景移除
    fgbg = cv2.createBackgroundSubtractorMOG2()

    # 人脸识别准备好识别方法
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    # 读取模型
    recognizer.read('trainner/trainner.yml')
    # 调用人脸分类器
    face_cascade = cv2.CascadeClassifier(
        'venv/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')

    font = cv2.FONT_HERSHEY_SIMPLEX
    idnum = 0
    #与模型ID相匹配的人名
    names = ['初始', 'ying', 'chenguoying', 'user2', 'user3']

    minW = 0.1 * camera.get(3)
    minH = 0.1 * camera.get(4)

    # 存储视频
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, 30.0, (640, 480))

    # 警戒区域点坐标
    global point1, point2, isNew
    point1 = None
    point2 = None
    isNew = False

    # 画警戒区域
    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
            global point1, point2
            global isNew
            isNew = True
            if point1 != None:
                point1 = None
                point2 = None
            point1 = (x, y)
            cv2.circle(original, point1, 10, (0, 255, 0), 2)
            cv2.imshow("contours", original)
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):  # 按住左键拖曳
            cv2.rectangle(original, point1, (x, y), (255, 0, 0), 2)
            cv2.imshow("contours", original)
        elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
            point2 = (x, y)
            cv2.rectangle(original, point1, point2, (0, 0, 255), 2)
            cv2.imshow("contours", original)

    while True:
        ret, original = camera.read()
        fgmask = fgbg.apply(original)
        out.write(original)
        #已设置警戒区域
        if point1 != None and point2 != None:
            cv2.rectangle(original, (point1[0], point1[1]), (point2[0], point2[1]), (0, 0, 255), 2)
            choosedArea = original[point1[1]:point2[1], point1[0]:point2[0]]
            if isNew:
                isNew = False
        else:
            choosedArea = original

        gray_frame = cv2.cvtColor(choosedArea, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)#高斯模糊

        #实时时间显示
        now = datetime.now()
        month=now.strftime('%b')
        day=now.strftime('%d')
        hour=now.strftime('%H')
        minute=now.strftime('%M')
        time = now.strftime('%b %d %H %M %S %p')
        cv2.putText(original, "now time: {}".format(time),
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # 识别人脸
        faces = face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH))
        )

        #场中人数变化时截图并发出警报邮件
        facenum_cur = len(faces)
        if facenum_cur==0:
            faceNum = 0

        if facenum_cur != faceNum and facenum_cur != 0:
            faceNum = facenum_cur
            # 保存入侵截图
            filename = save_path + str(time) + '.jpg'
            cv2.imwrite(filename, original)


        # 进行校验
        for (x, y, w, h) in faces:

            idnum, confidence = recognizer.predict(gray_frame[y:y + h, x:x + w])

            # 计算出一个检验结果
            if confidence < 100:
                idum = names[idnum]
                confidence = "{0}%", format(round(100 - confidence))

            else:
                idum = "unknown"
                confidence = "{0}%", format(round(100 - confidence))

            if idum == "unknown":
                cv2.putText(choosedArea, str(idum), (x + 5, y - 5), font, 1, (255, 0, 0), 1)
                cv2.rectangle(choosedArea, (x, y), (x + w, y + h), (255, 0, 0), 2)
                alarmNum_s += 1
                months_s.append(str(month))
                days_s.append(str(day))
                hours_s.append(str(hour))
                minutes_s.append(str(minute))
                alarmtimes_s.append(str(time))
                filenames_s.append(filename)
                # 保存到excel
                don = [[time, facenum_cur]]
                for x in don:
                    sheet.append(x)
                # 发送邮件
                ret1 = mail(facenum_cur, filename)
                if ret1:
                    print("邮件发送成功")
                else:
                    print("邮件发送失败")

            else:
                cv2.rectangle(choosedArea, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(choosedArea, str(idum), (x + 5, y - 5), font, 1, (0, 255,0), 1)
                alarmNum_a += 1
                months_a.append(str(month))
                days_a.append(str(day))
                hours_a.append(str(hour))
                minutes_a.append(str(minute))
                alarmtimes_a.append(str(time))
                filenames_a.append(filename)

        cv2.imshow("contours", original)  ##显示轮廓的图像
        cv2.setMouseCallback('contours', on_mouse)
        cv2.imshow("seg", fgmask)

        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break

    saveInSql(alarmNum_s, alarmNum_a, conn, cur)
    cv2.destroyAllWindows()
    camera.release()







