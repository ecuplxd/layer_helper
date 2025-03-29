from typing import List, Any, Dict

from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtWidgets import QWidget, QSpinBox, QCheckBox, QLineEdit, QHBoxLayout, QLabel


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
  field_updated = Signal()
  extracted_pdf = Signal(int, int)


NOTIFY = Notify()


def clear_all_children(node):
  for i in reversed(range(node.childCount())):
    node.removeChild(node.child(i))


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
  result = []

  if isinstance(items[0], list):
    for row in items:
      result.append(collect_field_val(row))
  else:
    result.append(collect_field_val(items))

  return result


def collect_field_val(items):
  val = {}
  for item in items:
    val[item['label']] = item['val']
  return val


def create_field(config: Dict):
  label = QLabel(config['label'] + '：')
  val = config.get('val')
  val_type = config['type']
  control = QWidget()

  if val is None:
    val = config.get('default')

  if val_type == 'num':
    control = QSpinBox()
    control.setValue(val)
    control.valueChanged.connect(lambda x: update_field(x, config))
  elif val_type == 'bool':
    control = QCheckBox()
    control.setChecked(val)
  elif val_type == 'text':
    control = QLineEdit()
    control.setText(val)
    control.setPlaceholderText(config['hint'])
    control.textChanged.connect(lambda x: update_field(x, config))

  return label, control


def update_field(v, config):
  config['val'] = v
  NOTIFY.field_updated.emit()


def render_fields(items: List[Any]):
  widget = QWidget()
  h = QHBoxLayout()
  h.setAlignment(Qt.AlignLeft)

  for item in items:
    label, control = create_field(item)
    h.addWidget(label)
    h.addWidget(control)

  widget.setLayout(h)

  return widget
