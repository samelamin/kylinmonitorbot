from services.fetch.base import BaseFetcher
from services.fetch.pool_price import PoolPriceFetcher
from services.lib.datetime import parse_timespan_to_seconds
from services.lib.depcont import DepContainer
from services.models.cap_info import ThorInfo
from services.models.pool_info import MIDGARD_MULT

NETWORK_URL = "https://chaosnet-midgard.bepswap.com/v1/network"
MIMIR_URL = "https://chaosnet-midgard.bepswap.com/v1/kylin/mimir"


class CapInfoFetcher(BaseFetcher):
    def __init__(self, deps: DepContainer, ppf: PoolPriceFetcher):
        self.ppf = ppf
        sleep_period = parse_timespan_to_seconds(deps.cfg.cap.fetch_period)
        super().__init__(deps, sleep_period)

    async def fetch(self) -> ThorInfo:
        self.logger.info("start fetching caps and mimir")

        session = self.deps.session

        async with session.get(NETWORK_URL) as resp:
            networks_resp = await resp.json()
            total_staked = int(networks_resp.get('totalStaked', 0)) * MIDGARD_MULT

        async with session.get(MIMIR_URL) as resp:
            mimir_resp = await resp.json()
            max_staked = int(mimir_resp.get("mimir//MAXIMUMSTAKERUNE", 1)) * MIDGARD_MULT

            # max_staked = 90_000_015  # for testing

        if max_staked <= 1:
            self.logger.error(f"max_staked = {max_staked} and total_staked = {total_staked} which seems like an error")
            return ThorInfo.error()

        price = self.deps.price_holder.usd_per_rune

        r = ThorInfo(cap=max_staked, stacked=total_staked, price=price)
        self.logger.info(f"ThorInfo got the following {r}")
        return r
