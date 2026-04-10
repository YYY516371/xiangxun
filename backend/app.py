from flask import Flask
from flask_cors import CORS

# 创建一个 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许前端访问

# 定义一个网址路径 "/"
@app.route('/')
def hello():
    return 'Hello World! 后端运行成功'

# 启动服务器
if __name__ == '__main__':
    app.run(debug=True, port=5000)