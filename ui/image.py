from typing import List, Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QLabel, QHeaderView
from cv2.typing import MatLike

from ui.drag import DragDropWidget
from ui.helper import cv_2_qimage
from util import read_img, img_bleach, make_dir, correct_img_orien, write_img, get_file_folder, \
  file_name_and_ext


class ImageWidget(DragDropWidget):
  funcs = [{'name': '漂白',
            'exec': '',
            'config': {}
            },
           {'name': '倾斜校正',
            'exec': '',
            'config': {}
            },
           {'name': '清晰增强',
            'exec': '',
            'config': {}
            },
           {'name': '去噪',
            'exec': '',
            'config': {}
            },
           {'name': '去阴影',
            'exec': '',
            'config': {}
            },
           {'name': '扭曲校正',
            'exec': '',
            'config': {}
            },
           {'name': '切边',
            'exec': '',
            'config': {}
            },
           {'name': '减小文件大小',
            'fun': '',
            'config': {}
            }
           ]
  last_images: List[MatLike] = []
  rendered = False

  def __init__(self):
    super().__init__()

    self.table = QTableWidget()
    self.config_layout = QVBoxLayout()
    self.status = QLabel()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    header = QHBoxLayout()
    for fun in self.funcs:
      name: str = fun['name']
      btn = QPushButton(name)
      btn.pressed.connect(lambda x=name: self.preview_op(x))
      header.addWidget(btn)
    header.addStretch()

    self.table.setColumnCount(4)
    self.table.setHorizontalHeaderLabels(['文件', '原图', '预览', '状态'])
    self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    self.table.verticalHeader().setDefaultSectionSize(250)

    h2 = QHBoxLayout()
    clear = QPushButton('清空')
    save = QPushButton('保存')
    h2.addStretch()
    h2.addWidget(self.status)
    h2.addWidget(clear)
    h2.addWidget(save)

    layout.addLayout(header)
    layout.addLayout(self.config_layout)
    layout.addWidget(self.table)
    layout.addLayout(h2)

    clear.pressed.connect(self.clear_table)
    save.pressed.connect(self.save_result)
    self.dropped.connect(self.update_table)
    self.setLayout(layout)

  def preview_op(self, name: str):
    fn = None

    if name == '漂白':
      fn = img_bleach
    elif name == '倾斜校正':
      fn = correct_img_orien
    else:
      pass

    if not fn:
      return

    last_images = self.last_images[:]
    self.last_images = []
    self.thread = Worker(last_images, fn, name)
    self.thread.updated.connect(self.preview_result)
    self.thread.start()

  def save_result(self):
    out = get_file_folder(self.files[0]) + '/out'
    make_dir(out)
    total = len(self.files)

    for r, image in enumerate(self.last_images):
      name, ext = file_name_and_ext(self.files[r])
      write_img(image, f'{out}/{name}.{ext}')

      self.table.selectRow(r)
      self.table.setCellWidget(r, 3, QLabel('√'))
      self.status.setText(f'{r + 1}/{total}')

  def clear_table(self):
    self.files = []
    self.rendered = False
    self.last_images = []
    self.table.setRowCount(0)
    self.status.setText('')

  def update_table(self, files: List[str] = None):
    self.table.setRowCount(0)
    self.table.setRowCount(len(self.files))

    if files is not None:
      self.rendered = False
      self.last_images = []

    for r, file in enumerate(self.files):
      self.table.setCellWidget(r, 0, QLabel(file))
      self.table.setCellWidget(r, 3, QLabel('待执行'))

    if not self.rendered:
      self.thread = Worker(self.files)
      self.thread.updated.connect(self.preview_result)
      self.thread.start()
      self.rendered = True

    self.status.setText(f'共 {len(self.files)} 个')

  def preview_result(self, r: int, image: MatLike, col: bool):
    pixmap = cv_2_qimage(image)
    thumbnail = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    label = QLabel()
    label.setPixmap(thumbnail)

    self.last_images.append(image)
    self.table.setCellWidget(r, col + 1, label)
    self.table.selectRow(r)
    self.status.setText(f'{r + 1}/{len(self.files)}')


class Worker(QThread):
  updated = Signal(int, Any, bool)

  def __init__(self, files, func=None, fun_name: str = None):
    super().__init__()
    self.files = files
    self.func = func
    self.fun_name = fun_name
    self.col = func is not None

  def run(self):
    for r, image in enumerate(self.files):
      if isinstance(image, str):
        image = read_img(image)

      if self.func:
        image = self.func(image)

      self.updated.emit(r, image, self.col)
