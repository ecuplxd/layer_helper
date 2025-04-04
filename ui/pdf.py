import time
from typing import Any, List

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout,
                               )
from cv2.typing import MatLike

from ui.drag import DragDropWidget
from ui.helper import (Field, Fields, VarType, clear_all_children, clear_layout, read_img_as_qt_thumb)
from ui.signal import NOTIFY
from util import (extract_name, extract_pdf, get_pdf_page, get_rotate_angle, list_at, merge_pdf, pdf_2_image,
                  rotate_img, rotate_pdf, split_name, split_pdf,
                  )


def regular_config():
  return [
    Field(label = '页数', type = VarType.NUM, val = 1),
    Field(label = '新文件名'),
  ]


def un_regular_config():
  return [
    Field(label = '范围', hint = '1 或 1-3'),
    Field(label = '新文件名'),
  ]


class PDFWidget(DragDropWidget):
  config_map = {
    '规则分割'  : Fields('规则分割', [regular_config()]),
    '不规则分割': Fields('不规则分割', [un_regular_config()], is_arr = True),
    '合并'      : Fields('合并', [
      Field(label = '新文件名', hint = '默认名为：merged-年月日时分秒')],
                         ),
    '校正方向'  : Fields('校正方向', [Field(label = '基准页', type = VarType.NUM, val = 1)])
  }

  files: List[str] = []
  cur = 0
  total = 0
  last_images: List[MatLike] = []
  angles: List[float] = []

  def __init__(self):
    super().__init__()
    self.thread = None
    self.config_layout = QVBoxLayout()
    self.funcs = QComboBox()
    self.add_btn = QPushButton('增加')
    self.file_tree = QTreeWidget()
    self.status = QLabel()
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    h = QHBoxLayout()
    self.funcs.addItems(['规则分割', '不规则分割', '合并', '校正方向'])
    h.addWidget(self.funcs)
    h.addWidget(self.add_btn)
    h.addStretch()

    self.file_tree.setColumnCount(5)
    self.file_tree.setHeaderLabels(['原文件', '配置', '缩略', '预览', '状态'])
    self.file_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

    h2 = QHBoxLayout()
    ok = QPushButton('执行')
    clear = QPushButton('清空')
    h2.addStretch()
    h2.addWidget(self.status)
    h2.addWidget(clear)
    h2.addWidget(ok)

    layout.addLayout(h)
    layout.addLayout(self.config_layout)
    layout.addWidget(self.file_tree)
    layout.addLayout(h2)

    self.funcs.currentIndexChanged.connect(self.update_config_ui)
    self.add_btn.pressed.connect(self.add_field)
    ok.pressed.connect(self.exe_fun)
    clear.pressed.connect(self.clear_files)
    self.dropped.connect(self.update_table)
    NOTIFY.field_updated.connect(self.update_table)
    NOTIFY.extracted_pdf.connect(self.mark_extract_done)

    self.update_config_ui()
    self.update_table()
    self.setLayout(layout)

  def add_field(self, idx = None):
    fields = self.cur_config_fields()

    if idx is None:
      fields.append(un_regular_config())
      idx = fields.size() - 1

    widget = Fields.render(fields.get_item(idx), idx)
    btn = widget.findChild(QPushButton)
    btn.pressed.connect(lambda: self._test(idx))

    self.config_layout.addWidget(widget)
    self.update_table()

  def _test(self, i):
    fields = self.cur_config_fields()
    fields.del_item(i)
    self.update_config_ui()
    self.update_table()

  def update_config_ui(self):
    idx = self.funcs.currentIndex()
    fields = self.cur_config_fields()
    clear_layout(self.config_layout)
    self.clear_files()
    self.add_btn.hide()

    if idx != 0:
      if idx == 1:
        self.add_btn.show()

        for i in range(fields.size()):
          self.add_field(i)
      else:
        self.config_layout.addWidget(Fields.render(fields.items))

  def update_table(self, files: List[str] = None):
    if files:
      self.file_tree.clear()

    self.total = 0
    self.files = files or self.files

    files = [file for file in self.files if '.pdf' in file]
    fun_name = self.funcs.currentText()

    if fun_name == '规则分割':
      for r, file in enumerate(files):
        item = self.file_tree.topLevelItem(r)
        fields = self.cur_config_fields()
        items = list_at(fields.items, r)

        if not items:
          items = regular_config()
          fields.append(items)

        config = Fields.get_val(items)

        if not item:
          item = QTreeWidgetItem(self.file_tree)
          self.file_tree.setItemWidget(item, 1, Fields.render(items))

        # Perf：解决渲染过慢的问题
        item.setExpanded(False)
        page_num = get_pdf_page(file)
        output_files = split_name(file, config['页数'], e = page_num, new_name = config['新文件名'])
        first_child = item.child(0)
        item.setText(0, f'{file} - {page_num} 页 {len(output_files)} 份')
        self.total += len(output_files)

        if not first_child or first_child.text(0) != output_files[0]:
          clear_all_children(item)
          for out_file in output_files:
            child = QTreeWidgetItem(item)
            child.setText(0, out_file)
            child.setText(4, '待执行')

        item.setExpanded(True)
    else:
      self.file_tree.clear()
      vals = self.cur_config_fields().get_vals()
      val = vals[0]

      for file in self.files:
        self.total += len(vals)
        page_num = get_pdf_page(file)
        item = QTreeWidgetItem(self.file_tree)
        item.setText(0, f'{file} - {page_num} 页')

      if fun_name == '合并':
        if val['新文件名']:
          self.status.setText(f'新文件名：{val['新文件名']}.pdf')
        else:
          self.status.setText(f'')
      elif fun_name == '不规则分割':
        for r, file in enumerate(self.files):
          tree_item = self.file_tree.topLevelItem(r)
          clear_all_children(tree_item)
          ranges = self.parse_range(file)

          for item in ranges:
            child = QTreeWidgetItem(tree_item)
            child.setText(0, item['full'])
            child.setText(4, '待执行')
          tree_item.setExpanded(True)
      elif fun_name == '校正方向':
        page_num = val['基准页'] - 1
        self.last_images = []
        self.angles = []

        for i, file in enumerate(self.files):
          tree_item = self.file_tree.topLevelItem(i)
          pdf_img = pdf_2_image(file, page_num)
          self.last_images.append(pdf_img)
          self.angles.append(0.0)
          self.file_tree.setItemWidget(tree_item, 2, read_img_as_qt_thumb(pdf_img))
          tree_item.setText(3, '校正中...')
          tree_item.setText(4, '待执行')

        self.thread2 = Worker2(self.last_images)
        self.thread2.updated.connect(self.preview_pdf)
        self.thread2.start()

  def preview_pdf(self, i: int, angle: float = 0.0):
    tree_item = self.file_tree.topLevelItem(i)
    image = self.last_images[i]
    rotated_img = rotate_img(image, angle)

    self.angles[i] = angle
    self.file_tree.setItemWidget(tree_item, 3, read_img_as_qt_thumb(rotated_img))

  def parse_range(self, pdf_file: str):
    vals = self.cur_config_fields().get_vals()
    page_num = get_pdf_page(pdf_file)
    result = []

    for val in vals:
      range_str = val['范围']
      new_name = val['新文件名']

      if not range_str:
        meta = {
          's'       : 0,
          'e'       : page_num,
          'new_name': new_name,
        }
      else:
        range_str = range_str.split('-')
        s = range_str[0] or 1
        e = list_at(range_str, 1, s)
        meta = {
          's'       : int(s) - 1,
          'e'       : int(e) - 1,
          'new_name': new_name
        }

      _, _, full = extract_name(pdf_file, meta['s'], meta['e'], new_name = meta['new_name'])
      meta['full'] = full
      result.append(meta)

    return result

  def mark_extract_done(self, i: int, j: int):
    self.cur += 1
    item = self.file_tree.topLevelItem(i)
    child = item.child(j)
    child.setText(4, '√')

    if item.child(j + 1):
      self.file_tree.scrollToItem(item.child(j + 1))
    else:
      self.file_tree.scrollToItem(child)

    self.status.setText(f'{self.cur}/{self.total}')

  def cur_config_fields(self):
    fields = self.config_map[self.funcs.currentText()]

    return fields

  def clear_files(self):
    self.files = []
    self.file_tree.clear()
    self.status.setText('')

  def exe_fun(self):
    self.cur = 0
    fields = self.cur_config_fields()
    vals = fields.get_vals()
    fun_name = self.funcs.currentText()

    if fun_name == '规则分割':
      self.thread = Worker(self.files, vals)
      self.thread.start()
    elif fun_name == '不规则分割':
      for i, file in enumerate(self.files):
        metas = self.parse_range(file)
        for j, meta in enumerate(metas):
          extract_pdf(file, meta['s'], meta['e'], new_name = meta['new_name'])
          self.mark_extract_done(i, j)
          time.sleep(0.03)
    elif fun_name == '合并':
      val = vals[0]
      merge_pdf(self.files, val['新文件名'])
      self.status.setText('已合并')
    elif fun_name == '校正方向':
      for i, file in enumerate(self.files):
        rotate_pdf(file, self.angles[i])
        item = self.file_tree.topLevelItem(i)
        item.setText(4, '√')
    else:
      pass


class Worker(QThread):
  def __init__(self, files: List[str], configs: List):
    super().__init__()
    self.files = files
    self.configs = configs

  def run(self):
    for r, file in enumerate(self.files):
      config = self.configs[r]
      split_pdf(file, config['页数'], new_name = config['新文件名'], r = r)


class Worker2(QThread):
  updated = Signal(Any, int)

  def __init__(self, images: List[MatLike]):
    super().__init__()
    self.images = images

  def run(self):
    for i, image in enumerate(self.images):
      out = get_rotate_angle(image)
      self.updated.emit(i, out['Rotate'])
      time.sleep(0.03)
