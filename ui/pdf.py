import time
from typing import List

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QVBoxLayout, QComboBox, QPushButton, QHBoxLayout, QTableWidget, QLabel, QHeaderView

from ui.drag import DragDropWidget
from ui.helper import clear_layout, text_field, num_filed, render_fields, collect_field_vals, NOTIFY, Status
from util import split_pdf


class PDFWidget(DragDropWidget):
  config_map = {
    '规则分割': {
      'items': [
        num_filed('页数'),
        text_field('新文件名'),
      ]
    },
    '不规则分割': {
      'arr': True,
      'items': [
        [
          text_field('范围', '1-3'),
          text_field('新文件名'),
        ],
      ],
    },
    '合并': {
      'items': [
        text_field('新文件名'),
      ]
    },
  }

  files: List[str] = ['./_test/pdf/S30C-0i25032516150.pdf']

  def __init__(self):
    super().__init__()
    self.config_layout = QVBoxLayout()
    self.funcs = QComboBox()
    self.add_btn = QPushButton('增加')
    self.table = QTableWidget()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    h = QHBoxLayout()
    self.funcs.addItems(['规则分割', '不规则分割', '合并'])
    h.addWidget(self.funcs)
    h.addWidget(self.add_btn)
    h.addStretch()

    self.table.setColumnCount(3)
    self.table.setHorizontalHeaderLabels(['原文件', '处理后', '状态'])
    self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

    h2 = QHBoxLayout()
    ok = QPushButton('执行')
    h2.addStretch()
    h2.addWidget(ok)

    layout.addLayout(h)
    layout.addLayout(self.config_layout)
    layout.addWidget(self.table)
    # layout.addStretch()
    layout.addLayout(h2)

    self.funcs.currentIndexChanged.connect(self.ui_form)
    self.add_btn.clicked.connect(self.add_field)
    ok.clicked.connect(self.exe_fun)
    self.dropped.connect(self.update_table)
    NOTIFY.updated.connect(self.update_table)
    NOTIFY.done.connect(self.mark_done)

    self.ui_form()
    self.setLayout(layout)

  def add_field(self):
    config = self.config_map.get(self.funcs.currentText())

    if config.get('arr'):
      render_fields(self.config_layout, config['items'][0])

  def ui_form(self):
    config = self.config_map.get(self.funcs.currentText())
    is_arr = config.get('arr')
    items = config['items']

    if is_arr:
      self.add_btn.show()
    else:
      self.add_btn.hide()

    clear_layout(self.config_layout)

    if is_arr:
      for group in items:
        render_fields(self.config_layout, group)
    else:
      render_fields(self.config_layout, items)

  def update_table(self, files: List[str] = None):
    self.table.setRowCount(0)
    self.files = files or self.files

    files = [file for file in self.files if '.pdf' in file]
    fun_name = self.funcs.currentText()
    output_files = []

    if fun_name == '规则分割':
      val = self.cur_config()
      output_files = split_pdf(files[0], val['页数'], new_name=val['新文件名'], preview=True)

    self.table.setRowCount(len(output_files))
    self.table.setCellWidget(0, 0, QLabel(files[0]))

    for r, file in enumerate(output_files):
      self.table.setCellWidget(r, 1, QLabel(file))
      self.table.setCellWidget(r, 2, Status())

  def mark_done(self, r: int):
    self.table.setCellWidget(r, 2, Status(True))
    self.table.selectRow(r)

  def cur_config(self):
    config = self.config_map[self.funcs.currentText()]
    vals = collect_field_vals(config['items'])

    return vals

  def exe_fun(self):
    config = self.config_map[self.funcs.currentText()]
    vals = collect_field_vals(config['items'])
    fun_name = self.funcs.currentText()

    if fun_name == '规则分割':
      val = self.cur_config()
      self.thread = Worker(self.files[0], val['页数'], val['新文件名'])
      self.thread.updated.connect(self.mark_done)
      self.thread.start()
    elif fun_name == '不规则分割':
      pass
    elif fun_name == '合并':
      pass
    else:
      pass

    print(vals)


class Worker(QThread):
  updated = Signal(int)

  def __init__(self, file: str, page: int, new_name: str):
    super().__init__()
    self.file = file
    self.page = page
    self.new_name = new_name
    NOTIFY.done.connect(lambda r: self.updated.emit(r))

  def run(self):
    split_pdf(self.file, self.page, new_name=self.new_name)

