# coding:utf8
import news
import datetime
import time
import testip
import hashlib
import xmltodict
import proxy
from flask import Flask, request, abort

WECHAT_TOKEN = 'XXXXX'  # token用来可微信公众平台对接 无限制只要与微信公众平台服务器配置处的一致即可

app = Flask(__name__)


@app.route('/wx', methods=['GET', 'POST'])  # /wx是我的路径 可以自己定义
def wechat():
    # 获取参数
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    # echostr = request.args.get('echostr')

    # 校验参数
    if not all([signature, timestamp, nonce]):  # echostr
        abort(400)
    # 签名加密
    li = [WECHAT_TOKEN, timestamp, nonce]
    # 列表排序重组加密
    li.sort()
    # 拼接字符
    tem_str = "".join(li)
    # sha1加密,以下步骤很重要
    s1 = hashlib.sha1()
    s1.update(tem_str.encode('utf8'))
    sigin = s1.hexdigest()
    # 签名值对比，相同证明请求来自微信
    # 错误返回403页面
    if signature != sigin:
        abort(403)
    else:
        # 正确返回echostr字符串
        # 表示是微信请求
        if request.method == 'GET':
            # 第一次接入服务器
            echostr = request.args.get('echostr')
            if not echostr:
                abort(403)
            else:
                return echostr
        elif request.method == 'POST':
            # 表示微信服务器转发消息到本地服务器
            xml_str = request.data
            # print(xml_str)
            if not xml_str:
                return abort(403)
            # 对xml字符串进行解析
            xml_dict = xmltodict.parse(xml_str)
            xml_dict1 = xml_dict.get('xml')
            # print(xml_dict1)
            # 提取消息类型
            msg_type = xml_dict1.get('MsgType')

            # print(msg_type)
            if msg_type == 'text':
                # 判断接收到消息是不是文本
                # 这是文本消息
                # 构造返回值，由为微信服务器回复消息
                # 重点：以下参数值一个不能少，一个字母不能错，大小写不能错，键名必须完全一样
                inputdata = xml_dict1.get('Content')
                # 获取用户输入的字符
                inputdata = str(inputdata)
                # 1⃣以字符串的方式存储

                data = news.getdata(inputdata)
                # 调用函数获取redis数据库中的数据并生成URL返回给用户
                resp_dict = {
                    "xml": {
                        'ToUserName': xml_dict1.get('FromUserName'),
                        'FromUserName': xml_dict1.get('ToUserName'),
                        'CreateTime': int(time.time()),
                        'MsgType': 'text',
                        'Content': data,
                    }
                }

            elif msg_type == 'event':
                # 判断用户操作，如果是关注，就回复data的内容
                data = "感谢小伙伴关注！" + "\n" + "\n" + "点击右下角帮助有惊喜！"

                if 'subscribe' == xml_dict1.get('Event'):
                    resp_dict = {
                        "xml": {
                            'ToUserName': xml_dict1.get('FromUserName'),
                            'FromUserName': xml_dict1.get('ToUserName'),
                            'CreateTime': int(time.time()),
                            'MsgType': 'text',
                            'Content': data
                        }
                    }
                # 将字典转为xml字符串
            resp_xml_str = xmltodict.unparse(resp_dict)
            # # 返回消息字符串
            return resp_xml_str


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)  # 端口可以自定义
