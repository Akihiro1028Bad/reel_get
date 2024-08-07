# app/routes.py
import asyncio
import logging
from quart import Blueprint, render_template, request, jsonify, websocket
from app import progress
from .scraper.instagram_scraper import InstagramReelScraper
from .downloader.reel_downloader import download_reels_from_external_site

main = Blueprint('main', __name__)

@main.route('/')
async def index():
    return await render_template('index.html')

@main.websocket('/ws')
async def ws():
    logging.info("WebSocket接続が確立されました。")
    while True:
        await websocket.send_json(progress.get())
        await asyncio.sleep(0.5)

@main.route('/scrape_and_download', methods=['POST'])
async def start_scrape_and_download():
    account_url = (await request.form)['account_url']
    logging.info(f"アカウントURL {account_url} のスクレイピングとダウンロードを開始します。")
    asyncio.create_task(scrape_and_download(account_url))
    return jsonify({'message': 'スクレイピングとダウンロードを開始しました'})

@main.route('/stop', methods=['POST'])
async def stop_process():
    progress.update(status='stopped')
    logging.info("プロセスの停止が要求されました。")
    return jsonify({'message': 'プロセスを停止しました'})

async def scrape_and_download(account_url):
    progress.update(status='running')
    scraper = InstagramReelScraper()
    try:
        logging.info(f"アカウント {account_url} のスクレイピングを開始します。")
        reel_urls = await scraper.scrape_reels(account_url)
        logging.info(f"スクレイピングが完了しました。{len(reel_urls)}個のリールURLが見つかりました。")

        if reel_urls is None or len(reel_urls) == 0:
            logging.warning("リールURLが見つかりませんでした。")
            return

        logging.info("ダウンロードプロセスを開始します...")
        await download_reels_from_external_site(scraper, reel_urls)
        logging.info("ダウンロードプロセスが完了しました。")
    except Exception as e:
        logging.error(f"プロセス中にエラーが発生しました: {str(e)}", exc_info=True)
    finally:
        scraper.close()
        progress.update(status='completed')
        logging.info("プロセスが完了しました。")