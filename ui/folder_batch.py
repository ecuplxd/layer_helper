import os.path
import time

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFileSystemModel, QHBoxLayout,
                               QHeaderView, QLabel, QListView, QPushButton, QSplitter, QTableWidget, QTreeView,
                               QVBoxLayout, QWidget,
                               )

from ui.helper import clear_layout, Status
from util import correct_img_orient, correct_pdf_orient, excel_2_pdf, file_2_type, find_files, img_2_pdf, word_2_pdf


class FolderBatchWidget(QWidget):
  ops = ['校正方向', '将以下文件转为 PDF']
  op_file_types = [['图片', 'PDF 扫描件'], ['Word', 'Excel', '图片']]
  file_type_map = {
    '图片'      : {
      'tran_fun': [correct_img_orient, img_2_pdf],
      'exts'    : [['.jpg', True], ['.png', True]]
    },
    'PDF 扫描件': {
      'tran_fun': [correct_pdf_orient, None],
      'exts'    : [['.pdf', True]]
    },
    'Word'      : {
      'tran_fun': [None, word_2_pdf],
      'exts'    : [['.doc', True], ['.docx', True]]
    },
    'Excel'     : {
      'tran_fun': [None, excel_2_pdf],
      'exts'    : [['.xls', True], ['.xlxs', True]]
    },
  }

  folders = []

  matched_files = []

  def __init__(self):
    super().__init__()

    self.thread = None
    self.file_type_layout = QVBoxLayout()
    self.folder_table = QTableWidget()
    self.file_table = QTableWidget()
    self.funcs_select = QComboBox()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    header = QHBoxLayout()

    self.funcs_select.addItems(self.ops)
    view_btn = QPushButton('选择目录')
    header.addWidget(self.funcs_select)
    header.addStretch()
    header.addWidget(view_btn)

    self.folder_table.setColumnCount(1)
    self.folder_table.setHorizontalHeaderLabels(['目录'])
    self.folder_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    self.file_table.setColumnCount(3)
    self.file_table.setHorizontalHeaderLabels(['原文件', '新文件', '状态'])
    self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    self.file_table.hide()

    footer = QHBoxLayout()
    ok_btn = QPushButton('执行')
    recur_flag = QCheckBox('递归')
    recur_flag.setChecked(True)
    footer.addStretch()
    footer.addWidget(recur_flag)
    footer.addWidget(ok_btn)

    splitter = QSplitter(Qt.Vertical)
    splitter.addWidget(self.folder_table)
    splitter.addWidget(self.file_table)

    layout.addLayout(header)
    layout.addLayout(self.file_type_layout)
    layout.addWidget(splitter)
    layout.addLayout(footer)

    self.setLayout(layout)

    self.funcs_select.currentIndexChanged.connect(self.show_file_type)
    view_btn.pressed.connect(self.choose_folders)
    ok_btn.pressed.connect(self.exec_fun)
    self.funcs_select.setCurrentIndex(1)

  def show_file_type(self, i: int = 0):
    clear_layout(self.file_type_layout)

    for file_type in self.op_file_types[i]:
      h_layout = QHBoxLayout()
      h_layout.addWidget(QLabel(file_type + '：'))
      config = self.file_type_map[file_type]
      exts = config['exts']

      for ext in exts:
        checkbox = QCheckBox(ext[0])
        checkbox.setChecked(ext[1])
        h_layout.addWidget(checkbox)
        # 坑
        checkbox.stateChanged.connect(lambda x, cur = ext: self.update_ext(x, cur))

      h_layout.addStretch()
      self.file_type_layout.addLayout(h_layout)

  def update_ext(self, flag: int, ext):
    ext[1] = flag != 0
    self.update_file_table()

  def update_folder_table(self, folders):
    self.folder_table.setRowCount(0)
    self.folder_table.setRowCount(len(folders))

    for r, folder in enumerate(folders):
      self.folder_table.setCellWidget(r, 0, QLabel(os.path.normpath(folder)))

  def update_file_table(self):
    if len(self.folders) == 0:
      return

    self.file_table.setRowCount(0)
    self.file_table.show()

    self.matched_files = []
    op_idx = self.funcs_select.currentIndex()

    for file_type in self.op_file_types[op_idx]:
      config = self.file_type_map.get(file_type)
      exts = config['exts']
      tran_fun = config['tran_fun'][op_idx]
      filters = [f'**/*{ext[0]}' for ext in exts if ext[1]]
      for file in find_files(self.folders, filters):
        self.matched_files.append({
          'name'    : os.path.normpath(file),
          'new_name': file_2_type(file),
          'status'  : '待执行',
          'tran_fun': tran_fun
        }
        )

    self.file_table.setRowCount(len(self.matched_files))

    for r, matched in enumerate(self.matched_files):
      self.file_table.setCellWidget(r, 0, QLabel(matched['name']))
      self.file_table.setCellWidget(r, 1, QLabel(matched['new_name']))
      self.file_table.setCellWidget(r, 2, QLabel(matched['status']))

  def exec_fun(self):
    self.thread = Worker(self.matched_files[:])
    self.thread.updated.connect(self.update_file_table_status)
    self.thread.start()

  def update_file_table_status(self, r):
    self.file_table.setCellWidget(r, 2, Status(True))
    self.file_table.selectRow(r)

  # https://gist.github.com/sneakers-the-rat/22c3449e2c7043c594712bce89c27e8e
  def choose_folders(self):
    file_dialog = QFileDialog()
    file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    file_dialog.setFileMode(QFileDialog.Directory)
    file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

    for widget_type in (QListView, QTreeView):
      for view in file_dialog.findChildren(widget_type):
        if isinstance(view.model(), QFileSystemModel):
          view.setSelectionMode(QAbstractItemView.ExtendedSelection)

    if file_dialog.exec():
      self.folders = file_dialog.selectedFiles()
      self.update_folder_table(self.folders)
      self.update_file_table()


class Worker(QThread):
  updated = Signal(int)

  def __init__(self, items):
    super().__init__()
    self.items = items

  def run(self):
    for (r, item) in enumerate(self.items):
      item['tran_fun'](item['name'], item['new_name'])
      time.sleep(0.03)
      self.updated.emit(r)
