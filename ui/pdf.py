from typing import List

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QVBoxLayout, QComboBox, QPushButton, QHBoxLayout, QHeaderView, \
  QTreeWidget, QTreeWidgetItem, QLabel

from ui.drag import DragDropWidget
from ui.helper import clear_layout, text_field, num_filed, render_fields, collect_field_vals, NOTIFY, \
  clear_all_children
from util import preview_split_pdf, list_at, get_pdf_page, split_pdf, merged_name, merge_pdf


def regular_config():
  return [
    num_filed('页数'),
    text_field('新文件名'),
  ]


def unregular_config():
  return [
    text_field('范围', '1-3'),
    text_field('新文件名'),
  ]


class PDFWidget(DragDropWidget):
  config_map = {
    '规则分割': {
      'items': [regular_config()]
    },
    '不规则分割': {
      'arr': True,
      'items': [
        unregular_config()
      ],
    },
    '合并': {
      'items': [
        text_field('新文件名'),
      ]
    },
  }

  files: List[str] = ['./_test/pdf/S30C-0i25031710240.pdf',
                      './_test/pdf/S30C-0i25032516120.pdf',
                      './_test/pdf/S30C-0i25032516150.pdf',
                      './_test/pdf/S30C-0i25032609510.pdf',
                      './_test/pdf/S30C-0i25032610080.pdf',
                      './_test/pdf/S30C-0i25032717070.pdf',
                      './_test/pdf/S30C-0i25032814300.pdf',
                      './_test/pdf/S30C-0i25032814320.pdf', ]
  cur = 0
  total = 0

  def __init__(self):
    super().__init__()
    self.config_layout = QVBoxLayout()
    self.funcs = QComboBox()
    self.add_btn = QPushButton('增加')
    self.file_tree = QTreeWidget()
    self.status = QLabel()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    h = QHBoxLayout()
    self.funcs.addItems(['规则分割', '不规则分割', '合并'])
    h.addWidget(self.funcs)
    h.addWidget(self.add_btn)
    h.addStretch()

    self.file_tree.setColumnCount(3)
    self.file_tree.setHeaderLabels(['原文件', '配置', '状态'])
    self.file_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

    h2 = QHBoxLayout()
    ok = QPushButton('执行')
    clear = QPushButton('清空')
    h2.addStretch()
    h2.addWidget(self.status)
    h2.addWidget(clear)
    h2.addWidget(ok)

    layout.addLayout(h)
    layout.addLayout(self.config_layout)
    layout.addWidget(self.file_tree)
    layout.addLayout(h2)

    self.funcs.currentIndexChanged.connect(self.update_config_ui)
    self.add_btn.clicked.connect(self.add_field)
    ok.clicked.connect(self.exe_fun)
    clear.clicked.connect(self.clear_files)
    self.dropped.connect(self.update_table)
    NOTIFY.field_updated.connect(self.update_table)
    NOTIFY.extracted_pdf.connect(self.mark_extract_done)

    self.update_config_ui()
    self.setLayout(layout)
    self.update_table()

  def add_field(self):
    items = self.cur_config_items()
    items.append(unregular_config())
    self.config_layout.addWidget(render_fields(items[-1]))

  def update_config_ui(self):
    clear_layout(self.config_layout)
    self.clear_files()
    idx = self.funcs.currentIndex()

    if idx == 1:
      self.add_btn.show()
      items = self.cur_config_items()
      for group in items:
        self.config_layout.addWidget(render_fields(group))
    else:
      self.add_btn.hide()

      if idx == 2:
        self.config_layout.addWidget(render_fields(self.cur_config_items()))

  def update_table(self, files: List[str] = None):
    if files:
      self.file_tree.clear()

    self.total = 0
    self.files = files or self.files

    files = [file for file in self.files if '.pdf' in file]
    fun_name = self.funcs.currentText()

    if fun_name == '规则分割':
      self.file_tree.showColumn(1)
      self.file_tree.showColumn(2)

      for r, file in enumerate(files):
        item = self.file_tree.topLevelItem(r)
        items = self.cur_config_items()
        fields = list_at(items, r)

        if not fields:
          fields = regular_config()
          items.append(fields)

        config = collect_field_vals(fields)[0]

        if not item:
          item = QTreeWidgetItem(self.file_tree)
          self.file_tree.setItemWidget(item, 1, render_fields(fields))

        # Perf：解决渲染过慢的问题
        item.setExpanded(False)
        page_num = get_pdf_page(file)
        output_files = preview_split_pdf(file, config['页数'], e=page_num, new_name=config['新文件名'])
        first_child = item.child(0)
        item.setText(0, f'{file} - {page_num} 页 {len(output_files)} 份')
        self.total += len(output_files)

        if not first_child or first_child.text(0) != output_files[0]:
          clear_all_children(item)
          for out_file in output_files:
            child = QTreeWidgetItem(item)
            child.setText(0, out_file)
            child.setText(2, '待执行')

        item.setExpanded(True)
    elif fun_name == '合并':
      self.file_tree.clear()
      self.file_tree.hideColumn(1)
      self.file_tree.hideColumn(2)

      for file in self.files:
        item = QTreeWidgetItem(self.file_tree)
        item.setText(0, file)

      val = collect_field_vals(self.cur_config_items())[0]

      if val['新文件名']:
        self.status.setText(val['新文件名'])
      else:
        self.status.setText(f'默认名为：merged-年月日时分秒')

  def mark_extract_done(self, i: int, j: int):
    self.cur += 1
    item = self.file_tree.topLevelItem(i)
    child = item.child(j)
    child.setText(2, '√')

    if item.child(j + 1):
      self.file_tree.scrollToItem(item.child(j + 1))
    else:
      self.file_tree.scrollToItem(child)

    self.status.setText(f'{self.cur}/{self.total}')

  def cur_config_items(self):
    config = self.config_map[self.funcs.currentText()]

    return config['items']

  def clear_files(self):
    self.files = []
    self.file_tree.clear()
    self.status.setText('')

  def exe_fun(self):
    items = self.cur_config_items()
    vals = collect_field_vals(items)
    fun_name = self.funcs.currentText()

    if fun_name == '规则分割':
      self.thread = Worker(self.files, vals)
      self.thread.start()
    elif fun_name == '不规则分割':
      pass
    elif fun_name == '合并':
      val = vals[0]
      merge_pdf(self.files, val['新文件名'])
      self.status.setText('已合并')
    else:
      pass


class Worker(QThread):
  def __init__(self, files: List[str], configs: List):
    super().__init__()
    self.files = files
    self.configs = configs

  def run(self):
    for r, file in enumerate(self.files):
      config = self.configs[r]
      split_pdf(file, config['页数'], new_name=config['新文件名'], r=r)
