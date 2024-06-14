import os
import json
import requests


def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Image downloaded and saved to {save_path}")
        else:
            print(f"Failed to download image from {url} (Status code: {response.status_code})")
    except Exception as e:
        print(f"An error occurred while downloading {url}: {e}")


def process_json_files(folder_path, image_save_folder):
    # 确保保存图片的文件夹存在
    os.makedirs(image_save_folder, exist_ok=True)

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                for item in data:
                    url = item.get('src')
                    if url and url.lower().endswith('.jpg'):
                        # 提取图片文件名
                        image_name = os.path.basename(url)
                        save_path = os.path.join(image_save_folder, image_name)
                        download_image(url, save_path)
                    else:
                        print(f"No valid JPEG URL found in item: {item}")


# 指定 JSON 文件所在的文件夹路径和图片保存的文件夹路径
json_folder_path = 'path/to/json/folder'
image_save_folder = 'path/to/save/images'

# 处理 JSON 文件并下载图片
process_json_files(json_folder_path, image_save_folder)
