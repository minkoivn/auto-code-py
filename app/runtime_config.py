# app/runtime_config.py
from typing import Dict, Any

class RuntimeConfig:
    """
    Chứa tất cả các cài đặt và thông tin cấu hình ứng dụng được xác định tại thời điểm chạy.
    Điều này bao gồm tên ứng dụng, phiên bản đã chọn và các cài đặt mô phỏng.
    """
    def __init__(
        self,
        app_name: str,
        app_version: int,
        simulation_settings: Dict[str, Any]
    ):
        self.application_name = app_name
        self.application_version = app_version
        # Lấy các cài đặt mô phỏng, cung cấp giá trị mặc định giống như settings.py để an toàn
        self.failure_chance = simulation_settings.get("failure_chance", 0.2)
        self.long_task_divisor = simulation_settings.get("long_task_divisor", 5)

    def __str__(self):
        return (
            f"RuntimeConfig(AppName='{self.application_name}', "
            f"AppVersion={self.application_version}, "
            f"FailureChance={self.failure_chance}, "
            f"LongTaskDivisor={self.long_task_divisor})"
        )
