from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class CastItem(QWidget):
    def __init__(self, actor_name=None, character_name=None, image_path=None, parent=None):
        super(CastItem, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.image_label = QLabel()
        self.actor_label = QLabel()
        self.character_label = QLabel()

        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.actor_label)
        self.layout.addWidget(self.character_label)

        # set text font style to italic for character_label
        font = self.character_label.font()
        font.setItalic(True)
        self.character_label.setFont(font)

        if actor_name and character_name and image_path:
            self.update_info(actor_name, character_name, image_path)

    def update_info(self, actor_name, character_name, image_path):
        self.actor_label.setText(actor_name)
        self.character_label.setText(character_name)
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(self.parent().parent().width(), self.parent().parent().height(),
                               aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
