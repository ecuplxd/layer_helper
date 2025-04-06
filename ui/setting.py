from typing import List

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QVBoxLayout

from ui.drag import DragDropWidget


class SettingWidget(DragDropWidget):
  setting = {
    'finish_open': True,
    'temp'       : './temp99999',
    'out'        : '',
    'work_dirs'  : [],
  }

  def __init__(self):
    super().__init__()
    self.table = QTableWidget()
    self.init_ui()

  def init_ui(self):
    setting = self.setting
    layout = QVBoxLayout()

    check = QCheckBox('完成后打开目录')
    check.setChecked(setting['finish_open'])

    h = QHBoxLayout()
    edit = QLineEdit()
    edit.setText(setting['temp'])
    h.addWidget(QLabel('临时目录'))
    h.addWidget(edit)
    h.addStretch()

    self.table.setColumnCount(1)
    self.table.setHorizontalHeaderLabels(['名称'])

    layout.addWidget(check)
    layout.addLayout(h)
    layout.addWidget(QLabel('常用目录（把目录拖进来）'))
    layout.addWidget(self.table)

    self.dropped.connect(self.update_table)

    layout.addStretch()
    self.setLayout(layout)
    self.update_table()

  def update_table(self, files: List[str] = None):
    work_dirs = self.setting['work_dirs']

    if files is not None:
      work_dirs = list(set(work_dirs + files))

    self.setting['work_dirs'] = work_dirs

    self.table.setRowCount(0)
    self.table.setRowCount(len(work_dirs))
    for r, file in work_dirs:
      self.table.setCellWidget(r, 0, QLabel(file))
