#! /usr/bin/env python
# encoding: utf-8

import random,time,hashlib,re,logging
from flask import render_template,redirect,url_for,request,flash
import urllib.request
import urllib.parse
from . import apply
from .form import *
from .general import GetUserInfo,CheckUserInfo,RedisOperation,UserFromRedis,SendMessage,RandomNum,CaptchaRedis,CreateVpn,CreateVpnPassword


#日志
LOG_FILE = "application.log"
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=5,
                                               encoding='utf-8')  # 实例化handler

fmt = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(fmt)  # 实例化formatter
handler.setFormatter(formatter)  # 为handler添加formatter

logger = logging.getLogger('application')  # 获取名为tst的logger
logger.addHandler(handler)  # 为logger添加handler
logger.setLevel(logging.DEBUG)



#申请首页
@apply.route('/apply', methods=['GET', 'POST'])
def sendinfo():
    #实例化表单类
    applyinfo_form = ApplyInfoForm()
    return render_template('apply.html', form=applyinfo_form)


#获取验证码
@apply.route('/GetCaptcha', methods=['GET', 'POST'])
def GetCaptcha():
    #获取手机号
    PhoneNumber_input = request.values.get('phone')

    #正则匹配正确是手机号
    try:
        PhoneNumber = re.match('^1[34578]\d{9}$', PhoneNumber_input).group()
    except Exception as err:
        return "请输入正确的手机号"


    #防止是否重复发送（前段还是后端做）

    #生成验证码
    captcha = RandomNum()
    #print("验证码%s" %captcha)

    #下面记录日志用的
    PhoneNumber_captcha = "手机号：" + PhoneNumber + "验证码：" + captcha

    #存入redis，redis中已经有了的，是覆盖还是不存？  默认是覆盖的。 成功的结果是True
    RedisResult = CaptchaRedis(PhoneNumber,captcha,"set")
    if RedisResult == False:
        ret = "验证码存入redis失败 " + PhoneNumber_captcha
        logger.info(ret)
        return ret


    #发送验证码到申请人的手机号上
    content = "您的申请VPN账号的验证码是：[ " + captcha + " ]" + "有效期30分钟"
    SendResult =  SendMessage(PhoneNumber, 'sms', content)

    # python 判断是否含有某个字符
    if "success" not in SendResult:
        ret = "验证码发送失败 "  + PhoneNumber_captcha
        logger.info(ret)
        return ret

    ret = "短信验证码正在发送中请等待，验证码有效时间30分钟。"
    logger.info(PhoneNumber + " " + ret)
    return ret



