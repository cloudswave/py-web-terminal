from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
import pexpect
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'WebTerminal'
socketio = SocketIO(app)

# 伪终端进程
shell = None

@socketio.on('connect')
def handle_connect():
    """客户端连接时启动 Shell"""
    global shell
    if not shell:
        # 使用 pexpect 启动 Bash
        shell = pexpect.spawn('bash', encoding='utf-8')
        # 启动一个线程来读取 Shell 的输出
        threading.Thread(target=read_and_forward_output, daemon=True).start()

def read_and_forward_output():
    """读取 Shell 的输出并发送到客户端"""
    global shell
    while True:
        try:
            output = shell.read_nonblocking(size=1024, timeout=0.1)
            socketio.emit('output', {'data': output})
        except pexpect.exceptions.TIMEOUT:
            continue
        except pexpect.exceptions.EOF:
            break

@socketio.on('input')
def handle_input(data):
    """处理客户端发送的输入"""
    global shell
    if shell:
        shell.send(data['data'])
@app.route('/')
def index():
    """渲染网页"""
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)