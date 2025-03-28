from typing import List, Any

from PySide6.QtWidgets import QWidget, QSpinBox, QCheckBox, QLineEdit, QFormLayout, QVBoxLayout, QHBoxLayout, QLabel


def clear_layout(layout):
  if layout is not None:
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget is not None:
        widget.deleteLater()
      else:
        clear_layout(item.layout())


def text_field(label: str, hint='选填'):
  return {
    'label': label,
    'type': 'text',
    'default': None,
    'hint': hint
  }

def num_filed(label: str):
  return {
    'label': label,
    'type': 'num',
    'default': 1,
  }

def create_field(config):
  label = QLabel(config['label'] + '：')
  val_type = config['type']
  default = config.get('default')
  control = QWidget()

  if val_type == 'num':
    control = QSpinBox()
    control.setValue(default)
  elif val_type == 'bool':
    control = QCheckBox()
  elif val_type == 'text':
    control = QLineEdit()
    control.setPlaceholderText(config['hint'])

  return label, control

def render_fields(parent: QVBoxLayout, items: List[Any], add_del = False):
  h = QHBoxLayout()

  for item in items:
    label, control = create_field(item)
    h.addWidget(label)
    h.addWidget(control)

  parent.addLayout(h)
