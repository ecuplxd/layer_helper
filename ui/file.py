import os
import re
import shutil
import time
from typing import Any, List

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout,
                               QWidget,
                               )

from ui.drag import DragDropWidget
from ui.helper import clear_layout, Field, Fields, VarType
from ui.signal import get_tab_idx, NOTIFY
from util import file_name_and_ext, filename_with_parent_dir, filter_file_by_glob, normal_join, normal_path, ocr_pdf


class FileWidget(QWidget):
  configs = [
    Fields('快速一对一移入', [Field(label = '重命名为', hint = '选填（同名文件将添加 .bak 后缀）')]),
    Fields('识别要素并重命名', [Field(label = '需要识别的内容', hint = '使用正则表达式', val = ''),
                                Field(label = '使用第几列数据进行匹配', type = VarType.NUM),
                                Field(label = '粘贴 Excel 数据', type = VarType.TEXTAREA),
                                Field(label = '跳过第一行', type = VarType.BOOL, val = True),
                                Field(label = '命名规则',
                                      hint = '选填，如：2025-{1}-{2}-判决书，将用第 1、2 列数据替换 {} 内容',
                                      )]
           ),
    Fields('按规则挑选文件',
           [Field(label = '待整理目录', type = VarType.TEXT),
            Field(label = '保存目录', type = VarType.TEXT),
            Field(label = '规则',
                  hint = '一行一个，out glob 规则 glob 规则', type = VarType.TEXTAREA)
            ]),
  ]

  excel_data = []
  cur_config = []
  rules = []
  cur = 0
  total = 0
  expanded = True

  def __init__(self):
    super().__init__()

    self.config = QVBoxLayout()
    self.funcs = QComboBox()
    self.center = QHBoxLayout()
    self.toggle_btn = QPushButton('全部收起')
    self.status = QLabel()
    self.c_left = DragDropWidget()
    self.l_table = QTableWidget()
    self.r_table = QTableWidget()
    self.file_tree = QTreeWidget()
    self.l_table.setLayout(QVBoxLayout())
    self.r_table.setLayout(QVBoxLayout())
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    header = QHBoxLayout()
    self.funcs.addItems(['快速一对一移入', '识别要素并重命名', '按规则挑选文件'])
    header.addWidget(self.funcs)
    header.addStretch()

    self.file_tree.setColumnCount(1)
    self.file_tree.setHeaderLabels(['名称', '保存信息', '状态'])
    self.file_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
    self.l_table.setColumnCount(3)
    self.l_table.setHorizontalHeaderLabels(['原文件', '识别结果', '状态'])
    self.l_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    self.l_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    self.l_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    self.r_table.setColumnCount(1)
    self.r_table.setHorizontalHeaderLabels(['移入目录'])
    self.r_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

    c_right = DragDropWidget()
    self.c_left.files = []

    self.c_left.setLayout(QVBoxLayout())
    c_right.setLayout(QVBoxLayout())

    self.c_left.layout().addWidget(self.l_table)
    c_right.layout().addWidget(self.r_table)

    self.center.addWidget(self.file_tree)
    self.center.addWidget(self.c_left)
    self.center.addWidget(c_right)

    footer = QHBoxLayout()
    clear = QPushButton('清空')
    ok = QPushButton('执行')
    footer.addStretch()
    footer.addWidget(self.status)
    footer.addWidget(self.toggle_btn)
    footer.addWidget(clear)
    footer.addWidget(ok)

    self.funcs.currentIndexChanged.connect(self.update_config)
    self.c_left.dropped.connect(self.update_l_table)
    NOTIFY.field_updated.connect(self.update_file_tree)
    c_right.dropped.connect(self.update_r_table)
    self.toggle_btn.pressed.connect(self.toggle_file_tree)
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
    self.toggle_btn.hide()
    self.file_tree.hide()

    if i == 0:
      self.l_table.hideColumn(1)
      self.l_table.hideColumn(2)
      self.l_table.show()
      self.r_table.show()
    elif i == 1:
      self.l_table.showColumn(1)
      self.l_table.showColumn(2)
      self.r_table.hide()
    elif i == 2:
      self.l_table.hide()
      self.r_table.hide()
      self.toggle_btn.show()
      self.file_tree.show()
      self.update_file_tree()

  def update_l_table(self, files: List[str] = None):
    self.l_table.setRowCount(0)
    self.l_table.setRowCount(len(files))

    for r, file in enumerate(files):
      self.l_table.setCellWidget(r, 0, QLabel(os.path.normpath(file)))
      self.l_table.setCellWidget(r, 2, QLabel('待执行'))

  def update_r_table(self, files: List[str] = None):
    self.r_table.setRowCount(0)
    self.r_table.setRowCount(len(files))

    for r, file in enumerate(files):
      self.r_table.setCellWidget(r, 0, QLabel(os.path.normpath(file)))

  def update_file_tree(self):
    if get_tab_idx() != 5:
      return

    idx = self.funcs.currentIndex()

    if idx == 2:
      result = self.collect_files()
      self.file_tree.clear()
      self.status.setText(f'共 {self.total} 个文件')

      for item in result:
        row = QTreeWidgetItem(self.file_tree)
        name = item['name']
        out = item['out']
        size = len(item['files'])
        row.setText(0, f'{name} - 共找出 {size} 个文件')
        row.setText(1, f'{out}')

        for file in item['files']:
          child = QTreeWidgetItem(row)
          child.setText(0, f'{file['src']}')
          child.setText(1, f'    {file['name']}')

        row.setExpanded(self.expanded)

  def collect_files(self):
    self.update_cur_config()
    self.total = 0
    result = []
    target = self.cur_config['待整理目录'] or ''
    out: str = self.cur_config['保存目录'] or ''
    rules = self.cur_config['规则'] or ''

    if not target or not out or not rules:
      return result

    rules = [line.split(' ') for line in rules.strip().split('\n')]

    for rule in rules:
      files: list[str] = []
      globs = rule[1:]

      for glob in globs:
        files += filter_file_by_glob(target, glob)

      files = list(set(files))
      self.total += len(files)
      result.append({
        'name' : rule[0],
        'out'  : os.path.join(out, rule[0]),
        'files': [filename_with_parent_dir(file) for file in files]
      })

    return result

  def update_cur_config(self):
    idx = self.funcs.currentIndex()
    config = self.configs[idx]
    val = config.get_vals()[0]
    self.cur_config = val

    return val

  def exec(self):
    idx = self.funcs.currentIndex()
    val = self.update_cur_config()

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
      self.parse_excel_data()
      self.thread = Worker(self.c_left.files)
      self.thread.updated.connect(self.match_content)
      self.thread.start()

    elif idx == 2:
      self.expanded = False
      self.toggle_file_tree()
      result = self.collect_files()
      self.cur = 0
      self.thread = Worker2(result)
      self.thread.updated.connect(self.mark_done)
      self.thread.start()

  def mark_done(self, i: int, j: int):
    self.cur += 1
    item = self.file_tree.topLevelItem(i)
    child = item.child(j)
    child.setText(2, '√')

    if item.child(j + 1):
      self.file_tree.scrollToItem(item.child(j + 1))
    else:
      self.file_tree.scrollToItem(child)

    self.status.setText(f'{self.cur}/{self.total}')

  def parse_excel_data(self):
    data: str = self.cur_config['粘贴 Excel 数据'] or ''
    rule: str = self.cur_config['命名规则'].strip()
    self.excel_data = [line.split('\t') for line in data.strip().split('\n')]

    token = ''
    rules = []
    for ch in rule:
      if ch == '{':
        if token:
          rules.append(token)
          token = ''
      elif ch == '}':
        rules.append(int(token))
        token = ''
      else:
        token += ch

    if token:
      rules.append(token)

    self.rules = rules

  def match_content(self, r: int, content: str):
    self.l_table.selectRow(r)
    self.status.setText(f'{r + 1}/{len(self.c_left.files)}')

    config = self.cur_config
    pattern = re.compile(config['需要识别的内容'])
    result = re.search(pattern, content)

    if config['跳过第一行']:
      rows = self.excel_data[1:]
    else:
      rows = self.excel_data[:]

    if result:
      i = config['使用第几列数据进行匹配']
      matched = result.group()
      in_list = None
      self.l_table.setCellWidget(r, 1, QLabel(matched))

      for row in rows:
        if row[i] in matched:
          in_list = row
          break

      if in_list is not None:
        file = self.c_left.files[r]
        file_name, _ = file_name_and_ext(file)
        new_name = ''

        for rule in self.rules:
          if isinstance(rule, int):
            new_name += in_list[rule]
          else:
            new_name += rule

        new_name = file.replace(file_name, new_name)
        os.rename(file, new_name)
        self.l_table.setCellWidget(r, 2, QLabel(f'重名为：{new_name}'))
      else:
        self.l_table.setCellWidget(r, 2, QLabel('无法匹配，请手动重命名'))

    else:
      self.l_table.setCellWidget(r, 1, QLabel('未识别到相关信息，请手动重命名'))

    self.l_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    self.l_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

  def clear(self):
    self.l_table.setRowCount(0)
    self.r_table.setRowCount(0)

  def toggle_file_tree(self):
    self.expanded = not self.expanded
    if self.expanded:
      self.toggle_btn.setText('全部收起')
      self.file_tree.expandAll()
    else:
      self.toggle_btn.setText('全部展开')
      self.file_tree.collapseAll()


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


class Worker2(QThread):
  updated = Signal(int, int)

  def __init__(self, result: List[Any]):
    super().__init__()
    self.result = result

  def run(self):
    for r, item in enumerate(self.result):
      out: str = item['out']

      if not os.path.exists(out):
        os.mkdir(out)

      for j, file in enumerate(item['files']):
        dst = normal_path(os.path.join(out, file['name']))
        shutil.copyfile(file['src'], dst)
        self.updated.emit(r, j)
        time.sleep(0.03)
