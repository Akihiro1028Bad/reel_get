# app/utils/helpers.py
# 共通のユーティリティ関数を定義するファイル

import time

def estimate_remaining_time(downloaded, total, start_time):
    """
    残り時間を推定する関数
    
    :param downloaded: ダウンロード済みのリール数
    :param total: 全リール数
    :param start_time: ダウンロード開始時間
    :return: 推定残り時間の文字列
    """
    if downloaded == 0:
        return "推定時間計算中..."
    
    elapsed_time = time.time() - start_time
    avg_time_per_download = elapsed_time / downloaded
    remaining_downloads = total - downloaded
    estimated_remaining_seconds = avg_time_per_download * remaining_downloads
    
    if estimated_remaining_seconds < 60:
        return f"約 {int(estimated_remaining_seconds)} 秒"
    elif estimated_remaining_seconds < 3600:
        return f"約 {int(estimated_remaining_seconds / 60)} 分"
    else:
        hours = int(estimated_remaining_seconds / 3600)
        minutes = int((estimated_remaining_seconds % 3600) / 60)
        return f"約 {hours} 時間 {minutes} 分"