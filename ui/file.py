import os
import shutil
from typing import List

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QVBoxLayout,
                               QWidget,
                               )

from ui.drag import DragDropWidget
from ui.helper import Field, Fields, VarType, clear_layout
from util import file_name_and_ext, normal_join


class FileWidget(QWidget):
  configs = [
    Fields('快速一对一移入', [Field(label = '重命名为（同名文件将添加 .bak 后缀）', hint = '选填')]),
    Fields('识别要素并重命名', [Field(label = '匹配内容', hint = '使用正则表达式'),
                                Field(label = '是否含有以下内容', type = VarType.TEXTAREA,
                                      hint = '粘贴表格内容，一行一个'
                                      ),
                                Field(label = '命名规则', hint = '选填')]
           )
  ]

  def __init__(self):
    super().__init__()

    self.config = QVBoxLayout()
    self.funcs = QComboBox()
    self.center = QHBoxLayout()
    self.status = QLabel()
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

    self.l_table.setColumnCount(1)
    self.l_table.setHorizontalHeaderLabels(['原文件'])
    self.l_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    self.r_table.setColumnCount(1)
    self.r_table.setHorizontalHeaderLabels(['目录'])
    self.r_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

    c_left = DragDropWidget()
    c_right = DragDropWidget()

    c_left.setLayout(QVBoxLayout())
    c_right.setLayout(QVBoxLayout())

    c_left.layout().addWidget(self.l_table)
    c_right.layout().addWidget(self.r_table)

    self.center.addWidget(c_left)
    self.center.addWidget(c_right)

    footer = QHBoxLayout()
    clear = QPushButton('清空')
    ok = QPushButton('执行')
    footer.addStretch()
    footer.addWidget(self.status)
    footer.addWidget(clear)
    footer.addWidget(ok)

    self.funcs.currentIndexChanged.connect(self.update_config)
    c_left.dropped.connect(self.update_l_table)
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

  def update_l_table(self, files: List[str] = None):
    self.l_table.setRowCount(0)
    self.l_table.setRowCount(len(files))

    for r, file in enumerate(files):
      self.l_table.setCellWidget(r, 0, QLabel(os.path.normpath(file)))

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

        print(file, dest_name)

        if os.path.exists(dest_name):
          os.rename(dest_name, dest_name + '.bak')

        shutil.move(file, dest_name)

      lefts.reverse()
      for item in lefts:
        self.l_table.removeRow(item.row())

      self.status.setText('完成！')

    elif idx == 1:
      pass

  def clear(self):
    self.l_table.setRowCount(0)
    self.r_table.setRowCount(0)
