### 环境配置

scholarly推荐从github中下载，避免更新停留在2023年

_但其中直接pip也可以_

```shell
git clone -b develop https://github.com/scholarly-python-package/scholarly.git
cd .\scholarly
pip install .
```

root/config目录下创建一系列 *.txt 配置文件，文件名后缀前与 *.py 同名


### 单机版本

离线运行/不需要在服务器上

所有网页通过spider来爬取

抽取出了爬取bib和摘要的代码
