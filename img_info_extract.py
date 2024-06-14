import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
import os
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket  # 使用websocket_client


appid = "3546bb92"    #填写控制台中获取的 APPID 信息
api_secret = "NmJjZWUxMTAyNjRjZTI2YTdhYjg5YWVk"   #填写控制台中获取的 APISecret 信息
api_key ="90e2847a516fa2dd8760dd8e8f19280c"    #填写控制台中获取的 APIKey 信息



imageunderstanding_url = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"#云端环境的服务地址



class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, imageunderstanding_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(imageunderstanding_url).netloc
        self.path = urlparse(imageunderstanding_url).path
        self.ImageUnderstanding_url = imageunderstanding_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.ImageUnderstanding_url + '?' + urlencode(v)
        #print(url)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws,one,two):
    print(" ")


# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, question= ws.question ))
    ws.send(data)


# 收到websocket消息的处理
def on_message(ws, message):
    #print(message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content, end="")
        global answer
        answer += content
        # print(1)
        if status == 2:
            ws.close()


def gen_params(appid, question):
    """
    通过appid和用户的提问来生成请参数
    """

    data = {
        "header": {
            "app_id": appid
        },
        "parameter": {
            "chat": {
                "domain": "image",
                "temperature": 0.5,
                "top_k": 4,
                "max_tokens": 2028,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
}

    return data


def main(appid, api_key, api_secret, imageunderstanding_url,question):

    wsParam = Ws_Param(appid, api_key, api_secret, imageunderstanding_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = appid
    #ws.imagedata = imagedata
    ws.question = question
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


def getText(role, content, text):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text


def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length


def checklen(text):
    #print("text-content-tokens:", getlength(text[1:]))
    while (getlength(text[1:])> 8000):
        del text[1]
    return text

def call_api(image_path, article_name):
    global answer  # 声明为全局变量
    imagedata = open(image_path, 'rb').read()
    text = [{"role": "user", "content": str(base64.b64encode(imagedata), 'utf-8'), "content_type": "image"}]
    Input = f"该图片是围绕'{article_name}'主题的，请从对象、环境、场景、人物等多角度详细描述这个图片，提取图片的主要特征，50字到100字"  # prompt
    question = checklen(getText("user", Input,text))
    answer = ""
    main(appid, api_key, api_secret, imageunderstanding_url, question)
    getText("assistant", answer, text)
    return answer


def process_image_folder(folder_path):
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg"):
            image_path = os.path.join(folder_path, filename)
            json_filename = filename.replace('.jpg', '_url.json')
            json_path = os.path.join(folder_path, json_filename)

            # 调用 API 获取返回结果
            api_result = call_api(image_path, filename)

            if api_result is not None:
                # 读取现有的 JSON 文件
                with open(json_path, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)

                # 更新 JSON 数据
                data['extract_info'] = api_result

                # 写入更新后的 JSON 数据
                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)

                print(f"API result successfully written to {json_path}")
            else:
                print(f"Failed to get API result for {image_path}")


def traverse_folders(root_folder_path):
    for folder_name in os.listdir(root_folder_path):
        folder_path = os.path.join(root_folder_path, folder_name)
        if os.path.isdir(folder_path):
            process_image_folder(folder_path)



if __name__ == '__main__':
    # 指定根文件夹路径
    root_folder_path = 'img_data_set'

    # 遍历文件夹并处理图片
    traverse_folders(root_folder_path)

    #text.clear
    # while(1):
    #     imagedata = open("img_“把握时机”：团结一致、姐妹互助_1.jpg", 'rb').read()
    #     text = [{"role": "user", "content": str(base64.b64encode(imagedata), 'utf-8'), "content_type": "image"}]
    #     Input = "请从对象、环境、场景、人物等多角度详细描述这个图片，提取图片的主要特征，50字到100字"  # prompt
    #     question = checklen(getText("user",Input))
    #     answer = ""
    #     main(appid, api_key, api_secret, imageunderstanding_url, question)
    #     getText("assistant", answer)
        # print(str(text))

