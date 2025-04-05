# 环境搭建

- 下载 Python https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe
- 下载 Git https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe
- 下载 Tesseract-OCR（用于 OCR） https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe
- 下载 Traineddata，选择 chi_sim 放入 tessdata 目录 https://github.com/tesseract-ocr/tessdata
- 下载 VSCode（可选，用于开发） https://code.visualstudio.com/Download

# 启定一个命令行

```shell
git clone clone https://github.com/ecuplxd/layer_helper.git
cd layer_helper
pip install uv
uv sync
# 启动
python main.py
```
