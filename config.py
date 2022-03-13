#! /usr/bin/env python
# encoding: utf-8

import os
#把当前文件的路径添加到系统路径中，这样可以直接使用
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    CSRF_ENABLED = True
    SECRET_KEY = 'youwillneverguess'
    #@staticmethod
    #def init_app(app):
        #pass

class ProductionConfig(Config):
    redis_con = 0

class DevlopConfig(Config):
    redis_con = 0

config = {
    'production': ProductionConfig,
    'develop': DevlopConfig,
    'default': ProductionConfig
}