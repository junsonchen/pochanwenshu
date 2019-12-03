# -*- coding: utf-8 -*-
import re
import hashlib


# md5加密方法
def get_md5_value(_str):
    if isinstance(_str, str):
        code_url = _str.encode("utf-8")
        m = hashlib.md5()
        m.update(code_url)
        return m.hexdigest()
    else:
        return None


# 处理文书号
def __deal_with_cf_wsh(cf_wsh):
    if cf_wsh:
        cf_wsh = re.sub(r'\r|\?|\n|\t| |　', '', cf_wsh)
        cf_wsh = re.sub(r'〔|\[|【|（|﹝|{　', '(', cf_wsh)
        cf_wsh = re.sub(r'〕|]|】|）|﹞|}', ')', cf_wsh)
        return cf_wsh
    else:
        return ""


# 处理其他字段
def __deal_with_other(_str):
    if _str:
        _str = re.sub(r'\r|\?|\n|\t| |　', '', _str)
        return _str
    else:
        return ""


# 处理type类型，一般是固定值
def __deal_with_type(_str):
    if _str:
        return _str
    else:
        return ''


# 去重的规则字段
def pochan_65_filter(item):
    if isinstance(item, dict):
        cf_wsh = item.get('cf_wsh')  # 文书号
        cf_wsh = __deal_with_cf_wsh(cf_wsh)

        cf_xzjg = item.get('cf_xzjg', '')  # 处罚机关
        cf_xzjg = __deal_with_other(cf_xzjg)

        oname = item.get('oname', '')  # 当事人，被申请人
        oname = __deal_with_other(oname)

        fb_rq = item.get('fb_rq', '')  # 发布时间
        fb_rq = __deal_with_other(fb_rq)

        sj_type = item.get('sj_type', '65')  # 数据类型值
        sj_type = __deal_with_type(sj_type)

        cf_cfmc = item.get("cf_cfmc",'')
        cf_cfmc = __deal_with_other(cf_cfmc)

        xq_url = item.get("xq_url", '')

        zqr = item.get('zqr', '')

        if xq_url:
            if cf_xzjg:
                if fb_rq:
                    if cf_cfmc:
                        if zqr:
                            if cf_wsh:
                                if oname:
                                    _str = xq_url + cf_xzjg + fb_rq + cf_cfmc + zqr + cf_wsh + oname + sj_type
                                    return get_md5_value(_str)
                                else:
                                    _str = xq_url + cf_xzjg + fb_rq + cf_cfmc + zqr + cf_wsh + sj_type
                            else:
                                _str = xq_url + cf_xzjg + fb_rq + cf_cfmc + zqr + sj_type
                                return get_md5_value(_str)
                        else:
                            _str = xq_url + cf_xzjg + fb_rq + cf_cfmc + sj_type
                            return get_md5_value(_str)
                    else:
                        _str = xq_url + cf_xzjg + fb_rq + sj_type
                        return get_md5_value(_str)
                else:
                    _str = xq_url + cf_xzjg + sj_type
                    return get_md5_value(_str)
            else:
                _str = xq_url + sj_type
                return get_md5_value(_str)
        else:
            return None
    return None


def filter_factory(item):
    sj_type = item.get('sj_type')
    if sj_type == '65':
        return pochan_65_filter(item)
    else:
        print('无去重规则')


if __name__ == '__main__':
    test_data = {
        "cf_xzjg": "dd",
        # "cf_xzjg": "",
        "oname": "uu",
        "fb_rq": "",
        "sj_type": '65',
    }
    print(filter_factory(test_data))
    # print(__deal_with_other('苏州市吴江区    人民法院'))