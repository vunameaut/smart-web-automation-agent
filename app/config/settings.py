from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Cấu hình toàn hệ thống cho Smart Web Automation Agent."""
    
    # Đường dẫn thư mục gốc dự án
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    
    # Đường dẫn lưu trữ dữ liệu, log, artifacts
    DATA_DIR: Path = Field(default=None)
    LOGS_DIR: Path = Field(default=None)
    ARTIFACTS_DIR: Path = Field(default=None)
    SCREENSHOTS_DIR: Path = Field(default=None)
    PROFILES_DIR: Path = Field(default=None)

    # Cấu hình Browser (Playwright)
    BROWSER_TYPE: str = Field(default="chromium")
    HEADLESS: bool = Field(default=False)  # Mặc định False để quan sát được
    SLOW_MO_MS: int = Field(default=300)   # Giảm tốc độ thao tác nhẹ để ổn định
    DEFAULT_TIMEOUT_MS: int = Field(default=30000)  # 30 giây timeout cho locator/action
    NAVIGATION_TIMEOUT_MS: int = Field(default=30000)
    VIEWPORT_WIDTH: int = Field(default=1280)
    VIEWPORT_HEIGHT: int = Field(default=800)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE_NAME: str = Field(default="agent.log")

    def model_post_init(self, __context) -> None:
        """Khởi tạo và đảm bảo các thư mục tồn tại trên máy cục bộ."""
        if self.DATA_DIR is None:
            self.DATA_DIR = self.BASE_DIR / "data"
        if self.LOGS_DIR is None:
            self.LOGS_DIR = self.BASE_DIR / "logs"
        if self.ARTIFACTS_DIR is None:
            self.ARTIFACTS_DIR = self.BASE_DIR / "artifacts"
        if self.SCREENSHOTS_DIR is None:
            self.SCREENSHOTS_DIR = self.ARTIFACTS_DIR / "screenshots"
        if self.PROFILES_DIR is None:
            self.PROFILES_DIR = self.DATA_DIR / "browser_profiles"

        # Tạo thư mục tự động nếu chưa có
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        self.PROFILES_DIR.mkdir(parents=True, exist_ok=True)


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Singleton getter cho cấu hình."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
