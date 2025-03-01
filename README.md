GoogleScholar下创建data目录，

加入[api_config.py](data%2Fapi_config.py)

设置 ipfoxy_proxy_auth = 'username:password@ip:port'

设置 app_key = '<API_KEY>'

设置 scholarly_DIY_choose 来修改/配置/默认 scholarly  

> 选择: None, use_proxy, con_spider, por_mirror 


scholarly推荐从github中下载，避免更新停留在2023年
```shell
git clone -b develop https://github.com/scholarly-python-package/scholarly.git
cd .\scholarly
pip install .
```


### 单机版本

离线运行/不需要在服务器上

所有网页通过spider来爬取

抽取出了爬取bib和摘要的代码
