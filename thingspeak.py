import os
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pytz
import pyimgur
from imgurpython import ImgurClient
from PIL import Image

# from imgurpython import ImgurClient


class Thingspeak():
    def __init__(self):
        self.access_token = os.environ.get('imgur_access_token', '')
        self.refresh_token = os.environ.get('imgur_refresh_token', '')
        self.client_id = os.environ.get('imgur_client_id', '')
        self.client_secret = os.environ.get('imgur_client_secret', '')

    def get_data_from_thingspeak(self, channel_id, api_read_key):
        url = 'https://thingspeak.com/channels/{channel_id}/feed.json?api_key={api_read_key}'.format(
            channel_id=channel_id, api_read_key=api_read_key)
        data = requests.get(url).json()
        if data.get('error') == 'Not Found':
            return 'Not Found', 'Not Found'
        time_list = list()
        entry_id_list = list()
        bpm_list = list()
        for data in data['feeds']:
            time_list.append(data.get('created_at'))
            entry_id_list.append(data.get('entry_id'))
            bpm_list.append(data.get('field1'))

        # 換成台灣時間
        tw_time_list = self.format_time(time_list)
        return tw_time_list, bpm_list

    # 解析时间字符串并转换为台湾时间
    def format_time(self, time_list):
        taiwan_tz = pytz.timezone('Asia/Taipei')
        tw_time_list = []
        for timestamp in time_list:
            dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
            dt_utc = pytz.utc.localize(dt)
            dt_taiwan = dt_utc.astimezone(taiwan_tz)
            tw_time_list.append(dt_taiwan.strftime('%Y-%m-%d %H:%M:%S'))
        return tw_time_list

    # 從 JSON 數據中提取數字並繪製折線圖
    def gen_chart(self, time_list, bpm_list):
        print(time_list, bpm_list)
        plt.figure(figsize=(12, 15))  # 設置圖片尺寸為 10x6
        bpm_list = [float(value) for value in bpm_list]
        # 绘制图表
        plt.plot(time_list, bpm_list, 'r-o')
        plt.xlabel('Time')
        plt.ylabel('BPM')
        plt.title('Thingspeak')
        plt.xticks(rotation=45)
        plt.savefig('chart.jpg', format='jpg')
        return

    def update_photo_size(self):
        img = Image.open('chart.jpg')   # 開啟圖片
        img2 = img.resize((240, 240))       # 調整圖片尺寸為 200x200
        img2.save('pre_chart.jpg')

    def refresh_access_token(self, client_id, client_secret, refresh_token):
        url = "https://api.imgur.com/oauth2/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        response = requests.post(url, data=payload)

        if response.status_code == 200:
            new_tokens = response.json()
            print("Access token refreshed successfully.")
            return new_tokens["access_token"], new_tokens["refresh_token"]
        else:
            print(f"Failed to refresh token. Status code: {response.status_code}")
            print(response.json())
            return None, None

    def upload_to_imgur_with_refresh(self):
        url = "https://api.imgur.com/3/image"
        res_url = dict()
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        for path_name in ['chart', 'pre_chart']:
            image_path = f"{path_name}.jpg"
            with open(image_path, "rb") as image_file:
                payload = {
                    "image": image_file,
                }
                response = requests.post(url, headers=headers, files=payload)

            if response.status_code == 401:  # Unauthorized, likely due to expired token
                print("Access token expired. Refreshing token...")
                new_access_token, new_refresh_token = self.refresh_access_token(
                    self.client_id, self.client_secret, self.refresh_token)
                if new_access_token:
                    return self.upload_to_imgur_with_refresh()
                else:
                    print("Failed to refresh access token.")
                    return None
            elif response.status_code == 200:
                print("Image uploaded successfully:")
                res_url[path_name] = response.json().get("data").get("link")
                print(response.json().get("data").get("link"))
            else:
                print(f"Failed to upload image. Status code: {response.status_code}")
                # print(response.json())
        return res_url

    # 上傳圖片到 Imgur
    # def upload_to_imgur(self):
    #     try:
    #         result_dict = dict()
    #         for path_name in ['chart', 'pre_chart']:
    #             CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
    #             CLIENT_ID = '0a91ee5aea1a67a'
    #             print("CLIENT_ID", CLIENT_ID)
    #             PATH = f"{path_name}.jpg" #A Filepath to an image on your computer"
    #             # title = "Uploaded with PyImgur"
    #             # 檢查檔案是否存在
    #             if os.path.exists(PATH):
    #                 print(f"檔案存在：{PATH}")
    #             else:
    #                 print(f"檔案不存在：{PATH}")
    #             headers = {"Authorization": f"Client-ID {CLIENT_ID}"}
    #             with open(PATH, "rb") as file:
    #                 response = requests.post(
    #                     "https://api.imgur.com/3/image",
    #                     headers=headers,
    #                     files={"image": file}
    #                 )
    #             if response.status_code == 200:
    #                 print("上傳成功！")
    #                 data = response.json()["data"]
    #                 result_dict[path_name] = data['link']
    #                 print(f"圖片網址: {data['link']}")
    #             else:
    #                 print("上傳失敗！")
    #                 print(f"狀態碼: {response.status_code}")
    #                 print(f"回應內容: {response.text}")
    #                 response.raise_for_status()
    #         return result_dict
    #         # result_dict = dict()
    #         # CLIENT_ID = os.environ.get('IMGUR_CLIENT_ID')
    #         # CLIENT_ID = '0a91ee5aea1a67a'
    #         # print("CLIENT_ID", CLIENT_ID)
    #         # im = pyimgur.Imgur(CLIENT_ID)
    #         # PATH = 'chart.jpg'
    #         # title = "Uploaded with PyImgur"
    #         # uploaded_image = im.upload_image(PATH, title=title)
    #         # print("uploaded_image", uploaded_image)
    #         # print("uploaded_image link", str(uploaded_image.link))
    #         # print("type uploaded_image link", type(uploaded_image.link))
    #         # image_url = uploaded_image.link
    #         # result_dict['chart'] = image_url
    #         # PATH = "pre_chart.jpg" #A Filepath to an image on your computer"
    #         # title = "Uploaded with pre_PyImgur"

    #         # pre_im = pyimgur.Imgur(CLIENT_ID)
    #         # uploaded_pre_image = pre_im.upload_image(PATH, title=title)
    #         # # print(uploaded_image.title)
    #         # pre_image_url = uploaded_pre_image.link
    #         # result_dict['pre_chart'] = pre_image_url
    #         # return  result_dict
    #     except Exception as e:
    #         # 捕获错误并打印详细信息
    #         print(f"Error during upload: {str(e)}")
    #         response = getattr(e, 'response', None)
    #         if response:
    #             print(f"Response Text: {response.text}")
    #         raise


if __name__ == "__main__":
    # imgur upload
    # https://medium.com/front-end-augustus-study-notes/imgur-api-3a41f2848bb8

    res = Thingspeak().upload_to_imgur_with_refresh()
    print(res)
