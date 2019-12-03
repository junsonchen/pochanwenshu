# -*- coding: utf-8 -*-
import re


def get_jcrq_date(txt):
    """
    处理网站日期的函数
    :param date:
    :return:
    """
    if txt:
        data = re.findall(r'(二〇.*?日)', txt)
        if data:
            return data[-1]
        data = re.findall(r'(二○.*?日)', txt)
        if data:
            return data[-1]
        data = re.findall(r'(二O.*?日)', txt)
        if data:
            return data[-1]
        data = re.findall(r'(二○.*)', txt)
        if data:
            return data[-1]
        return ''
    return ''


def deal_chinese_data(str_data):
    """
    二0一八年八月二十二日
    二零一八年八月二十二日
    2018年10月22日
    二〇一九年三月十三日
    :param str_data:
    :return:
    """
    if str_data:
        data_replace = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9','十': '1','零': '0', '年': '-', '月': '-', '日': '', '○': '0', '〇': '0','0':'0'}
        temp1 = "".join([data_replace.get(i, '') for i in str_data])
        data_base = re.match(r'^\d+-\d+-\d+$',temp1)
        if data_base:
            temp2 = temp1.split("-")
            # print(temp2)
            year = temp2[0]
            month = temp2[1]
            day = temp2[2]
            if month == '1':
                mymonth = '01'
            elif len(month) == 1:
                mymonth = "0" + month
            else:
                mymonth = month
            if len(day) == 1:
                if day == '1':
                    day = '10'
                else:
                    day = "0"+day
            elif len(day) == 2:
                if day == '21':
                    day = '20'
                elif day == '31':
                    day = '30'
                else:
                    day = day
            elif len(day) == 3:
                if day == '311':
                    day = '31'
                elif day == '211':
                    day = '21'
                else:
                    day = day.replace("1","")
            else:
                pass

            result = year + "-" + mymonth + "-" + day
            re_parte = re.match(r'^\d{4}-\d{2}-\d{2}$',result)
            if re_parte:
                return result
            else:
                return ""
        date_my = re.match(r'^\d{4}年\d{2}月\d{2}日',str_data)
        if date_my:
            results = re.findall("\d+",str_data)
            result = results[0] + "-" + results[1] + "-" + results[2]
            return result

        date_my = re.match(r'^\d{4}年\d{1}月\d{2}日', str_data)
        if date_my:
            results = re.findall("\d+", str_data)
            result = results[0] + "-" + "0" + results[1] + "-" + results[2]
            return result

        date_my = re.match(r'^\d{4}年\d{1}月\d{1}日', str_data)
        if date_my:
            results = re.findall("\d+", str_data)
            result = results[0] + "-" + "0" + results[1] + "-" + "0" + results[2]
            return result

        date_my = re.match(r'^\d{4}年\d{2}月\d{1}日', str_data)
        if date_my:
            results = re.findall("\d+", str_data)
            result = results[0] + "-" + results[1] + "-" + "0" + results[2]
            return result

        date_biaozhun = re.match(r'\d{4}-\d{2}-\d{2}',str_data)
        if date_biaozhun:
            result = date_biaozhun.group()
            return result

    else:
        return ""


if __name__ == '__main__':
    txt = '江苏省靖江市人民法院民事裁定书（2011）泰靖商破字第0004-1号申请人陈灿宏，男，公民身份证号码321024196906170633，住靖江市靖城街道办事处江平路230号。被申请人靖江侨荣房地产开发有限公司，住所地在靖江市江阳路200号。法定代表人盛强，经理。申请人陈灿宏以被申请人靖江侨荣房地产开发有限公司结欠其本息8131159元，未按约归还，且有多起作为被执行人的案件未能履行，不能清偿到期债务为由，于2011年5月4日向本院申请对被申请人进行破产清算。并提供了被申请人2009年4月10日向申请人出具的借条，借条载明，被申请人尚欠应付申请人工程款6067856.64元（其中3848304.64元自2009年1月按月利率1分计息，2219552元自2009年4月按月利率1分计息），应付保修金724653.64元。上述款项暂定2010年12月31日归还，结息日期为每年的12月31日，逾期不能归还，该款由靖江市侨发物业管理处负责归还。本院于2011年5月5日向被申请人送达破产申请书及申请材料的副本，被申请人在规定期限内未提出异议。另查明，本院已于2011年4月19日裁定受理靖江市侨发物业管理处的破产清算申请。本院认为，被申请人不能清偿到期债务，申请人申请被申请人进行破产清算，符合法律规定，依法应予受理。依照《中华人民共和国企业破产法》第二条第一款、第七条第二款、第十条第一款之规定，裁定如下：受理申请人陈灿宏对被申请人靖江侨荣房地产开发有限公司的破产清算申请。本裁定作出之日起发生法律效力。审判长许安海审判员苏孔兴审判员黄建明二O一一年五月十三日书记员孔浜'
    a = get_jcrq_date(txt)
    print('原始日期:{}'.format(a))
    b = deal_chinese_data(a)
    print('处理完成日期:{}'.format(b))