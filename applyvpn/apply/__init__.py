#! /usr/bin/env python
# encoding: utf-8

#apply 模块的蓝本。同样还可以有很多其他的类似的模块的蓝本。
from flask import Blueprint

#创建蓝本对象应该是 views.py中用到
apply = Blueprint('apply', __name__)

# 导入路由模块、或者其他模块。
# 这样导入apply包的时候--》__init__.py--》导入了这个包中的视图等模块，这样就可以直接使用了
# 在蓝本的末尾导入,因为在这里还要导入蓝本，防止循环导入依赖
from . import views
