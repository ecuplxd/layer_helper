# -*- encoding: utf-8 -*-

import glob
import json
import os
import shutil
import time
from typing import Any, List

import comtypes
import cv2
import fitz
import numpy as np
import pandas as pd
from cv2.typing import MatLike
from pymupdf.mupdf import PDF_ENCRYPT_KEEP
from pytesseract import pytesseract
from scipy import ndimage
from win32com.client import DispatchEx

from ui.signal import NOTIFY


def parse_sfz(id_str: str):
  birth = id_str[6: 14]
  birth_format = birth[0:4] + '/' + birth[4:6] + '/' + birth[6:]
  # 奇数男性，偶数女性
  gender = id_str[-2]

  return gender, pd.to_datetime(birth_format)


def list_at(l: List[Any], idx: int, default = None):
  try:
    return l[idx]
  except IndexError:
    return default


# 路径相关
def make_dir(folder: str):
  if os.path.exists(folder):
    return

  os.mkdir(folder)


def del_folder(folder: str, recreate = True):
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


def file_name_and_ext(file):
  return os.path.splitext(os.path.basename(file))


def get_file_folder(file: str):
  return os.path.dirname(get_file_name(file))


def file_2_type(file, ext = 'pdf'):
  return os.path.normpath(get_file_name(file) + '.' + ext)


def find_file(folder: str, filter_str: str, rec = True):
  matches = glob.glob(folder + '/' + filter_str, recursive = rec)

  return matches


def find_files(folders: List[str], filter_strs: List[str], rec = True):
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
  json_str = excel_data.to_json(orient = 'records', force_ascii = False)
  rows = json.loads(json_str)

  return rows


def json_file_2_json(json_file: str):
  with open(json_file, encoding = 'utf-8', mode = 'r') as f:
    return json.loads(f.read())


# pdf 工具类
def merge_pdf(pdf_files: List[str], new_name: str = None, del_raw = False):
  new_doc = fitz.open()

  for file in pdf_files:
    doc = fitz.open(file)
    new_doc.insert_pdf(doc, from_page = 0, to_page = -1)
    doc.close()

  out, new_name = merge_name(pdf_files[0], new_name)
  save_pdf(new_doc, out, new_name)

  if del_raw:
    del_files(pdf_files)


def merge_name(file: str, new_name: str = None):
  out = get_file_folder(file)

  if not new_name:
    time_str = time.strftime("%Y%m%d%H%M%S", time.localtime())
    new_name = f'merged-{time_str}'

  return out, new_name


def save_pdf(doc, out, name):
  make_dir(out)
  doc.save(os.path.join(out, name + '.pdf'), garbage = 4)
  doc.close()


def _extract_pdf(doc, s = 0, e = -1):
  new_doc = fitz.open()
  new_doc.insert_pdf(doc, from_page = s, to_page = e)

  return new_doc


def extract_pdf(pdf_file, s: int = 0, e = -1, out: str = None, new_name: str = None):
  """
  提取 pdf 文件指定页码范围为一个新的 pdf 文件
  :param pdf_file:
  :param s:
  :param e:
  :param out:
  :param new_name:
  :return:
  """
  doc = fitz.open(pdf_file)
  new_doc = _extract_pdf(doc, s, e)

  out, new_name, _ = extract_name(pdf_file, s, e, out, new_name)
  save_pdf(new_doc, out, new_name)
  doc.close()


def extract_name(pdf_file: str, s: int = 0, e: int = -1, out: str = None, new_name: str = None):
  out = out or get_file_name(pdf_file)
  new_name = new_name or f'part_{s + 1}_{e + 1}'
  full = os.path.normpath(os.path.join(out, new_name + '.pdf'))

  return out, new_name, full


def split_pdf(pdf_file: str, step = 1, s = 0, e = None, out: str = None, new_name = None, r = 0):
  """
  规则分割 pdf 文件
  :param pdf_file:
  :param s:
  :param e:
  :param step:
  :param out:
  :param new_name:
  :param r:
  :return:
  """
  page_num = e or get_pdf_page(pdf_file)
  idx = 0

  for i in range(s, page_num, step):
    end = min(i + step - 1, page_num - 1)
    extract_pdf(pdf_file, i, end, out, new_name)
    NOTIFY.extracted_pdf.emit(r, idx)
    time.sleep(0.03)

    idx += 1


def get_pdf_page(pdf_file: str):
  doc = fitz.open(pdf_file)
  count = doc.page_count
  doc.close()
  return count


def split_name(pdf_file, step = 1, s = 0, e = None, out = None, new_name = None):
  outputs = []
  page_num = e or get_pdf_page(pdf_file)

  for i in range(s, page_num, step):
    if new_name:
      _, _, full = extract_name(pdf_file, out = out, new_name = f'{i}_{new_name}')
    else:
      end = min(i + step - 1, page_num - 1)
      _, _, full = extract_name(pdf_file, i, end, out)

    outputs.append(os.path.normpath(full))

  return outputs


