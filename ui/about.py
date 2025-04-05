from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.helper import read_img_as_qt_thumb


class AboutWidget(QWidget):
  def __init__(self):
    super().__init__()

    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    layout.addWidget(QLabel('有任何使用上的问题或者需要添加其他功能，欢迎联系作者'))
    layout.addWidget(QLabel('微信：ecuplxd'))
    link = QLabel('Github：<a href="https://github.com/ecuplxd/layer_helper">layer_helper</a>')
    link.setTextInteractionFlags(Qt.TextBrowserInteraction)
    link.setOpenExternalLinks(True)
    link.setCursor(QCursor(Qt.PointingHandCursor))
    layout.addWidget(link)

    layout.addWidget(QLabel('\n觉得很实用，奖励作者一杯咖啡~'))
    h = QHBoxLayout()
    h.addWidget(read_img_as_qt_thumb('./res/alipay.jpg'))
    h.addWidget(QLabel('\t'))
    h.addWidget(read_img_as_qt_thumb('./res/wechat.png'))
    h.addStretch()

    layout.addLayout(h)
    layout.addStretch()

    self.setLayout(layout)
