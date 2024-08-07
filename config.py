# config.py
# アプリケーションの設定を管理するファイル

import os

class Config:
    # デバッグモード
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 外部ダウンロードサイトのURL
    EXTERNAL_DOWNLOAD_SITE = os.environ.get('EXTERNAL_DOWNLOAD_SITE', 'https://snapinsta.app/')
    
    # ダウンロードしたリールの保存先ディレクトリ
    DOWNLOAD_DIRECTORY = os.environ.get('DOWNLOAD_DIRECTORY', 'downloaded_reels')

# 開発環境用の設定
class DevelopmentConfig(Config):
    DEBUG = True

# 本番環境用の設定
class ProductionConfig(Config):
    DEBUG = False

# 環境に応じて適切な設定を選択
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    return config[os.environ.get('FLASK_ENV', 'default')]