def ocr_pdf(pdf_file: str, page = 0, dpi = 350):
  img = pdf_2_image(pdf_file, page, dpi)
  result = pytesseract.image_to_string(img, lang = 'chi_sim')
  result = result.replace(' ', '')

  return result


def pdf_2_image(pdf_file: str, page = 0, dpi = 350):
  doc = fitz.open(pdf_file)
  page = doc.load_page(page)
  pix = page.get_pixmap(dpi = dpi)
  img = np.frombuffer(pix.samples_mv, dtype = np.uint8).reshape((pix.height, pix.width, 3)).copy()
  doc.close()

  return img


def correct_pdf_orient(pdf_file: str, page = 0, new_name: str = None, incremental = False):
  image = pdf_2_image(pdf_file, page)
  angle = get_rotate_angle(image)['Rotate']
  rotate_pdf(pdf_file, angle)


def rotate_pdf(pdf_file: str, angle: float = 0.0, new_name: str = None, incremental = False):
  if angle == 0:
    return

  angle = int(((360 - angle) / 90) * 90)
  doc = fitz.open(pdf_file)

  for page in doc:
    page.set_rotation(angle)

  if incremental:
    doc.save(doc.name, incremental = True, encryption = PDF_ENCRYPT_KEEP)
  else:
    name = new_name or doc.name.replace('.pdf', f'-校正方向.pdf')
    doc.save(name)
    
  doc.close()


# https://zhuanlan.zhihu.com/p/384500542
# https://stackoverflow.com/questions/6011115/doc-to-pdf-using-python
def word_2_pdf(word_file: str, new_name: str = None):
  wdFormatPDF = 17
  word = comtypes.client.CreateObject('Word.Application')
  doc = word.Documents.Open(word_file)
  new_name = new_name or file_2_type(word_file)
  doc.SaveAs(new_name, FileFormat = wdFormatPDF)
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


def cv_img_2_pdf(img_file: str, image: MatLike):
  temp_name = './temp123456.jpg'
  new_name = file_2_type(img_file)
  write_img(image, temp_name)
  img_2_pdf(temp_name, new_name)
  os.remove(temp_name)

  return new_name


# word 工具类
def merge_word(word_files: List[str], new_name: str):
  pass


def split_word(word_file: str, step = 1):
  pass


# 图片类
def rotate_img(image, angle = 0):
  if angle == 0:
    return image

  return ndimage.rotate(image, 360 - angle)


def img_bleach(image, window_size = 15, k = 0.2, r = 128):
  if len(image.shape) > 2:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  else:
    gray = image

  mean = cv2.blur(gray, (window_size, window_size))
  mean_square = cv2.blur(gray * gray, (window_size, window_size))
  std = np.sqrt(mean_square - mean * mean)

  # 计算阈值
  threshold = mean * (1 + k * (std / r - 1))

  # 阈值化图像
  binary = np.zeros_like(gray)
  binary[gray > threshold] = 255

  return binary


def float_convertor(x):
  if x.isdigit():
    out = float(x)
  else:
    out = x
  return out


def resize_im(im, scale, max_scale = None):
  f = float(scale) / min(im.shape[0], im.shape[1])

  if max_scale is not None and f * max(im.shape[0], im.shape[1]) > max_scale:
    f = float(max_scale) / max(im.shape[0], im.shape[1])

  return cv2.resize(im, (0, 0), fx = f, fy = f)


def get_rotate_angle(image):
  # resized_img = resize_im(image, scale=600, max_scale=1200)
  k = pytesseract.image_to_osd(image, config = '--psm 0')
  out = { i.split(":")[0]: float_convertor(i.split(":")[-1].strip()) for i in k.rstrip().split("\n") }

  return out


def correct_img_orient(image):
  out = get_rotate_angle(image)
  img_rotated = rotate_img(image, out['Rotate'])

  return img_rotated


def read_img(img_file: str):
  with open(img_file, 'rb') as f:
    return cv2.imdecode(np.frombuffer(f.read(), np.int8), cv2.IMREAD_COLOR)


def write_img(image, name):
  ext = name.split('.')[-1]

  with open(name, 'wb') as f:
    ret, buf = cv2.imencode(f".{ext}", image)
    if ret:
      f.write(buf.tobytes())
      return True
    else:
      return False


def main():
  # img = read_img('./_test/imgs/微信图片_20250328111930.jpg')
  # new_image = img_bleach(img)
  # cv2.imwrite('./test.jpg', new_image)
  correct_pdf_orient('./S30C-0i25031710240.pdf')


if __name__ == '__main__':
  main()
