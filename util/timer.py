import asyncio


class Timer:
    def __init__(self):
        self.run = False
        self.jobs = []
        self.panic = False

    def current_time(self):
        pass

    async def loop(self, fn):
        while not self.panic:
            fn["function"]()
            await asyncio.sleep(fn["period"])

    async def main(self):
        for job in self.jobs:
            asyncio.create_task(self.loop(job))

        await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})

