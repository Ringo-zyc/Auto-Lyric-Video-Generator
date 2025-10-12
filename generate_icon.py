# generate_icon.py
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from io import BytesIO

# 创建 256x256 图标
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 绘制音符图标
# 绘制圆形背景
draw.ellipse((10, 10, size-10, size-10), fill=(75, 0, 130, 255))  # 紫色背景

# 绘制音符主体
draw.rectangle((70, 70, 150, 180), fill=(255, 255, 255, 255))  # 白色音符主体
draw.rectangle((150, 110, 180, 140), fill=(255, 255, 255, 255))  # 音符尾部
draw.ellipse((160, 60, 200, 100), fill=(255, 255, 255, 255))  # 音符头部

# 保存为 ICO 文件
img.save('app_icon.ico', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])