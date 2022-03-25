import re
import requests
import redis
from lxml import etree


def getdata():
    connent = redis.Redis(host='127.0.0.1', port=6379, db=6)  # 连接数据库 将数据存放到redis第6个数据库中

    for page in range(1, 2836):  # 采集第一页到2836页，第一次数据采集的时候需要对照漏洞库的页数 手动输入 第一次采集完成 以后就不用了
        url = f'https://avd.aliyun.com/nonvd/list?page={page}'
        # 非CVE漏洞库地址https://avd.aliyun.com/nonvd/list?page=
        # CVE漏洞库地址https://avd.aliyun.com/nvd/list?page=
        heads = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
        }
        response = requests.get(url=url, headers=heads, timeout=5)
        response.encoding = 'utf8'
        response = response.text
        obj = re.compile(
            '<tr>.*?target="_blank">(?P<number>.*?)</a></td>.*?<td>(?P<name>.*?)</td>.*?<button.*?>(?P<status>.*?)</button>.*?nowrap="nowrap">(?P<date>.*?)</td>' + '.*?(?P<level>.*?)</button>.*?</tr>',
            re.S)
        # 正则 取数据用
        result = obj.finditer(response)
        for data in result:  # 这里取的首页数据
            number = str(data.group("number"))
            number = number.replace("\n", "")
            number = number.replace(" ", "")
            name = str(data.group("name"))
            name = name.replace("\n", "")
            name = name.replace(" ", "")
            date = str(data.group("date"))
            date = date.replace("\n", "")
            date = date.replace(" ", "")

            try:
                urla = 'https://avd.aliyun.com/detail?id=' + number

                res = requests.get(url=urla, headers=heads)  # 这里取的漏洞详情页数据
                tree = etree.HTML(res.text)
                describe = tree.xpath('/html/body/div[3]/div/div[1]/div[2]/div[1]/div/text()')[0]

                describe = describe.replace("\n", "")
                describe = describe.replace(" ", "")

                proposal = tree.xpath('/html/body/div[3]/div/div[1]/div[2]/div[1]/div/text()')[0]
                proposal = proposal.replace("\n", "")
                proposal = proposal.replace(" ", "")

                level = tree.xpath('/html/body/div[3]/div/div[2]/div/div[1]/div/div/header/div[2]/text()')[0]
                level = level.replace("\n", "")
                level = level.replace(" ", "")

                rt = {'编号': number, '漏洞名称': name, '披露日期': date, '漏洞描述': describe, '整改建议': proposal,
                      '等级': level}  # 键值对 数据来是上面爬的
                idkey = date + name  # redise hash命名  为了方便后面判断 所以这里以时间和漏洞名称组合取名
                connent.hmset(idkey, rt)  # hmset写入值


            except:
                pass


getdata()
