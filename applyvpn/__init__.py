#! /usr/bin/env python
#初始化项目的工厂函数

from flask import Flask
#config.py中导入config字典
from config import config
from flask_bootstrap import Bootstrap

#CSS框架
bootstrap = Bootstrap()

def create_apply(env):
    env_config = config.get(env)
    app = Flask(__name__)
    #app不是目录app，是flask对象app
    #app.config.from_object 是flask python系统是使用方法，不在自己写的config
    app.config.from_object(env_config)

    bootstrap.init_app(app)

    #导入之前申明出来的蓝本对象。应该是。
    from .apply import apply as apply_blueprint
    app.register_blueprint(apply_blueprint, urlprefix='/apply')

    return app




