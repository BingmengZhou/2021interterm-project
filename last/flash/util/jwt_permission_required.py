# utils/jwt_permission_required.py
import jwt
from django.conf import settings
from django.http import JsonResponse
from users.models import Users


def auth_permission_required(func):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            try:
                if func == "func":
                    auth = request.META.get('HTTP_AUTHORIZATION').split()
                else:
                    auth = request.request.META['HTTP_AUTHORIZATION'].split()
            except AttributeError:
                return JsonResponse({"status_code": 401, "message": "没有权限"})
            if auth[0].lower() == 'token':
                try:
                    dict = jwt.decode(auth[1], settings.SECRET_KEY, algorithms=['HS256'])
                    username = dict.get('data').get('username')
                except jwt.ExpiredSignatureError:
                    return JsonResponse({"status_code": 401, "message": "token 已过期"})
                except jwt.InvalidTokenError:
                    return JsonResponse({"status_code": 401, "message": "token 无效"})
                except Exception as e:
                    return JsonResponse({"status_code": 401, "message": "无法获取用户对象"})
                try:
                    Users.objects.get(username=username)
                except Users.DoesNotExist:
                    return JsonResponse({"status_code": 401, "message": "用户不存在"})
            else:
                return JsonResponse({"status_code": 401, "message": "不支持身份验证类型"})
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator