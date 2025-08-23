
import os
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, date
import zhdate  # 农历库，需要安装: pip install zhdate
import concurrent.futures
import threading
import time

# 从测试号信息获取
appID = os.environ.get("WECHAT_APP_ID", "wxfa76619e96951810")
appSecret = os.environ.get("WECHAT_APP_SECRET", "3d32b71d5cfc17a39cfe30d83b092755")
# 收信人ID列表（支持多个收件人）
openId_list = [
    "odUBK7GG1cfl2sa5zCJowIRP-VEA",  # 第一个收件人
    "odUBK7Byrzx22RxyqT-IijtNAO2c"   # 第二个收件人
]
# 天气预报模板ID（请更新为新创建的模板ID）
weather_template_id = os.environ.get("WECHAT_TEMPLATE_ID", "Fs5N_zwXqzU5yow5vKAz6nWeCXNSdf_gaYrynMzAmvE")

# 城市配置
CITY_CONFIG = {
    "101210204009": "🏠 home卧龙",
    "101191104007": "🏫 University常大", 
    "101190401006": "🏫 University苏科大",
    "101210203004": "🏠 home吴村"
}

# 恋爱纪念日配置
LOVE_START_DATE = date(2023, 8, 27)

# 生日配置（农历）
BABY_BIRTHDAY = (9, 11)  # 农历9月11日
MY_BIRTHDAY = (12, 20)   # 农历腊月二十

def get_weather(city_id):
    """获取指定城市ID的天气信息"""
    try:
        url = f"https://forecast.weather.com.cn/town/weather1dn/{city_id}.shtml"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        print(f"🌐 正在请求: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"📡 响应状态码: {resp.status_code}")
        resp.encoding = 'utf-8'
        text = resp.text
        print(f"📄 页面内容长度: {len(text)} 字符")
        
        # 从页面标题获取城市名称
        soup = BeautifulSoup(text, 'html.parser')
        title_element = soup.find('title')
        title = title_element.text if title_element else ""
        city_name = CITY_CONFIG.get(city_id, city_id)
        
        # 解析JavaScript中的天气数据
        print(f"🔍 正在搜索JavaScript天气数据...")
        forecast_match = re.search(r'var forecast_default = ({.*?});', text)
        if forecast_match:
            print(f"✅ 找到JavaScript数据: {forecast_match.group(1)[:100]}...")
            forecast_data = json.loads(forecast_match.group(1))
            print(f"📊 解析的天气数据: {forecast_data}")
            
            current_temp = forecast_data.get('temp', '--')
            weather_desc = forecast_data.get('weather', '--')
            wind_info = forecast_data.get('wind', '--')
            humidity = forecast_data.get('humidity', '--')
            max_temp = forecast_data.get('maxTemp', '--')
            min_temp = forecast_data.get('minTemp', '--')
            
            temp_range = f"{min_temp}°C~{max_temp}°C"
            
            # 解析生活指数
            life_advice = parse_life_index(text)
            
            return {
                'city_name': city_name,
                'current_temp': f"{current_temp}°C",
                'weather': weather_desc,
                'temp_range': temp_range,
                'wind': wind_info,
                'humidity': f"{humidity}%",
                'clothing_advice': life_advice['clothing'],
                'uv_advice': life_advice['uv'],
                'protection_advice': life_advice['protection']
            }
        else:
            # 如果无法解析JavaScript数据，使用默认值
            print(f"❌ 未找到JavaScript天气数据，使用默认值")
            title_element = soup.find('title')
            page_title = title_element.text if title_element else '无标题'
            print(f"🔎 页面标题: {page_title}")
            print(f"🔎 页面前500字符: {text[:500]}")
            return {
                'city_name': city_name,
                'current_temp': '--°C',
                'weather': '晴',
                'temp_range': '--°C~--°C',
                'wind': '微风',
                'humidity': '--%',
                'clothing_advice': '适中穿着',
                'uv_advice': '紫外线中等',
                'protection_advice': '建议防晒'
            }
            
    except Exception as e:
        print(f"获取天气信息失败: {e}")
        city_name = CITY_CONFIG.get(city_id, city_id)
        return {
            'city_name': city_name,
            'current_temp': '--°C',
            'weather': '晴',
            'temp_range': '--°C~--°C',
            'wind': '微风',
            'humidity': '--%',
            'clothing_advice': '适中穿着',
            'uv_advice': '紫外线中等',
            'protection_advice': '建议防晒'
        }


def parse_life_index(html_text):
    """解析生活指数"""
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # 尝试从生活指数区域获取信息
        life_section = soup.find('div', class_='weather_shzs')
        
        clothing_advice = "适中穿着"
        uv_advice = "紫外线中等"
        protection_advice = "建议防晒"
        
        if life_section:
            # 尝试解析穿衣指数，使用更安全的方式
            try:
                # 直接使用字符串搜索来判断穿衣建议
                page_text = str(life_section)
                if '热' in page_text or '短袖' in page_text or '短裤' in page_text:
                    clothing_advice = "热：穿短袖短裤"
                elif '凉快' in page_text or '薄长袖' in page_text:
                    clothing_advice = "凉快：穿薄长袖"
                elif '温暖' in page_text or '长袖' in page_text:
                    clothing_advice = "温暖：穿长袖衣物"
                elif '寒冷' in page_text or '厚外套' in page_text:
                    clothing_advice = "寒冷：穿厚外套"
                
                # 判断紫外线强度
                if '紫外线很强' in page_text or '紫外线强' in page_text:
                    uv_advice = "紫外线很强"
                    protection_advice = "必须防晒：打伞+防晒霜"
                elif '紫外线中等' in page_text or '紫外线中' in page_text:
                    uv_advice = "紫外线中等"
                    protection_advice = "建议防晒：戴帽子"
                elif '紫外线弱' in page_text or '紫外线较弱' in page_text:
                    uv_advice = "紫外线较弱"
                    protection_advice = "无需特别防晒"
            except Exception as e:
                print(f"解析生活指数失败: {e}")
        
        return {
            'clothing': clothing_advice,
            'uv': uv_advice,
            'protection': protection_advice
        }
        
    except Exception as e:
        print(f"解析生活指数失败: {e}")
        return {
            'clothing': "适中穿着",
            'uv': "紫外线中等",
            'protection': "建议防晒"
        }

def calculate_love_days():
    """计算恋爱天数"""
    today = date.today()
    love_days = (today - LOVE_START_DATE).days
    return love_days

def get_lunar_info():
    """获取农历信息"""
    try:
        today = datetime.now()
        lunar_date = zhdate.ZhDate.from_datetime(today)
        return f"农历{lunar_date.chinese()}"
    except Exception as e:
        print(f"获取农历信息失败: {e}")
        return "农历信息获取失败"

def calculate_birthday_countdown():
    """计算生日倒计时"""
    try:
        today = datetime.now()
        current_year = today.year
        
        # 计算宝宝的生日倒计时（农历9月11日）
        try:
            # 尝试今年的农历生日
            baby_lunar_this_year = zhdate.ZhDate(current_year, BABY_BIRTHDAY[0], BABY_BIRTHDAY[1])
            baby_solar_this_year = baby_lunar_this_year.to_datetime().date()
            
            if baby_solar_this_year < today.date():
                # 如果今年的生日已过，计算明年的
                baby_lunar_next_year = zhdate.ZhDate(current_year + 1, BABY_BIRTHDAY[0], BABY_BIRTHDAY[1])
                baby_solar_next_year = baby_lunar_next_year.to_datetime().date()
                baby_days = (baby_solar_next_year - today.date()).days
            else:
                baby_days = (baby_solar_this_year - today.date()).days
                
        except Exception as e:
            print(f"计算宝宝生日失败: {e}")
            baby_days = "--"
        
        # 计算我的生日倒计时（农历腊月20日）
        try:
            # 尝试今年的农历生日
            my_lunar_this_year = zhdate.ZhDate(current_year, MY_BIRTHDAY[0], MY_BIRTHDAY[1])
            my_solar_this_year = my_lunar_this_year.to_datetime().date()
            
            if my_solar_this_year < today.date():
                # 如果今年的生日已过，计算明年的
                my_lunar_next_year = zhdate.ZhDate(current_year + 1, MY_BIRTHDAY[0], MY_BIRTHDAY[1])
                my_solar_next_year = my_lunar_next_year.to_datetime().date()
                my_days = (my_solar_next_year - today.date()).days
            else:
                my_days = (my_solar_this_year - today.date()).days
                
        except Exception as e:
            print(f"计算我的生日失败: {e}")
            my_days = "--"
        
        return {
            'baby_birthday': baby_days,
            'my_birthday': my_days
        }
        
    except Exception as e:
        print(f"计算生日倒计时失败: {e}")
        return {
            'baby_birthday': "--",
            'my_birthday': "--"
        }

def get_weather_emoji(weather):
    """根据天气状况返回对应的emoji"""
    weather_emoji_map = {
        '晴': '☀️',
        '多云': '⛅',
        '阴': '☁️',
        '阵雨': '🌦️',
        '小雨': '🌧️',
        '中雨': '🌧️',
        '大雨': '🌧️',
        '雨': '🌧️',
        '雷阵雨': '🌩️',
        '雷阵阵雨': '🌩️',
        '雪': '🌨️',
        '小雪': '🌨️',
        '中雪': '🌨️',
        '大雪': '🌨️',
        '霧': '🌫️',
        '雾': '🌫️',
        '沙尘': '🌪️',
        '沙暴': '🌪️',
        '高温': '🌡️',
        '低温': '❄️'
    }
    
    for key, emoji in weather_emoji_map.items():
        if key in weather:
            return emoji
    return '🌤️'  # 默认天气emoji

def get_daily_love():
    """获取每日恋爱寄语"""
    love_quotes = [
        "💕 今天也要好好爱你哦！",
        "✨ 和你在一起的每一天都是美好的",
        "🌹 想你是我每天必做的事情",
        "💖 希望我们能一直这样幸福下去",
        "🌈 你是我的小幸运，也是我的大满足",
        "🌟 每个有你的日子都充满阳光",
        "💝 爱你不是三分钟热度，而是永恒的温度"
    ]
    
    # 根据日期选择不同的寄语
    today = datetime.now()
    quote_index = today.day % len(love_quotes)
    return love_quotes[quote_index]
def get_access_token():
    # 获取access token的url
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}' \
        .format(appID.strip(), appSecret.strip())
    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    return access_token


def get_all_cities_weather():
    """获取所有城市的天气信息，返回每个城市的独立数据"""
    cities_data = {}
    city_keys = ["city1", "city2", "city3", "city4"]
    
    for i, (city_id, city_name) in enumerate(CITY_CONFIG.items()):
        print(f"🌍 正在获取 {city_name} 的天气信息...")
        try:
            weather_data = get_weather(city_id)
            city_key = city_keys[i]
            
            # 构建城市名称和天气详情分开的信息（不包含emoji，在模板中添加）
            city_name = weather_data['city_name']
            weather_details = f"{weather_data['weather']} {weather_data['current_temp']} {weather_data['temp_range']} {weather_data['clothing_advice']}"
            
            # 每个城市使用两个字段
            cities_data[f"{city_key}_name"] = city_name
            cities_data[f"{city_key}_weather"] = weather_details
            print(f"✅ {city_key}: {weather_data['city_name']} - {weather_data['weather']} {weather_data['current_temp']}")
        except Exception as e:
            print(f"获取 {city_name} 天气失败: {e}")
            city_key = city_keys[i]
            cities_data[city_key] = f"{city_name}\n😔 数据获取失败，请稍后再试"
    
    return cities_data
    
def send_weather(access_token, cities_weather_data):
    """发送天气推送消息"""
    try:
        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        
        # 计算恋爱天数
        love_days = calculate_love_days()
        
        # 计算生日倒计时
        birthday_info = calculate_birthday_countdown()
        
        # 获取农历信息
        lunar_info = get_lunar_info()
        
        # 获取每日寄语
        daily_love = get_daily_love()
        
        # 获取每个城市的名称和天气详情（分开存储）
        city1_name = cities_weather_data.get("city1_name", "home卧龙")
        city1_weather = cities_weather_data.get("city1_weather", "数据获取失败")
        city2_name = cities_weather_data.get("city2_name", "University常大")
        city2_weather = cities_weather_data.get("city2_weather", "数据获取失败")
        city3_name = cities_weather_data.get("city3_name", "University苏科大")
        city3_weather = cities_weather_data.get("city3_weather", "数据获取失败")
        city4_name = cities_weather_data.get("city4_name", "home吴村")
        city4_weather = cities_weather_data.get("city4_weather", "数据获取失败")
        
        # 构建日期信息
        date_info = f"{today_str} {lunar_info}"
        
        # 构建一个包含所有信息的综合寄语
        comprehensive_message = f"今天是我们在一起的第{love_days}天 宝宝生日还有{birthday_info['baby_birthday']}天 我的生日还有{birthday_info['my_birthday']}天 {daily_love}"
        
        # 打印详细的调试信息 - 10字段结构
        print(f"\n📋 详细字段信息 (10字段结构):")
        print(f"🏠 city1_name: '{city1_name}' (长度: {len(city1_name)})")
        print(f"🌤️ city1_weather: '{city1_weather}' (长度: {len(city1_weather)})")
        print(f"🏫 city2_name: '{city2_name}' (长度: {len(city2_name)})")
        print(f"🌤️ city2_weather: '{city2_weather}' (长度: {len(city2_weather)})")
        print(f"🏫 city3_name: '{city3_name}' (长度: {len(city3_name)})")
        print(f"🌤️ city3_weather: '{city3_weather}' (长度: {len(city3_weather)})")
        print(f"🏠 city4_name: '{city4_name}' (长度: {len(city4_name)})")
        print(f"🌤️ city4_weather: '{city4_weather}' (长度: {len(city4_weather)})")
        print(f"💕 love_days: '今天是我们在一起的第{love_days}天' (长度: {len(f'今天是我们在一起的第{love_days}天')})")
        print(f"🎂 birthday_info: '宝宝生日还有{birthday_info['baby_birthday']}天 我还有{birthday_info['my_birthday']}天生日' (长度: {len(f'宝宝生日还有{birthday_info["baby_birthday"]}天 我还有{birthday_info["my_birthday"]}天生日')})")
        
        # 打印收件人信息
        print(f"📧 将向 {len(openId_list)} 个收件人并发送进消息（提高速度）")
        for i, openId in enumerate(openId_list, 1):
            print(f"  {i}. {openId}")
        
        # 定义单个收件人发送函数
        def send_to_single_user(openId, user_index):
            """向单个用户发送消息"""
            print(f"📤 正在向收件人 {user_index} ({openId}) 发送消息...")
            
            # 使用新的10字段结构：每个城市2个字段 + 恋爱信息 + 生日信息
            body = {
                "touser": openId.strip(),
                "template_id": weather_template_id.strip(),
                "url": "https://weixin.qq.com",
                "data": {
                    "city1_name": {
                        "value": city1_name
                    },
                    "city1_weather": {
                        "value": city1_weather
                    },
                    "city2_name": {
                        "value": city2_name
                    },
                    "city2_weather": {
                        "value": city2_weather
                    },
                    "city3_name": {
                        "value": city3_name
                    },
                    "city3_weather": {
                        "value": city3_weather
                    },
                    "city4_name": {
                        "value": city4_name
                    },
                    "city4_weather": {
                        "value": city4_weather
                    },
                    "love_days": {
                        "value": f"今天是我们在一起的第{love_days}天"
                    },
                    "birthday_info": {
                        "value": f"宝宝生日还有{birthday_info['baby_birthday']}天 我还有{birthday_info['my_birthday']}天生日"
                    }
                }
            }
            
            try:
                send_url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
                response = requests.post(send_url, json=body, timeout=10)
                result = response.json()
                
                if result.get('errcode') == 0:
                    print(f"  ✅ 收件人 {user_index} 发送成功！")
                    return {'user_index': user_index, 'openId': openId, 'success': True, 'result': result}
                else:
                    print(f"  ❌ 收件人 {user_index} 发送失败: {result}")
                    return {'user_index': user_index, 'openId': openId, 'success': False, 'result': result}
                    
            except Exception as e:
                print(f"  ❌ 收件人 {user_index} 发送异常: {e}")
                return {'user_index': user_index, 'openId': openId, 'success': False, 'error': str(e)}
        
        # 开始计时
        start_time = time.time()
        
        # 使用线程池并发发送
        success_count = 0
        fail_count = 0
        results = []
        
        print(f"\n🚀 开始并发发送...")
        
        # 创建线程池，最大线程数为收件人数量（最多5个）
        max_workers = min(len(openId_list), 5)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有发送任务
            future_to_user = {
                executor.submit(send_to_single_user, openId, i): (openId, i) 
                for i, openId in enumerate(openId_list, 1)
            }
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(future_to_user):
                openId, user_index = future_to_user[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result['success']:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"  ❌ 收件人 {user_index} 处理异常: {e}")
                    fail_count += 1
                    results.append({'user_index': user_index, 'openId': openId, 'success': False, 'error': str(e)})
        
        # 结束计时
        end_time = time.time()
        total_time = end_time - start_time
        
        # 汇总结果
        print(f"\n📊 发送结果汇总：")
        print(f"  ✅ 成功: {success_count} 人")
        print(f"  ❌ 失败: {fail_count} 人")
        print(f"  📊 总计: {len(openId_list)} 人")
        print(f"  ⏱️ 总耗时: {total_time:.2f} 秒")
        print(f"  🚀 平均每人: {total_time/len(openId_list):.2f} 秒")
        
        if success_count > 0:
            print(f"✅ 有 {success_count} 人成功收到天气推送！")
        
        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'total_count': len(openId_list),
            'total_time': total_time,
            'avg_time_per_user': total_time / len(openId_list),
            'results': results
        }
        
    except Exception as e:
        print(f"发送消息失败: {e}")
        return None



def weather_report_all_cities():
    """一次性发送所有城市天气推送"""
    print("🎆 开始获取所有城市天气信息...")
    
    # 1.获取access_token
    access_token = get_access_token()
    if not access_token:
        print("❌ 获取access_token失败！")
        return
    
    print(f"✅ 获取access_token成功")
    
    # 2.获取所有城市天气信息
    cities_weather_data = get_all_cities_weather()
    print(f"🌤️ 所有城市天气数据: {cities_weather_data}")
    
    # 3.发送一条包含所有城市信息的推送
    try:
        result = send_weather(access_token, cities_weather_data)
        print("\n🎉 所有城市天气推送完成！")
        return result
    except Exception as e:
        print(f"❌ 发送推送时发生错误: {e}")
        return None

def weather_report(city_id=None):
    """单城市天气推送（兼容原有接口）- 现在使用多城市格式"""
    print("⚠️ 注意：weather_report已废弃，请使用weather_report_all_cities()")
    # 直接调用多城市推送
    return weather_report_all_cities()



if __name__ == '__main__':
    print("🌈 微信天气推送系统 v2.1 - 支持多收件人")
    print("📍 支持多城市推送：")
    for city_id, city_name in CITY_CONFIG.items():
        print(f"  - {city_name}")
    print(f"💕 恋爱纪念日：{LOVE_START_DATE}")
    print(f"📅 今天是在一起的第 {calculate_love_days()} 天")
    print(f"📧 收件人数量：{len(openId_list)} 人")
    for i, openId in enumerate(openId_list, 1):
        print(f"  {i}. {openId}")
    print()
    
    # 执行合并推送（一次发送所有城市）
    weather_report_all_cities()
    
    # 如果只想推送单个城市，可以使用：
    # weather_report("101210204009")  # 只推送卧龙
