#! /usr/bin/env python
# encoding: utf-8

#从applyvpn包中导入create_apply函数。create_apply在applyvpn的__init__.py中
from applyvpn import create_apply

#执行函数，初始化对象
app = create_apply('default')

if __name__ ==   '__main__':
    app.run(host = '0.0.0.0',port = 8080,debug = True)



