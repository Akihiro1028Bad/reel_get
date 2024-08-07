# app/scraper/instagram_scraper.py
import logging
import asyncio
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app import progress

class InstagramReelScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        self.start_time = None
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("WebDriverが正常に初期化されました。")

    async def find_element(self, by, value):
        return await asyncio.to_thread(self.wait.until, EC.presence_of_element_located((by, value)))

    async def find_elements(self, by, value):
        return await asyncio.to_thread(self.driver.find_elements, by, value)

    async def execute_script(self, script, *args):
        return await asyncio.to_thread(self.driver.execute_script, script, *args)

    async def scrape_reels(self, account_url):
        logging.info(f"以下のURLのスクレイピングを開始しました: {account_url}")
        try:
            await asyncio.to_thread(self.driver.get, account_url)
        except Exception as e:
            logging.error(f"ページの読み込み中にエラーが発生しました: {str(e)}")
            return []

        await asyncio.sleep(5)  # ページ読み込みの待機
        reel_urls = set()
        last_height = await self.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10
        no_new_reels_count = 0
        max_no_new_reels = 3

        while scroll_attempts < max_scroll_attempts and no_new_reels_count < max_no_new_reels and progress.get()['status'] != 'stopped':
            await self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(3)
            await self.close_popup()

            link_elements = await self.find_elements(By.TAG_NAME, "a")
            
            new_reels_found = False
            for element in link_elements:
                href = await asyncio.to_thread(element.get_attribute, 'href')
                if href and re.search(r'/(reel|p)/[\w-]+', href):
                    clean_url = self.clean_url(href)
                    if clean_url not in reel_urls:
                        reel_urls.add(clean_url)
                        new_reels_found = True
                        logging.info(f"新しいリールURLが見つかりました: {clean_url}")

            if new_reels_found:
                no_new_reels_count = 0
            else:
                no_new_reels_count += 1

            progress.update(total_reels=len(reel_urls))
            logging.info(f"現在見つかっているユニークなリールURLの総数: {len(reel_urls)}")

            new_height = await self.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_height = new_height

            logging.info(f"スクロール試行回数: {scroll_attempts}, 新しいリールが見つからなかった回数: {no_new_reels_count}")

        logging.info(f"スクレイピングが完了しました。見つかったリールの総数: {len(reel_urls)}")
        return list(reel_urls)

    async def close_popup(self):
        logging.info("ポップアップを閉じる処理を開始します")
        try:
            xpaths = [
                "//div[@role='button' and contains(@class, 'x1i10hfl') and .//svg[contains(@aria-label, '閉じる') or contains(@aria-label, 'Close')]]",
                "//div[@role='button']//svg[contains(@aria-label, '閉じる') or contains(@aria-label, 'Close')]",
                "//button[contains(@class, 'xjbqb8w')]",
                "//*[local-name()='svg' and (@aria-label='閉じる' or @aria-label='Close')]/.."
            ]
            
            for xpath in xpaths:
                try:
                    close_button = await self.find_element(By.XPATH, xpath)
                    await self.execute_script("arguments[0].click();", close_button)
                    logging.info(f"XPath: {xpath} を使用してポップアップを閉じました")
                    await asyncio.sleep(1)
                    return True
                except Exception as e:
                    logging.warning(f"XPath: {xpath} でのポップアップ閉じる試行が失敗しました: {str(e)}")
            
            # すべての方法が失敗した場合、ESCキーを押してみる
            await asyncio.to_thread(ActionChains(self.driver).send_keys, Keys.ESCAPE)
            logging.info("ESCキーを押してポップアップを閉じる試行をしました")
            
            return False
        except Exception as e:
            logging.error(f"ポップアップを閉じる際に予期せぬエラーが発生しました: {str(e)}")
            return False

    def clean_url(self, url):
        base_url = url.split('?')[0]
        base_url = base_url.replace('/reels/', '/reel/')
        return base_url

    def close(self):
        self.driver.quit()
        logging.info("WebDriverを閉じました。")