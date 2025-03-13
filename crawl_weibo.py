import re

import requests
import time
import random
import pandas as pd
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def crawl_weibo_data(keyword, pages=5, config=None):
    """爬取 card_type=9 的微博数据，包括嵌套在 card_group 中的数据"""
    if config is None:
        raise ValueError("缺少微博配置信息")

    encoded_keyword = quote(keyword, safe='')
    api_url = f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{encoded_keyword}&page_type=searchall&page={{page}}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Cookie": config.get("COOKIE", ""),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": f"https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{encoded_keyword}"
    }
    if "XSRF_TOKEN" in config:
        headers["X-XSRF-TOKEN"] = config["XSRF_TOKEN"]

    results = []
    for page in range(1, pages + 1):
        try:
            url = api_url.format(page=page)
            logging.info(f"正在爬取第 {page} 页：{url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "utf-8"
            data = response.json()
            cards = data.get("data", {}).get("cards", [])
            for card in cards:
                if card.get("card_type") == 9:
                    mblog = card.get("mblog", {})
                    content = mblog.get("text", mblog.get("raw_text", ""))
                    link = card.get("scheme", "")
                    mid = mblog.get("id", "")
                    if content and link:
                        results.append({"content": content, "link": link, "mid": mid})
                        logging.info(f"成功提取帖子 (mid={mid})：{content[:50]}...")
                    else:
                        logging.warning(f"无法提取内容或链接，跳过此帖子：{mblog}")
                elif card.get("card_type") == 11:
                    card_group = card.get("card_group", [])
                    for sub_card in card_group:
                        if sub_card.get("card_type") == 9:
                            mblog = sub_card.get("mblog", {})
                            content = mblog.get("text", mblog.get("raw_text", ""))
                            link = sub_card.get("scheme", card.get("scheme", ""))  # 若无 scheme，使用外层
                            mid = mblog.get("id", "")
                            if content and link:
                                results.append({"content": content, "link": link, "mid": mid})
                                logging.info(f"成功提取嵌套帖子 (mid={mid})：{content[:50]}...")
                            else:
                                logging.warning(f"无法提取嵌套帖子内容或链接，跳过：{mblog}")
                else:
                    logging.info(f"跳过非 card_type=9 数据：card_type={card.get('card_type')}")
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logging.error(f"爬取第 {page} 页失败：{e}")
            continue
    return results


def fetch_full_text(mid, config=None, max_retries=3):
    """使用 Selenium 动态加载微博详情页并提取全文，带重试机制"""
    if config is None:
        raise ValueError("缺少微博配置信息")

    for attempt in range(max_retries):
        try:
            url = f"https://m.weibo.cn/status/{mid}"
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            logging.info(f"正在加载页面（尝试 {attempt + 1}/{max_retries}）：{url}")
            driver.get(url)
            time.sleep(3)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            text_div = (soup.select_one("div[class*='weibo-text']") or
                        soup.select_one("article.weibo-main") or
                        soup.select_one("div.card") or
                        soup.select_one("div.main-text") or
                        soup.select_one("div.weibo-detail"))

            driver.quit()

            if text_div:
                full_text = text_div.get_text(strip=True)
                if full_text:
                    logging.info(f"成功提取全文：{url}，内容：{full_text[:50]}...")
                    return full_text
                else:
                    logging.warning(f"提取到空内容：{url}")
                    return None
            else:
                logging.warning(f"未找到正文元素：{url}")
                return None
        except Exception as e:
            logging.error(f"动态加载失败（尝试 {attempt + 1}/{max_retries}）：{mid}，错误：{e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(1, 3))
            else:
                logging.error(f"达到最大重试次数，放弃：{mid}")
                return None


def extract_content_details(results, config=None):
    """提取 content 字段的细分类别并爬取全文"""
    if config is None:
        raise ValueError("缺少微博配置信息")

    def extract_text(html_content):
        if pd.isna(html_content):
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text().strip()

    def extract_topics(content):
        if pd.isna(content):
            return []
        return re.findall(r'#([^#]+)#', content)

    def extract_links(html_content):
        if pd.isna(html_content):
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        return [a["href"] for a in soup.find_all("a", href=True)]

    df = pd.DataFrame(results)
    df["initial_text"] = df["content"].apply(extract_text)
    df["topics"] = df["content"].apply(extract_topics)
    df["links"] = df["content"].apply(extract_links)
    df["pure_text"] = df["initial_text"]

    for index, row in df.iterrows():
        if "全文" in row["content"]:
            full_text = fetch_full_text(row["mid"], config)
            if full_text and full_text.strip():
                df.loc[index, "pure_text"] = full_text
                logging.info(f"更新 pure_text for mid={row['mid']}: {full_text[:50]}...")
            else:
                logging.warning(f"未能获取有效全文，保留初始文本 for mid={row['mid']}")
    df = df.drop(columns=["initial_text"])
    return df