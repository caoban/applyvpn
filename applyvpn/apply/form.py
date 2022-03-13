#! /usr/bin/env python
# encoding: utf-8
#从Flask-WTF导入Form类，而表单字段和验证函数直接从WTForms导入。
from flask_wtf import FlaskForm
from wtforms import SubmitField,StringField ,PasswordField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp



class ApplyInfoForm(FlaskForm):
    name = StringField(
        # 标签
        label="姓名",
        # 验证器
        validators=[
            DataRequired('请输入姓名')
        ],
        #description="姓名",
        # 附加选项,会自动在前端判别
        render_kw={
            "class": "form-control",
            "placeholder": "请输入姓名",
            "required":'required'               #表示输入框不能为空
        }
    )

    worknumber = StringField(
        label="工号",
        # 验证器
        validators=[
            DataRequired('请输入工号')
        ],
        #description="邮箱",
        # 附加选项,会自动在前端判别
        render_kw={
            "class": "form-control",
            "placeholder": "请输入工号",
            "required": 'required'          #表示输入框不能为空
        }
    )

    phone = StringField(
        label="手机号码",
        # 验证器
        validators=[
            DataRequired('请输入手机号码'),
            Regexp("1[3578]\d{9}", message="手机格式不正确")       #用正则匹配手机号码规则
        ],
        #description="手机",
        # 附加选项,会自动在前端判别
        render_kw={
            "class": "form-control",
            "placeholder": "请输入手机号码",
            "required": 'required'              #表示输入框不能为空
        }
    )

    #前后台最好是一致的
    captcha = StringField(
        label="验证码",
        # 验证器
        validators=[
            DataRequired('请输入验证码'),
            Length(min=6, max=6, message="验证码为6位数。")  # 6位数字的验证吗
        ],
        # description="验证码",
        # 附加选项,会自动在前端判别
        render_kw={
            "class": "form-control",
            "placeholder": "请输入验证码",
            "required": 'required'  # 表示输入框不能为空
        }
    )


    reason = TextAreaField(
        label="申请理由",
        # 验证器
        validators=[
            DataRequired('请输入申请理由')
        ],
        #description="手机",
        # 附加选项,会自动在前端判别
        render_kw={
            "class": "form-control",
            "placeholder": "请输入申请理由",
            "required": 'required'              #表示输入框不能为空
        }
    )
    #使用前段的标签来提交
    #submit = SubmitField('申请')




class AuditForm(FlaskForm):
    submit_pass = SubmitField('审核通过')
    submit_refuse = SubmitField('审核拒绝')

    reason = TextAreaField(
        label="审核结果说明：",
        # 验证器
        validators=[
            DataRequired('请输入审核结果说明')
        ],
        render_kw={
            "class": "form-control",
            "placeholder": "请输入审核结果说明",
            "required": 'required'              #表示输入框不能为空
        }
    )
