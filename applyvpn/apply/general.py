import requests,json,redis,hashlib,random,paramiko,time
import logging.handlers

'''
通用的操作函数在这里
例如获取用户信息和比对用户信息
'''

#根据用户的工号来获取frigate里面的信息
def GetUserInfo(InputWorkNumber):
    url = "http://ucenter.devops.suhan/user/getUserByWeiXinUserId?weiXinUserId=" + InputWorkNumber
    try :
        UserInfoStr = requests.get(url).text
        UserInfo = json.loads(UserInfoStr)
        return UserInfo
    except Exception as e :
        return False

#核对用户输入的信息和frigate中的信息是否一致
def CheckUserInfo(Inputdata,FrigateUserInfo):

    #信息都是根据工号查出来的，所以不用对比工号
    if Inputdata['name'] == FrigateUserInfo['name']:
        if Inputdata['phone'] == FrigateUserInfo['mobile']:
            return True
        else:
            return "输入的手机号：[" + Inputdata['phone'] + "]与输入的工号：[" +  Inputdata['worknumber'] + "]不匹配"
    else:
        return "输入的姓名：[" + Inputdata['name'] +  " ]与输入的工号：[" + Inputdata['worknumber'] + "] 不匹配"


#查询输入的信息是否在redis中存在和写入新的数据到redis中
def RedisOperation(Inputdata,FrigateUserInfo,Operation):
    try:
        pool = redis.ConnectionPool(host='redis.servers.dev.suhan',port=6379,db=14,decode_responses=True)
        r = redis.Redis(connection_pool=pool)

        #以工号为查询和插入条件，对应到一个申请人
        worknumber_value = FrigateUserInfo['qiyeWeixinUserId']
        name_value = FrigateUserInfo['name']
        mobile_value = FrigateUserInfo['mobile']
        reason_value = Inputdata['reason']
        email = FrigateUserInfo['email']

        # 工号姓名和手机号MD5加密下。存，取都通过这个。访问的url也是。
        people_info =  worknumber_value + name_value + mobile_value
        people_info_md5 = hashlib.md5(people_info.encode(encoding='utf-8')).hexdigest()

        if Operation == 'set':
            #设置成功返回True,value会被覆盖。
            HmsetResult = r.hmset(people_info_md5,{'name':name_value,'worknumber':worknumber_value,'mobile':mobile_value,'email':email,'reason':reason_value})
            #设置过期时间，单位秒。14400s=4个小时。忘记审核的话，4个小时失效后还可以申请。
            r.expire(people_info_md5, 14400)
            return HmsetResult,people_info_md5

        elif Operation == 'get':
            #hget返回是个单个value，hmget返回的是列表
            GetResult = r.hget(people_info_md5,'worknumber')
            return GetResult

        elif Operation =='exists':
            #有返回True。 也可以使用get方式判断有没有
            ExistsResult = r.hexists(people_info_md5,'worknumber')
            return ExistsResult

    #redis 连接失败的错误
    except Exception as err:
        return False


#def GetUserFromRedis(worknumber):
def UserFromRedis(people_info_md5,Operation):
    try:
        pool = redis.ConnectionPool(host='redis.servers.dev.suhan',port=6379,db=14,decode_responses=True)
        r = redis.Redis(connection_pool=pool)

        if Operation == 'get':
            UserInfo = r.hgetall(people_info_md5)
            return UserInfo

        elif Operation == 'del':
            UserDel = r.delete(people_info_md5)
            return UserDel

        elif Operation =='exists':
            #有返回True。 也可以使用get方式判断有没有
            ExistsResult = r.hexists(people_info_md5,'worknumber')
            return ExistsResult
    # redis 连接失败的错误
    except Exception as err:
        return False




#手机验证码存入redis中,检查输入的验证码对不对
def CaptchaRedis(phone,captcha,Operation):
    try:
        pool = redis.ConnectionPool(host='redis.servers.dev.suhan',port=6379,db=13,decode_responses=True)
        r = redis.Redis(connection_pool=pool)

        phone_key = phone + "_captcha"

        if Operation == 'set':
            SetResult = r.set(phone_key,captcha)
            #验证码有效时间30分钟=1800秒
            r.expire(phone_key, 1800)
            return SetResult

        elif Operation == 'del':
            UserDel = r.delete(phone_key)
            return UserDel

        elif Operation =='check':
            #有返回True。 也可以使用get方式判断有没有
            rediscaptcha = r.get(phone_key)
            # print("获取和输入的验证码")
            # print("rediscaptcha%s--->" %rediscaptcha)
            # print("captcha%s--->" % captcha)

            #输入的一致就成功，不一致就失败
            if rediscaptcha == captcha:
                #print("rediscaptcha--->TRUE")
                return True
            else:
                #print("rediscaptcha--->FALSE")
                return False

    # redis 连接失败的错误
    except Exception as err:
        return False


