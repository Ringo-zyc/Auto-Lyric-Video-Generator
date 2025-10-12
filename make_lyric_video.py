import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from PIL.Image import Resampling
import pylrc
import moviepy.editor as mpy
import subprocess

# --- 1. 项目设置与资源定义 ---
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_SIZE = (VIDEO_WIDTH, VIDEO_HEIGHT)

# --- 文件路径 ---
SONG_FOLDER_NAME = "JODY - 山下達郎"
SONG_FOLDER = os.path.join("Songs", SONG_FOLDER_NAME)
OUTPUT_FOLDER = "Output"
COVER_IMAGE_PATH = os.path.join(SONG_FOLDER, "封面.png")
SONG_PATH = os.path.join(SONG_FOLDER, "jody.mp3")
LYRICS_PATH = os.path.join(SONG_FOLDER, "JODY - 山下達郎.LRC")
FONTS = {
    "regular": os.path.join("Fonts", "NotoSansJP-Regular.ttf"),
    "bold": os.path.join("Fonts", "NotoSansJP-Bold.ttf")
}
OUTPUT_VIDEO_PATH = os.path.join(OUTPUT_FOLDER, f"{SONG_FOLDER_NAME}.mp4")

# --- 视觉效果参数 ---
COLOR_LYRIC_STANDARD = (255, 255, 255, 180)
COLOR_LYRIC_HIGHLIGHT = (255, 255, 255, 255)
COLOR_LYRIC_GLOW = (255, 255, 255, 90)
SHADOW_COLOR = (0, 0, 0, 160)
BACKGROUND_BLUR_RADIUS = 60
COVER_SIZE_RATIO = 0.5
LYRICS_AREA_X = 500
LYRICS_AREA_WIDTH = VIDEO_WIDTH - LYRICS_AREA_X - int(VIDEO_WIDTH * 0.08)

# --- 字体加载 ---
FONT_SIZE_LYRIC = 50
FONT_SIZE_SMALL = 38
try:
    FONT_LYRIC = ImageFont.truetype(FONTS["bold"], FONT_SIZE_LYRIC)
    FONT_SMALL = ImageFont.truetype(FONTS["regular"], FONT_SIZE_SMALL)
except IOError as e:
    print(f"错误: 字体文件加载失败。请确保文件存在且路径正确。\n详细信息: {e}")
    exit()
LINE_SPACING = 20
LYRIC_SPACING = 35


# --- 2. 工具函数 ---
def parse_lyrics(audio_duration):
    """解析LRC文件并计算每句歌词的结束时间"""
    try:
        with open(LYRICS_PATH, "r", encoding="utf-8") as f:
            lrc_string = f.read()
    except Exception as e:
        print(f"读取歌词文件 '{LYRICS_PATH}' 时出错: {e}");
        return None
    subs = pylrc.parse(lrc_string)
    if not subs: return []
    processed_lyrics = []
    for i, sub in enumerate(subs):
        text = sub.text.strip()
        if not text or (i > 0 and text == processed_lyrics[-1]["text"]): continue
        end_time = subs[i + 1].time if i + 1 < len(subs) else audio_duration
        processed_lyrics.append({"start": sub.time, "end": end_time, "duration": end_time - sub.time, "text": text})
    print(f"解析完成，共 {len(processed_lyrics)} 行歌词。")
    return processed_lyrics


def wrap_text(text, font, max_width):
    """改进的智能换行函数"""
    if ' ' not in text:  # 中文、日文等无空格语言
        lines, line = [], ""
        for char in text:
            test_line = line + char
            if font.getbbox(test_line)[2] <= max_width:
                line = test_line
            else:
                lines.append(line);
                line = char
        if line: lines.append(line)
        return lines
    # 英文等有空格语言
    lines, words = [], text.split(' ')
    current_line = ""
    for word in words:
        while font.getbbox(word)[2] > max_width:
            for i in range(1, len(word)):
                if font.getbbox(word[:i + 1])[2] > max_width:
                    lines.append(word[:i]);
                    word = word[i:];
                    break
        if not current_line:
            current_line = word
        else:
            test_line = current_line + " " + word
            if font.getbbox(test_line)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line);
                current_line = word
    if current_line: lines.append(current_line)
    return lines


