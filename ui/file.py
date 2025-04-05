import os
import re
import shutil
from typing import List

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QVBoxLayout,
                               QWidget,
                               )

from ui.drag import DragDropWidget
from ui.helper import Field, Fields, VarType, clear_layout
from util import file_name_and_ext, normal_join, ocr_pdf


class FileWidget(QWidget):
  configs = [
    Fields('快速一对一移入', [Field(label = '重命名为（同名文件将添加 .bak 后缀）', hint = '选填')]),
    Fields('识别要素并重命名', [Field(label = '需要识别的内容', hint = '使用正则表达式', val = '被告:.*,'),
                                Field(label = '使用第几列数据进行匹配', type = VarType.NUM),
                                Field(label = '粘贴 Excel 数据', type = VarType.TEXTAREA),
                                Field(label = '命名规则',
                                      hint = '选填，如：2025-{1}-{2}-判决书，将用第 1、2 列数据替换 {} 内容'
                                      )]
           )
  ]

  def __init__(self):
    super().__init__()

    self.config = QVBoxLayout()
    self.funcs = QComboBox()
    self.center = QHBoxLayout()
    self.status = QLabel()
    self.c_left = DragDropWidget()
    self.l_table = QTableWidget()
    self.r_table = QTableWidget()
    self.l_table.setLayout(QVBoxLayout())
    self.r_table.setLayout(QVBoxLayout())
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    header = QHBoxLayout()
    self.funcs.addItems(['快速一对一移入', '识别要素并重命名'])
    header.addWidget(self.funcs)
    header.addStretch()

    self.l_table.setColumnCount(2)
    self.l_table.setHorizontalHeaderLabels(['原文件', '状态'])
    self.l_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    self.r_table.setColumnCount(1)
    self.r_table.setHorizontalHeaderLabels(['移入目录'])
    self.r_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

    c_right = DragDropWidget()
    self.c_left.files = []

    self.c_left.setLayout(QVBoxLayout())
    c_right.setLayout(QVBoxLayout())

    self.c_left.layout().addWidget(self.l_table)
    c_right.layout().addWidget(self.r_table)

    self.center.addWidget(self.c_left)
    self.center.addWidget(c_right)

    footer = QHBoxLayout()
    clear = QPushButton('清空')
    ok = QPushButton('执行')
    footer.addStretch()
    footer.addWidget(self.status)
    footer.addWidget(clear)
    footer.addWidget(ok)

    self.funcs.currentIndexChanged.connect(self.update_config)
    self.c_left.dropped.connect(self.update_l_table)
    c_right.dropped.connect(self.update_r_table)
    clear.pressed.connect(self.clear)
    ok.pressed.connect(self.exec)

    layout.addLayout(header)
    layout.addLayout(self.config)
    layout.addLayout(self.center)
    layout.addLayout(footer)

    self.setLayout(layout)
    self.update_config()

  def update_config(self):
    i = self.funcs.currentIndex()
    clear_layout(self.config)
    self.config.addWidget(Fields.render(self.configs[i].items, vertical = True))

    if i == 0:
      self.l_table.hideColumn(1)
      self.r_table.show()
    else:
      self.l_table.showColumn(1)
      self.r_table.hide()

  def update_l_table(self, files: List[str] = None):
    self.l_table.setRowCount(0)
    self.l_table.setRowCount(len(files))

    for r, file in enumerate(files):
      self.l_table.setCellWidget(r, 0, QLabel(os.path.normpath(file)))
      self.l_table.setCellWidget(r, 1, QLabel('待执行'))

  def update_r_table(self, files: List[str] = None):
    self.r_table.setRowCount(0)
    self.r_table.setRowCount(len(files))

    for r, file in enumerate(files):
      self.r_table.setCellWidget(r, 0, QLabel(os.path.normpath(file)))

  def exec(self):
    idx = self.funcs.currentIndex()
    config = self.configs[idx]
    val = config.get_vals()[0]

    self.status.setText('执行中，请稍后...')
    if idx == 0:
      lefts = self.l_table.selectedIndexes()
      rights = self.r_table.selectedIndexes()
      new_name = val['重命名为']

      for i, item in enumerate(lefts):
        file = self.l_table.cellWidget(item.row(), 0).text()
        name, ext = file_name_and_ext(file)
        name = new_name or name
        dest = self.r_table.cellWidget(rights[i].row(), 0).text()
        dest_name = normal_join(dest, name + ext)

        if os.path.exists(dest_name):
          os.rename(dest_name, dest_name + '.bak')

        shutil.move(file, dest_name)

      lefts.reverse()
      for item in lefts:
        self.l_table.removeRow(item.row())

      self.status.setText('完成！')

    elif idx == 1:
      self.thread = Worker(self.c_left.files)
      self.thread.updated.connect(self.match_content)
      self.thread.start()

  def match_content(self, r: int, content: str):
    self.l_table.selectRow(r)
    self.status.setText(f'{r + 1}/{len(self.c_left.files)}')

    idx = self.funcs.currentIndex()
    config = self.configs[idx].get_vals()[0]
    pattern = re.compile(config['匹配内容'])
    result = re.search(pattern, content)

    if result:
      matched = result.group()
      self.l_table.setCellWidget(r, 1, QLabel(f'匹配到信息：{matched}'))
    else:
      self.l_table.setCellWidget(r, 1, QLabel('未匹配到相关信息，请手动重命名'))

    self.l_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

  def clear(self):
    self.l_table.setRowCount(0)
    self.r_table.setRowCount(0)


class Worker(QThread):
  updated = Signal(int, str)

  def __init__(self, files: List[str], page = 0):
    super().__init__()
    self.files = files
    self.page = page

  def run(self):
    for r, file in enumerate(self.files):
      content = ocr_pdf(file, self.page)
      self.updated.emit(r, content)
