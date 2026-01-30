<div align="center">

# 🎵 Auto-Lyric-Video-Generator

**Automated Lyric Video Creator**

[![License](https://img.shields.io/github/license/Ringo-zyc/Auto-Lyric-Video-Generator?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey?style=flat-square)]()
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41cd52?style=flat-square)](https://www.riverbankcomputing.com/software/pyqt/)

*One-click generation of beautiful dynamic lyric videos from audio, LRC lyrics, and cover images*

[中文](README.md) | [日本語](README_JP.md)

</div>

---

## ✨ Features

| Feature | Description |
|:---:|:---|
| 🎤 **LRC Precision Sync** | Accurately parses `.lrc` files for perfect synchronization of lyrics and music |
| 🌐 **Smart Line Breaking** | Built-in jieba tokenization for intelligent line breaking in Chinese, Japanese, and English |
| 🎨 **Dynamic Background** | Automatically generates blurred breathing background animation based on the cover |
| 💿 **Rounded Cover** | Automatically processes album covers into refined rounded effects |
| 📊 **Waveform Preview** | GUI interface integrates audio waveform visualization |
| 📁 **Batch Processing** | Supports folder batch recognition and queue generation |

---

## 📸 Interface Preview

<div align="center">
  <img src="assets/gui_screenshot.png" alt="GUI Screenshot" width="600"/>
  <p><em>Clean and Elegant Apple-style User Interface</em></p>
</div>

---

## 🚀 Quick Start

### 📥 1. Clone the Project

```bash
git clone https://github.com/Ringo-zyc/Auto-Lyric-Video-Generator.git
cd Auto-Lyric-Video-Generator
```

### 📦 2. Install Dependencies

> **Prerequisites**: Python 3.7+ and [FFmpeg](https://ffmpeg.org/download.html) (must be added to system PATH)

```bash
pip install moviepy numpy Pillow pylrc PyQt5 jieba
```

### ▶️ 3. Launch Application

```bash
python music_video_app.py
```

---

## 📁 Project Structure

```
Auto-Lyric-Video-Generator/
├── 📱 music_video_app.py    # PyQt5 GUI Main Program
├── 🎬 video_generator.py    # Core Video Generation Engine
├── 📝 make_lyric_video.py   # Command Line Version (Standalone)
├── 🔤 Fonts/                # Font Files (Noto Sans SC/JP)
├── 🎵 Songs/                # Input File Example Directory
├── 📤 Output/               # Video Output Directory
└── 🖼️ assets/               # README Assets
```

---

## 📝 Usage Instructions

### Prepare Resources

| File Type | Naming Requirement | Note |
|:-------:|:-------:|:-----|
| 🎵 Audio | `song.mp3` | Supports MP3 format |
| 📄 Lyrics | `song.lrc` | LRC file with the same name as audio |
| 🖼️ Cover | `cover.png/jpg` | Recommended 1:1 square ratio |

### Two Working Modes

- **Single Track Mode**: Manually select audio, lyrics, and cover files
- **Batch Mode**: Select the root directory containing multiple song folders, the program automatically matches and batch generates

---

## 👀 Preview

<div align="center">
  <a href="https://www.bilibili.com/video/BV1XzTkz3Eo3/">
    <img src="assets/demo_thumbnail.png" alt="Demo Video" width="600"/>
  </a>
  <p><em>👆 Click image to watch Bilibili demo video</em></p>
</div>

---

## 🤝 Contribution

Welcome to submit [Issue](https://github.com/Ringo-zyc/Auto-Lyric-Video-Generator/issues) and [Pull Request](https://github.com/Ringo-zyc/Auto-Lyric-Video-Generator/pulls)!

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Made with ❤️ by <a href="https://github.com/Ringo-zyc">Ringo-zyc</a></sub>
</div>
