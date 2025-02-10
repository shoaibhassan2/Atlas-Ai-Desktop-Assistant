import sys
import os
import random
import re
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSizePolicy, QSpacerItem, QMessageBox, QGraphicsDropShadowEffect, QGridLayout, QFrame, QStackedLayout
from PyQt5.QtGui import QFont, QPixmap, QIcon, QMovie, QColor, QFontDatabase, QPalette, QBrush
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QMimeData

def get_base_path():
    """Get the base path for the current execution."""  # inserted
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return base_path
    base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""  # inserted
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)

MATERIALS_PATH = resource_path('materials')
print(f'[DEBUG] MATERIALS_PATH resolved to: {MATERIALS_PATH}')
if not os.path.exists(MATERIALS_PATH):
    raise FileNotFoundError(f'Materials folder not found at: {MATERIALS_PATH}')

class DropPanel(QWidget):
    """\n    Custom QWidget to handle drag-and-drop functionality for files.\n    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAcceptDrops(True)
        self.setStyleSheet('\n            QWidget {\n                background-color: rgba(0, 0, 0, 0.7);\n                border: 2px solid #1c715f;  /* scifi_green */\n                border-radius: 10px;\n                color: #F0F0F0;  /* light */\n            }\n            ')
        self.drag_image_label = QLabel(self)
        self.drag_image_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(self.parent.drag_image_path):
            try:
                drag_pixmap = QPixmap(self.parent.drag_image_path)
                if drag_pixmap.isNull():
                    raise FileNotFoundError(f'Invalid image file: {self.parent.drag_image_path}')
                scaled_pixmap = drag_pixmap.scaled(QSize(self.parent.DRAG_IMAGE_MAX_WIDTH, self.parent.DRAG_IMAGE_MAX_HEIGHT), self.parent.DRAG_IMAGE_SCALE_MODE, self.parent.DRAG_IMAGE_TRANSFORMATION_MODE)
                self.drag_image_label.setPixmap(scaled_pixmap)
                self.drag_image_label.setStyleSheet('border: none; background-color: transparent;')
            except Exception as e:
                print(f'Error loading drag.png: {e}')
                QMessageBox.warning(self, 'Resource Missing', 'Error loading \'drag.png\'. Using placeholder text.')
                self.drag_image_label.setText('Drop Here')
                self.drag_image_label.setFont(QFont('Arial', 16))
                self.drag_image_label.setStyleSheet('color: #F0F0F0; border: none; background-color: transparent;')
        else:  # inserted
            print(f'{self.parent.drag_image_path} not found.')
            QMessageBox.warning(self, 'Resource Missing', 'drag.png not found in materials folder.')
            self.drag_image_label.setText('Drop Here')
            self.drag_image_label.setFont(QFont('Arial', 16))
            self.drag_image_label.setStyleSheet('color: #F0F0F0; border: none; background-color: transparent;')
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(self.drag_image_label, alignment=Qt.AlignCenter)
            

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self.parent.is_valid_file(file_path):
                    event.acceptProposedAction()
                    self.setStyleSheet('\n                        QWidget {\n                            background-color: rgba(0, 0, 0, 0.9);\n                            border: 2px solid #00FFCC;  /* progress_fg */\n                            border-radius: 10px;\n                            color: #F0F0F0;\n                        }\n                        ')
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet('\n            QWidget {\n                background-color: rgba(0, 0, 0, 0.7);\n                border: 2px solid #1c715f;  /* scifi_green */\n                border-radius: 10px;\n                color: #F0F0F0;\n            }\n            ')
        event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self.parent.is_valid_file(file_path):
                    try:
                        analyzer_dir = os.path.join(get_base_path(), 'analyzer')
                        os.makedirs(analyzer_dir, exist_ok=True)
                        print(f'Created \'analyzer\' directory at: {analyzer_dir}')
                        file_name = os.path.basename(file_path)
                        destination = os.path.join(analyzer_dir, file_name)
                        if os.path.exists(destination):
                            base, extension = os.path.splitext(file_name)
                            destination = os.path.join(analyzer_dir, f'{base}_{random.randint(1000, 9999)}{extension}')
                        with open(file_path, 'rb') as src, open(destination, 'wb') as dst:
                            dst.write(src.read())
                        if self.parent.is_image_file(destination):
                            self.parent.display_image_on_scanimage_panel(destination)
                    except Exception as e:
                        print(f'Error saving file: {e}')
                        QMessageBox.critical(self, 'Save Error', f'Could not save file \'{file_name}\'.\nError: {str(e)}')
                            
                else:
                    QMessageBox.warning(self, 'Invalid File', f'The file \'{os.path.basename(file_path)}\' is not a valid image or document.')
        self.setStyleSheet('\n            QWidget {\n                background-color: rgba(0, 0, 0, 0.7);\n                border: 2px solid #1c715f;  /* scifi_green */\n                border-radius: 10px;\n                color: #F0F0F0;\n            }\n            ')
        event.acceptProposedAction()
                

class AtlasUI(QMainWindow):
    WINDOW_X = 100
    WINDOW_Y = 100
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    WINDOW_FIXED_WIDTH = 1200
    WINDOW_FIXED_HEIGHT = 650
    LEFT_PANEL_MIN_WIDTH = 380
    MIC_BUTTON_SIZE = QSize(50, 50)
    TOP_GIF_PANEL_HEIGHT = 140
    MAIN_GIF_SIZE = QSize(340, 350)
    SPACER_WIDTH = 200
    ATLAS_LABEL_HEIGHT = 300
    ATLAS_LABEL_FONT_SIZE = 36
    LISTENING_FONT_SIZE = 24
    RESPONSE_FONT_SIZE = 24
    USER_RESPONSE_FONT_SIZE = 16
    BOTTOM_RIGHT_GIF_SIZE = QSize(180, 180)
    MAIN_GIF_DESIRED_SIZE = QSize(430, 430)
    SECONDARY_GIF_DESIRED_SIZE = QSize(180, 180)
    DRAG_IMAGE_MAX_WIDTH = 130
    DRAG_IMAGE_MAX_HEIGHT = 100
    DRAG_IMAGE_SCALE_MODE = Qt.KeepAspectRatio
    DRAG_IMAGE_TRANSFORMATION_MODE = Qt.SmoothTransformation
    DRAG_IMAGE_PANEL_HEIGHT = 90
    DRAG_IMAGE_PANEL_WIDTH = 330
    DRAG_IMAGE_ALIGNMENT = Qt.AlignCenter
    NEW_PANEL_SIZE = QSize(212, 160)
    NEW_PANEL_SHIFT_DOWN = 25
    NEW_PANEL_SHIFT_LEFT = 25
    NEW_PANEL_BACKGROUND_COLOR = '#000000'
    NEW_PANEL_LUEM_GIF_PATH = os.path.join(MATERIALS_PATH, 'map.gf')
    NEW_PANEL_SCAN_GIF_PATH = os.path.join(MATERIALS_PATH, 'scan.gf')
    NEW_PANEL_8MEE_GIF_PATH = os.path.join(MATERIALS_PATH, '8mee.gf')
    font_path = os.path.join(MATERIALS_PATH, 'Faster Stroker.otf')
    code_font_path = os.path.join(MATERIALS_PATH, 'writing.ttf')
    star7_font_path = os.path.join(MATERIALS_PATH, 'STAR7.ttf')
    faster_stroker_font_path = os.path.join(MATERIALS_PATH, 'Faster Stroker.otf')
    writing_font_path = os.path.join(MATERIALS_PATH, 'writing.ttf')
    mic_image_path = os.path.join(MATERIALS_PATH, 'mic.png')
    gif_path_main = os.path.join(MATERIALS_PATH, 'giphy.cfg')
    gif_path_secondary = os.path.join(MATERIALS_PATH, 'processing.cfg')
    drag_image_path = os.path.join(MATERIALS_PATH, 'drag.png')
    cpu_icon_path = os.path.join(MATERIALS_PATH, 'cpu.png')
    memory_icon_path = os.path.join(MATERIALS_PATH, 'ram.png')
    ram_icon_path = os.path.join(MATERIALS_PATH, 'ram.png')
    disk_icon_path = os.path.join(MATERIALS_PATH, 'disk.png')
    loading_icon_path = os.path.join(MATERIALS_PATH, 'loading.png')
    colors = {'black': '#000000', 'cyan': '#00FFFF', 'greenish_cyan': '#00FFCC', 'cyan_blue': '#004c6a', 'scifi_green': '#1c715f', 'scifi_blue': '#00bebe', 'orange': '#FF8D00', 'light': '#F0F0F0', 'c': '#FF6200', 'progress_bg': '#2c2c2c', 'progress_fg': '#00FFCC'}
    font_primary = QFont('Orbitron', 18)
    font_secondary = QFont('Roboto', 14)
    font_accent = QFont('Exo 2', 20, QFont.Bold)
    loaded_font_family = None
    code_font_family = None
    star7_font_family = None
    faster_stroker_font_family = None
    writing_font_family = None
    standard_number_font = 'Arial'
    current_bot_response = ''

    def __init__(self):
        super().__init__()
        self.is_mic_active = True
        self.listener = None
        self.loaded_font_family = self.load_custom_font(self.font_path)
        self.code_font_family = self.load_custom_font(self.code_font_path)
        self.star7_font_family = self.load_custom_font(self.star7_font_path)
        self.faster_stroker_font_family = self.load_custom_font(self.faster_stroker_font_path)
        self.writing_font_family = self.load_custom_font(self.writing_font_path)
        self.setup_ui_structure()
        self.setup_styles()
        self.setup_timers_and_animations()
        self.create_system_metrics_panel()
        self.create_additional_right_panel()
        self.add_top_image_layer()
        self.revert_timer = QTimer()
        self.revert_timer.setSingleShot(True)
        self.revert_timer.timeout.connect(self.show_luem_gif)
        self.prev_disk_io = psutil.disk_io_counters()

    def set_listener(self, listener_object):
        """\n        Assign the external Listener instance to this GUI, enabling us to\n        pause and resume listening as needed.\n        """  # inserted
        self.listener = listener_object

    def setup_ui_structure(self):
        self.setWindowTitle('Atlas')
        self.setGeometry(self.WINDOW_X, self.WINDOW_Y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setFixedSize(self.WINDOW_FIXED_WIDTH, self.WINDOW_FIXED_HEIGHT)
        icon_path = resource_path('Atlas.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QGridLayout()
        self.central_widget.setLayout(self.central_layout)
        self.central_layout.setSpacing(0)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.main_content_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_content_widget.setLayout(self.main_layout)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        self.left_panel_widget = self.create_left_panel()
        self.content_layout.addWidget(self.left_panel_widget, stretch=4)
        self.middle_panel_layout = self.create_middle_panel()
        self.content_layout.addLayout(self.middle_panel_layout, stretch=6)
        self.right_panel_widget = self.create_right_panel()
        self.content_layout.addWidget(self.right_panel_widget, stretch=3)
        self.central_layout.addWidget(self.main_content_widget, 0, 0)
        listening_text = 'Listening...'
        response_text = 'Response:'
        listening_text_formatted = f"<span style=\'color: {self.colors['greenish_cyan']}; font-family: {(self.star7_font_family if self.star7_font_family else 'Orbitron')}; font-size: {self.LISTENING_FONT_SIZE}px;\'>{self.format_text_with_standard_numbers(listening_text)}</span>"
        response_text_formatted = f"<span style=\'color: {self.colors['greenish_cyan']}; font-family: {(self.code_font_family if self.code_font_family else 'Orbitron')}; font-size: {self.RESPONSE_FONT_SIZE}px;\'>{self.format_text_with_standard_numbers(response_text)}</span>"
        initial_html = f'{listening_text_formatted}<br>{response_text_formatted}'
        self.left_panel_textedit.setHtml(initial_html)

    def create_left_panel(self):
        left_panel_layout = QVBoxLayout()
        self.left_panel_textedit = QTextEdit()
        self.setup_text_edit(text_edit=self.left_panel_textedit, text_color=self.colors['greenish_cyan'])
        left_panel_layout.addWidget(self.left_panel_textedit)
        self.mic_button = QPushButton()
        self.mic_button.setFixedSize(self.MIC_BUTTON_SIZE)
        self.mic_button.clicked.connect(self.toggle_mic)
        self.set_mic_button_style(active=True)
        self.load_mic_icon()
        mic_glow = QGraphicsDropShadowEffect()
        mic_glow.setBlurRadius(15)
        mic_glow.setColor(QColor(self.colors['cyan_blue']))
        mic_glow.setOffset(0, 0)
        self.mic_button.setGraphicsEffect(mic_glow)
        mic_container = QVBoxLayout()
        mic_container.addWidget(self.mic_button, alignment=Qt.AlignCenter)
        mic_label = QLabel('Mic')
        mic_label.setAlignment(Qt.AlignCenter)
        mic_label.setFont(self.font_secondary)
        mic_label.setStyleSheet(f"color: {self.colors['light']};")
        mic_container.addWidget(mic_label, alignment=Qt.AlignCenter)
        mic_widget = QWidget()
        mic_widget.setLayout(mic_container)
        left_panel_layout.addWidget(mic_widget, alignment=Qt.AlignRight)
        widget = QWidget()
        widget.setLayout(left_panel_layout)
        widget.setMinimumWidth(self.LEFT_PANEL_MIN_WIDTH)
        return widget

    def create_middle_panel(self):
        middle_layout = QVBoxLayout()
        user_said_container = QWidget()
        user_said_layout = QHBoxLayout()
        user_said_layout.setContentsMargins(10, 0, 0, 0)
        user_said_container.setLayout(user_said_layout)
        self.top_gif_panel = QLabel('User Said: \n')
        self.top_gif_panel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        if self.faster_stroker_font_family:
            top_font = QFont(self.faster_stroker_font_family, 20, QFont.Bold)
        else:  # inserted
            top_font = QFont('Exo 2', 20, QFont.Bold)
        self.top_gif_panel.setFont(top_font)
        self.top_gif_panel.setStyleSheet(f'''QLabel {{   background-color: rgba(0, 0, 0, 0.7);  color: {self.colors['scifi_blue']};  border: 2px solid {self.colors['scifi_blue']};   font-size: 24px;   padding: 15px;   border-radius: 10px;}}''')
        self.top_gif_panel.setWordWrap(True)
        user_said_shadow = QGraphicsDropShadowEffect()
        user_said_shadow.setBlurRadius(20)
        user_said_shadow.setColor(QColor(self.colors['scifi_blue']))
        user_said_shadow.setOffset(0, 0)
        self.top_gif_panel.setGraphicsEffect(user_said_shadow)
        original_min_height = 170
        decreased_min_height = int(original_min_height * 0.8)
        self.top_gif_panel.setMinimumHeight(decreased_min_height)
        self.top_gif_panel.setMinimumWidth(380)
        user_said_layout.addWidget(self.top_gif_panel, alignment=Qt.AlignLeft)
        middle_layout.addWidget(user_said_container, alignment=Qt.AlignTop)
        atlas_gif_container = QWidget()
        atlas_gif_layout = QGridLayout()
        atlas_gif_layout.setContentsMargins(0, 0, 0, 0)
        atlas_gif_container.setLayout(atlas_gif_layout)
        self.gif_label = QLabel()
        self.gif_label.setFixedSize(self.MAIN_GIF_SIZE)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet('background-color: rgba(0, 0, 0, 0.8);')
        self.load_gif(self.gif_label, self.gif_path_main, 'Main GIF Not Found', desired_size=self.MAIN_GIF_DESIRED_SIZE)
        atlas_gif_layout.addWidget(self.gif_label, 0, 0, Qt.AlignCenter)
        main_gif_shadow = QGraphicsDropShadowEffect()
        main_gif_shadow.setBlurRadius(25)
        main_gif_shadow.setColor(QColor(self.colors['cyan']))
        main_gif_shadow.setOffset(0, 0)
        self.gif_label.setGraphicsEffect(main_gif_shadow)
        self.atlas_label = QLabel('A   T   l   a   s')
        self.atlas_label.setAlignment(Qt.AlignCenter)
        if self.loaded_font_family:
            self.atlas_label.setFont(QFont(self.loaded_font_family, self.ATLAS_LABEL_FONT_SIZE, QFont.Bold))
        else:  # inserted
            self.atlas_label.setFont(QFont('Orbitron', self.ATLAS_LABEL_FONT_SIZE, QFont.Bold))
        self.atlas_label.setStyleSheet(f'QLabel {{   color: white;   background-color: transparent;   font-size: {self.ATLAS_LABEL_FONT_SIZE}px;}}')
        self.atlas_label.setContentsMargins(0, 0, 0, 0)
        atlas_shadow = QGraphicsDropShadowEffect()
        atlas_shadow.setBlurRadius(25)
        atlas_shadow.setColor(QColor(self.colors['cyan']))
        atlas_shadow.setOffset(0, 0)
        self.atlas_label.setGraphicsEffect(atlas_shadow)
        atlas_gif_layout.addWidget(self.atlas_label, 0, 0, Qt.AlignCenter)
        self.atlas_label.raise_()
        middle_layout.addWidget(atlas_gif_container, alignment=Qt.AlignCenter)
        self.new_bottom_panel = self.create_new_bottom_panel()
        self.scanimage_panel = self.create_scanimage_panel()
        bottom_container = QHBoxLayout()
        bottom_container.setSpacing(15)
        bottom_container.addWidget(self.new_bottom_panel)
        bottom_container.addWidget(self.scanimage_panel)
        middle_layout.addLayout(bottom_container)
        vertical_spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        middle_layout.addItem(vertical_spacer)
        return middle_layout

    def create_right_panel(self):
        right_layout = QVBoxLayout()
        self.bottom_right_gif_label = QLabel()
        self.bottom_right_gif_label.setFixedSize(self.BOTTOM_RIGHT_GIF_SIZE)
        self.bottom_right_gif_label.setAlignment(Qt.AlignCenter)
        self.bottom_right_gif_label.setStyleSheet('background-color: rgba(0, 0, 0, 0.6); border-radius: 10px;')
        self.load_gif(self.bottom_right_gif_label, self.gif_path_secondary, 'Secondary GIF Not Found', desired_size=self.SECONDARY_GIF_DESIRED_SIZE)
        right_layout.addWidget(self.bottom_right_gif_label, alignment=Qt.AlignBottom)
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_layout)
        return right_panel_widget

    def create_system_metrics_panel(self):
        self.system_metrics_panel = QWidget(self.central_widget)
        self.system_metrics_panel.setFixedSize(200, 186)
        self.system_metrics_panel.setStyleSheet(f"\n            QWidget {{                 background-color: rgba(10, 10, 10, 0.85);\n                border: 2px solid {self.colors['cyan_blue']};\n                border-radius: 10px;\n            }}\n            ")
        self.system_metrics_panel.move(self.width() - self.system_metrics_panel.width() - 25, 25)
        metrics_layout = QVBoxLayout()
        metrics_layout.setContentsMargins(10, 10, 10, 10)
        metrics_layout.setSpacing(10)
        self.system_metrics_panel.setLayout(metrics_layout)
        title_label = QLabel('Metrics')
        if self.loaded_font_family:
            title_font = QFont(self.loaded_font_family, 14, QFont.Bold)
        else:  # inserted
            title_font = QFont('Orbitron', 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self.colors['cyan']};")
        title_label.setAlignment(Qt.AlignCenter)
        metrics_layout.addWidget(title_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"color: {self.colors['cyan_blue']};")
        metrics_layout.addWidget(separator)
        self.metrics = {'CPU': QLabel(), 'RAM': QLabel(), 'Disk': QLabel()}
        for metric_name, label in self.metrics.items():
            metric_container = QHBoxLayout()
            metric_container.setSpacing(5)
            icon_label = QLabel()
            icon_label.setFixedSize(38, 38)
            icon_path = self.get_metric_icon_path(metric_name)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon_label.setPixmap(pixmap)
                else:  # inserted
                    icon_label.setText('🔍')
            else:  # inserted
                icon_label.setText('🔍')
            metric_container.addWidget(icon_label, alignment=Qt.AlignLeft)
            if self.loaded_font_family:
                name_font = QFont(self.loaded_font_family, 10)
            else:  # inserted
                name_font = QFont('Orbitron', 10)
            name_label = QLabel(metric_name)
            name_label.setFont(name_font)
            name_label.setStyleSheet(f"color: {self.colors['light']};")
            metric_container.addWidget(name_label, alignment=Qt.AlignLeft)
            metric_container.addStretch()
            if self.loaded_font_family:
                value_font = QFont(self.loaded_font_family, 10, QFont.Bold)
            else:  # inserted
                value_font = QFont('Orbitron', 10, QFont.Bold)
            label.setFont(value_font)
            label.setStyleSheet(f"color: {self.colors['greenish_cyan']};")
            label.setText('%')
            metric_container.addWidget(label, alignment=Qt.AlignRight)
            metrics_layout.addLayout(metric_container)
        metrics_layout.addStretch()
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setBlurRadius(20)
        glow_effect.setColor(QColor(self.colors['cyan']))
        glow_effect.setOffset(0, 0)
        self.system_metrics_panel.setGraphicsEffect(glow_effect)
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_system_metrics)
        self.metrics_timer.start(1000)

    def get_metric_icon_path(self, metric_name):
        icons = {'CPU': self.cpu_icon_path, 'RAM': self.ram_icon_path, 'Disk': self.disk_icon_path}
        return icons.get(metric_name, '')

    def update_system_metrics(self):
        try:
            cpu_percent = int(psutil.cpu_percent(interval=None))
            ram_percent = int(psutil.virtual_memory().percent)
            current_disk_io = psutil.disk_io_counters()
            read_bytes_diff = current_disk_io.read_bytes - self.prev_disk_io.read_bytes
            write_bytes_diff = current_disk_io.write_bytes - self.prev_disk_io.write_bytes
            self.prev_disk_io = current_disk_io
            read_mb = read_bytes_diff / 1048576
            write_mb = write_bytes_diff / 1048576
            max_read_mb = 100
            max_write_mb = 100
            read_percent = min(read_mb / max_read_mb * 100, 100)
            write_percent = min(write_mb / max_write_mb * 100, 100)
            disk_percent = max(read_percent, write_percent)
            self.metrics['CPU'].setText(f'{cpu_percent}%')
            self.metrics['RAM'].setText(f'{ram_percent}%')
            self.metrics['Disk'].setText(f'{int(disk_percent)}%')
        except Exception as e:
            print(f'Error fetching system metrics: {e}')
            cpu_percent = ram_percent = disk_percent = 0
            self.metrics['CPU'].setText('N/A')
            self.metrics['RAM'].setText('N/A')
            self.metrics['Disk'].setText('N/A')

            

    def create_additional_right_panel(self):
        self.additional_right_panel = QWidget(self.central_widget)
        self.additional_right_panel.setFixedSize(self.NEW_PANEL_SIZE)
        self.additional_right_panel.setStyleSheet(f'''
            QWidget {{
                background-color: {self.NEW_PANEL_BACKGROUND_COLOR};
                border: none;
            }}
        ''')

        # Calculate the new position of the panel
        original_x = self.system_metrics_panel.x()
        original_y = self.system_metrics_panel.y() + self.system_metrics_panel.height() + 10
        new_x = original_x - self.NEW_PANEL_SHIFT_LEFT + 5
        new_y = original_y - 3 + self.NEW_PANEL_SHIFT_DOWN
        self.additional_right_panel.move(new_x, new_y)

        # Create a stacked layout
        self.additional_right_panel_layout = QStackedLayout(self.additional_right_panel)

        # Helper function to load GIFs
        def _load_gif(label, gif_path, placeholder_text):
            """ Loads a GIF into QLabel or sets a placeholder text if missing. """
            if os.path.exists(gif_path):
                try:
                    movie = QMovie(gif_path)
                    if movie.isValid():
                        movie.setScaledSize(self.NEW_PANEL_SIZE)
                        label.setMovie(movie)
                        movie.start()
                        return
                    else:
                        raise FileNotFoundError(f'Invalid GIF file: {gif_path}')
                except Exception as e:
                    print(f'Error loading {os.path.basename(gif_path)}: {e}')
            else:
                print(f'{gif_path} not found.')

            # If the GIF file is missing or invalid, use a placeholder
            QMessageBox.warning(self, 'Resource Missing', f'Error loading \'{os.path.basename(gif_path)}\'. Using placeholder text.')
            label.setText(placeholder_text)
            label.setFont(QFont('Arial', 16))
            label.setStyleSheet(f"color: {self.colors['light']};")

        # Create and load GIFs
        self.luem_gif_label = QLabel(self.additional_right_panel)
        self.luem_gif_label.setAlignment(Qt.AlignCenter)
        self.luem_gif_label.setFixedSize(self.NEW_PANEL_SIZE)
        self.luem_gif_label.setStyleSheet('background-color: transparent; border: none;')
        _load_gif(self.luem_gif_label, self.NEW_PANEL_LUEM_GIF_PATH, "Luem GIF Not Found")

        self.scan_gif_label = QLabel(self.additional_right_panel)
        self.scan_gif_label.setAlignment(Qt.AlignCenter)
        self.scan_gif_label.setFixedSize(self.NEW_PANEL_SIZE)
        self.scan_gif_label.setStyleSheet('background-color: transparent; border: none;')
        _load_gif(self.scan_gif_label, self.NEW_PANEL_SCAN_GIF_PATH, "Scan GIF Not Found")

        self.eightmee_gif_label = QLabel(self.additional_right_panel)
        self.eightmee_gif_label.setAlignment(Qt.AlignCenter)
        self.eightmee_gif_label.setFixedSize(self.NEW_PANEL_SIZE)
        self.eightmee_gif_label.setStyleSheet('background-color: transparent; border: none;')
        _load_gif(self.eightmee_gif_label, self.NEW_PANEL_8MEE_GIF_PATH, "8mee GIF Not Found")

        # Add widgets to layout
        self.additional_right_panel_layout.addWidget(self.luem_gif_label)
        self.additional_right_panel_layout.addWidget(self.scan_gif_label)
        self.additional_right_panel_layout.addWidget(self.eightmee_gif_label)

        # Set the container for the layout
        container = QWidget(self.additional_right_panel)
        container.setLayout(self.additional_right_panel_layout)
        container.setGeometry(0, 0, self.NEW_PANEL_SIZE.width(), self.NEW_PANEL_SIZE.height())

        # Set the default widget to display
        self.additional_right_panel_layout.setCurrentWidget(self.luem_gif_label)

        # Show the panel
        self.additional_right_panel.show()


    def create_new_bottom_panel(self):
        drop_panel = DropPanel(parent=self)
        drop_panel.setFixedHeight(self.DRAG_IMAGE_PANEL_HEIGHT)
        drop_panel.setFixedWidth(self.DRAG_IMAGE_PANEL_WIDTH)
        return drop_panel

    def create_scanimage_panel(self):
        scanimage_panel = QWidget()
        scanimage_panel.setFixedSize(70, 70)
        scanimage_panel.setStyleSheet(f"\n            QWidget {{                background-color: transparent;\n                border: 2px solid {self.colors['cyan_blue']};\n                border-radius: 10px;\n            }}\n            ")
        self.scanimage_label = QLabel(scanimage_panel)
        self.scanimage_label.setAlignment(Qt.AlignCenter)
        pixmap_path = os.path.join(MATERIALS_PATH, 'scanpannel.png')
        if os.path.exists(pixmap_path):
            pixmap = QPixmap(pixmap_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.scanimage_label.setPixmap(pixmap)
            else:  # inserted
                self.scanimage_label.setText('Scan')
                self.scanimage_label.setFont(QFont('Arial', 12))
                self.scanimage_label.setStyleSheet(f"color: {self.colors['light']};")
        else:  # inserted
            self.scanimage_label.setText('Scan')
            self.scanimage_label.setFont(QFont('Arial', 12))
            self.scanimage_label.setStyleSheet(f"color: {self.colors['light']};")
        layout = QVBoxLayout(scanimage_panel)
        layout.addWidget(self.scanimage_label)
        layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        spacer_top = QSpacerItem(0, 3, QSizePolicy.Minimum, QSizePolicy.Fixed)
        container_layout.addItem(spacer_top)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        spacer_left = QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        h_layout.addItem(spacer_left)
        h_layout.addWidget(scanimage_panel)
        container_layout.addLayout(h_layout)
        container.setLayout(container_layout)
        return container

    def setup_styles(self):
        palette = QPalette()
        gradient = QBrush(QColor(self.colors['black']))
        palette.setBrush(QPalette.Window, gradient)
        self.setPalette(palette)

    def setup_text_edit(self, text_edit: QTextEdit, text_color: str):
        text_edit.setReadOnly(True)
        text_edit.setFont(self.font_primary)
        text_edit.setStyleSheet(f"""QTextEdit {{   background: qlineargradient(       spread:pad, x1:0.2, y1:0.2, x2:0.8, y2:0.8,       stop:0 rgba(0, 255, 204, 0.07),       stop:1 rgba(0, 255, 255, 0.2)   );  color: {text_color};  border: 2px solid {self.colors['orange']};   border-radius: 15px;   padding: 12px;  font-family: {self.font_primary.family()};  font-size: {self.font_primary.pointSize()}px;}}""")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(self.colors['cyan']))
        shadow.setOffset(0, 0)
        text_edit.setGraphicsEffect(shadow)

    def setup_timers_and_animations(self):
        self.dot_count = 0
        self.listening_timer = QTimer()
        self.listening_timer.timeout.connect(self.animate_dots)
        self.listening_timer.start(500)
        self.hover_animation = QPropertyAnimation(self.new_bottom_panel, b'windowOpacity')
        self.hover_animation.setDuration(300)
        self.hover_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = '.' * self.dot_count
        listening_font = self.faster_stroker_font_family if self.faster_stroker_font_family else 'Orbitron'
        response_font = self.code_font_family if self.code_font_family else 'Orbitron'
        listening_text = f'Listening{dots}'
        response_text = 'Response:'
        user_response = self.current_bot_response
        listening_text_formatted = f"<span style=\'color: {self.colors['greenish_cyan']}; font-family: {listening_font}; font-size: {self.LISTENING_FONT_SIZE}px;\'>{self.format_text_with_standard_numbers(listening_text)}</span>"
        response_text_formatted = f"<span style=\'color: {self.colors['greenish_cyan']}; font-family: {response_font}; font-size: {self.RESPONSE_FONT_SIZE}px;\'>{self.format_text_with_standard_numbers(response_text)}</span>"
        user_response_formatted = f"<span style=\'color: {self.colors['greenish_cyan']}; font-family: {(self.writing_font_family if self.writing_font_family else 'Arial')}; font-size: {self.USER_RESPONSE_FONT_SIZE}px;\'>{self.format_text_with_standard_numbers(user_response)}</span>"
        combined_html = f'{listening_text_formatted}<br>{response_text_formatted}<br>{user_response_formatted}'
        self.left_panel_textedit.setHtml(combined_html)

    def toggle_mic(self):
        """\n        Toggle the microphone state between active and paused. Update both\n        the GUI (button style and icon) and the listening thread (if attached).\n        """  # inserted
        self.is_mic_active = not self.is_mic_active
        print(f"[GUI] Toggling mic. New state: {('Active' if self.is_mic_active else 'Paused')}0")
        if self.listener is not None:
            if self.is_mic_active:
                self.listener.resume_listening()
                print('[GUI] Microphone listening resumed in listener.')
            else:  # inserted
                self.listener.pause_listening()
                print('[GUI] Microphone listening paused in listener.')
        self.set_mic_button_style(self.is_mic_active)
        if not self.is_mic_active:
            self.mic_button.setText('🔇')
            self.mic_button.setIcon(QIcon())
        else:  # inserted
            self.mic_button.setText('')
            self.load_mic_icon()

    def set_mic_button_style(self, active: bool):
        if active:
            self.mic_button.setStyleSheet(f"\n                QPushButton {{                    background-color: rgba(0, 0, 0, 0.8);\n                    border: 2px solid {self.colors['scifi_blue']};\n                    border-radius: 25px;\n                }}\n                QPushButton:hover {{                    background-color: {self.colors['scifi_blue']};\n                }}\n                ")
        else:  # inserted
            self.mic_button.setStyleSheet(f"\n                QPushButton {{                    background-color: {self.colors['scifi_blue']};\n                    border: 2px solid {self.colors['scifi_blue']};\n                    border-radius: 25px;\n                }}\n                QPushButton:hover {{                    background-color: {self.colors['scifi_blue']};\n                }}\n                ")

    def load_mic_icon(self):
        if os.path.exists(self.mic_image_path):
            try:
                mic_image = QPixmap(self.mic_image_path)
                mic_image = mic_image.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.mic_button.setIcon(QIcon(mic_image))
                self.mic_button.setIconSize(QSize(40, 40))
            except Exception as e:
                print(f'Error loading mic image: {e}')
                QMessageBox.warning(self, 'Resource Missing', 'Error loading \'mic.png\'. Using default icon.')
                self.mic_button.setText('🎤')
                self.mic_button.setFont(QFont('Arial', 16))
                
        else:  
            print(f'{self.mic_image_path} not found.')
            QMessageBox.warning(self, 'Resource Missing', 'Mic image not found. Using fallback icon.')
            self.mic_button.setText('🎤')
            self.mic_button.setFont(QFont('Arial', 16))
            return None

    def load_gif(self, label: QLabel, path: str, fallback_text: str, desired_size: QSize=None):
        try:
            if os.path.exists(path):
                movie = QMovie(path)
                if movie.isValid():
                    if desired_size:
                        movie.setScaledSize(desired_size)
                    label.setMovie(movie)
                    movie.start()
                else:
                    raise FileNotFoundError(f'Invalid GIF file: {path}')
            else:
                raise FileNotFoundError(f'{path} not found.')
        except Exception as e:
            print(f'Error loading GIF: {e}')
            QMessageBox.warning(self, 'Resource Missing', f'Error loading \'{path}\'. Using placeholder text.')
            label.setText(fallback_text)
            label.setFont(QFont('Arial', 16))
            label.setStyleSheet(f"color: {self.colors['light']};")


    def load_custom_font(self, font_path: str):
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id == (-1):
                print(f'Failed to load font from {font_path}')
                return
            loaded_families = QFontDatabase.applicationFontFamilies(font_id)
            if loaded_families:
                loaded_font_family = loaded_families[0]
                print(f'Loaded custom font: {loaded_font_family}')
                return loaded_font_family
            print(f'No font families found in {font_path}')
            return
        print(f'Font file \'{font_path}\' does not exist.')

    def format_text_with_standard_numbers(self, text):
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        formatted_text = re.sub('(\\d+)', lambda match: f'<span style=\'font-family: {self.standard_number_font}, Roboto, sans-serif;\'>{match.group(1)}</span>', text)
        return formatted_text

    def update_user_said_in_gui(self, user_text):
        user_said_font = self.faster_stroker_font_family if self.faster_stroker_font_family else 'Orbitron'
        user_text_font = self.writing_font_family if self.writing_font_family else 'Arial'
        user_said_formatted = f"<span style=\'font-family: {user_said_font}; font-size: 24px; color: {self.colors['scifi_blue']};\'>{self.format_text_with_standard_numbers('User Said:')}</span>"
        user_text_formatted = f"<br><span style=\'font-family: {user_text_font}; font-size: {self.USER_RESPONSE_FONT_SIZE}px; color: {self.colors['c']};\'>{self.format_text_with_standard_numbers(user_text)}</span>"
        html_content = f'{user_said_formatted}{user_text_formatted}'
        self.top_gif_panel.setText(html_content)

    def append_bot_response_in_gui(self, bot_text):
        self.current_bot_response = bot_text
        if bot_text.strip().lower().startswith('#writing'):
            self.show_eightmee_gif()
        else:  # inserted
            if 'visual scanning' in bot_text.lower():
                self.show_scan_gif()
            else:  # inserted
                self.revert_timer.stop()
                self.show_eightmee_gif()
                self.revert_timer.start(2000)
        self.animate_dots()

    def show_visual_scanning_gif(self):
        self.additional_right_panel_layout.setCurrentWidget(self.scan_gif_label)

    def show_luem_gif(self):
        self.additional_right_panel_layout.setCurrentWidget(self.luem_gif_label)

    def show_eightmee_gif(self):
        self.additional_right_panel_layout.setCurrentWidget(self.eightmee_gif_label)

    def show_scan_gif(self):
        self.additional_right_panel_layout.setCurrentWidget(self.scan_gif_label)

    def eventFilter(self, source, event):
        if source == self.new_bottom_panel:
            if event.type() == event.Enter:
                self.new_bottom_panel.setStyleSheet(f"\n                    QWidget {                        background-color: rgba(0, 0, 0, 0.8);\n                        border: 2px solid {self.colors['cyan_blue']};\n                        border-radius: 10px;\n                        color: {self.colors['light']};\n                    }\n                    ")
                return True
            if event.type() == event.Leave:
                self.new_bottom_panel.setStyleSheet(f"\n                    QWidget {                        background-color: rgba(0, 0, 0, 0.7);\n                        border: 2px solid {self.colors['scifi_green']};\n                        border-radius: 10px;\n                        color: {self.colors['light']};\n                    }\n                    ")
                return True
        return super().eventFilter(source, event)

    def add_top_image_layer(self):
        self.top_image_path = os.path.join(MATERIALS_PATH, 'toplayer.pngg')
        if os.path.exists(self.top_image_path):
            self.top_label = QLabel(self.central_widget)
            self.top_label.setGeometry(0, 0, self.width(), self.height())
            self.top_label.setScaledContents(True)
            pixmap = QPixmap(self.top_image_path)
            if pixmap.isNull():
                print(f'Failed to load image from {self.top_image_path}')
                QMessageBox.warning(self, 'Resource Missing', 'Failed to load \'toplayer.png\'.')
                self.top_label.setText('Top Image Not Found')
                self.top_label.setStyleSheet(f"color: {self.colors['light']};")
                self.top_label.setAlignment(Qt.AlignCenter)
            else:  # inserted
                self.top_label.setPixmap(pixmap)
            self.top_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.top_label.raise_()
            self.central_layout.addWidget(self.top_label, 0, 0, Qt.AlignTop | Qt.AlignLeft)
            self.top_label.show()
        else:  # inserted
            print(f'{self.top_image_path} not found.')
            QMessageBox.warning(self, 'Resource Missing', 'toplayer.png not found in materials folder.')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'top_label') and self.top_label.pixmap():
            self.top_label.setGeometry(0, 0, self.width(), self.height())
            self.top_label.setPixmap(self.top_label.pixmap().scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        if hasattr(self, 'system_metrics_panel'):
            self.system_metrics_panel.move(self.width() - self.system_metrics_panel.width() - 25, 25)
        if hasattr(self, 'additional_right_panel'):
            new_x = self.system_metrics_panel.x() - self.NEW_PANEL_SHIFT_LEFT + 5
            new_y = self.system_metrics_panel.y() + self.system_metrics_panel.height() + 10 - 3 + self.NEW_PANEL_SHIFT_DOWN
            self.additional_right_panel.move(new_x, new_y)

    def is_valid_file(self, file_path):
        valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        valid_document_extensions = ['.pdf', '.txt', '.docx']
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext in valid_image_extensions or ext in valid_document_extensions:
            return True
        return False

    def is_image_file(self, file_path):
        valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        return ext in valid_image_extensions

    def display_image_on_scanimage_panel(self, image_path):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.scanimage_label.setPixmap(pixmap)
            else:  # inserted
                print(f'Failed to load image from {image_path}')
                self.scanimage_label.setText('Image')
                self.scanimage_label.setFont(QFont('Arial', 12))
                self.scanimage_label.setStyleSheet(f"color: {self.colors['light']};")
        else:  # inserted
            print(f'Image path does not exist: {image_path}')
            self.scanimage_label.setText('Image')
            self.scanimage_label.setFont(QFont('Arial', 12))
            self.scanimage_label.setStyleSheet(f"color: {self.colors['light']};")

    def clear_scanimage_panel(self):
        self.scanimage_label.clear()
        self.scanimage_label.setText('Scan')
        self.scanimage_label.setFont(QFont('Arial', 12))
        self.scanimage_label.setStyleSheet(f"color: {self.colors['light']};")

def main():
    app = QApplication(sys.argv)
    ui = AtlasUI()
    ui.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()