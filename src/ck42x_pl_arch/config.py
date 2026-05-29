from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_NAME = "ck42x-pl-arch"
CONFIG_DIR = Path(os.environ.get("CK42X_PL_ARCH_CONFIG", Path.home() / ".config" / APP_NAME))
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT = Path.home() / "Documents" / "CK42X-PL-Arch" / "missions"
DEFAULT_PAYLOADBAY_TEMPLATE = CONFIG_DIR / "payloadbay-exfil-fat16.img"
PAYLOADBAY_TEMPLATE_URL = (
    "https://www.ck42x.com/downloads/flipper/companions/payloadbay-exfil-fat16.img"
)


@dataclass
class Settings:
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    output_dir: str = str(DEFAULT_OUTPUT)
    handoff_script_name: str = "agent.ps1"
    last_slug: str = ""
    flipper_port: str = ""
    flipper_baud: int = 115200
    flipper_payload_dir: str = "/ext/ck42x-payloads"
    flipper_mass_storage_image: str = "/ext/apps_data/mass_storage/payloadbay.img"
    auto_deploy_after_forge: bool = False
    deploy_use_mounted_volume: bool = True
    deploy_upload_image: bool = True
    payloadbay_template_url: str = PAYLOADBAY_TEMPLATE_URL
    payloadbay_template_path: str = str(DEFAULT_PAYLOADBAY_TEMPLATE)

    @classmethod
    def load(cls) -> Settings:
        if not CONFIG_FILE.exists():
            return cls()
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError):
            return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir).expanduser()
