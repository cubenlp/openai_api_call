#!/usr/bin/env python
from flask import Flask, request, Response
import requests, random
import os


# 配置
## 配置密钥
API_LIST = ['sk-real-1', 'sk-real-2', 'sk-real-3']
fake_keys = ['sk-fake-1', 'sk-fake-2', 'sk-fake-3']
fake_keys = [ 'Bearer ' + key for key in fake_keys]

## 设置日志路径
home = os.path.expanduser("~")
log_path = os.path.join(home, '.chatlog/chatdata.log')
api_path = os.path.join(home, '.chatlog/apilist.log')
os.makedirs(os.path.dirname(log_path), exist_ok=True)
os.makedirs(os.path.dirname(api_path), exist_ok=True)

# 创建 Flask 应用
app = Flask(__name__)

## 配置标准的 API 转发
@app.route('/v1/chat/completions', methods=['POST'])
def forward_request():
    try:
        # 获取请求头、请求体和查询参数
        api_key = request.headers.get('Authorization')
        url = 'https://api.openai.com/v1/chat/completions'
        data = request.get_json()
        params = request.args

        # 如果 API 密钥为“伪密钥”，则进行替换
        if api_key in fake_keys:
            api_key = "Bearer " + random.choice(API_LIST)
        
        # 记录陌生的 API 请求
        api_key = api_key.strip("Bearer ").strip()
        if not api_key in API_LIST:
            with open(api_path, 'a') as f:
                f.write(f'{api_key}\n\n')
            raise Exception("Unknown API key!") # 拦截陌生的 API 请求

        # 将数据转发到目标 API，并获取响应
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{api_key}"
        }
        response = requests.post(url, json=data, params=params, headers=headers, stream=True)

        # 保存请求数据
        with open(log_path, 'a', encoding="utf-8") as f:
            f.write(f'#Request\n{data}\n#Request\n')

        # 构造响应对象并返回
        return Response(response.content, status=response.status_code)
    except Exception as e:
        return Response(f"invalid request!\n", status=400)

## API 使用日志查询
@app.route('/<path:path>', methods=['GET'])
def handle_all(path):
    try:
        api_key = request.headers.get('Authorization')
        if api_key in fake_keys:
            api_key = "Bearer " + random.choice(API_LIST)
        headers = {
                "Content-Type": "application/json",
                "Authorization": f"{api_key}"}
        if path == 'v1/dashboard/billing/usage':
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            url = f'https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}'
            response = requests.get(url, headers=headers)
            return Response(response.content, status=response.status_code)
        elif path == 'v1/dashboard/billing/subscription':
            url = 'https://api.openai.com/v1/dashboard/billing/subscription'
            response = requests.get(url, headers=headers)
            return Response(response.content, status=response.status_code)
        else:
            return Response(f"invalid request!\n", status=400)
    except Exception as e:
        return Response(f"invalid request!\n", status=400)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
