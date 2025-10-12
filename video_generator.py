import os
import sys
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from PIL.Image import Resampling
import pylrc
import moviepy.editor as mpy
import jieba


# --- 1. 工具函数 ---
def resource_path(relative_path):
    """获取资源的绝对路径，兼容PyInstaller。"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def detect_language(text):
    """根据文本中的字符范围检测主要语言。"""
    if not text: return 'en'
    if re.search("[\u4e00-\u9fa5]", text): return 'zh'
    if re.search("[\u3040-\u309f\u30a0-\u30ff]", text): return 'ja'
    return 'en'


def load_fonts(lang, fonts_dir, size_lyric, size_small):
    """根据检测到的语言加载对应的字体文件。"""
    font_map = {'zh': "NotoSansSC", 'ja': "NotoSansJP", 'en': "NotoSans"}
    font_name = font_map.get(lang, "NotoSans")
    try:
        print(f"检测到语言: {lang}, 加载字体: {font_name}")
        fonts = {
            "bold": ImageFont.truetype(resource_path(os.path.join(fonts_dir, f"{font_name}-Bold.ttf")), size_lyric),
            "regular": ImageFont.truetype(resource_path(os.path.join(fonts_dir, f"{font_name}-Regular.ttf")),
                                          size_small)
        }
        return fonts
    except IOError:
        raise IOError(f"字体文件加载失败: {font_name}。请确保Fonts文件夹和字体文件存在。")


def wrap_text(text, font, max_width, lang):
    """根据语言智能换行。"""
    lines = []
    if lang == 'en':
        words = text.split(' ')
        line = ''
        for word in words:
            if font.getbbox(line + ' ' + word)[2] <= max_width:
                line += ' ' + word if line else word
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
    elif lang == 'zh':
        words = jieba.lcut(text)
        line = ''
        for word in words:
            if font.getbbox(line + word)[2] <= max_width:
                line += word
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
    else:
        line = ''
        for char in text:
            if font.getbbox(line + char)[2] <= max_width:
                line += char
            else:
                if line: lines.append(line)
                line = char
        if line: lines.append(line)
    return lines if lines else [""]


def parse_lyrics(lyrics_path, audio_duration):
    """解析LRC文件。"""
    try:
        with open(lyrics_path, "r", encoding="utf-8") as f:
            lrc_string = f.read()
    except Exception:
        return None
    subs = pylrc.parse(lrc_string)
    if not subs: return []
    processed_lyrics = []
    for i, sub in enumerate(subs):
        text = sub.text.strip()
        if not text: continue
        end_time = subs[i + 1].time if i + 1 < len(subs) else audio_duration
        processed_lyrics.append({"start": sub.time, "end": end_time, "text": text})
    return processed_lyrics


# --- 2. 视觉元素创建函数 ---
def create_dynamic_background(image_path, duration, video_size, blur_radius):
    with Image.open(image_path).convert("RGB") as pil_image:
        scale = max(video_size[0] / pil_image.width, video_size[1] / pil_image.height)
        new_size = (int(pil_image.width * scale), int(pil_image.height * scale))
        pil_image = pil_image.resize(new_size, Resampling.LANCZOS)
        left = (pil_image.width - video_size[0]) / 2
        top = (pil_image.height - video_size[1]) / 2
        pil_image = pil_image.crop((left, top, left + video_size[0], top + video_size[1]))
        base_blurred = pil_image.filter(ImageFilter.GaussianBlur(blur_radius))
        base_array = np.array(base_blurred, dtype=np.float32)

    def make_frame(t):
        frame = base_array.copy()
        brightness_factor = 1.0 + 0.05 * np.sin(t * 0.3)
        frame *= brightness_factor
        return np.clip(frame, 0, 255).astype('uint8')

    return mpy.VideoClip(make_frame, duration=duration).set_fps(24)


def create_cover_clip(image_path, duration, video_size, cover_size, cover_pos, corner_radius):
    with Image.open(image_path).convert("RGBA") as img:
        img.thumbnail(cover_size, Resampling.LANCZOS)
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, *img.size), radius=corner_radius, fill=255)
        img.putalpha(mask)
        frame_img = Image.new("RGBA", video_size, (0, 0, 0, 0))
        final_pos = (cover_pos[0] + (cover_size[0] - img.width) // 2, cover_pos[1] + (cover_size[1] - img.height) // 2)
        frame_img.paste(img, final_pos, img)
        frame_array = np.array(frame_img)
    return mpy.VideoClip(lambda t: frame_array, duration=duration).set_fps(24)


def create_lyrics_clip(lyrics, duration, fonts, lang, cfg):
    font_lyric, font_small = fonts["bold"], fonts["regular"]
    lyric_details = []
    cumulative_y = 0
    for lyric in lyrics:
        lines = wrap_text(lyric["text"], font_lyric, cfg['area_width'], lang)
        height = sum(font_lyric.getbbox(l)[3] + cfg['line_spacing'] for l in lines) - cfg['line_spacing']
        lyric_details.append({"lines": lines, "y_pos": cumulative_y, "height": height})
        cumulative_y += height + cfg['lyric_spacing']

    current_scroll_y = 0.0

    def make_frame(t):
        nonlocal current_scroll_y
        frame = Image.new("RGBA", cfg['video_size'], (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        idx = next((i for i, l in enumerate(lyrics) if l["start"] <= t < l["end"]), -1)
        if idx == -1: return np.array(frame)

        details = lyric_details[idx]
        target_scroll_y = details["y_pos"] + details["height"] / 2
        current_scroll_y += (target_scroll_y - current_scroll_y) * 0.08
        draw_origin_y = cfg['area_y'] + cfg['area_height'] / 2 - current_scroll_y

        for i, details in enumerate(lyric_details):
            y, is_hl = draw_origin_y + details["y_pos"], (i == idx)
            font = font_lyric if is_hl else font_small
            color = cfg['color_hl'] if is_hl else cfg['color_std']
            pixel_dist = abs((details['y_pos'] + details['height'] / 2) - current_scroll_y)
            distance_factor = max(0, 1 - pixel_dist / (cfg['video_size'][1] / 2.5)) ** 2
            alpha = int(color[3] * distance_factor)
            final_color = (*color[:3], alpha)
            line_y = y
            for line in details["lines"]:
                line_height = font.getbbox(line)[3]
                if not (line_y + line_height > 0 and line_y < cfg['video_size'][1]):
                    line_y += line_height + cfg['line_spacing']
                    continue
                tw = font.getbbox(line)[2]
                x = cfg['area_x'] + (cfg['area_width'] - tw) / 2
                shadow_color = (*cfg['shadow_color'][:3], int(alpha * 0.4))
                draw.text((x + 2, line_y + 2), line, font=font, fill=shadow_color)
                draw.text((x, line_y), line, font=font, fill=final_color)
                line_y += line_height + cfg['line_spacing']
        return np.array(frame)

    return mpy.VideoClip(make_frame, duration=duration).set_fps(24)


# --- 3. 主生成函数 ---
def generate_music_video(audio_path, lyrics_path, cover_path, output_path, progress_callback=None):
    def progress(p, msg):
        if progress_callback: progress_callback(p, msg)

    # 布局固定为 16:9
    VIDEO_WIDTH, VIDEO_HEIGHT = 1280, 720
    cover_size_h = int(VIDEO_HEIGHT * 0.6)
    cover_size_w = cover_size_h
    cover_pos_x = int(VIDEO_WIDTH * 0.08)
    cover_pos_y = (VIDEO_HEIGHT - cover_size_h) // 2
    lyrics_config = {
        'area_x': cover_pos_x + cover_size_w + int(VIDEO_WIDTH * 0.05),
        'area_y': 0,
        'area_width': VIDEO_WIDTH - (cover_pos_x + cover_size_w + int(VIDEO_WIDTH * 0.13)),
        'area_height': VIDEO_HEIGHT
    }

    VIDEO_SIZE = (VIDEO_WIDTH, VIDEO_HEIGHT)
    FONT_SIZE_LYRIC, FONT_SIZE_SMALL = (50, 38)
    lyrics_config.update({
        'video_size': VIDEO_SIZE, 'line_spacing': 15, 'lyric_spacing': 30,
        'color_std': (255, 255, 255, 180), 'color_hl': (255, 255, 255, 255),
        'shadow_color': (0, 0, 0, 160)
    })

    audio_clip = background = cover = lyrics = final_clip = None
    try:
        progress(0, "准备中...")
        audio_clip = mpy.AudioFileClip(audio_path)
        duration = audio_clip.duration
        progress(5, "解析歌词...")
        lyrics_data = parse_lyrics(lyrics_path, duration)
        if not lyrics_data: raise ValueError("歌词文件为空或无法解析。")

        progress(10, "检测语言并加载字体...")
        full_lyrics_text = " ".join([l['text'] for l in lyrics_data])
        detected_lang = detect_language(full_lyrics_text)
        fonts = load_fonts(detected_lang, "Fonts", FONT_SIZE_LYRIC, FONT_SIZE_SMALL)

        progress(15, "创建视觉元素...")
        background = create_dynamic_background(cover_path, duration, VIDEO_SIZE, 60)
        cover = create_cover_clip(cover_path, duration, VIDEO_SIZE, (cover_size_w, cover_size_h),
                                  (cover_pos_x, cover_pos_y), int(cover_size_w * 0.12))
        lyrics = create_lyrics_clip(lyrics_data, duration, fonts, detected_lang, lyrics_config)

        progress(20, "即将开始渲染...")

        total_frames = int(duration * 24)

        def make_final_frame(t):
            current_frame = int(t * 24)
            # 优化进度条：20%到95%分配给渲染过程
            progress_val = 20 + int((current_frame / total_frames) * 75)
            if current_frame % 24 == 0:  # 每秒更新一次状态，避免过于频繁
                progress(progress_val, f"正在渲染: {current_frame}/{total_frames} 帧")

            result = background.get_frame(t).astype(np.float32)
            cover_frame = cover.get_frame(t)
            alpha_cover = cover_frame[..., 3:4] / 255.0
            result = cover_frame[..., :3] * alpha_cover + result * (1.0 - alpha_cover)
            lyrics_frame = lyrics.get_frame(t)
            alpha_lyrics = lyrics_frame[..., 3:4] / 255.0
            result = lyrics_frame[..., :3] * alpha_lyrics + result * (1.0 - alpha_lyrics)

            fade_in, fade_out = 1.5, 2.5
            if t < fade_in:
                result *= (t / fade_in)
            elif t > duration - fade_out:
                result *= max(0, (duration - t) / fade_out)
            return np.clip(result, 0, 255).astype(np.uint8)

        final_clip = mpy.VideoClip(make_final_frame, duration=duration).set_fps(24).set_audio(audio_clip)

        progress(95, "正在合成音频并导出文件...")
        final_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac", threads=os.cpu_count(),
            preset="medium", ffmpeg_params=["-crf", "22", "-pix_fmt", "yuv420p"]
        )
        progress(100, "视频合成成功！")
    finally:
        for clip in [audio_clip, background, cover, lyrics, final_clip]:
            if clip:
                try:
                    clip.close()
                except Exception:
                    pass
