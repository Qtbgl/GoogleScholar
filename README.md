GoogleScholar下创建data目录，

加入[api_config.py](data%2Fapi_config.py)

设置 ipfoxy_proxy_auth = 'username:password@ip:port'

设置 app_key = '<API_KEY>'

设置 scholarly_use_proxy = True

设置scholarly_alter_code = True

scholarly推荐从github中下载，避免更新停留在2023年
```shell
git clone -b develop https://github.com/scholarly-python-package/scholarly.git
cd .\scholarly
pip install .
```
