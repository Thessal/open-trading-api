from rest import kis_api_overseas as kis_api
from telegram import Logger
from telegram import Commander
import logging
import asyncio


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())

    # kis_api.auth(svr="vps")
    kis_api.auth(svr="prod")
    kis_api.get_acct_balance()

    try:
        print(kis_api.get_current_price(exchange="NAS", symbol="TSLA"))
    except Exception as e:
        print(e)
    kis_api.get_orders()

    logger = logging.getLogger("all")
    print('PyCharm')