#提交信息，核对信息，显示信息
@apply.route('/apply/verifyinfo', methods=['GET', 'POST'])
def verifyinfo():
    # #前段ajax发送POST请求，后端获取。ajax拿到html数据，不能展示成页面和跳转。这个方法放弃
    # Inputdata_ajax = request.get_json()

    #实例一个表单对象。form表单提交的时候，这样获取。
    applyinfo_form = ApplyInfoForm()

    #页面点击提交的时候进行验证,如果数据能被所有验证函数接受，则返回true，否则返回false
    if applyinfo_form.validate_on_submit():
        #用户输入的新和frigate中根据工号用户信息。这个是form表单提交的时候获取数据的方法
        Inputdata = applyinfo_form.data

        # 调用验证码redis函数，先来验证输入的验证和redis中的验证码是否一致。验证码正确是True 失败是False
        checkcaptcha = CaptchaRedis(Inputdata['phone'], Inputdata['captcha'], "check")
        if checkcaptcha == False:
            checkcaptcharesult = "验证码验证错误,请确认输入的验证码是否正确。"
            return render_template('all_result.html', apply_result=checkcaptcharesult)


        #根据工号去取frigate中的数据。成功是 True 失败是 False。
        FrigateUserInfo = GetUserInfo(Inputdata['worknumber'])
        if FrigateUserInfo == False:
            apply_result = "根据工号查询用户信息失败，请确认输入的工号是否正确"
            logger.info(apply_result)
            return render_template('all_result.html', apply_result=apply_result)


        #验证redis里面是否已经有用户申请的信息。True 表示redis中有用户信息，就是申请过了。redis中数据保存4小时有效
        if RedisOperation(Inputdata,FrigateUserInfo,'exists') == True:
            RedisOperationcontent = "[ " + Inputdata['worknumber'] + " ]"+ "号员工已提交申请，请等待。"
            logger.info(RedisOperationcontent)
            return render_template('all_result.html', apply_result=RedisOperationcontent)


        #redis里面没有申请人信息，就是没有申请过。继续往下执行

        #验证frigate信息和输入信息是否一致。
        CheckResult = CheckUserInfo(Inputdata,FrigateUserInfo)
        if CheckResult == True:
            logger.info("申请人信息核对成功")
            #信息对比通过，把用户信息写入redis
            SetResult,people_info_md5 = RedisOperation(Inputdata,FrigateUserInfo,'set')

            #set redis是否成功
            if SetResult == False:
                SetContent = "用户申请时信息存入redis失败，请联系管理员"
                logger.info(SetContent)
                return render_template('all_result.html', apply_result=SetContent)
                #return SetContent

            logger.info("用户申请成功，信息如下：" + str(Inputdata))
            #要发送给审核人一个审核页面的url
            content = "请审核：http://10.101.9.243:8080/audit/" + people_info_md5 + "   4小时之内此链接有效"

            #需要收到审核页面的人员 多人使用列表的形式。
            AuditUserInfo = {
                'user1':{'name': '徐仲夏', 'worknumber': 'HB300', 'mobile': '13918133224', 'reason': '审核人'},
                'user2':{'name': '苏晗', 'worknumber': 'HB493', 'mobile': '13601723491', 'reason': '审核人'}
            }
            for key in AuditUserInfo.keys():
                #SendMessage 第一个参数是人员的信息工号。
                SendMessage(AuditUserInfo[key]['worknumber'], 'qiyeweixin', content)
                logger.info("通过企业微信发送审核地址给审核人%s-->%s" %(AuditUserInfo[key]['name'],content))


            #返回提示申请成功
            ResultContent = "提交成功，请等待账号创建，创建成功会发送账号到你的企业微信"
            return render_template('all_result.html', apply_result=ResultContent)


        #验证frigate信息和输入信息不一致，返回验证结果
        else:
            return render_template('all_result.html', apply_result=CheckResult)



    #如果form表单提交的数据验证不成功，就重新输入信息。
    else:
        #验证函数里面可以加一些基础的判断：例如手机号对不对什么的,就让重新输入
        return redirect(url_for('apply.sendinfo'))




#审核页面，点击审核连接的时候进入到这个里面
@apply.route('/audit/<people_info_md5>', methods=['GET', 'POST'])
def Audit(people_info_md5):
    #实例化审核页面的form类
    Audit_Form = AuditForm()

    #捕获redis失效后点击审核报错
    try:
        #从reids中获取申请用户的信息，展示，审核
        UserInfo = UserFromRedis(people_info_md5,"get")
        #print("----待审核的信息>%s" %UserInfo)
        name = UserInfo['name']
        worknumber = UserInfo['worknumber']
        mobile = UserInfo['mobile']
        userreason = UserInfo['reason']
        email = UserInfo['email']

    except Exception:
        ret = "此次申请超过4小时未审核，已失效。如有需要请通知用户重新申请。"
        return render_template('all_result.html', apply_result=ret)

    return render_template('audit.html', form=Audit_Form,name=name,worknumber=worknumber,mobile=mobile,email=email,userreason=userreason,people_info_md5=people_info_md5)



