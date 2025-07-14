# app/orchestrator.py (Nâng cấp lên hệ thống tự chủ)
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import time
# Sửa import: Thêm invoke_planner_ai
from ai_agent import modify_application_code, fix_application_code, invoke_planner_ai

# --- Thiết lập ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ORCHESTRATOR] [%(levelname)s] - %(message)s")
EVOLUTION_LOG_FILE = Path("app/logs/evolution_log.json")
PLAN_FILE = Path("app/logs/plan.json") # File để lưu kế hoạch
MAX_HISTORY_ENTRIES = 10

# --- Các hàm quản lý nhật ký và kế hoạch ---
def load_json_file(filepath: Path) -> list | dict:
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_json_file(filepath: Path, data: list | dict):
    filepath.parent.mkdir(exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_evolution_entry(user_request: str, ai_description: str):
    history = load_json_file(EVOLUTION_LOG_FILE)
    entry = {"timestamp": datetime.now().isoformat(), "user_request": user_request, "ai_change_description": ai_description}
    history.append(entry)
    save_json_file(EVOLUTION_LOG_FILE, history)

# --- Hàm cho các chế độ ---
def execute_manual_request(user_request: str):
    """Thực hiện một yêu cầu đơn lẻ từ người dùng."""
    logging.info(f"Đang thực hiện yêu cầu thủ công: '{user_request}'")
    history = load_json_file(EVOLUTION_LOG_FILE)[-MAX_HISTORY_ENTRIES:]
    try:
        description = modify_application_code(user_request, history)
        save_evolution_entry(user_request, description)
        logging.info(f"Đã ghi lại thay đổi vào nhật ký: '{description}'")
    except Exception as e:
        logging.critical(f"Không thể hoàn thành yêu cầu thủ công. Lỗi: {e}")

def execute_autonomous_goal(user_goal: str):
    """Thực hiện một mục tiêu lớn một cách tự chủ."""
    logging.info(f"--- BẮT ĐẦU CHẾ ĐỘ TỰ CHỦ VỚI MỤC TIÊU: {user_goal} ---")
    
    # Bước 1: Gọi AI Planner để tạo kế hoạch
    history = load_json_file(EVOLUTION_LOG_FILE)[-MAX_HISTORY_ENTRIES:]
    plan = invoke_planner_ai(user_goal, history)
    
    if not plan:
        logging.critical("Không thể tạo kế hoạch. Dừng chế độ tự chủ.")
        return
        
    save_json_file(PLAN_FILE, {"goal": user_goal, "steps": plan, "completed_steps": 0})
    logging.info(f"Đã lưu kế hoạch vào '{PLAN_FILE}'.")
    
    # Bước 2: Thực thi từng bước trong kế hoạch
    for i, step_data in enumerate(plan):
        step_description = step_data.get("description")
        logging.info(f"--- Đang thực hiện Bước {i+1}/{len(plan)}: {step_description} ---")
        
        try:
            # Sử dụng hàm modify_application_code để thực hiện bước này
            # Chúng ta coi mỗi bước là một "yêu cầu" cho Executor AI
            history = load_json_file(EVOLUTION_LOG_FILE)[-MAX_HISTORY_ENTRIES:]
            ai_change_desc = modify_application_code(step_description, history)
            
            # Ghi lại thành công của bước này vào nhật ký
            save_evolution_entry(f"Tự chủ (Bước {i+1}): {step_description}", ai_change_desc)
            
            # Cập nhật tiến độ kế hoạch
            plan_data = load_json_file(PLAN_FILE)
            plan_data["completed_steps"] = i + 1
            save_json_file(PLAN_FILE, plan_data)
            
            logging.info(f"✅ HOÀN THÀNH BƯỚC {i+1}. Đợi hệ thống ổn định...")
            # Đợi một chút để supervisor khởi động lại và ổn định
            time.sleep(10)

        except Exception as e:
            logging.critical(f"❌ LỖI KHI THỰC HIỆN BƯỚC {i+1}. Lỗi: {e}")
            logging.error("Hệ thống tự sửa lỗi sẽ được kích hoạt bởi Supervisor.")
            logging.error("Chế độ tự chủ sẽ tạm dừng. Hãy sửa lỗi và chạy lại.")
            break # Dừng vòng lặp kế hoạch nếu có lỗi
            
    else: # Chỉ chạy khi vòng for hoàn thành không bị break
        logging.info("🎉 TẤT CẢ CÁC BƯỚC TRONG KẾ HOẠCH ĐÃ HOÀN THÀNH! MỤC TIÊU ĐẠT ĐƯỢC. 🎉")
        PLAN_FILE.unlink(missing_ok=True) # Xóa file kế hoạch khi xong


def main():
    """Hàm chính điều phối, hỗ trợ chế độ thủ công và tự chủ."""
    if len(sys.argv) < 2:
        print("Sử dụng:")
        print("  - Chế độ thủ công: python app/orchestrator.py \"Yêu cầu cụ thể\"")
        print("  - Chế độ tự chủ:   python app/orchestrator.py --goal \"Mục tiêu lớn của bạn\"")
        sys.exit(1)
        
    if sys.argv[1] == '--goal':
        if len(sys.argv) < 3:
            print("Lỗi: Vui lòng cung cấp mục tiêu sau --goal.")
            sys.exit(1)
        user_goal = " ".join(sys.argv[2:])
        execute_autonomous_goal(user_goal)
    else:
        user_request = " ".join(sys.argv[1:])
        execute_manual_request(user_request)

# trigger_self_correction giữ nguyên
def trigger_self_correction(error_message: str):
    logging.info("Đã nhận tín hiệu tự sửa lỗi từ Supervisor.")
    fix_application_code(error_message)

if __name__ == "__main__":
    main()