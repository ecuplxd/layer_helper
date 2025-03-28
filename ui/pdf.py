from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QHBoxLayout, QFormLayout, QSpinBox, \
  QCheckBox, QLineEdit

from ui.helper import clear_layout, text_field, num_filed, render_fields


class PDFWidget(QWidget):
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


  def __init__(self):
    super().__init__()
    self.config_layout = QVBoxLayout()
    self.funcs = QComboBox()
    self.add_btn = QPushButton('增加')
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    h = QHBoxLayout()
    self.funcs.addItems(['规则分割', '不规则分割', '合并'])
    h.addWidget(self.funcs)
    h.addWidget(self.add_btn)
    h.addStretch()

    h2 = QHBoxLayout()
    ok = QPushButton('执行')
    h2.addStretch()
    h2.addWidget(ok)

    layout.addLayout(h)
    layout.addLayout(self.config_layout)
    layout.addStretch()
    layout.addLayout(h2)

    self.funcs.currentIndexChanged.connect(self.ui_form)
    self.add_btn.clicked.connect(self.add_field)

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


  def update_form(self):
    pass
