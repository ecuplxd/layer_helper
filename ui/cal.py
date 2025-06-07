from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QPlainTextEdit,
                               QPushButton, QVBoxLayout,
                               QWidget)

from ui.helper import clear_layout, Field, Fields, VarType
from ui.signal import get_tab_idx, NOTIFY
from util import cal_fees, cal_fenqi


class CalWidget(QWidget):
  form = [
    Fields('诉讼费', [Field(label = '计算减半', type = VarType.BOOL, val = True)]),
    Fields('分期', [
      Field(label = '开始日期', hint = 'yyyy/mm/dd'),
      Field(label = '期数', type = VarType.NUM, val = 24)
    ]
           ),
  ]

  def __init__(self):
    super().__init__()

    self.funcs = QComboBox()
    self.form_container = QHBoxLayout()
    self.l_input = QPlainTextEdit(placeholderText = '粘贴标的额，一行一个')
    self.r_input = QPlainTextEdit(placeholderText = '结果显示在这里')
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()
    header = QHBoxLayout()

    self.funcs.addItems(['诉讼费', '分期'])

    header.addWidget(self.funcs)
    header.addLayout(self.form_container)
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

    self.funcs.currentIndexChanged.connect(self.update_config)
    clear.pressed.connect(self.clear_input)
    ok.pressed.connect(self.cal)
    NOTIFY.field_updated.connect(self.cal)

    layout.addLayout(header)
    layout.addLayout(center)
    layout.addLayout(footer)

    self.r_input.setReadOnly(True)
    self.setLayout(layout)
    self.update_config()

  def update_fenqi(self):
    idx, val = self.get_form_val()
    start_date = val['开始日期']
    total = val['期数']

    if start_date and total:
      self.r_input.setPlainText(cal_fenqi(start_date, total))

  def update_config(self, i = 0):
    clear_layout(self.form_container)
    fields = self.form[i]
    self.form_container.addWidget(Fields.render(fields.items))

    if i == 0:
      self.l_input.show()
    else:
      self.l_input.hide()

  def clear_input(self):
    self.l_input.setPlainText('')
    self.r_input.setPlainText('')

  def get_form_val(self):
    idx = self.funcs.currentIndex()
    fields = self.form[self.funcs.currentIndex()]
    val = Fields.get_val(fields.items)

    return idx, val

  def cal(self):
    if get_tab_idx() != 8:
      return

    idx, val = self.get_form_val()

    if idx == 0:
      nums = [float(line.strip()) for line in self.l_input.toPlainText().strip().split('\n') if line]
      results = [cal_fees(num, val['计算减半']) for num in nums]
      self.r_input.setPlainText('\n'.join(results))
    elif idx == 1:
      self.update_fenqi()
