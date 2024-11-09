import os
from typing import Union

from fastapi import FastAPI, Path, Query


app = FastAPI()


# 获取当前脚本所在目录
app_dir = os.path.dirname(os.path.abspath(__file__))

# 获取上一级目录
project_root = os.path.dirname(app_dir)
