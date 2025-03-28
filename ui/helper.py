from typing import List, Any, Dict

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QSpinBox, QCheckBox, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel


class Status(QLabel):
  def __init__(self, done=False):
    super().__init__()

    self.setText('待执行')

    if done:
      self.done()

  def done(self):
    self.setText('√')
    self.setStyleSheet("QLabel {color: green}")


class Notify(QObject):
  updated = Signal()
  done = Signal(int)


NOTIFY = Notify()


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
    'hint': hint,
    'val': None,
  }


def num_filed(label: str):
  return {
    'label': label,
    'type': 'num',
    'default': 1,
    'val': 1,
  }


def collect_field_vals(items: List[Any]):
  result = {}

  for item in items:
    result[item['label']] = item['val']

  return result


def create_field(config: Dict):
  label = QLabel(config['label'] + '：')
  val_type = config['type']
  default = config.get('default')
  control = QWidget()

  if val_type == 'num':
    control = QSpinBox()
    control.setValue(default)
    control.valueChanged.connect(lambda x: update_field(x, config))
  elif val_type == 'bool':
    control = QCheckBox()
  elif val_type == 'text':
    control = QLineEdit()
    control.setPlaceholderText(config['hint'])
    control.textChanged.connect(lambda x: update_field(x, config))

  return label, control


def update_field(v, config):
  config['val'] = v
  NOTIFY.updated.emit()


def render_fields(parent: QVBoxLayout, items: List[Any]):
  h = QHBoxLayout()

  for item in items:
    label, control = create_field(item)
    h.addWidget(label)
    h.addWidget(control)

  h.addStretch()
  parent.addLayout(h)
