from PySide6.QtCore import QObject, Signal


class Notify(QObject):
  field_updated = Signal()
  extracted_pdf = Signal(int, int)


NOTIFY = Notify()
TAB_IDX = 0


def update_tab_idx(idx: int):
  global TAB_IDX

  TAB_IDX = idx


def get_tab_idx():
  return TAB_IDX
