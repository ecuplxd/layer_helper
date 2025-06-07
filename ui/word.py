import os.path
from typing import List

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QVBoxLayout

from ui.drag import DragDropWidget
from ui.helper import clear_layout, Field, Fields
from ui.signal import get_tab_idx, NOTIFY
from util import file_2_type, get_file_folder, merge_pdf, merge_word, normal_join, word_2_pdf


class WordWidget(DragDropWidget):
  configs = [
    Fields('转为 PDF', [Field(label = '新文件名', hint = '选填')]),
    Fields('合并为 Word', [Field(label = '新文件名', hint = '默认名为：merged-年月日时分秒')]),
    Fields('合并为 PDF', [Field(label = '新文件名', hint = '默认名为：merged-年月日时分秒')]),
  ]

  def __init__(self):
    super().__init__()

    self.table = QTableWidget()
    self.config = QVBoxLayout()
    self.funcs = QComboBox()
    self.status = QLabel()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    header = QHBoxLayout()
    self.funcs.addItems(['转为 PDF', '合并为 Word', '合并为 PDF'])
    header.addWidget(self.funcs)
    header.addLayout(self.config)
    header.addStretch()

    self.table.setColumnCount(3)
    self.table.setHorizontalHeaderLabels(['原文件', '输出', '状态'])

    footer = QHBoxLayout()
    clear = QPushButton('清空')
    exe = QPushButton('执行')
    footer.addStretch()
    footer.addWidget(self.status)
    footer.addWidget(clear)
    footer.addWidget(exe)

    clear.pressed.connect(self.clear_table)
    exe.pressed.connect(self.exec_fun)
    self.funcs.currentIndexChanged.connect(self.update_config)
    self.dropped.connect(self.update_table)
    NOTIFY.field_updated.connect(self.update_table)

    layout.addLayout(header)
    layout.addWidget(self.table)
    layout.addLayout(footer)
    self.setLayout(layout)
    self.update_config()

  def update_config(self, files: List[str] = None):
    i = self.funcs.currentIndex()
    clear_layout(self.config)
    self.config.addWidget(Fields.render(self.configs[i].items))
    self.update_table()

  def clear_table(self):
    self.files = []
    self.update_table()

  def update_table(self):
    if get_tab_idx() != 1:
      return

    self.table.setRowCount(0)
    self.table.setRowCount(len(self.files))

    for r, file in enumerate(self.files):
      self.table.setCellWidget(r, 0, QLabel(os.path.normpath(file)))
      self.table.setCellWidget(r, 1, QLabel(file_2_type(file)))
      self.table.setCellWidget(r, 2, QLabel('待执行'))

    self.status.setText(f'共 {len(self.files)} 个')

    i = self.funcs.currentIndex()
    if i == 0:
      self.table.showColumn(1)
      self.table.showColumn(2)
    else:
      if i == 1:
        self.table.hideColumn(1)
        self.table.hideColumn(2)
      else:
        self.table.hideColumn(1)
        self.table.showColumn(2)
      val = self.configs[i].get_vals()[0]
      self.status.setText(f'新文件名：{val['新文件名'] or '使用默认'}')

  def exec_fun(self):
    i = self.funcs.currentIndex()
    val = self.configs[i].get_vals()[0]
    new_name = val['新文件名']

    if i == 0 or i == 2:
      self.thread = Worker(self.files)

      if i == 2:
        self.thread.new_name = 'temp'
        self.status.setText('合并中，请稍后...')
        self.thread.all_done.connect(self.merge_pdf)

      self.thread.updated.connect(self.mark_done)
      self.thread.start()
    elif i == 1:
      self.status.setText('合并中，请稍后...')
      merge_word(self.files, new_name)
      self.status.setText('合并完成！')
    else:
      pass

  def merge_pdf(self, pdf_files: List[str]):
    i = self.funcs.currentIndex()
    val = self.configs[i].get_vals()[0]
    new_name = val['新文件名']
    merge_pdf(pdf_files, new_name, True)
    self.status.setText('合并完成！')

  def mark_done(self, r: int):
    self.table.setCellWidget(r, 2, QLabel('√'))
    self.status.setText(f'{r + 1}/{len(self.files)}')
    self.table.selectRow(r)


class Worker(QThread):
  updated = Signal(int)
  all_done = Signal(list)
  files: List[str]

  def __init__(self, files: List[str], new_name: str = None):
    super().__init__()
    self.files = files
    self.new_name = new_name

  def run(self):
    outs = []

    for r, file in enumerate(self.files):
      new_name = self.new_name

      if new_name is not None:
        out = get_file_folder(file)
        new_name = normal_join(out, f'{new_name}-{r}.pdf')
        outs.append(new_name)

      word_2_pdf(file, new_name)
      self.updated.emit(r)

    self.all_done.emit(outs)
