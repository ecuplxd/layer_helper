import time
from typing import List

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QVBoxLayout, QComboBox, QPushButton, QHBoxLayout, QHeaderView, \
  QTreeWidget, QTreeWidgetItem, QLabel

from ui.drag import DragDropWidget
from ui.helper import clear_layout, text_field, num_filed, render_fields, collect_field_vals, NOTIFY, \
  clear_all_children
from util import split_name, list_at, get_pdf_page, split_pdf, merge_pdf, extract_name, extract_pdf


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
        unregular_config(),
      ],
    },
    '合并': {
      'items': [
        text_field('新文件名', '默认名为：merged-年月日时分秒'),
      ]
    },
  }

  files: List[str] = []
  cur = 0
  total = 0

  def __init__(self):
    super().__init__()
    self.thread = None
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
    self.add_btn.pressed.connect(self.add_field)
    ok.pressed.connect(self.exe_fun)
    clear.pressed.connect(self.clear_files)
    self.dropped.connect(self.update_table)
    NOTIFY.field_updated.connect(self.update_table)
    NOTIFY.extracted_pdf.connect(self.mark_extract_done)

    self.update_config_ui()
    self.update_table()
    self.setLayout(layout)

  def add_field(self, idx=None):
    items = self.cur_config_items()

    if idx is None:
      items.append(unregular_config())
      idx = len(items) - 1

    widget = render_fields(items[idx], idx)
    btn = widget.findChild(QPushButton)
    btn.pressed.connect(lambda: self._test(idx))

    self.config_layout.addWidget(widget)
    self.update_table()

  def _test(self, i):
    items = self.cur_config_items()
    items.pop(i)
    self.update_config_ui()
    self.update_table()

  def update_config_ui(self):
    idx = self.funcs.currentIndex()
    items = self.cur_config_items()
    clear_layout(self.config_layout)
    self.clear_files()
    self.add_btn.hide()

    if idx == 0:
      self.file_tree.showColumn(1)
    else:
      self.file_tree.hideColumn(1)
      if idx == 1:
        self.add_btn.show()

        for i, _ in enumerate(items):
          self.add_field(i)
      elif idx == 2:
        self.config_layout.addWidget(render_fields(items))

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
        output_files = split_name(file, config['页数'], e=page_num, new_name=config['新文件名'])
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
    else:
      self.file_tree.clear()
      vals = collect_field_vals(self.cur_config_items())

      for file in self.files:
        self.total += len(vals)
        page_num = get_pdf_page(file)
        item = QTreeWidgetItem(self.file_tree)
        item.setText(0, f'{file} - {page_num} 页')

      if fun_name == '合并':
        val = vals[0]
        if val['新文件名']:
          self.status.setText(f'新文件名：{val['新文件名']}.pdf')
        else:
          self.status.setText(f'')
      else:
        for r, file in enumerate(self.files):
          tree_item = self.file_tree.topLevelItem(r)
          clear_all_children(tree_item)
          ranges = self.parse_range(file)

          for item in ranges:
            child = QTreeWidgetItem(tree_item)
            child.setText(0, item['full'])
            child.setText(2, '待执行')
          tree_item.setExpanded(True)

  def parse_range(self, pdf_file: str):
    vals = collect_field_vals(self.cur_config_items())
    page_num = get_pdf_page(pdf_file)
    result = []

    for val in vals:
      range_str = val['范围']
      new_name = val['新文件名']

      if not range_str:
        meta = {
          's': 0,
          'e': page_num,
          'new_name': new_name,
        }
      else:
        range_str = range_str.split('-')
        s = range_str[0] or 1
        e = list_at(range_str, 1, s)
        meta = {
          's': int(s) - 1,
          'e': int(e) - 1,
          'new_name': new_name
        }

      _, _, full = extract_name(pdf_file, meta['s'], meta['e'], new_name=meta['new_name'])
      meta['full'] = full
      result.append(meta)

    return result

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
    self.cur = 0
    items = self.cur_config_items()
    vals = collect_field_vals(items)
    fun_name = self.funcs.currentText()

    if fun_name == '规则分割':
      self.thread = Worker(self.files, vals)
      self.thread.start()
    elif fun_name == '不规则分割':
      for i, file in enumerate(self.files):
        metas = self.parse_range(file)
        for j, meta in enumerate(metas):
          extract_pdf(file, meta['s'], meta['e'], new_name=meta['new_name'])
          self.mark_extract_done(i, j)
          time.sleep(0.03)
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
