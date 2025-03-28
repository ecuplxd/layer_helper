import sys

from PySide6.QtCore import QTranslator, QLocale
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QTabWidget

from ui.folder_batch import FolderBatchWidget
from ui.pdf import PDFWidget


class MainWindow(QMainWindow):
  tabs = ['PDF', 'Word', 'Excel', '图片', '批处理', '新版诉状制作', '常规文书制作', '关于']
  tab_widgets = {
    'PDF': PDFWidget,
    '批处理': FolderBatchWidget
  }

  def __init__(self):
    super().__init__()

    center_widget = QWidget()
    center_widget.setLayout(QVBoxLayout())
    self.setCentralWidget(center_widget)
    self.init_ui()

  def init_ui(self) -> None:
    self.init_copyright()

    tab_widget = self.init_tab()
    self.centralWidget().layout().addWidget(tab_widget)

  def init_copyright(self):
    self.setWindowTitle('律师小助手——by 超萌超可爱')
    self.setWindowIcon(QIcon('./res/favicon.ico'))

  def init_tab(self):
    tab_widget = QTabWidget()

    for name in self.tabs:
      factory = self.tab_widgets.get(name) or QWidget
      tab = factory()
      tab.setObjectName(name)
      tab_widget.addTab(tab, name)

    tab_widget.setCurrentIndex(0)

    return tab_widget


def main():
  app = QApplication(sys.argv)

  QLocale.setDefault(QLocale(QLocale.Chinese, QLocale.China))
  translator = QTranslator(app)
  translator.load('./res/qt_zh_CN.qm')
  translator.load('qtbase_zh_CN')
  app.installTranslator(translator)

  screen = app.primaryScreen()
  resolution = screen.size()
  w = resolution.width()
  h = resolution.height()
  window = MainWindow()
  window.resize(w // 2, h // 2)
  window.show()

  app.exec()


if __name__ == "__main__":
  main()
