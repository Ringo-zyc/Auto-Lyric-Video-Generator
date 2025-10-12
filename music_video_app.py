import sys
import os
import glob
import re
import subprocess
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QProgressBar, QFileDialog, QFrame,
                             QTextEdit, QSlider, QMessageBox, QLineEdit, QListWidget,
                             QStackedWidget, QListWidgetItem, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QColor, QPainterPath, QPen
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

try:
    from video_generator import generate_music_video
except ImportError:
    QMessageBox.critical(None, "错误", "无法找到 'video_generator.py'。\n请确保它与本程序在同一个文件夹下。")
    sys.exit()

# --- 1. 全新 Apple 风格样式表 (QSS) ---
STYLE_SHEET = """
    #MainWindow {
        background-color: #F4F6F9;
    }
    #LeftPanel {
        background-color: #FFFFFF;
        border-right: 1px solid #E1E4E8;
    }
    #PreviewBox, #PlayerBox, QTextEdit, QListWidget, QLineEdit, #WaveformFrame {
        background-color: #FFFFFF;
        border: 1px solid #E4E7ED;
        border-radius: 12px;
    }
    #ControlGroupBox {
        background-color: #F9FAFB;
        border: 1px solid #E4E7ED;
        border-radius: 10px;
    }
    QLabel, QLineEdit {
        color: #1D1D1F;
        background-color: transparent;
        border: none;
    }
    QTextEdit, QListWidget {
        color: #333333;
        padding: 10px;
    }
    QListWidget::item {
        padding: 8px;
        border-radius: 6px;
    }
    QListWidget::item:selected, QListWidget::item:hover {
        background-color: #EBF5FF;
        color: #007AFF;
    }
    QPushButton {
        background-color: #007AFF;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #1A8CFF;
    }
    QPushButton:pressed {
        background-color: #0071E3;
    }
    QPushButton:disabled {
        background-color: #B2D7FF;
        color: #EAF2F8;
    }
    QPushButton#PlayerButton {
        background-color: #F5F5F7;
        border: 1px solid #E4E7ED;
        color: #555;
        font-size: 16pt;
        font-weight: bold;
        border-radius: 20px;
        min-width: 40px; max-width: 40px;
        min-height: 40px; max-height: 40px;
    }
    QPushButton#PlayerButton:hover {
        border-color: #007AFF;
    }
    QPushButton#ModeButton {
        background-color: #FFFFFF;
        color: #5A5A5A;
        font-weight: normal;
        border: 1px solid #DCDFE6;
        padding: 8px;
    }
    QPushButton#ModeButton:checked {
        background-color: #007AFF;
        color: white;
        border: 1px solid #007AFF;
    }
    QProgressBar {
        border: none;
        border-radius: 4px;
        text-align: center;
        background-color: #EAEAEA;
        color: #1D1D1F;
    }
    QProgressBar::chunk {
        background-color: #007AFF;
        border-radius: 4px;
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: #EAEAEA;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #FFFFFF;
        border: 2px solid #007AFF;
        width: 14px;
        height: 14px;
        margin: -7px 0;
        border-radius: 8px;
    }
"""


