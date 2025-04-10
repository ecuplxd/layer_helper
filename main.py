import sys

from PySide6.QtCore import QLocale, QSettings, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ui.about import AboutWidget
from ui.cal import CalWidget
from ui.file import FileWidget
from ui.folder_batch import FolderBatchWidget
from ui.image import ImageWidget
from ui.pdf import PDFWidget
from ui.word import WordWidget


class MainWindow(QMainWindow):
  tabs = ['PDF', 'Word', 'Excel', '图片', '批处理', '文件处理', '新版诉状', '常规文书', '计算器', '设置', '关于']
  tab_widgets = {
    'PDF'     : PDFWidget,
    '批处理'  : FolderBatchWidget,
    '图片'    : ImageWidget,
    'Word'    : WordWidget,
    '文件处理': FileWidget,
    '计算器'  : CalWidget,
    '关于'    : AboutWidget,
  }

  def __init__(self):
    super().__init__()

    self.settings = QSettings('ecuplxd', 'layer_helper')

    center_widget = QWidget()
    center_widget.setLayout(QVBoxLayout())
    self.setCentralWidget(center_widget)
    self.init_ui()

    self.restoreGeometry(self.settings.value('geometry'))
    self.restoreState(self.settings.value('windowState'))
    self.show()

  def init_ui(self) -> None:
    self.init_copyright()

    tab_widget = self.init_tab()
    self.centralWidget().layout().addWidget(tab_widget)
    tab_widget.setCurrentIndex(0)

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

    return tab_widget

  def closeEvent(self, event):
    self.settings.setValue('geometry', self.saveGeometry())
    self.settings.setValue('windowState', self.saveState())
    super().closeEvent(event)


def restore_size(app: QApplication):
  screen = app.primaryScreen()
  resolution = screen.size()
  w = resolution.width()
  h = resolution.height()

  return w // 2, h // 2


def init_tr(app: QApplication):
  QLocale.setDefault(QLocale(QLocale.Chinese, QLocale.China))
  translator = QTranslator(app)
  translator.load('./res/qt_zh_CN.qm')
  translator.load('qtbase_zh_CN')
  app.installTranslator(translator)


def main():
  app = QApplication(sys.argv)
  init_tr(app)
  window = MainWindow()
  # w, h = restore_size(app)
  # window.resize(w, h)

  app.exec()


if __name__ == "__main__":
  main()
