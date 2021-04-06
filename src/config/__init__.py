from configparser import ConfigParser
from pathlib import Path
from typing import Tuple


class Config(ConfigParser):
    """
    Global Configuration
    """

    def __init__(self) -> None:
        config_file = Path(__file__).parent / "config.ini"
        super().__init__()
        self.read(config_file)

    def get_s3_bucket(self) -> str:
        return self.get("S3", "s3_bucket")

    def get_s3_prefix(self) -> str:
        return self.get("S3", "s3_prefix")

    def get_es_url(self) -> str:
        return self.get("ES", "es_url")

    def get_es_credentials(self) -> Tuple[str, str]:
        return self.get("ES", "es_login"), self.get("ES", "es_password")

    def get_es_index(self) -> str:
        return self.get("ES", "es_index")

    def get_embedding_size(self) -> int:
        return self.getint("ES", "embedding_size")

    def get_embedder_url(self) -> str:
        public_ip = self.get("embedder", "public_ip")
        port = self.get("embedder", "port")
        return f"http://{public_ip}:{port}"

    def get_system_id(self) -> str:
        return self.get("DEFAULT", "system-id")


config = Config()