#审核结果对应的操作
@apply.route('/apply/audit_result', methods=['GET', 'POST'])
def AuditResult():
    # 审核页面上取到的信息。
    audit_reason = request.values.get('reason')
    worknumber = request.values.get('worknumber')
    mobile = request.values.get('mobile')
    name = request.values.get('name')
    email = request.values.get('email')
    userreason = request.values.get('userreason')
    people_info_md5 = request.values.get('people_info_md5')


    ApplyUserToTxt = "姓名:" + name + " 工号:" + worknumber + " 手机号:" + mobile +  " 用户申请理由:" + userreason + " 审核说明:" + audit_reason

    if request.values.get('submit_pass') == '审核通过':
        #判断redis中是否有信息，避免重复审核的报错。redis中没有，就说明被审核过了，redis中删除了。
        if UserFromRedis(people_info_md5,"exists") == False:
            ret = "此申请已经被审核"
            logger.info(ret + ApplyUserToTxt)
            return render_template('all_result.html', apply_result=ret)


        #VPN信息
        logger.info("审核通过，VPN创建中...")

        #准备传入的信息。vpn的用户名和密码
        VpnName = email.strip().split("@")[0]
        #passpword = "7ZGCPJtE"
        passpword = CreateVpnPassword()

        #调用创建vpn的函数。 成功返回True，失败返回False
        # VpnName是邮箱前缀，name是中文名。passpword是随机出来的用户的vpn密码
        VpnResutl = CreateVpn(VpnName, name, passpword)

        #VPN的信息。用户名和密码都是先生成出来，再去创建VPN的
        content = " VPN地址：" + "1.1.1.1" + "  账号:" + VpnName + "  密码:" + passpword

        #如果创建失败。比如连接不上防火墙导致创建失败
        if VpnResutl == False:
            VpnResutlDescribe = " 创建VPN账号时失败： " + content
            # 创建失败的VPN的信息记录在日志中，方便查看是谁的创建失败了
            logger.info(ApplyUserToTxt + VpnResutlDescribe)
            ret = "创建VPN账号时失败,申请信息记录在日志中。问题解决后，可以再次点击审核链接进行审核。"
            return render_template('all_result.html', apply_result=ret)



        VpnResutlDescribe = " VPN创建成功: "
        #content是发送给用户的，contentToLog是记录日志用的
        contentToLog = VpnResutlDescribe + content
        logger.info(ApplyUserToTxt + contentToLog)

        #等待创建返回，成功，给用户发送邮件
        logger.info("VPN信息记录到vpn-user.txt文件中...")

        # 创建后VPN的信息记录在文件中
        localtime = time.asctime(time.localtime(time.time()))
        with open('vpn-user.txt','a+',encoding='utf-8') as f:
            f.write(localtime + " 审核通过 " + ApplyUserToTxt + content + '\n' )

        #发送信息给对应的人。
        SendMessageResult = SendMessage(worknumber, "qiyeweixin", content)
        logger.info("已成功发送VPN信息到申请人企业微信")

        # 删除redis中申请人的数据。删除成功结果是1
        DelUserRedis = UserFromRedis(people_info_md5, "del")
        if DelUserRedis == 1:
            logger.info("成功删除redis中" + name + "的申请记录")
        else:
            logger.error("删除redis中" + name + "申请记录失败")

        ret = "审核通过VPN创建成功，并成功发送账号密码给" + name
        return render_template('all_result.html', apply_result=ret)


    #审核拒绝，就发送拒绝理由给申请人企业微信
    elif request.values.get('submit_refuse') == '审核拒绝':
        try :
            #发送邮件说明原因。
            content = "VPN申请被拒绝，拒绝原因为：" + audit_reason
            SendMessage(worknumber, "qiyeweixin", content)

            #记录日志
            logger.info("VPN审核拒绝" + ApplyUserToTxt)

            #审核被拒绝的用户也记录在文件中。审核拒绝的用户，就没有记录VPN信息
            localtime = time.asctime(time.localtime(time.time()))
            with open('vpn-user.txt', 'a+', encoding='utf-8') as f:
                f.write(localtime + " 审核拒绝 " + ApplyUserToTxt + '\n')

            # 删除redis中申请人的数据。删除成功结果是1
            DelUserRedis = UserFromRedis(people_info_md5, "del")
            if DelUserRedis == 1:
                logger.info("VPN审核拒绝，删除" + name + "redis信息成功")
            else:
                logger.error("VPN审核拒绝，删除" + name + "redis信息失败")

            ret = "审核不通过"
            return render_template('all_result.html', apply_result=ret)


        #审核通过后redis信息会删除，捕获再次点击审核时报的异常
        except Exception as e:
            logger.info("此申请已经被审核" + ApplyUserToTxt)
            ret = "此申请已经被审核"
            return render_template('all_result.html', apply_result=ret)


