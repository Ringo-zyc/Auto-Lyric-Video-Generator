<div align="center">

# 🎵 Auto-Lyric-Video-Generator

**自動歌詞動画生成ツール | Automated Lyric Video Creator**

[![License](https://img.shields.io/github/license/Ringo-zyc/Auto-Lyric-Video-Generator?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey?style=flat-square)]()
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41cd52?style=flat-square)](https://www.riverbankcomputing.com/software/pyqt/)

*オーディオ、LRC 歌詞、カバー画像から美しい動的歌詞動画をワンクリックで合成します*

[English](README_EN.md) | [中文](README.md)

</div>

---

## ✨ 機能と特徴

| 機能 | 説明 |
|:---:|:---|
| 🎤 **LRC 精密同期** | `.lrc` ファイルを正確に解析し、歌詞と音楽を完璧に同期させます |
| 🌐 **多言語スマート改行** | jieba 分かち書きを内蔵し、中国語、日本語、英語の改行をスマートに処理します |
| 🎨 **動的背景** | カバー画像に基づいて、ぼかしと呼吸感のある背景アニメーションを自動生成します |
| 💿 **角丸カバー** | アルバムカバーを洗練された角丸効果に自動処理します |
| 📊 **波形プレビュー** | GUI インターフェースにオーディオ波形の可視化を統合しました |
| 📁 **一括処理** | フォルダの一括認識とキュー生成をサポートします |

---

## 📸 画面プレビュー

<div align="center">
  <img src="assets/gui_screenshot.png" alt="GUI Screenshot" width="600"/>
  <p><em>Apple スタイルのシンプルでエレガントなユーザーインターフェース</em></p>
</div>

---

## 🚀 クイックスタート

### 📥 1. プロジェクトのクローン

```bash
git clone https://github.com/Ringo-zyc/Auto-Lyric-Video-Generator.git
cd Auto-Lyric-Video-Generator
```

### 📦 2. 依存関係のインストール

> **前提条件**：Python 3.7+ および [FFmpeg](https://ffmpeg.org/download.html)（システム PATH に追加済みであること）

```bash
pip install moviepy numpy Pillow pylrc PyQt5 jieba
```

### ▶️ 3. アプリケーションの起動

```bash
python music_video_app.py
```

---

## 📁 プロジェクト構造

```
Auto-Lyric-Video-Generator/
├── 📱 music_video_app.py    # PyQt5 GUI メインプログラム
├── 🎬 video_generator.py    # コア動画生成エンジン
├── 📝 make_lyric_video.py   # コマンドライン版（スタンドアロン）
├── 🔤 Fonts/                # フォントファイル (Noto Sans SC/JP)
├── 🎵 Songs/                # 入力ファイル例のディレクトリ
├── 📤 Output/               # 動画出力ディレクトリ
└── 🖼️ assets/               # README リソースファイル
```

---

## 📝 使用方法

### リソースファイルの準備

| ファイルタイプ | 命名規則 | 説明 |
|:-------:|:-------:|:-----|
| 🎵 オーディオ | `song.mp3` | MP3 形式をサポート |
| 📄 歌詞 | `song.lrc` | オーディオと同じファイル名の LRC ファイル |
| 🖼️ カバー | `cover.png/jpg` | 1:1 の正方形比率を推奨 |

### 2つの動作モード

- **シングルモード**：オーディオ、歌詞、カバーファイルを手動で選択します
- **一括モード**：複数の曲フォルダを含むルートディレクトリを選択すると、プログラムが自動的にマッチングして一括生成します

---

## 👀 効果プレビュー

<div align="center">
  <a href="https://www.bilibili.com/video/BV1XzTkz3Eo3/">
    <img src="assets/demo_thumbnail.png" alt="Demo Video" width="600"/>
  </a>
  <p><em>👆 画像をクリックして Bilibili のデモ動画を視聴</em></p>
</div>

---

## 🤝 貢献

[Issue](https://github.com/Ringo-zyc/Auto-Lyric-Video-Generator/issues) や [Pull Request](https://github.com/Ringo-zyc/Auto-Lyric-Video-Generator/pulls) の送信を歓迎します！

## 📄 ライセンス

本プロジェクトは [MIT License](LICENSE) の下で公開されています。

---

<div align="center">
  <sub>Made with ❤️ by <a href="https://github.com/Ringo-zyc">Ringo-zyc</a></sub>
</div>
