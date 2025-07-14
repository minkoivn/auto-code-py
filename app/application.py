# app/application.py
import time
import os
import signal
import unittest
import logging
from flask import Flask, request, jsonify
import json
import sys

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lưu trữ hàm get_world_time và các test case vào file riêng
# Tạo file old_get_world_time.py
# Sao chép hàm get_world_time và các test case từ file này sang file old_get_world_time.py

#app/old_get_world_time.py
# Sao chép nội dung của hàm get_world_time và class TestGetWorldTime từ file này sang file old_get_world_time.py

class TestGetWorldTime(unittest.TestCase):
    pass


class TestGetData(unittest.TestCase):
    def test_get_data_success(self):
        with open('data.json', 'w') as f:
            json.dump({'message': 'Success'}, f)
        with app.test_client() as client:
            response = client.get('/data')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), {'message': 'Success'})
        os.remove('data.json')

    def test_get_data_file_not_found(self):
        with app.test_client() as client:
            response = client.get('/data')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.data), {'error': 'File data.json not found'})

    def test_get_data_invalid_json(self):
        with open('data.json', 'w') as f:
            f.write('invalid json')
        with app.test_client() as client:
            response = client.get('/data')
            self.assertEqual(response.status_code, 500)
            self.assertIn('Invalid JSON data', json.loads(response.data)['error'])
        os.remove('data.json')

    def test_get_root_success(self):
        with app.test_client() as client:
            response = client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"<h1>Hello, world!</h1>", response.data)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    logging.info("Nhận request GET /")
    return "<h1>Hello, world!</h1>"

@app.route('/', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        logging.info(f"Nhận dữ liệu từ client: {data}")
        # Lưu dữ liệu vào file tạm thời
        with open('data.json', 'w') as f:
            json.dump(data, f)
        return jsonify({'message': 'Dữ liệu đã được nhận thành công'}), 200
    except json.JSONDecodeError:
        logging.error(f"Lỗi: Dữ liệu không hợp lệ (JSONDecodeError)")
        return jsonify({'error': 'Dữ liệu gửi lên không hợp lệ'}), 400
    except Exception as e:
        logging.exception(f"Lỗi khi nhận dữ liệu: {e}")
        return jsonify({'error': 'Lỗi khi xử lý yêu cầu'}), 500

@app.route('/file', methods=['POST'])
def manage_file():
    try:
        data = request.get_json()
        filename = data.get('filename')
        filetype = data.get('filetype')
        action = data.get('action')

        if not filename or not filetype or not action:
            return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400

        if action == 'add':
            # Thêm tệp
            with open(filename, 'w') as f:
                f.write("")  # Tạo tệp trống
            return jsonify({'message': f'Tệp {filename} đã được thêm'}), 201
        elif action == 'delete':
            # Xóa tệp
            if os.path.exists(filename):
                os.remove(filename)
                return jsonify({'message': f'Tệp {filename} đã được xóa'}), 200
            else:
                return jsonify({'error': f'Tệp {filename} không tồn tại'}), 404
        else:
            return jsonify({'error': 'Hành động không hợp lệ'}), 400
    except OSError as e:
        logging.exception(f"Lỗi hệ thống khi quản lý tệp: {e}")
        return jsonify({'error': f'Lỗi hệ thống: {e}'}), 500
    except Exception as e:
        logging.exception(f"Lỗi khi quản lý tệp: {e}")
        return jsonify({'error': 'Lỗi khi xử lý yêu cầu'}), 500

def process_data():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            # Gọi orchestrator
            import orchestrator  # giả định orchestrator ở cùng thư mục
            orchestrator.process(data)
    except FileNotFoundError:
        logging.warning(f"Lỗi: File data.json không tồn tại.")
    except json.JSONDecodeError as e:
        logging.error(f"Lỗi JSONDecodeError: {e}", exc_info=True)
    except Exception as e:
        logging.exception(f"Lỗi khi xử lý data.json: {e}")

@app.route('/data', methods=['GET'])
def get_data():
    try:
        logging.info("Nhận request GET /data")
        if os.path.exists('data.json'):
            with open('data.json', 'r') as f:
                data = json.load(f)
                logging.info("Trả về dữ liệu thành công")
                return jsonify(data), 200
        else:
            logging.warning("File data.json không tồn tại")
            return jsonify({'error': 'File data.json not found'}), 404
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON data: {str(e)}", exc_info=True)
        return jsonify({'error': f'Invalid JSON data: {str(e)}'}), 500
    except Exception as e:
        logging.exception(f"An error occurred: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

def run_app():
    """
    Đây là nơi chứa logic chính của ứng dụng của bạn.
    """
    print(f"[{time.ctime()}] --- Ứng dụng đang chạy (PID: {os.getpid()}) --- Phiên bản 1.0")
    
    # Để kiểm tra, hãy thử thay đổi nội dung của tệp này khi nó đang chạy.
    # Ví dụ: thay đổi "Phiên bản 1.0" thành "Phiên bản 1.1" và lưu lại.
    # main.py sẽ tự động phát hiện và khởi động lại nó.
    
    # Để kiểm tra phục hồi lỗi, hãy tạo ra lỗi cú pháp và lưu lại.
    # Ví dụ: xóa dấu ngoặc ở cuối dòng print bên dưới.
    # print(f"Một dòng code không lỗi"
    
    count = 0
    def handle_signal(signum, frame):
        print(f"[{time.ctime()}] --- Ứng dụng nhận được tín hiệu {signal.Signals(signum).name} ---")
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        print(f"[{time.ctime()}] AI đang làm việc... Lần thứ {count+1} 🤖")
        process_data()
        count += 1
        time.sleep(18)

if __name__ == "__main__":
    try:
        unittest.main(argv=['first-arg-is-ignored'], exit=False) # Chạy test trước
        app.run(debug=False, port=3000)
    except Exception as e:
        # Ghi lỗi vào stderr để main.py có thể bắt được
        print(f"Ứng dụng gặp lỗi và bị sập: {e}", file=sys.stderr)
        # Thoát với mã lỗi để báo hiệu cho supervisor
        sys.exit(1)