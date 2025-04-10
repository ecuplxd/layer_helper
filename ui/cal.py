from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from util import cal_fees


class CalWidget(QWidget):
  cal_half = True

  def __init__(self):
    super().__init__()

    self.funcs = QComboBox()
    self.l_input = QPlainTextEdit(placeholderText = '粘贴标的额，一行一个')
    self.r_input = QPlainTextEdit()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    header = QHBoxLayout()
    half = QCheckBox('同时计算减半')
    half.setChecked(self.cal_half)
    self.funcs.addItems(['诉讼费'])

    header.addWidget(self.funcs)
    header.addWidget(half)
    header.addStretch()

    center = QHBoxLayout()

    center.addWidget(self.l_input)
    center.addWidget(self.r_input)

    footer = QHBoxLayout()
    ok = QPushButton('执行')
    clear = QPushButton('清空')
    footer.addStretch()
    footer.addWidget(clear)
    footer.addWidget(ok)

    clear.pressed.connect(self.clear_input)
    ok.pressed.connect(self.cal)

    layout.addLayout(header)
    layout.addLayout(center)
    layout.addLayout(footer)

    self.setLayout(layout)

  def clear_input(self):
    self.l_input.setPlainText('')
    self.r_input.setPlainText('')

  def cal(self):
    idx = self.funcs.currentIndex()

    if idx == 0:
      nums = [float(line.strip()) for line in self.l_input.toPlainText().strip().split('\n')]
      results = [cal_fees(num) for num in nums]
      self.r_input.setPlainText('\n'.join(results))
