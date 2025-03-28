# -*- encoding: utf-8 -*-

import glob
import json
import os
import shutil
import time
from typing import List, Any

import comtypes
import cv2
import fitz
import numpy as np
import pandas as pd
from pytesseract import pytesseract
from scipy import ndimage
from win32com.client import DispatchEx

from ui.helper import Notify, NOTIFY


def parse_sfz(id_str: str):
  birth = id_str[6: 14]
  birth_format = birth[0:4] + '/' + birth[4:6] + '/' + birth[6:]
  # 奇数男性，偶数女性
  gender = id_str[-2]

  return gender, pd.to_datetime(birth_format)


def list_at(l: List[Any], idx: int, default=None):
  try:
    return l[idx]
  except IndexError:
    return default


# 路径相关
def make_dir(folder: str):
  if os.path.exists(folder):
    return

  os.mkdir(folder)


def del_folder(folder: str, recreate=True):
  try:
    if os.path.exists(folder):
      shutil.rmtree(folder)

      if recreate:
        make_dir(folder)
    else:
      print(f'{folder} 不存在')
  except OSError as e:
    print(f'删除 {folder} 失败：{e}')


def get_file_name(file: str):
  return os.path.splitext(os.path.abspath(file))[0]


def file_2_type(file, ext='pdf'):
  return os.path.normpath(get_file_name(file) + '.' + ext)


def find_file(folder: str, filter_str: str, rec=True):
  matches = glob.glob(folder + '/' + filter_str, recursive=rec)

  return matches


def find_files(folders: List[str], filter_strs: List[str], rec=True):
  result = []

  for folder in folders:
    for filter_str in filter_strs:
      result += find_file(folder, filter_str, rec)

  return result


def del_files(files: List[str]):
  for file in files:
    os.remove(file)


# json 相关
def excel_2_json(excel_file: str):
  excel_data = pd.read_excel(excel_file)
  json_str = excel_data.to_json(orient='records', force_ascii=False)
  rows = json.loads(json_str)

  return rows


def json_file_2_json(json_file: str):
  with open(json_file, encoding='utf-8', mode='r') as f:
    return json.loads(f.read())


# pdf 工具类
def merge_pdf(pdf_files: List[str], new_name: str = None, del_raw=False):
  new_doc = fitz.open()

  for file in pdf_files:
    doc = fitz.open(file)
    new_doc.insert_pdf(doc, from_page=0, to_page=-1)
    doc.close()

  new_doc.save(new_name)
  new_doc.close()

  if del_raw:
    del_files(pdf_files)


def extract_pdf(pdf_file, s: int = 0, e=0, out: str = None, new_name: str = None, preview=False):
  """
  提取 pdf 文件指定页码范围为一个新的 pdf 文件
  :param pdf_file:
  :param s:
  :param e:
  :param out:
  :param new_name:
  :return:
  """
  out = out or get_file_name(pdf_file)
  new_name = new_name or f'part_{s + 1}_{e + 1}'
  full = os.path.join(out, new_name + '.pdf')

  if preview:
    return full

  doc = fitz.open(pdf_file)
  new_doc = fitz.open()
  new_doc.insert_pdf(doc, from_page=s, to_page=e)

  make_dir(out)
  new_doc.save(full)
  new_doc.close()
  doc.close()


def split_pdf(pdf_file: str, step=1, s=0, e=None, out: str = None, new_name=None, preview=False):
  """
  规则分割 pdf 文件
  :param pdf_file:
  :param s:
  :param e:
  :param step:
  :param out:
  :param new_name:
  :param preview:
  :return:
  """
  doc = fitz.open(pdf_file)
  page_num = e or doc.page_count
  doc.close()
  outputs = []
  idx = 0

  for i in range(s, page_num, step):
    end = min(i + step - 1, page_num - 1)

    if new_name:
      outputs.append(extract_pdf(pdf_file, i, end, out, f'{i}-{new_name}', preview))
    else:
      outputs.append(extract_pdf(pdf_file, i, end, out, new_name, preview))

    if not preview:
      NOTIFY.done.emit(idx)
      time.sleep(0.03)

    idx += 1

  return outputs


def ocr_pdf(pdf_file: str, page=0, dpi=350):
  doc = fitz.open(pdf_file)
  page = doc.load_page(page)
  pix = page.get_pixmap(dpi)
  img = np.frombuffer(pix.samples_mv, dtype=np.uint8).reshape((pix.height, pix.width, 3)).copy()
  result = pytesseract.image_to_string(img, lang='chi_sim')
  result = result.replace(' ', '')

  return result


def correct_pdf_orien(pdf_file: str):
  pass


def rotate_pdf(pdf_file: str, angle):
  pass


# https://zhuanlan.zhihu.com/p/384500542
# https://stackoverflow.com/questions/6011115/doc-to-pdf-using-python
def word_2_pdf(word_file: str, new_name: str = None):
  wdFormatPDF = 17
  word = comtypes.client.CreateObject('Word.Application')
  doc = word.Documents.Open(word_file)
  new_name = new_name or file_2_type(word_file)
  doc.SaveAs(new_name, FileFormat=wdFormatPDF)
  doc.Close()
  word.Quit()


# https://zhuanlan.zhihu.com/p/564822327
def excel_2_pdf(excel_file, new_name: str = None):
  xl_app = DispatchEx("Excel.Application")
  xl_app.Visible = False
  xl_app.DisplayAlerts = 0
  books = xl_app.Workbooks.Open(excel_file, False)
  new_name = new_name or file_2_type(excel_file)
  books.ExportAsFixedFormat(0, new_name)
  books.Close(False)
  xl_app.Quit()


def img_2_pdf(img_file: str, new_name: str = None):
  doc = fitz.open()
  img_doc = fitz.open(img_file)
  pdf_bytes = img_doc.convert_to_pdf()
  img_pdf = fitz.open('pdf', pdf_bytes)
  doc.insert_pdf(img_pdf)
  new_name = new_name or file_2_type(img_file)
  doc.save(new_name)


# word 工具类
def merge_word(word_files: List[str], new_name: str):
  pass


def split_word(word_file: str, step=1):
  pass


# 图片类
def rotate_img(img_file: str):
  pass


def float_convertor(x):
  if x.isdigit():
    out = float(x)
  else:
    out = x
  return out


def correct_img_orien(img_file: str, new_name: str = None):
  img = cv2.imread(img_file)
  k = pytesseract.image_to_osd(img)
  out = {i.split(":")[0]: float_convertor(i.split(":")[-1].strip()) for i in k.rstrip().split("\n")}
  img_rotated = ndimage.rotate(img, 360 - out["Rotate"])
  cv2.imwrite(new_name or img_file, img_rotated)


def main():
  # correct_img_orien('./_test/2.jpg', './test.jpg')
  split_pdf('./_test/pdf/S30C-0i25032516150.pdf')


if __name__ == '__main__':
  main()
