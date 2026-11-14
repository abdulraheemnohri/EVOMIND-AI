import os
from pathlib import Path
class Settings:
    host=os.getenv("EVOMIND_HOST","127.0.0.1")
    port=int(os.getenv("EVOMIND_PORT","8000"))
    data_dir=Path(os.getenv("EVOMIND_DATA_DIR","data")).resolve()
    models_dir=Path(os.getenv("EVOMIND_MODELS_DIR","models")).resolve()
    db_path=Path(os.environ["EVOMIND_DB"]).resolve() if os.getenv("EVOMIND_DB") else None
    @classmethod
    def prepare(cls):
        cls.data_dir.mkdir(parents=True,exist_ok=True)
        cls.models_dir.mkdir(parents=True,exist_ok=True)
settings=Settings()
