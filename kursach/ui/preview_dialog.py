import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QScrollArea, QWidget
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from core.file_ops import get_file_preview


class PreviewDialog(QDialog):
    def __init__(self, file_path: str):
        super().__init__()
        self.setWindowTitle(f"Предпросмотр: {file_path}")
        self.resize(800, 600)
        self.file_path = file_path

        self.setup_ui()
        self.load_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        self.title_label = QLabel(f"📄 {self.file_path}")
        layout.addWidget(self.title_label)

        # Область для текста
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setVisible(False)
        layout.addWidget(self.text_preview)

        # Область для изображения
        self.scroll_area = QScrollArea()
        self.scroll_area.setVisible(False)
        self.scroll_area.setWidgetResizable(True)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(self.scroll_area)

        # Область для информации
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

    def load_preview(self):
        try:
            preview_type, preview_data = get_file_preview(self.file_path)

            if preview_type == "text":
                self.text_preview.setVisible(True)
                self.scroll_area.setVisible(False)
                self.text_preview.setText(preview_data)
                self.info_label.setText("")

            elif preview_type == "image":
                self.text_preview.setVisible(False)
                self.scroll_area.setVisible(True)

                image_path, info = preview_data

                # Загружаем изображение
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Масштабируем если слишком большое
                    max_size = 700
                    if pixmap.width() > max_size or pixmap.height() > max_size:
                        pixmap = pixmap.scaled(max_size, max_size,
                                               Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)

                    self.image_label.setPixmap(pixmap)
                    self.info_label.setText(info)
                else:
                    self.text_preview.setVisible(True)
                    self.scroll_area.setVisible(False)
                    self.text_preview.setText(f"Не удалось загрузить изображение\n\n{info}")

        except Exception as e:
            self.text_preview.setVisible(True)
            self.text_preview.setText(f"Ошибка при загрузке предпросмотра:\n{str(e)}")

    def closeEvent(self, event):
        """Очищаем временные файлы при закрытии"""
        try:
            # Удаляем временные файлы предпросмотра
            temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), '')
            for file in os.listdir(temp_dir):
                if file.startswith('preview_'):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
        except:
            pass
        super().closeEvent(event)