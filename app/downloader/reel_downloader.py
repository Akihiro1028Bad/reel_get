# app/downloader/reel_downloader.py
import logging
import asyncio
import aiohttp
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from app import progress
from app.utils.helpers import estimate_remaining_time
from config import get_config
import time

config = get_config()

async def download_reels_from_external_site(scraper, reel_urls):
    if not reel_urls:
        logging.warning("ダウンロードするリールURLがありません。")
        return

    logging.info(f"外部サイト {config.EXTERNAL_DOWNLOAD_SITE} にアクセスしています")
    try:
        await asyncio.to_thread(scraper.driver.get, config.EXTERNAL_DOWNLOAD_SITE)
    except Exception as e:
        logging.error(f"外部サイトへのアクセス中にエラーが発生しました: {str(e)}")
        return

    await asyncio.sleep(2)

    download_start_time = time.time()  # ダウンロード開始時間を記録

    async with aiohttp.ClientSession() as session:
        for reel_url in reel_urls:
            if progress.get()['status'] == 'stopped':
                logging.info("ダウンロードプロセスが停止されました。")
                break

            try:
                logging.info(f"{reel_url} のダウンロードを開始します")
                progress.update(current_reel=reel_url)

                download_url = await get_download_url(session, scraper, reel_url)
                await download_file(session, download_url, reel_url)

                current_progress = progress.get()
                current_progress['downloaded_reels'] += 1
                current_progress['estimated_time'] = estimate_remaining_time(
                    current_progress['downloaded_reels'],
                    current_progress['total_reels'],
                    download_start_time
                )
                progress.update(**current_progress)

                logging.info(f"{reel_url} のダウンロードが完了しました")

            except Exception as e:
                logging.error(f"{reel_url} のダウンロード中にエラーが発生しました: {str(e)}")

    logging.info("すべてのリールのダウンロードが完了しました")

async def get_download_url(session, scraper, reel_url):
    logging.info(f"{reel_url} のダウンロードURLを取得しています")
    try:
        # URL入力欄が見つからない場合、ページをリロード
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                input_field = await scraper.find_element(By.ID, "url")
                break
            except TimeoutException:
                if attempt < max_attempts - 1:
                    logging.warning(f"URLの入力フィールドが見つかりません。ページをリロードします（試行 {attempt + 1}/{max_attempts}）")
                    await asyncio.to_thread(scraper.driver.refresh)
                    await asyncio.sleep(2)
                else:
                    logging.error(f"URLの入力フィールドが見つかりません。最大試行回数 {max_attempts} に達しました。")
                    raise

        await scraper.execute_script("arguments[0].value = arguments[1]", input_field, reel_url)
        
        download_button = await scraper.find_element(By.ID, "btn-submit")
        await scraper.execute_script("arguments[0].click();", download_button)
        
        await asyncio.sleep(3)

        # 広告を閉じる
        if not await close_ad(scraper):
            logging.warning("広告を閉じることができませんでしたが、処理を続行します")

        download_link = await scraper.find_element(By.CSS_SELECTOR, "a.btn.download-media.flex-center")
        download_url = await asyncio.to_thread(download_link.get_attribute, 'href')
        logging.info(f"ダウンロードリンクを取得しました: {download_url}")
        return download_url
    except Exception as e:
        logging.error(f"ダウンロードURLの取得中にエラーが発生しました: {str(e)}")
        raise

async def close_ad(scraper):
    logging.info("広告を閉じる処理を開始します")
    try:
        ad_close_selectors = [
            (By.ID, "close-modal"),
            (By.ID, "dismiss-button"),
            (By.CSS_SELECTOR, ".close-button[aria-label='Close ad']"),
            (By.XPATH, "//div[contains(@class, 'close-button') and @aria-label='Close ad']")
        ]

        for by, selector in ad_close_selectors:
            try:
                close_ad_button = await scraper.find_element(by, selector)
                await scraper.execute_script("arguments[0].click();", close_ad_button)
                logging.info(f"広告を閉じました: {selector}")
                await asyncio.sleep(1)
                return True
            except Exception as e:
                logging.debug(f"{selector} での広告を閉じる試行が失敗しました: {str(e)}")

        logging.warning("すべての方法で広告を閉じることができませんでした")
        return False
    except Exception as e:
        logging.error(f"広告を閉じる処理中に予期せぬエラーが発生しました: {str(e)}")
        return False

async def download_file(session, download_url, reel_url):
    logging.info(f"{download_url} からファイルをダウンロードしています")
    try:
        async with session.get(download_url) as response:
            if response.status == 200:
                now = datetime.now()
                date_time = now.strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(config.DOWNLOAD_DIRECTORY, f"{reel_url.split('/')[-1]}_{date_time}.mp4")
                with open(filename, 'wb') as f:
                    f.write(await response.read())
                logging.info(f"{filename} にリールを保存しました")
            else:
                logging.error(f"{reel_url} のダウンロードに失敗しました。ステータスコード: {response.status}")
    except Exception as e:
        logging.error(f"ファイルのダウンロード中にエラーが発生しました: {str(e)}")
        raise