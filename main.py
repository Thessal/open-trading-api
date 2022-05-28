from util import clock, debug
from rest import kis_api_overseas as kis_api
# from telegram import Commander
# from commander import commander
import logging
import asyncio
import strat.strats
from util.timer import Timer

if __name__ == '__main__':
    # # kis_api.auth(svr="vps")
    kis_api.auth(svr="prod")
    kis_api.get_acct_balance()

    logger = logging.getLogger("all")
    clock = clock.Clock()
    dmgrs_lst = dmgr.dmgrs.initialize(kis_api, clock, logger)
    strats_lst = strat.strats.initialize_strats(kis_api, clock, logger)
    commander = commander.commander(dmgrs=dmgrs_lst, strats=strats_lst)
    # debug = debug.Debug(cfg={"clock":clock})

    t = Timer()
    t.jobs = []
    t.jobs += [{"function": clock.tick, "period": 0.1}]
    t.jobs += [{"function": commander.loop, "period": 1}]
    t.jobs += [{"function": dmgr.loop, "period": 1} for dmgr in dmgrs_lst]
    t.jobs += [
        {"function": strats_lst[0].loop, "period": 15},
        {"function": strats_lst[1].loop, "period": 15},
    ]
    # t.jobs += [{"function": debug.loop, "period": 1}]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(t.main())
    # raise NotImplemented