def SendMessage(FrigateUserInfo,mode,content):
    mailurl = 'http://notice.ops.suhan/sender/mail/'
    smsurl = 'http://notice.ops.suhan/sender/sms/'
    qiyeweixinurl = 'http://notice.ops.suhan/sender/qiyeweixin/'

    if mode == 'mail':
        # email 的数据
        PayloadMail = {
            # 'tos': FrigateUserInfo['email'],
            'subject': FrigateUserInfo['worknumber'],
            'content': content
        }

        result = requests.post(mailurl, data=PayloadMail)
        return result.text

    elif mode == 'qiyeweixin':
        # 企业微信的发送数据格式
        PayloadQiyeweixin = {
            'tos': FrigateUserInfo,
            'content': content
        }

        result = requests.post(qiyeweixinurl, data=PayloadQiyeweixin)
        return result.text

    elif mode == 'sms':
        # 短信的发送格式
        PayloadSms = {
            'tos': FrigateUserInfo,
            'content': content
        }

        result = requests.post(smsurl, data=PayloadSms)
        return result.text



# #日志函数
# def Logger():
#     LOG_FILE = "application.log"
#     handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')  # 实例化handler
#
#     fmt = '%(asctime)s - %(levelname)s - %(message)s'
#     formatter = logging.Formatter(fmt)  # 实例化formatter
#     handler.setFormatter(formatter)  # 为handler添加formatter
#
#     logger = logging.getLogger('application')  # 获取名为tst的logger
#     logger.addHandler(handler)  # 为logger添加handler
#     logger.setLevel(logging.DEBUG)






#6位随机数
def RandomNum():
    VarNum = ""
    for i in range(0,6):
        x = random.randint(0,9)
        VarNum =VarNum + str(x)
    return VarNum



#生成VPN用户的密码。数字，小写字母，大写字母
def CreateVpnPassword():
    # 从指定的字符中，随机选几个数字，最后拼接成用户的密码
    password_big = "".join(random.sample(['A', 'L', 'E', 'F', 'Q', 'Y', 'K', 'D', 'G'], 3))
    password_num = "".join(random.sample(['1', '2', '3', '4', '5', '6', '7', '8', '9'], 3))
    password_lowercase = "".join(random.sample(['a', 'e', 'h', 'n', 'm', 't', 'q'], 2))
    UserPassword = password_big + password_num + password_lowercase
    return UserPassword


#创建VPN账号
def CreateVpn(EmailName,AliasName,password):
    date = time.strftime('%Y%m%d%H%M%S')
    FirewallIp = '1.1.1.1'
    FirewallPort = 80
    FirewallUser = 'user123'
    FirewallPasswd = 'password123'


    # EmailName = "han.su"
    # AliasName = "苏晗"
    # password = "111111"

    user_manage = "user-manage user " + EmailName
    #中文名不用了，到防火墙上会乱码
    #alias_name = "alias " + AliasName
    vpnpassword = "password " + password

    cmd = ['sys', user_manage, 'parent-group /xxxxx/xxxx',vpnpassword, 'quit', 'quit']
    #cmd = ['sys', 'user-manage user han.su', 'alias 苏晗', 'parent-group /xxxx/xxxx','password xxxxxx', 'quit', 'quit']

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(FirewallIp, port=FirewallPort, username=FirewallUser, password=FirewallPasswd, allow_agent=False,look_for_keys=False)
        ssh_shell = ssh.invoke_shell()

        # 打印接收到的数据
        for m in cmd:
            ssh_shell.sendall(m + '\n')
            data = ssh_shell.recv(4096).decode('utf8')
            #不打印，创建vpn时的输出不会打印出来
            print("result-->%s" % data)
            time.sleep(0.5)

        ssh.close()
        return True

    except Exception as err:
        context = "创建VPN失败"
        return False




