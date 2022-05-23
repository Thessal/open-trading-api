# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 11:23:04 2022

@author: KIS Developers
"""

import time, copy
import yaml
import requests
import json

import pandas as pd

from collections import namedtuple
from datetime import datetime
from decimal import *

with open(r'./config/kisdev_vi.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

_TRENV = tuple()
_last_auth_time = datetime.now()
_autoReAuth = False
_DEBUG = True
_isPaper = True

_base_headers = {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "charset": "UTF-8",
    'User-Agent': _cfg['my_agent']
}


def _getBaseHeader():
    if _autoReAuth: reAuth()
    return copy.deepcopy(_base_headers)


def _setTRENV(cfg):
    nt1 = namedtuple('KISEnv', ['my_app', 'my_sec', 'my_acct', 'my_prod', 'my_token', 'my_url', 'svr', 'market'])
    d = {
        'my_app': cfg['my_app'],
        'my_sec': cfg['my_sec'],
        'my_acct': cfg['my_acct'],
        'my_prod': cfg['my_prod'],
        'my_token': cfg['my_token'],
        'my_url': cfg['my_url'],
        'svr': cfg['svr'],
        'market': cfg['market'],
    }

    global _TRENV
    _TRENV = nt1(**d)


def isPaperTrading():
    return _isPaper


def changeTREnv(token_key, svr='prod', product='01'):
    cfg = dict()

    global _isPaper
    if svr == 'prod':
        ak1 = 'my_app'
        ak2 = 'my_sec'
        _isPaper = False
    elif svr == 'vps':
        ak1 = 'paper_app'
        ak2 = 'paper_sec'
        _isPaper = True

    cfg['my_app'] = _cfg[ak1]
    cfg['my_sec'] = _cfg[ak2]

    if svr == 'prod' and product == '01':
        cfg['my_acct'] = _cfg['my_acct_stock']
    elif svr == 'prod' and product == '03':
        cfg['my_acct'] = _cfg['my_acct_future']
    elif svr == 'vps' and product == '01':
        cfg['my_acct'] = _cfg['my_paper_stock']
    elif svr == 'vps' and product == '03':
        cfg['my_acct'] = _cfg['my_paper_future']

    cfg['my_prod'] = product
    cfg['my_token'] = token_key
    cfg['my_url'] = _cfg[svr]

    cfg["market"] = _cfg["market"]
    cfg["svr"] = svr

    _setTRENV(cfg)


def _getResultObject(json_data):
    _tc_ = namedtuple('res', json_data.keys())

    return _tc_(**json_data)


def auth(svr='prod', product='01'):
    p = {
        "grant_type": "client_credentials",
    }
    print(svr)
    if svr == 'prod':
        ak1 = 'my_app'
        ak2 = 'my_sec'
    elif svr == 'vps':
        ak1 = 'paper_app'
        ak2 = 'paper_sec'

    p["appkey"] = _cfg[ak1]
    p["appsecret"] = _cfg[ak2]

    url = f'{_cfg[svr]}/oauth2/tokenP'

    global _last_auth_time
    try:
        with open("./config/token.json", "r") as f:
            cfg_token = json.load(f)
        my_token = cfg_token["my_token"]
        _last_auth_time = datetime.fromtimestamp(float(cfg_token["_last_auth_time"]))
        assert ((datetime.now() - _last_auth_time).seconds < 86400 - 30000)
    except:
        res = requests.post(url, data=json.dumps(p), headers=_getBaseHeader())
        rescode = res.status_code
        if rescode == 200:
            my_token = _getResultObject(res.json()).access_token
        else:
            print('Get Authentification token fail!\nYou have to restart your app!!!')
            return
        _last_auth_time = datetime.now()
        with open("./config/token.json", "w") as f:
            json.dump({
                "my_token": my_token,
                "_last_auth_time": _last_auth_time.timestamp(),
            }, f)

    changeTREnv(f"Bearer {my_token}", svr, product)

    _base_headers["authorization"] = _TRENV.my_token
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec

    if (_DEBUG):
        print(f'[{_last_auth_time}] => get AUTH Key completed!')


# end of initialize
def reAuth(svr='prod', product='01'):
    n2 = datetime.now()
    if (n2 - _last_auth_time).seconds >= 86400:
        auth(svr, product)


def getEnv():
    return _cfg


def getTREnv():
    return _TRENV


# 주문 API에서 사용할 hash key값을 받아 header에 설정해 주는 함수
# Input: HTTP Header, HTTP post param
# Output: None
def set_order_hash_key(h, p):
    url = f"{getTREnv().my_url}/uapi/hashkey"

    res = requests.post(url, data=json.dumps(p), headers=h)
    rescode = res.status_code
    if rescode == 200:
        h['hashkey'] = _getResultObject(res.json()).HASH
    else:
        print("Error:", rescode)


class APIResp:
    def __init__(self, resp):
        self._rescode = resp.status_code
        self._resp = resp
        self._header = self._setHeader()
        self._body = self._setBody()
        self._err_code = self._body.rt_cd
        self._err_message = self._body.msg1

    def getResCode(self):
        return self._rescode

    def _setHeader(self):
        fld = dict()
        for x in self._resp.headers.keys():
            if x.islower():
                fld[x] = self._resp.headers.get(x)
        _th_ = namedtuple('header', fld.keys())

        return _th_(**fld)

    def _setBody(self):
        _tb_ = namedtuple('body', self._resp.json().keys())

        return _tb_(**self._resp.json())

    def getHeader(self):
        return self._header

    def getBody(self):
        return self._body

    def getResponse(self):
        return self._resp

    def isOK(self):
        try:
            if (self.getBody().rt_cd == '0'):
                return True
            else:
                return False
        except:
            return False

    def getErrorCode(self):
        return self._err_code

    def getErrorMessage(self):
        return self._err_message

    def printAll(self):
        print("<Header>")
        for x in self.getHeader()._fields:
            print(f'\t-{x}: {getattr(self.getHeader(), x)}')
        print("<Body>")
        for x in self.getBody()._fields:
            print(f'\t-{x}: {getattr(self.getBody(), x)}')

    def printError(self):
        print('-------------------------------\nError in response: ', self.getResCode())
        print(self.getBody().rt_cd, self.getErrorCode(), self.getErrorMessage())
        print('-------------------------------')

    # end of class APIResp


########### API call wrapping

def _url_fetch(api_url, ptr_id, params, appendHeaders=None, postFlag=False, hashFlag=True):
    url = f"{getTREnv().my_url}{api_url}"

    headers = _getBaseHeader()

    # 추가 Header 설정
    tr_id = ptr_id
    if ptr_id[0] in ('T', 'J', 'C'):
        if isPaperTrading():
            tr_id = 'V' + ptr_id[1:]

    headers["tr_id"] = tr_id
    headers["custtype"] = "P"

    if appendHeaders is not None:
        if len(appendHeaders) > 0:
            for x in appendHeaders.keys():
                headers[x] = appendHeaders.get(x)

    if (_DEBUG):
        print("< Sending Info >")
        print(f"URL: {url}, TR: {tr_id}")
        print(f"<header>\n{headers}")
        print(f"<body>\n{params}")

    if (postFlag):
        if (hashFlag): set_order_hash_key(headers, params)
        res = requests.post(url, headers=headers, data=json.dumps(params))
    else:
        res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        ar = APIResp(res)
        if (_DEBUG): ar.printAll()
        return ar
    else:
        print("Error Code : " + str(res.status_code) + " | " + res.text)
        return None


# 계좌 잔고를 DataFrame 으로 반환
# Input: None (Option) rtCashFlag=True 면 예수금 총액을 반환하게 된다
# Output: DataFrame (Option) rtCashFlag=True 면 예수금 총액을 반환하게 된다

def get_acct_balance(rtCashFlag=False):
    url = '/uapi/overseas-stock/v1/trading/inquire-balance'

    dict_OVERS_EXCG_CD = {
        "미국전체": "NASD",
        "나스닥": "NAS",
        "뉴욕": "NYSE",
        "아멕스": "AMEX",
        "홍콩": "SEHK",
        "중국상해": "SHAA",
        "중국심천": "SZAA",
        "일본": "TKSE",
    }
    dict_TR_CRCY_CD = {
        "미국달러": "USD",
        "홍콩달러": "HKD",
        "중국위안화": "CNY",
        "일본엔화": "JPY",
        "베트남동": "VND",
    }
    if getTREnv().market in ["NASD", "NAS", "NYSE", "AMEX", ]:
        currency = dict_TR_CRCY_CD["미국달러"]
        if (getTREnv().svr == "vps"):
            tr_id = "VTTT3012R"
        elif (getTREnv().svr == "prod"):
            tr_id = "JTTT3012R"
    elif getTREnv().market in ["SEHK", "SHAA", "SZAA", "TKSE", ]:
        if (getTREnv().svr == "vps"):
            tr_id = "VTTS3012R"
        elif (getTREnv().svr == "prod"):
            tr_id = "TTTS3012R"

    params = {
        'CANO': getTREnv().my_acct,
        'ACNT_PRDT_CD': '01',
        'OVRS_EXCG_CD': getTREnv().market,
        'TR_CRCY_CD': currency,
        'CTX_AREA_FK200': '',
        'CTX_AREA_NK200': ''
    }
    # TODO: CTX_AREA_FK200 처리

    t1 = _url_fetch(url, tr_id, params)
    if rtCashFlag and t1.isOK():
        r2 = t1.getBody().output2
        return int(r2[0]['dnca_tot_amt'])

    output1 = t1.getBody().output1
    if t1.isOK() and output1:  # body 의 rt_cd 가 0 인 경우만 성공
        tdf = pd.DataFrame(output1)
        cf1 = ['cano', 'prdt_type_cd', 'ovrs_pdno', 'ovrs_item_name',
               'ovrs_cblc_qty', 'ord_psbl_qty', 'now_pric2', 'ovrs_stck_evlu_amt',
               'tr_crcy_cd', 'ovrs_excg_cd']
        cf2 = ['계좌번호', '상품유형코드', '종목코드', '종목명',
               '보유수량', '매도가능수량', '현재가', '평가금액',
               '통화코드', '거래소코드']
        cf_numeric = ["ovrs_cblc_qty", "ord_psbl_qty", "now_pric2", "ovrs_stck_evlu_amt", ]
        tdf = tdf[cf1]
        tdf[cf_numeric] = tdf[cf_numeric].apply(pd.to_numeric)
        tdf.set_index('ovrs_pdno', inplace=True)
        ren_dict = dict(zip(cf1, cf2))
        return tdf.rename(columns=ren_dict)
    else:
        t1.printError()
        return pd.DataFrame()


# 종목의 주식, ETF, 선물/옵션 등의 구분값을 반환. 현재는 무조건 주식(J)만 반환
def _getStockDiv(stock_no):
    return 'J'


# 종목별 현재가를 dict 로 반환
# Input: 종목코드
# Output: 현재가 Info dictionary. 반환된 dict 가 len(dict) < 1 경우는 에러로 보면 됨

def get_current_price(exchange, symbol):
    url = "/uapi/overseas-price/v1/quotations/price"
    tr_id = "HHDFS00000300"

    params = {
        "AUTH": "",
        "EXCD": exchange,
        "SYMB": symbol,
    }

    t1 = _url_fetch(url, tr_id, params)

    output = t1.getBody().output
    if t1.isOK() and output["rsym"] != '':
        return {
            "exchange": exchange,
            "symbol": symbol,
            "실시간조회종목코드": output["rsym"],
            "소수점자리수": int(output["zdiv"]),
            "전일종가": Decimal(output["base"]),
            "전일거래량": int(output["pvol"]),
            "현재가": Decimal(output["last"]),
            "거래량": int(output["tvol"]),
            "가능여부": output["ordy"],
        }
    else:
        t1.printError()
        return dict()


# 주문 base function
# Input: 종목코드, 주문수량, 주문가격, Buy Flag(If True, it's Buy order), order_type="00"(지정가)
# Output: HTTP Response

def do_order(excg_code, stock_code, order_qty, order_price, prd_code="01", buy_flag=True, order_type="00"):
    url = "/uapi/overseas-stock/v1/trading/order"

    '''
    [실전투자] 
    JTTT1002U : 미국 매수 주문 
    JTTT1006U : 미국 매도 주문 
    TTTS0308U : 일본 매수 주문 
    TTTS0307U : 일본 매도 주문 
    TTTS0202U : 상해 매수 주문 
    TTTS1005U : 상해 매도 주문 
    TTTS1002U : 홍콩 매수 주문 
    TTTS1001U : 홍콩 매도 주문 
    
    [모의투자] 
    VTTT1002U : 미국 매수 주문 
    VTTT1001U : 미국 매도 주문 
    VTTS0308U : 일본 매수 주문 
    VTTS0307U : 일본 매도 주문 
    VTTS0202U : 상해 매수 주문 
    VTTS1005U : 상해 매도 주문 
    VTTS1002U : 홍콩 매수 주문 
    VTTS1001U : 홍콩 매도 주문
    '''

    if getTREnv().market in ["NASD", "NAS", "NYSE", "AMEX", ]:
        if (getTREnv().svr == "vps"):
            if buy_flag:
                tr_id = "VTTT1002U"
            else:
                tr_id = "VTTT1001U"
        elif (getTREnv().svr == "prod"):
            if buy_flag:
                tr_id = "JTTT1002U"
            else:
                tr_id = "JTTT1006U"

    '''
    OVRS_EXCG_CD
    NASD : 나스닥 
    NYSE : 뉴욕 
    AMEX : 아멕스 
    SEHK : 홍콩 
    SHAA : 중국상해 
    SZAA : 중국심천 
    TKSE : 일본
    
    
    ORD_DVSN
    [Header tr_id JTTT1002U (미국 매수 주문)] 
    00 : 지정가 
    32 : LOO(장개시지정가) 
    34 : LOC(장마감지정가) 
    
    [Header tr_id JTTT1006U(미국 매도 주문)] 
    00 : 지정가 
    31 : MOD(장개시시장가) 
    32 : LOO(장개시지정가) 
    34 : LOC(장마감지정가) 
    
    [Header tr_id JTTT1006U (홍콩 매도 주문)] 
    00 : 지정가 
    05 : 단주지정가 셋팅 
    
    [그외 tr_id] 
    제거
    '''
    params = {
        'CANO': getTREnv().my_acct,
        'ACNT_PRDT_CD': prd_code,
        'OVRS_EXCG_CD': excg_code,
        'PDNO': stock_code,
        'ORD_QTY': str(order_qty),
        'OVRS_ORD_UNPR': str(order_price),
        'CTAC_TLNO': '',
        "MGCO_APTM_ODNO": "",
        'ORD_SVR_DVSN_CD': '0',
        'ORD_DVSN': order_type,
    }
    if not buy_flag:
        params['SLL_TYPE'] = '00'

    t1 = _url_fetch(url, tr_id, params, postFlag=True, hashFlag=True)

    if t1.isOK():
        return t1
    else:
        t1.printError()
        return None


# 사자 주문. 내부적으로는 do_order 를 호출한다.
# Input: 종목코드, 주문수량, 주문가격
# Output: True, False

def do_sell(excg_code, stock_code, order_qty, order_price, prd_code="01", order_type="00"):
    t1 = do_order(excg_code, stock_code, order_qty, order_price, buy_flag=False, order_type=order_type)
    return t1.isOK()


# 팔자 주문. 내부적으로는 do_order 를 호출한다.
# Input: 종목코드, 주문수량, 주문가격
# Output: True, False

def do_buy(excg_code, stock_code, order_qty, order_price, prd_code="01", order_type="00"):
    t1 = do_order(excg_code, stock_code, order_qty, order_price, buy_flag=True, order_type=order_type)
    return t1.isOK()


# 정정취소 가능한 주문 목록을 DataFrame 으로 반환
# Input: None
# Output: DataFrame

def get_orders(prd_code='01'):
    url = "/uapi/overseas-stock/v1/trading/inquire-nccs"

    if getTREnv().market in ["NASD", "NAS", "NYSE", "AMEX", ]:
        if (getTREnv().svr == "vps"):
            tr_id = "VTTT3018R"
        elif (getTREnv().svr == "prod"):
            tr_id = "JTTT3018R"
    '''
    [실전투자] 
    JTTT3018R : 미국 미체결 내역 
    TTTS3018R : 홍콩/중국/일본 미체결 내역 
    
    [모의투자] 
    VTTT3018R : 미국 미체결 내역 
    VTTS3018R : 홍콩/중국/일본 미체결 내역
    '''

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "OVRS_EXCG_CD": getTREnv().market,
        "SORT_SQN": "DS",
        "CTX_AREA_FK200": '',
        "CTX_AREA_NK200": '',
    }

    # TODO: CTX_AREA_FK200 처리
    # TODO: tr_cont 처리

    t1 = _url_fetch(url, tr_id, params)
    if t1.isOK() and t1.getBody().output:
        tdf = pd.DataFrame(t1.getBody().output)
        cf1 = ['pdno', 'prdt_name', 'ft_ord_qty', 'ft_ccld_qty', 'nccs_qty',
               'ft_ord_unpr3', 'ft_ccld_unpr3', 'ft_ccld_amt3', 'ord_tmd', 'ord_gno_brno',
               'odno', 'orgn_odno', "tr_mket_name", "ovrs_excg_cd",
               "sll_buy_dvsn_cd", "sll_buy_dvsn_cd_name",
               ]
        cf2 = ['종목코드', '종목명', '주문수량', '체결수량', '미체결수량',
               '주문가격', '체결가격', '체결금액', '시간', '주문점',
               '주문번호', '원번호', "거래시장명", "거래소코드",
               '매수매도코드', '매수매도구분']
        tdf = tdf[cf1]
        # tdf.set_index('orgn_odno', inplace=True)
        ren_dict = dict(zip(cf1, cf2))  # FIXME : 미체결수량 등 int 처리해줘야함
        return tdf.rename(columns=ren_dict)

    else:
        t1.printError()
        return pd.DataFrame()


# 특정 주문 취소(01)/정정(02)
# Input: 주문 번호(get_orders 를 호출하여 얻은 DataFrame 의 index  column 값이 취소 가능한 주문번호임)
#       주문점(통상 06010), 주문수량, 주문가격, 상품코드(01), 주문유형(00), 정정구분(취소-02, 정정-01)
# Output: APIResp object

def _do_cancel_revise(excg_code, order_no, symbol, order_qty, order_price, prd_code, order_dv, cncl_dv, ):
    url = "/uapi/overseas-stock/v1/trading/order-rvsecncl"

    if getTREnv().svr == "prod":
        if getTREnv().market == "NAS":
            tr_id = "JTTT1004U"

    # elif getTREnv().svc == "":
    '''
    [실전투자] 
    JTTT1004U : 미국 정정 취소 주문 
    TTTS1003U : 홍콩 정정 취소 주문 
    TTTS0309U : 일본 정정 취소 주문 
    TTTS0302U : 상해 취소 주문 
    
    [모의투자] 
    VTTT1004U : 미국 정정 취소 주문 
    VTTS1003U : 홍콩 정정 취소 주문 
    VTTS0309U : 일본 정정 취소 주문 
    VTTS0302U : 상해 취소 주문
    '''
    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "OVRS_EXCG_CD": excg_code,
        "PDNO": symbol,
        "ORGN_ODNO": order_no,
        "ORD_DVSN": order_dv,
        "RVSE_CNCL_DVSN_CD": cncl_dv,  # 취소(02) 01 : 정정
        "ORD_QTY": str(order_qty),
        "OVRS_ORD_UNPR": str(order_price),
        "CTAC_TLNO": "",
        "MGCO_APTM_ODNO": "",
        "ORD_SVR_DVSN_CD": "0"
    }

    t1 = _url_fetch(url, tr_id, params=params, postFlag=True)

    if t1.isOK():
        return t1
    else:
        t1.printError()
        return None


# 특정 주문 취소
#
def do_cancel(excg_code, order_no, order_qty, symbol, order_price='', prd_code='01', order_dv='00', cncl_dv='02', ):
    return _do_cancel_revise(excg_code, order_no, symbol, order_qty, order_price, prd_code, order_dv, cncl_dv)


# 특정 주문 정정
#
def do_revise(excg_code, order_no, order_qty, symbol, order_price, prd_code='01', order_dv='00', cncl_dv='01', ):
    return _do_cancel_revise(excg_code, order_no, symbol, order_qty, order_price, prd_code, order_dv, cncl_dv)


# 모든 주문 취소
# Input: None
# Output: None

def do_cancel_all():
    raise NotImplementedError
    tdf = get_orders()
    od_list = tdf.index.to_list()
    qty_list = tdf['주문수량'].to_list()
    price_list = tdf['주문가격'].to_list()
    branch_list = tdf['주문점'].to_list()
    cnt = 0
    for x in od_list:
        ar = do_cancel(x, qty_list[cnt], price_list[cnt], branch_list[cnt])
        cnt += 1
        print(ar.getErrorCode(), ar.getErrorMessage())
        time.sleep(.2)


# 내 계좌의 일별 주문 체결 조회
# Input: 시작일, 종료일 (Option)지정하지 않으면 현재일
# output: DataFrame

def get_my_complete(sdt, edt=None, prd_code='01', zipFlag=True):
    raise NotImplementedError

    url = "/uapi/overseas-stock/v1/trading/inquire-ccnl"

    if getTREnv().svc == "prod":
        if getTREnv().market == "NAS":
            tr_id = "JTTT3001R"

    '''
    [실전투자] 
    JTTT3001R : 미국 주문체결 내역 
    TTTS3035R : 홍콩/중국/일본 주문체결 내역 
    
    [모의투자] 
    VTTT3001R : 미국 주문체결 내역 
    VTTS3035R : 홍콩/중국/일본 주문체결 내역
    '''

    if (edt is None):
        ltdt = datetime.now().strftime('%Y%m%d')
    else:
        ltdt = edt

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "INQR_STRT_DT": sdt,
        "PDNO": "",
        "ORD_STRT_DT": ltdt,
        "ORD_END_DT": ltdt,
        "SLL_BUY_DVSN": "00",
        # 00: 전체
        # 01: 매도
        # 02: 매수
        "CCLD_NCCS_DVSN": "00",
        # 00: 전체
        # 01: 체결
        # 02: 미체결
        "OVRS_EXCG_CD": "",
        "SORT_SQN": "",
        "ORD_DT": "",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": "",

    }

    t1 = _url_fetch(url, tr_id, params)

    # output1 과 output2 로 나뉘어서 결과가 옴. 지금은 output1만 DF 로 변환
    if t1.isOK():
        tdf = pd.DataFrame(t1.getBody().output1)
        tdf.set_index('odno', inplace=True)
        if (zipFlag):
            return tdf[
                ['ord_dt', 'orgn_odno', 'sll_buy_dvsn_cd_name', 'pdno', 'ord_qty', 'ord_unpr', 'avg_prvs', 'cncl_yn',
                 'tot_ccld_amt', 'rmn_qty']]
        else:
            return tdf
    else:
        t1.printError()
        return pd.DataFrame()


# 잔고 확인
def get_buyable_cash(prd_code='01'):
    url = "/uapi/overseas-stock/v1/trading/inquire-present-balance"
    tr_id = "CTRP6504R"

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "WCRC_FRCR_DVSN_CD": "02",
        "NATN_CD": "840", # 미국
        "TR_MKET_CD": "01", # 나스닥
        "INQR_DVSN_CD": "01" # 일반해외주식
    }
    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        body = t1.getBody()
        output = {}
        for o in body.output2:
            if o["crcy_cd"] == "USD":
                output.update(o)
        output.update(body.output3)
        output["AUM"] = float(output["frcr_dncl_amt_2"])
        return output
    else:
        t1.printError()
        return {}


# 시세 Function

# 종목별 체결 Data
# Input: 종목코드
# Output: 체결 Data DataFrame
# 주식체결시간, 주식현재가, 전일대비, 전일대비부호, 체결거래량, 당일 체결강도, 전일대비율
def get_stock_completed(stock_no):
    raise NotImplementedError

    url = "/uapi/domestic-stock/v1/quotations/inquire-ccnl"

    tr_id = "FHKST01010300"

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_no
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return pd.DataFrame(t1.getBody().output)
    else:
        t1.printError()
        return pd.DataFrame()


# 종목별 history data (현재 기준 30개만 조회 가능)
# Input: 종목코드, 구분(D, W, M 기본값은 D)
# output: 시세 History DataFrame
def get_stock_history(stock_no, gb_cd='D'):
    raise NotImplementedError

    url = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"

    params = {
        "FID_COND_MRKT_DIV_CODE": _getStockDiv(stock_no),
        "FID_INPUT_ISCD": stock_no,
        "FID_PERIOD_DIV_CODE": gb_cd,
        "FID_ORG_ADJ_PRC": "0000000001"
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return pd.DataFrame(t1.getBody().output)
    else:
        t1.printError()
        return pd.DataFrame()


# 종목별 history data 를 표준 OHLCV DataFrame 으로 반환
# Input: 종목코드, 구분(D, W, M 기본값은 D), (Option)adVar 을 True 로 설정하면
#        OHLCV 외에 inter_volatile 과 pct_change 를 추가로 반환한다.
# output: 시세 History OHLCV DataFrame
def get_stock_history_by_ohlcv(stock_no, gb_cd='D', adVar=False):
    raise NotImplementedError

    hdf1 = get_stock_history(stock_no, gb_cd)

    chosend_fld = ['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
    renamed_fld = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

    hdf1 = hdf1[chosend_fld]
    ren_dict = dict()
    i = 0
    for x in chosend_fld:
        ren_dict[x] = renamed_fld[i]
        i += 1

    hdf1.rename(columns=ren_dict, inplace=True)
    hdf1[['Date']] = hdf1[['Date']].apply(pd.to_datetime)
    hdf1[['Open', 'High', 'Low', 'Close', 'Volume']] = hdf1[['Open', 'High', 'Low', 'Close', 'Volume']].apply(
        pd.to_numeric)
    hdf1.set_index('Date', inplace=True)

    if (adVar):
        hdf1['inter_volatile'] = (hdf1['High'] - hdf1['Low']) / hdf1['Close']
        hdf1['pct_change'] = (hdf1['Close'] - hdf1['Close'].shift(-1)) / hdf1['Close'].shift(-1) * 100

    return hdf1

# # 투자자별 매매 동향
# # Input: 종목코드
# # output: 매매 동향 History DataFrame (Date, PerBuy, ForBuy, OrgBuy) 30개 row를 반환
# def get_stock_investor(stock_no):
#     url = "/uapi/domestic-stock/v1/quotations/inquire-investor"
#     tr_id = "FHKST01010900"
#
#     params = {
#         "FID_COND_MRKT_DIV_CODE": _getStockDiv(stock_no),
#         "FID_INPUT_ISCD": stock_no
#     }
#
#     t1 = _url_fetch(url, tr_id, params)
#
#     if t1.isOK():
#         hdf1 = pd.DataFrame(t1.getBody().output)
#
#         chosend_fld = ['stck_bsop_date', 'prsn_ntby_qty', 'frgn_ntby_qty', 'orgn_ntby_qty']
#         renamed_fld = ['Date', 'PerBuy', 'ForBuy', 'OrgBuy']
#
#         hdf1 = hdf1[chosend_fld]
#         ren_dict = dict()
#         i = 0
#         for x in chosend_fld:
#             ren_dict[x] = renamed_fld[i]
#             i += 1
#
#         hdf1.rename(columns=ren_dict, inplace=True)
#         hdf1[['Date']] = hdf1[['Date']].apply(pd.to_datetime)
#         hdf1[['PerBuy', 'ForBuy', 'OrgBuy']] = hdf1[['PerBuy', 'ForBuy', 'OrgBuy']].apply(pd.to_numeric)
#         hdf1['EtcBuy'] = (hdf1['PerBuy'] + hdf1['ForBuy'] + hdf1['OrgBuy']) * -1
#         hdf1.set_index('Date', inplace=True)
#         # sum을 맨 마지막에 추가하는 경우
#         # tdf.append(tdf.sum(numeric_only=True), ignore_index=True) <- index를 없애고  만드는 경우
#         # tdf.loc['Total'] = tdf.sum() <- index 에 Total 을 추가하는 경우
#         return hdf1
#     else:
#         t1.printError()
#         return pd.DataFrame()
