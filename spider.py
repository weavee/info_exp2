import json

import requests
from bs4 import BeautifulSoup
import time
import re
import os

# 清除代理设置
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 目标 URL
base_url = "https://www.un.org/zh/articles-by-property/2936"
search_url = base_url + "?page="


# 函数用于清理文件名
def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)


# 自定义请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


# 函数用于发送请求并处理错误
def get_response(url, retries=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            else:
                print(f"Error {response.status_code} for URL: {url}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, retrying ({attempt + 1}/{retries})...")
            time.sleep(2)  # 等待一段时间再重试
    return None


# 遍历多个页面
# for page in range(20, 30):  # 根据需要调整页面范围
#     url = search_url + str(page)
if 1 == 1:
    url = base_url
    response = get_response(url)

    if response:
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('div', class_='col-xs-12 col-sm-6 col-md-4 col-lg-4')

        for article in articles:
            title = article.find('h3').text.strip()
            match_content = article.find('p').text.strip()
            article_url = "https://www.un.org" + article.find('a')['href']

            # 获取文章详细内容
            article_response = get_response(article_url)
            if article_response:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                # 获取文章内容
                paragraphs = article_soup.find('div', class_='article-body').find_all('p')
                article_content = "\n".join([p.text.strip() for p in paragraphs])

                # 获取日期
                if len(paragraphs) > 1:
                    date = paragraphs[1].text.strip()
                    if len(date) > len("2022年10月10日"):
                        continue
                else:
                    # date = "Date not found"
                    continue
            else:
                article_content = "Failed to retrieve article content"
                date = "Date not found"

            if len(date)==0:
                continue
            # 创建结果字典
            result = {
                    'Title': title,
                    'Description': match_content,
                    'URL': article_url,
                    'Date': date,
                    'Content': article_content
            }

            # 清理标题以创建有效的文件名
            filename = clean_filename(f"{title}.json")


            # 保存结果到单独的JSON文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

            print(f"Data for '{title}' has been saved to {filename}")
            time.sleep(1)  # 防止请求过于频繁
    else:
        print(f"Failed to retrieve page {page}")
