import base64
import json
import re

import pymysql
from flask import Flask, request, g, current_app, Response,render_template
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy
from pymysql import connect
from common import *
from flask_httpauth import HTTPBasicAuth
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from flask_cors import CORS
import json
from wtforms import Form
import flask_jwt_extended
import jsonify
import re
import jwt
from utils import camshift
from utils import face_detection
from utils import peopledetection
from utils import face_reco
from utils import get_faces
from utils import invade
from utils import shishi
from utils import chart
import datetime

from forms import UserForm

app = Flask(__name__)
CORS(app, supports_credentials=True)
auth = HTTPBasicAuth()
app.config['SECERT_KEY'] = 'asbdjsfldanir'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:010421@localhost:3306/xhkdb'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app, use_native_unicode='utf8')

class User(db.Model):
    __tablename__='shows'
    pk_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=False, nullable=True)
    password = db.Column(db.String(50), unique=False, nullable=True)
    email = db.Column(db.String(50), unique=False, nullable=True)
    juris = db.Column(db.String(10))

    def __repr__(self):
        return '<User %r, %r, %r, %r, %r>' % (self.pk_id, self.username, self.password, self.email, self.juris)

# #生成token
# def generate_auth_token(api_user):
#     s = Serializer(SECERT_KEY, expires_in=3600)
#     token = s.dumps({"id":api_user}).decode("ascii")
#     return token
#
#
# # 解析token
# def verify_auth_token(token):
#     s = Serializer(current_app.config["SECRET_KEY"])
#     try:
#         data = s.loads(token)
#         return data
#     except SignatureExpired:
#         return None
#     except BadSignature:
#         return None
#     user = User.query.get(data['id'])
#     return user
#
#
# # 验证token
# @auth.verify_password
# def verify_password(username, password):
#     user_id = re.sub(r'^"|"$', '', username)
#     user_id = verify_auth_token(user_id)
#     if not user_id:
#         user_id = connect(user=username, password=password)
#         if not user_id:
#             return None
#     g.user_id = user_id.get('user_id')
#     return True


@app.route('/api/user/login', methods=['post'])
# @auth.login_required
def login():
    result["message"] = "登录失败"
    result["success"] = False
    result["details"] = None

    user_info = request.get_json()
    print(user_info)
    #data = request.values.get("username")
    if user_info:
        #data = eval(user_info)
        username = user_info["username"]
        password = user_info["password"]
        #juris = data.get('juris')
        data = User.query.filter_by(username=username, password=password).first()

        if data:
            #token = create_access_token(identity={'username'=data.username})
            result["message"] = "登陆成功"
            result["success"] = True
            result["details"] = {"id":data.pk_id, "username": data.username}
            return Response(json.dumps(result), status=200)
        result["details"] = "用户名或密码错误"
        return Response(json.dumps(result), status=400)
    return Response(json.dumps(result), status=500)

@app.route('/api/user/register', methods=['post'])
def register():
    result["message"] = "注册失败"
    result["success"] = False
    result["details"] = None
    print(request.get_json())
    user_info = request.get_json()
    if user_info:
        if user_info["password"] == user_info["r_password"]:
            data = User.query.filter_by(username=user_info["username"]).first()
            data1 = User.query.filter_by(email=user_info["email"]).first()
            if not data and not data1:
                result["message"] = "注册成功"
                result["success"] = True
                result["details"] = {"username": user_info["username"], "password":user_info["password"]}
                print(result["details"])
                users = User(username=user_info["username"], password=user_info["password"], email=user_info["email"])
                db.session.add(users)
                db.session.commit()
                return Response(json.dumps(result), status=200)
            else:
                result["details"] = "信息不正确"
                return Response(json.dumps(result), status=400)
        else:
            result["details"] = "信息不正确"
            return Response(json.dumps(result), status=400)
    else:
        result["details"] = "信息不正确"
        return Response(json.dumps(result), status=400)
    return Response(json.dumps(result), status=500)

@app.route('/api/user/message', methods=['post'])
def get_mess():
    data = User.query.all()
    b = {}
    users = []
    for i in range(len(data)):
        b["username"] = data[i].username
        b["password"] = data[i].password
        b["email"] = data[i].email
        b["juris"] = data[i].juris
        users.append(b)
    result["message"] = "连接成功"
    result["success"] = True
    result["details"] = users
    return Response(json.dumps(result), status=200)

@app.route('/')  # 主页
def index():
    # jinja2模板，具体格式保存在index.html文件中
    return render_template('index.html')


# camshift  http://127.0.0.1:5000/camshift_feed
def gen_cam(camera):
    while True:
        frame = camera.trace()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/camshift_feed')  # 这个地址返回视频流响应
def camshift_feed():
    return Response(gen_cam(camshift.camshift()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# face_detection  http://127.0.0.1:5000/facedetection_feed
def gen_facedetection(camera):
    while True:
        frame = camera.detection()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/facedetection_feed')  # 这个地址返回视频流响应
def facedetection_feed():
    return Response(gen_facedetection(face_detection.face_detection()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# peopledetection  http://127.0.0.1:5000/peopledetection_feed
def gen_peopledetection(camera):
    while True:
        frame = camera.peopledetection()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/peopledetection_feed')  # 这个地址返回视频流响应
def peopledetection_feed():
    return Response(gen_peopledetection(peopledetection.peopledetection()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# peopledetection  http://127.0.0.1:5000/peopledetection_feed
def gen_facereco(camera):
    while True:
        frame = camera.process()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/facereco_feed')  # 这个地址返回视频流响应
def facereco_feed():
    return Response(gen_facereco(face_reco.Face_Recognizer()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# peopledetection  http://127.0.0.1:5000/peopledetection_feed
def gen_getface(camera):
    start  = datetime.datetime.now()
    while True:
        frame = camera.processin()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        end = datetime.datetime.now()
        if int((end - start).seconds) >= 60:
            break

@app.route('/getface_feed')  # 这个地址返回视频流响应
def getface_feed():
    return Response(gen_getface(get_faces.Face_Register()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_invade(camera):
    while True:
        frame = camera.detection()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/invade_feed')  # 这个地址返回视频流响应
def invade_feed():
    return Response(gen_invade(invade.face_detection()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_shishi(camera):
    while True:
        frame = camera.trace()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/shishi_feed')  # 这个地址返回视频流响应
def shishi_feed():
    return Response(gen_shishi(shishi.shishi()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/zhexian_feed')  # 这个地址返回视频流响应
def zhexian_feed():
    with open(r'chart_face_detection.png', 'rb') as f:
        res = base64.b64encode(f.read())
        return res

@app.route('/zhuzhuang_feed')  # 这个地址返回视频流响应
def zhuzhuang_feed():
    with open(r'chart_face_detection.png', 'rb') as f:
        res = base64.b64encode(f.read())
        return res

if __name__ == '__main__':
    app.run()
