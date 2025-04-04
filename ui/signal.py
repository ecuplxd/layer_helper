from PySide6.QtCore import QObject, Signal


class Notify(QObject):
  field_updated = Signal()
  extracted_pdf = Signal(int, int)


NOTIFY = Notify()
