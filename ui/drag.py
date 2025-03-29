from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget
from natsort import natsorted


class DragDropWidget(QWidget):
  dropped = Signal(list)

  def __init__(self):
    super().__init__()

    self.setAcceptDrops(True)

  def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
      event.acceptProposedAction()

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      event.setDropAction(Qt.CopyAction)
      event.accept()
      urls = event.mimeData().urls()
      result = [url.toLocalFile() for url in urls]
      sorted_files = natsorted(result)

      self.dropped.emit(sorted_files)
