from rest import kis_api_overseas as kis_api
from telegram import Logger
# from telegram import Commander
import logging
import asyncio
import numpy as np
from decimal import *

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())

    # kis_api.auth(svr="vps")
    kis_api.auth(svr="prod")
    # kis_api.DEBUG_auth(svr="prod")
    kis_api.get_acct_balance()

    test_price = kis_api.get_current_price(exchange="NAS", symbol="AGRI")
    # test_buy = kis_api.do_buy(
    #     excg_code={"NAS": "NASD"}[test_price["exchange"]],
    #     stock_code=test_price['symbol'],
    #     order_qty=1,
    #     order_price=(test_price["현재가"] * Decimal(0.99)).quantize(
    #         Decimal('1.' + '0' * min(2, test_price["소수점자리수"])), rounding=ROUND_DOWN),
    #     prd_code="01", order_type="00")
    # test_sell = kis_api.do_sell(
    #     excg_code={"NAS": "NASD"}[test_price["exchange"]],
    #     stock_code=test_price['symbol'],
    #     order_qty=1,
    #     order_price=(test_price["현재가"] * Decimal(1.01)).quantize(
    #         Decimal('1.' + '0' * min(2, test_price["소수점자리수"])), rounding=ROUND_UP),
    #     prd_code="01", order_type="00")

    orders = kis_api.get_orders()
    order_to_revise = orders.iloc[0]
    order_to_cancel = orders.iloc[-1]
    kis_api.do_revise(
        excg_code=order_to_revise["거래소코드"],
        order_no=order_to_revise["주문번호"],
        order_qty=order_to_revise["미체결수량"],
        symbol=order_to_revise["종목코드"],
        order_price=(test_price["현재가"] * (
            Decimal(0.98) if order_to_revise["매수매도구분"] == "매수" else Decimal(1.02))).quantize(
            Decimal('1.' + '0' * min(2, test_price["소수점자리수"])),
            rounding=ROUND_DOWN if order_to_revise["매수매도구분"] == "매수" else ROUND_UP)
        , prd_code='01', order_dv='00', cncl_dv='01',
    )
    # TODO
    # # kis_api.do_cancel(excg_code, order_no, order_qty, order_price, symbol, prd_code='01', order_dv='00', cncl_dv='02',)
    # kis_api._do_cancel_revise()
    kis_api.do_cancel_all()

    logger = logging.getLogger("all")
    print('PyCharm')
