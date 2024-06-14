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


def download_image(url, save_path):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Image downloaded and saved to {save_path}")
        else:
            print(f"Failed to download image from {url} (Status code: {response.status_code})")
    except Exception as e:
        print(f"An error occurred while downloading {url}: {e}")


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


def process_article(article_response):
    article_soup = BeautifulSoup(article_response.content, 'html.parser')
    image_divs = article_soup.find_all('div', class_='field-name-field-image')
    article_name_tag = article_soup.find('h1', class_='text-center')
    article_name = article_name_tag.get_text(strip=True) if article_name_tag else 'No Title'
    article_name_cleaned = clean_filename(article_name)

    image_data = []

    # Create a directory for the article images and JSON files
    folder_path = f'img_{article_name_cleaned}'
    os.makedirs(folder_path, exist_ok=True)

    # Extract image source and metadata
    for index, div in enumerate(image_divs, start=1):
        img_tag = div.find('img')
        if img_tag and img_tag.has_attr('src'):
            src = img_tag['src']
            alt = img_tag.get('alt', '')

            # Save the JSON file for each image
            json_data = {
                'article_name': article_name,
                'src': src,
                'description': alt
            }
            json_filename = os.path.join(folder_path, f'img_{article_name_cleaned}_{index}_url.json')
            with open(json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)
            print(f"Image data successfully extracted and saved to {json_filename}")

            # Download the image
            image_filename = os.path.join(folder_path, f'img_{article_name_cleaned}_{index}.jpg')
            download_image(src, image_filename)

            time.sleep(1)  # Add a delay between requests


# 遍历多个页面
for page in range(1, 15):  # 根据需要调整页面范围
    url = search_url + str(page)
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
            # List to store image data
            image_data = []
            article_name = "unKnown"
            if article_response:
                process_article(article_response)


    else:
        print(f"Failed to retrieve page {page}")
