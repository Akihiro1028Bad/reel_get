# app/__init__.py
import logging
from quart import Quart
from config import get_config
from threading import Lock

class Progress:
    def __init__(self):
        self._data = {
            'total_reels': 0,
            'downloaded_reels': 0,
            'status': 'idle',
            'current_reel': '',
            'estimated_time': ''
        }
        self._lock = Lock()

    def update(self, **kwargs):
        with self._lock:
            self._data.update(kwargs)

    def get(self):
        with self._lock:
            return self._data.copy()

# グローバル進捗オブジェクトの作成
progress = Progress()

def create_app():
    # Quartアプリケーションの作成
    app = Quart(__name__, template_folder='../templates', static_folder='../static')
    
    # 設定の読み込み
    app.config.from_object(get_config())

    # ロギングの設定
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # ルートの登録
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    logging.info("アプリケーションが正常に初期化されました。")

    return app