class CoverPreview(QLabel):
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = None
        self._placeholder_text = "点击或拖入封面图片"
        self.setObjectName("PreviewBox")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0].toLocalFile()
        if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            self.file_selected.emit(url)

    def mousePressEvent(self, event):
        # 访问父级的父级的is_single_mode方法
        if self.parentWidget().parent().is_single_mode():
            path, _ = QFileDialog.getOpenFileName(self, "选择封面图片", "", "图片文件 (*.png *.jpg *.jpeg *.webp)")
            if path: self.file_selected.emit(path)

    def set_preview_image(self, path):
        self._pixmap = QPixmap(path) if path and os.path.exists(path) else None
        self.update()

    def paintEvent(self, event):
        # super().paintEvent(event) # 不再调用父类，完全自定义绘制
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 绘制带圆角的背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(self.rect(), 12, 12)

        if not self._pixmap:
            painter.setPen(QColor("#B0B5C0"))
            painter.setFont(QFont("Microsoft YaHei UI", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, self._placeholder_text)
            return

        scaled_pixmap = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled_pixmap.width()) / 2
        y = (self.height() - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setObjectName("WaveformFrame")
        self.wave_data = np.array([])

    def set_waveform(self, data):
        if data is None or data.size == 0:
            self.wave_data = np.array([])
        else:
            max_val = np.max(np.abs(data));
            data = np.abs(data) / max_val if max_val != 0 else data
            num_samples = self.width() * 2
            if data.size > num_samples and num_samples > 0:
                step = data.size // num_samples
                data = data[::step]
            self.wave_data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.wave_data.size == 0: return

        pen = QPen(QColor("#3498DB"), 2);
        painter.setPen(pen)
        path = QPainterPath();
        h, w, num_points = self.height(), self.width(), self.wave_data.size
        path.moveTo(0, h / 2)
        for i, val in enumerate(self.wave_data): path.lineTo((i / num_points) * w, h / 2 - val * (h / 2.2))
        painter.drawPath(path)
        path_rev = QPainterPath();
        path_rev.moveTo(0, h / 2)
        for i, val in enumerate(self.wave_data): path_rev.lineTo((i / num_points) * w, h / 2 + val * (h / 2.2) * 0.4)
        pen.setColor(QColor("#A9CCE3"));
        painter.setPen(pen)
        painter.drawPath(path_rev)


class VideoGenerationThread(QThread):
    task_started = pyqtSignal(dict)
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        self._is_cancelled = False

    def run(self):
        total_tasks = len(self.tasks)
        for i, task in enumerate(self.tasks):
            if self._is_cancelled: break
            self.task_started.emit(task)
            self.msleep(200)

            song_name = task.get('name', 'video')
            try:
                # ** CRITICAL FIX **: Prepare args correctly for the generator function
                args_for_generator = {
                    'audio_path': task['audio_path'],
                    'lyrics_path': task['lyrics_path'],
                    'cover_path': task['cover_path'],
                    'output_path': task['output_path'],
                }
                generate_music_video(**args_for_generator, progress_callback=lambda p, m: self.progress.emit(p,
                                                                                                             f"({i + 1}/{total_tasks}) {m}"))
            except Exception as e:
                self.error.emit(f"处理 '{song_name}' 时出错: {e}")
                continue
        if not self._is_cancelled:
            self.finished_signal.emit(f"全部 {total_tasks} 个任务已成功完成！")

    def cancel(self):
        self._is_cancelled = True


class MusicVideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音乐视频创作台")
        self.setGeometry(100, 100, 1200, 800)
        self.setObjectName("MainWindow")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setFont(QFont("Microsoft YaHei UI", 10))
        self.setStyleSheet(STYLE_SHEET)

        self.files = {'cover': None, 'lrc': None, 'audio': None}
        self.batch_tasks = []
        self.player = QMediaPlayer()
        self.worker_thread = None
        self.init_ui()
        self.connect_signals()
        self.switch_mode(0)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.left_panel = QFrame();
        self.left_panel.setObjectName("LeftPanel");
        self.left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout(self.left_panel);
        left_layout.setContentsMargins(15, 15, 15, 15);
        left_layout.setSpacing(15)
        mode_layout = QHBoxLayout()
        self.single_mode_btn = QPushButton("单独处理");
        self.single_mode_btn.setObjectName("ModeButton");
        self.single_mode_btn.setCheckable(True)
        self.batch_mode_btn = QPushButton("批量处理");
        self.batch_mode_btn.setObjectName("ModeButton");
        self.batch_mode_btn.setCheckable(True)
        mode_layout.addWidget(self.single_mode_btn);
        mode_layout.addWidget(self.batch_mode_btn)
        left_layout.addLayout(mode_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.create_single_mode_panel())
        self.stacked_widget.addWidget(self.create_batch_mode_panel())
        left_layout.addWidget(self.stacked_widget, 1)

        self.start_btn = QPushButton("开始生成");
        self.start_btn.setFixedHeight(45)
        left_layout.addWidget(self.start_btn)
        main_layout.addWidget(self.left_panel)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget);
        content_layout.setContentsMargins(20, 20, 20, 20);
        content_layout.setSpacing(15)

        preview_layout = QHBoxLayout();
        preview_layout.setSpacing(15)
        self.cover_preview = CoverPreview(self)
        self.lyrics_preview = QTextEdit()
        self.lyrics_preview.setReadOnly(True)
        self.lyrics_preview.mousePressEvent = lambda e: self.select_file('lrc') if self.is_single_mode() else None
        preview_layout.addWidget(self.cover_preview, 1);
        preview_layout.addWidget(self.lyrics_preview, 1)
        content_layout.addLayout(preview_layout, 1)

        self.waveform_widget = WaveformWidget()
        content_layout.addWidget(self.waveform_widget)

        player_box = QFrame();
        player_box.setObjectName("PlayerBox");
        player_box.setFixedHeight(80)
        player_layout = QHBoxLayout(player_box);
        player_layout.setContentsMargins(15, 15, 15, 15)
        self.play_btn = QPushButton("▶");
        self.play_btn.setObjectName("PlayerButton")
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00 / 00:00");
        self.time_label.setMinimumWidth(100)
        player_layout.addWidget(self.play_btn);
        player_layout.addWidget(self.time_slider, 1);
        player_layout.addWidget(self.time_label)
        content_layout.addWidget(player_box)

        self.progress_bar = QProgressBar();
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("欢迎使用！");
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)
        main_layout.addWidget(content_widget)

    def create_single_mode_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget);
        layout.setContentsMargins(0, 15, 0, 0);
        layout.setSpacing(10)

        for file_type, name in [('cover', '封面'), ('lrc', '歌词'), ('audio', '音频')]:
            box = QFrame();
            box.setObjectName("ControlGroupBox")
            box_layout = QVBoxLayout(box)
            label = QLabel(f"未选择{name}文件");
            setattr(self, f"label_{file_type}", label)
            button = QPushButton(f"选择{name}...");
            button.clicked.connect(lambda _, t=file_type: self.select_file(t))
            box_layout.addWidget(label);
            box_layout.addWidget(button)
            layout.addWidget(box)

        layout.addStretch()
        return widget

    def create_batch_mode_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget);
        layout.setContentsMargins(0, 15, 0, 0);
        layout.setSpacing(10)
        self.batch_folder_btn = QPushButton("选择文件夹...");
        self.task_list_widget = QListWidget()
        layout.addWidget(self.batch_folder_btn);
        layout.addWidget(self.task_list_widget, 1)
        return widget

    def connect_signals(self):
        self.single_mode_btn.clicked.connect(lambda: self.switch_mode(0));
        self.batch_mode_btn.clicked.connect(lambda: self.switch_mode(1))
        self.start_btn.clicked.connect(self.start_generation)
        self.batch_folder_btn.clicked.connect(self.select_batch_folder)
        self.cover_preview.file_selected.connect(lambda path: self.set_file('cover', path))
        self.play_btn.clicked.connect(self.toggle_playback)
        self.player.stateChanged.connect(self.update_player_state);
        self.player.positionChanged.connect(self.update_slider_position)
        self.player.durationChanged.connect(self.update_duration);
        self.time_slider.sliderMoved.connect(self.player.setPosition)

    def switch_mode(self, index):
        self.stacked_widget.setCurrentIndex(index);
        self.single_mode_btn.setChecked(index == 0);
        self.batch_mode_btn.setChecked(index == 1)
        self.reset_inputs();
        self.status_label.setText(f"已切换到 {('单独处理' if index == 0 else '批量处理')} 模式。")

    def reset_inputs(self):
        self.files = {'cover': None, 'lrc': None, 'audio': None};
        self.batch_tasks = []
        self.set_preview_content(None, None, None)
        self.task_list_widget.clear()
        for ft in ['cover', 'lrc', 'audio']: getattr(self, f'label_{ft}').setText(f"未选择{ft}文件")
        self.check_start_button_state()

    def set_file(self, file_type, path):
        if self.is_single_mode():
            self.files[file_type] = path
            getattr(self, f"label_{file_type}").setText(os.path.basename(path))
            self.set_preview_content(**self.files)
            self.check_start_button_state()

    def set_preview_content(self, cover, lrc, audio):
        self.cover_preview.set_preview_image(cover)
        self.lyrics_preview.setPlaceholderText(
            "点击选择或拖入 .lrc 歌词文件..." if self.is_single_mode() else "批量处理时，歌词将在此处预览")
        if lrc and os.path.exists(lrc):
            try:
                with open(lrc, 'r', encoding='utf-8') as f:
                    self.lyrics_preview.setText(f.read())
            except Exception as e:
                self.show_error(f"读取歌词失败: {e}")
        else:
            self.lyrics_preview.clear()

        if audio and os.path.exists(audio):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio)));
            self.play_btn.setEnabled(True);
            self.time_slider.setEnabled(True);
            self.extract_waveform(audio)
        else:
            self.player.setMedia(QMediaContent());
            self.play_btn.setEnabled(False);
            self.time_slider.setEnabled(False)
            self.waveform_widget.set_waveform(None);
            self.update_time_label(0, 0)

    def extract_waveform(self, audio_path):
        try:
            from moviepy.editor import AudioFileClip
            with AudioFileClip(audio_path) as clip:
                arr = clip.to_soundarray(fps=4000)
            if arr.ndim > 1: arr = arr.mean(axis=1)
            self.waveform_widget.set_waveform(arr)
        except Exception as e:
            print(f"提取波形失败: {e}"); self.waveform_widget.set_waveform(None)

    def select_file(self, file_type):
        if not self.is_single_mode(): return
        filters = {'cover': "图片 (*.png *.jpg)", 'lrc': "歌词 (*.lrc)", 'audio': "音频 (*.mp3 *.wav)"}
        path, _ = QFileDialog.getOpenFileName(self, f"选择{file_type.upper()}文件", "", filters[file_type])
        if path: self.set_file(file_type, path)

    def select_batch_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.batch_tasks = self._collect_tasks(folder)
            self.task_list_widget.clear()
            if not self.batch_tasks:
                self.status_label.setText("未找到有效歌曲。")
            else:
                for task in self.batch_tasks: self.task_list_widget.addItem(task['name'])
                self.status_label.setText(f"找到 {len(self.batch_tasks)} 个任务。")
            self.check_start_button_state()

    def check_start_button_state(self):
        is_single = self.is_single_mode()
        ready = (all(self.files.values()) if is_single else bool(self.batch_tasks))
        self.start_btn.setEnabled(ready)

    def start_generation(self):
        if self.player.state() == QMediaPlayer.PlayingState: self.player.pause()

        output_dir = QFileDialog.getExistingDirectory(self, "选择输出文件夹",
                                                      os.path.join(os.path.expanduser("~"), "Videos",
                                                                   "MusicVideoOutput"))
        if not output_dir: return

        tasks = self._collect_tasks(self.files if self.is_single_mode() else self.batch_folder, output_dir)
        if not tasks: self.show_error("没有可执行的任务。"); return

        self.start_btn.setEnabled(False);
        self.progress_bar.setVisible(True)
        self.worker_thread = VideoGenerationThread(tasks)
        self.worker_thread.task_started.connect(self.update_preview_for_task)
        self.worker_thread.progress.connect(self.update_progress)
        self.worker_thread.finished_signal.connect(self.on_generation_finished)
        self.worker_thread.error.connect(self.show_error)
        self.worker_thread.start()

    def _collect_tasks(self, source, output_dir=None):
        if isinstance(source, dict):
            if not all(source.values()): return []
            name = os.path.splitext(os.path.basename(source['audio']))[0]
            # ** CRITICAL FIX ** Map to correct keys for the generator
            return [{
                'audio_path': source['audio'],
                'lyrics_path': source['lrc'],
                'cover_path': source['cover'],
                'name': name,
                'output_path': os.path.join(output_dir, f"{name}.mp4")
            }]

        folder = source;
        tasks = []
        audio_files = glob.glob(os.path.join(folder, '*.mp3'))
        cover_file = next(
            iter(glob.glob(os.path.join(folder, 'cover.*')) + glob.glob(os.path.join(folder, 'folder.*'))), None)
        if cover_file and audio_files:
            for audio in audio_files:
                lrc = os.path.splitext(audio)[0] + '.lrc'
                if os.path.exists(lrc): tasks.append(
                    {'name': os.path.splitext(os.path.basename(audio))[0], 'audio_path': audio, 'lyrics_path': lrc,
                     'cover_path': cover_file})
        else:
            for sub in os.scandir(folder):
                if sub.is_dir():
                    audio = next(iter(glob.glob(os.path.join(sub.path, '*.mp3'))), None)
                    lrc = next(iter(glob.glob(os.path.join(sub.path, '*.lrc'))), None)
                    cover = next(
                        iter(glob.glob(os.path.join(sub.path, 'cover.*')) + ([cover_file] if cover_file else [])), None)
                    if audio and lrc and cover: tasks.append(
                        {'name': sub.name, 'audio_path': audio, 'lyrics_path': lrc, 'cover_path': cover})
        if output_dir:
            for task in tasks: task['output_path'] = os.path.join(output_dir, f"{task['name']}.mp4")
        return tasks

    def update_preview_for_task(self, task):
        self.set_preview_content(task['cover_path'], task['lyrics_path'], task['audio_path'])
        for i in range(self.task_list_widget.count()):
            if self.task_list_widget.item(i).text() == task['name']:
                self.task_list_widget.setCurrentRow(i);
                break

    def update_progress(self, value, message):
        self.progress_bar.setValue(value); self.status_label.setText(message)

    def on_generation_finished(self, message):
        self.status_label.setText(message); self.check_start_button_state(); self.progress_bar.setValue(
            100); QMessageBox.information(self, "完成", message)

    def show_error(self, message):
        QMessageBox.warning(self, "出错啦", message); self.status_label.setText(
            f"错误: {message}"); self.check_start_button_state(); self.progress_bar.setVisible(False)

    def toggle_playback(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def update_player_state(self, state):
        self.play_btn.setText("❚❚" if state == QMediaPlayer.PlayingState else "▶")

    def update_slider_position(self, position):
        self.time_slider.blockSignals(True); self.time_slider.setValue(position); self.time_slider.blockSignals(
            False); self.update_time_label(position, self.player.duration())

    def update_duration(self, duration):
        self.time_slider.setRange(0, duration); self.update_time_label(self.player.position(), duration)

    def update_time_label(self, pos, dur):
        self.time_label.setText(
            f"{pos // 1000 // 60:02}:{pos // 1000 % 60:02} / {dur // 1000 // 60:02}:{dur // 1000 % 60:02}")

    def is_single_mode(self):
        return self.stacked_widget.currentIndex() == 0

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning(): self.worker_thread.cancel(); self.worker_thread.wait()
        event.accept()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MusicVideoApp()
    window.show()
    sys.exit(app.exec_())