def check_ffmpeg():
    """检查 FFmpeg 是否可用"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# --- 3. 视觉元素创建函数 ---
def create_dynamic_background(image_path, duration):
    """
    创建基于封面的、具有微妙动态的舒缓背景。
    通过缓慢、平滑地改变整体亮度，营造出光影流动的“呼吸感”。
    """
    print("正在创建舒缓的动态背景...")

    # --- 可调节参数 ---
    # 速度控制 (值越小，光影流动越慢，感觉越舒缓)
    SPEED = 0.2
    # 强度控制 (值越小，明暗变化幅度越小，动态感越不明显)
    INTENSITY = 0.1 # 0.1 表示亮度在基准上下浮动10% (例如从90%到110%)
    # ------------------

    with Image.open(image_path).convert("RGB") as pil_image:
        # 基础的模糊背景图
        base_blurred = pil_image.resize(VIDEO_SIZE, Resampling.LANCZOS).filter(
            ImageFilter.GaussianBlur(BACKGROUND_BLUR_RADIUS))
        # 将图像数据转为浮点数，便于进行乘法运算
        base_array = np.array(base_blurred, dtype=np.float32)

    def make_frame(t):
        # 1. 使用 sin 函数创建一个在 -1 到 1 之间平滑变化的值
        # t * SPEED 控制了变化的速度
        sine_wave = np.sin(t * SPEED)

        # 2. 计算亮度的调节因子
        # 我们希望亮度在 (1 - INTENSITY) 和 (1 + INTENSITY) 之间变化
        # 例如，当 INTENSITY 为 0.1 时，亮度因子就在 0.9 和 1.1 之间变化
        brightness_factor = 1.0 + sine_wave * INTENSITY

        # 3. 将亮度因子应用到整个图像数组上
        dynamic_bg = base_array * brightness_factor

        # 4. 将计算后的浮点数值裁剪回 0-255 的范围，并转换为图像所需的 uint8 类型
        return np.clip(dynamic_bg, 0, 255).astype('uint8')

    print("舒缓动态背景创建完成。")
    return mpy.VideoClip(make_frame, duration=duration)


def create_cover_clip(image_path, duration):
    """创建静态封面图层，无阴影"""
    print("正在创建封面图层...")
    target_size = int(VIDEO_HEIGHT * COVER_SIZE_RATIO)
    radius = int(target_size * 0.12)
    # 使用抗锯齿技术创建圆角遮罩
    with Image.open(image_path).convert("RGBA") as img:
        mask = Image.new("L", (target_size * 4, target_size * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, target_size * 4, target_size * 4), radius=radius * 4, fill=255)
        mask = mask.resize((target_size, target_size), Resampling.LANCZOS)
        img = img.resize((target_size, target_size), Resampling.LANCZOS)
        img.putalpha(mask)
    # 创建一个全尺寸的透明画布，并将处理好的封面粘贴上去
    frame_img = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
    x_pos = int(VIDEO_WIDTH * 0.08)
    y_pos = (VIDEO_HEIGHT - img.height) // 2
    frame_img.paste(img, (x_pos, y_pos), img)

    # 即使是静态图像，也统一使用 VideoClip 和 make_frame 以确保稳定性
    frame_array = np.array(frame_img)

    def make_frame(t):
        return frame_array

    print("封面图层创建完成。")
    return mpy.VideoClip(make_frame, duration=duration)


def create_lyrics_clip(lyrics, duration):
    """创建带平滑滚动和动态布局的歌词图层"""
    print("正在创建歌词动画...")
    # 1. 预计算所有歌词的布局信息
    lyric_details = []
    cumulative_y = 0
    for lyric in lyrics:
        lines = wrap_text(lyric["text"], FONT_LYRIC, LYRICS_AREA_WIDTH * 0.95)
        height = sum(FONT_LYRIC.getbbox(l)[3] + LINE_SPACING for l in lines) - LINE_SPACING
        lyric_details.append({"lines": lines, "y_pos": cumulative_y, "height": height})
        cumulative_y += height + LYRIC_SPACING

    # 2. 创建动画帧
    current_scroll_y = 0.0

    def make_frame(t):
        nonlocal current_scroll_y
        frame = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        idx = next((i for i, l in enumerate(lyrics) if l["start"] <= t < l["end"]), -1)
        if idx == -1: return np.array(frame)

        details = lyric_details[idx]
        target_scroll_y = details["y_pos"] + details["height"] / 2
        current_scroll_y += (target_scroll_y - current_scroll_y) * 0.08
        draw_origin_y = VIDEO_HEIGHT / 2 - current_scroll_y

        for i, details in enumerate(lyric_details):
            y, is_hl = draw_origin_y + details["y_pos"], (i == idx)
            font = FONT_LYRIC if is_hl else FONT_SMALL
            color = COLOR_LYRIC_HIGHLIGHT if is_hl else COLOR_LYRIC_STANDARD

            # 改进: 基于像素距离计算透明度，修复“歌词消失”问题
            line_center_y = details["y_pos"] + details["height"] / 2
            pixel_dist = abs(line_center_y - current_scroll_y)
            # 屏幕高度的1/3作为标准距离，超过则开始快速淡出
            normalized_dist = pixel_dist / (VIDEO_HEIGHT / 3)
            distance_factor = max(0, 1 - normalized_dist)
            alpha = color[3] if is_hl else int(color[3] * distance_factor ** 2)

            final_color = (*color[:3], int(alpha))
            line_y = y
            for line in details["lines"]:
                line_height = font.getbbox(line)[3]
                if not (line_y + line_height > 0 and line_y < VIDEO_HEIGHT):
                    line_y += line_height + LINE_SPACING;
                    continue
                tw = font.getbbox(line)[2];
                x = LYRICS_AREA_X + (LYRICS_AREA_WIDTH - tw) / 2

                if is_hl:
                    for dx in [-2, 0, 2]:
                        for dy in [-2, 0, 2]:
                            if dx or dy: draw.text((x + dx, line_y + dy), line, font=font, fill=COLOR_LYRIC_GLOW)

                draw.text((x + 2, line_y + 2), line, font=font, fill=(*SHADOW_COLOR[:3], int(alpha * 0.4)))
                draw.text((x, line_y), line, font=font, fill=final_color)
                line_y += line_height + LINE_SPACING
        return np.array(frame)

    print("歌词动画创建完成。")
    return mpy.VideoClip(make_frame, duration=duration)


# --- 4. 主函数与视频合成 ---
def main():
    """主执行函数"""
    print("视频合成开始...")
    if not all(os.path.exists(f) for f in [COVER_IMAGE_PATH, SONG_PATH, LYRICS_PATH, *FONTS.values()]):
        print("错误：一个或多个必需文件未找到。请检查所有路径是否正确。");
        return
    if not check_ffmpeg():
        print("错误：FFmpeg 未安装或未正确添加到系统环境变量。");
        return
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    with mpy.AudioFileClip(SONG_PATH) as audio_clip:
        duration = audio_clip.duration
        print(f"音频时长: {duration:.2f}秒")
        lyrics_data = parse_lyrics(duration)
        if not lyrics_data: return

        print("-" * 20)
        background = create_dynamic_background(COVER_IMAGE_PATH, duration)
        cover = create_cover_clip(COVER_IMAGE_PATH, duration)
        lyrics = create_lyrics_clip(lyrics_data, duration)
        print("-" * 20)

        # --- 最终方案：手动合成所有图层并应用特效 ---
        print("正在手动合成图层并应用特效...")

        def make_final_frame(t):
            # 1. 获取各图层帧
            bg_frame = background.get_frame(t).astype('float')
            cover_frame = cover.get_frame(t).astype('float')
            lyrics_frame = lyrics.get_frame(t).astype('float')

            # 2. 手动 Alpha 合成 (封面)
            alpha_cover = cover_frame[:, :, 3:] / 255.0
            bg_frame = cover_frame[:, :, :3] * alpha_cover + bg_frame * (1 - alpha_cover)

            # 3. 手动 Alpha 合成 (歌词)
            alpha_lyrics = lyrics_frame[:, :, 3:] / 255.0
            bg_frame = lyrics_frame[:, :, :3] * alpha_lyrics + bg_frame * (1 - alpha_lyrics)

            # 4. 手动应用淡入淡出
            fade_in, fade_out = 1.5, 2.5
            if t < fade_in:
                bg_frame *= (t / fade_in)
            elif t > duration - fade_out:
                bg_frame *= (duration - t) / fade_out

            return np.clip(bg_frame, 0, 255).astype('uint8')

        final_video = mpy.VideoClip(make_final_frame, duration=duration).set_audio(audio_clip)

        print(f"正在导出最终视频到 '{OUTPUT_VIDEO_PATH}'...")
        try:
            final_video.write_videofile(
                OUTPUT_VIDEO_PATH, fps=24, codec="libx264", audio_codec="aac",
                threads=8, preset="medium", ffmpeg_params=["-crf", "20"], logger='bar'
            )
            print(f"\n视频合成成功！文件已保存至: {OUTPUT_VIDEO_PATH}")
        except Exception as e:
            print(f"\n视频导出失败: {e}")


if __name__ == "__main__":
    main()
