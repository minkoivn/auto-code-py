# app/web_server.py
from flask import Flask, render_template_string

app = Flask(__name__)

# Basic HTML structure for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent X Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; }
        p { line-height: 1.6; }
        .footer { margin-top: 30px; text-align: center; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Chào mừng đến với AI Agent X!</h1>
        <p>Đây là giao diện web đầu tiên để tương tác với AI Agent X của bạn.</p>
        <p>Trong tương lai, bạn sẽ có thể xem nhật ký tiến hóa, kích hoạt các chu trình mới và kiểm soát AI từ đây.</p>
        <p>Hiện tại, trang này chỉ là một placeholder.</p>
    </div>
    <div class="footer">
        Đang chạy trên localhost:3000
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    print("🚀 Đang khởi động AI Agent X Web Interface...")
    print("🌐 Truy cập tại: http://127.0.0.1:3000")
    app.run(debug=True, port=3000)
