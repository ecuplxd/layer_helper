from dataclasses import dataclass
from enum import Enum
from typing import List, TypeVar

import cv2
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QSpinBox, QCheckBox, QLineEdit, QHBoxLayout, QLabel, QPushButton


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


def text_field(label: str, hint='选填', val: str = None):
  return {
    'label': label,
    'type': 'text',
    'default': None,
    'hint': hint,
    'val': val,
  }


def num_filed(label: str):
  return {
    'label': label,
    'type': 'num',
    'default': 1,
    'val': 1,
  }


class VarType(Enum):
  TEXT = 1
  BOOL = 2
  NUM = 3
  DATE = 4


T = TypeVar('T')


@dataclass
class Field:
  label: str
  type: VarType = VarType.TEXT
  val: T = None
  hint: str = ''
  default: T = None

  changed = Signal(T)

  def set_val(self, val: T):
    self.val = val
    NOTIFY.field_updated.emit()

  def render(self):
    label = QLabel(self.label + '：')
    val = self.val
    val_type = self.type
    control = QWidget()

    if val is None:
      val = self.default

    if self.type == VarType.NUM:
      control = QSpinBox()
      control.setValue(val)
      control.valueChanged.connect(self.set_val)
    elif val_type == VarType.BOOL:
      control = QCheckBox()
      control.setChecked(val)
    elif val_type == VarType.TEXT:
      control = QLineEdit()
      control.setText(val)
      control.setPlaceholderText(self.hint)
      control.textChanged.connect(self.set_val)

    return label, control


@dataclass
class Fields:
  name: str
  items: List[Field | List[Field]]
  is_arr: bool = False

  def size(self):
    return len(self.items)

  def get_item(self, i=0):
    return self.items[i]

  def del_item(self, i: int):
    self.items.pop(i)

  @staticmethod
  def render(fields: List[Field], i=None):
    widget = QWidget()
    h = QHBoxLayout()
    h.setAlignment(Qt.AlignLeft)

    for field in fields:
      label, control = field.render()
      h.addWidget(label)
      h.addWidget(control)

    if i is not None:
      btn = QPushButton('删除')
      h.addWidget(btn)
      btn.pressed.connect(widget.deleteLater)

    widget.setLayout(h)

    return widget

  @staticmethod
  def get_val(fields: List[Field]):
    val = {}
    for field in fields:
      val[field.label] = field.val
    return val

  def append(self, field: Field):
    self.items.append(field)

  def get_vals(self):
    result = []

    if not self.items or len(self.items) == 0:
      return result

    if self.is_arr:
      for group in self.items:
        result.append(Fields.get_val(group))
    else:
      result.append(Fields.get_val(self.items))

    return result


def cv_2_qimage(image):
  image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
  height, width, channel = image_rgb.shape
  bytes_per_line = channel * width
  q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
  pixmap = QPixmap.fromImage(q_image)

  return pixmap
