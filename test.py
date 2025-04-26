import requests
import json
import hashlib
import re
import traceback
from config import SESSDATA  # 导入SESSDATA

# 测试参数
video_url = 'https://www.bilibili.com/video/BV1Qp4y1S7Qp?vd_source=d81daf5a496785b674d4a7ec46d91731&spm_id_from=333.788.videopod.episodes&p=5'


def get_aid_cid(video_url):
    print(f'开始获取视频aid和cid，URL: {video_url}')
    try:
        # 从URL中提取aid或bvid
        if 'av' in video_url:
            aid = re.search(r'/av(\d+)/*', video_url).group(1)
            api_url = f'https://api.bilibili.com/x/web-interface/view?aid={aid}'
        elif 'BV' in video_url:
            bvid = re.search(r'BV[a-zA-Z0-9]{10}', video_url).group(0)
            api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        else:
            print('错误：无法从URL中提取视频ID')
            return None, None
            
        print(f'请求API: {api_url}')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }
        if SESSDATA:
            headers['Cookie'] = f'SESSDATA={SESSDATA}'
        
        response = requests.get(api_url, headers=headers)
        print(f'响应状态码: {response.status_code}')
        # print(f'响应内容: {response.text}')
        
        if response.status_code != 200:
            print(f'错误：API请求失败，状态码：{response.status_code}')
            return None, None
            
        data = response.json()
        if data['code'] != 0:
            print(f'错误：API返回错误码 {data["code"]}，消息：{data["message"]}')
            return None, None
            
        aid = str(data['data']['aid'])
        # 获取指定P的cid
        p = int(re.search(r'p=(\d+)', video_url).group(1)) - 1  # 将p转换为索引
        cid = str(data['data']['pages'][p]['cid'])
        print(f'获取到 aid: {aid}, cid: {cid}')
        return aid, cid
    except Exception as e:
        print(f'获取aid和cid时发生错误: {str(e)}')
        return None, None

def get_play_list(start_url, cid, quality):
    print(f'开始获取视频播放列表，cid: {cid}, quality: {quality}')
    try:
        # 从URL中提取bvid
        bvid = re.search(r'BV[a-zA-Z0-9]{10}', start_url).group(0)
        # 使用新的API
        url_api = f'https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={bvid}&qn={quality}&type=&platform=html5&high_quality=1&fnver=0&fnval=4048&fourk=1'
        print(f'请求URL: {url_api}')
        
        headers = {
            'Referer': 'https://www.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Origin': 'https://www.bilibili.com'
        }
        if SESSDATA:
            headers['Cookie'] = f'SESSDATA={SESSDATA}'
            
        # print(f'请求头: {headers}')
        
        response = requests.get(url_api, headers=headers)
        print(f'响应状态码: {response.status_code}')
        # print(f'响应头: {response.headers}')
        # print(f'响应内容: {response.text}')
        
        if response.status_code != 200:
            print(f'错误：播放列表API请求失败，状态码：{response.status_code}')
            return []
            
        try:
            html = response.json()
            # print(f'解析后的JSON: {html}')
        except json.JSONDecodeError as e:
            print(f'错误：响应内容不是有效的JSON格式: {str(e)}')
            return []
        
        if html.get('code') != 0:
            print(f'错误：播放列表API返回错误码 {html.get("code")}，消息：{html.get("message")}')
            return []
            
        video_list = []
        data = html.get('data', {})
        
        # 检查不同的视频URL来源
        if 'durl' in data:
            for item in data['durl']:
                if 'url' in item:
                    video_list.append(item['url'])
        elif 'dash' in data:
            # 处理 DASH 格式的视频
            dash = data['dash']
            if 'video' in dash and dash['video']:
                # 获取最高质量的视频URL
                video_list.append(dash['video'][0]['baseUrl'])
            
        if not video_list:
            print('错误：未在响应中找到有效的视频URL')
            print('响应数据结构:', json.dumps(data, indent=2))
            return []
            
        print(f'找到 {len(video_list)} 个视频片段')
        return video_list
    except Exception as e:
        print(f'获取播放列表时发生错误: {str(e)}')
        print('错误详细信息:', traceback.format_exc())
        return []

# 执行测试
if __name__ == '__main__':
    # 先获取aid和cid
    aid, cid = get_aid_cid(video_url)
    if aid and cid:
        # 获取视频播放列表
        video_list = get_play_list(video_url, cid, '80')  # 80表示1080P
        print(f'最终获取到的视频列表: {video_list}') 