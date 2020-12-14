from aiogram import filters
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import *
from aiogram.utils.helper import HelperMode

from services.dialog.base import BaseDialog, message_handler
from services.dialog.settings_menu import SettingsDialog
from services.dialog.stake_info import StakeDialog
from services.fetch.fair_price import fair_rune_price
from services.models.cap_info import ThorInfo
from services.models.price import PriceReport
from services.notify.types.price_notify import PriceNotifier


class MainStates(StatesGroup):
    mode = HelperMode.snake_case

    MAIN_MENU = State()
    ASK_LANGUAGE = State()
    SETTINGS = State()


class MainMenuDialog(BaseDialog):
    @message_handler(commands='start,lang', state='*')
    async def entry_point(self, message: Message):
        await self.deps.broadcaster.register_user(message.from_user.id)
        loc_man = self.deps.loc_man
        if message.get_command(pure=True) == 'lang' or await loc_man.get_lang(message.from_user.id,
                                                                              self.deps.db) is None:
            await SettingsDialog(self.loc, self.data, self.deps).ask_language(message)
        else:
            info = await ThorInfo.get_old_cap(self.deps.db)
            await message.answer(self.loc.welcome_message(info),
                                 reply_markup=self.loc.kbd_main_menu(),
                                 disable_notification=True)
            await MainStates.MAIN_MENU.set()

    @message_handler(commands='cap', state='*')
    async def cmd_cap(self, message: Message):
        info = await ThorInfo.get_old_cap(self.deps.db)
        await message.answer(self.loc.welcome_message(info),
                             disable_web_page_preview=True,
                             disable_notification=True)

    @message_handler(commands='price', state='*')
    async def cmd_price(self, message: Message):
        fp = await fair_rune_price(self.deps.price_holder)
        pn = PriceNotifier(self.deps)
        price_1h, price_24h, price_7d = await pn.historical_get_triplet()
        fp.real_rune_price = self.deps.price_holder.usd_per_rune
        btc_price = self.deps.price_holder.btc_per_rune

        price_text = self.loc.notification_text_price_update(PriceReport(
            price_1h, price_24h, price_7d,
            fair_price=fp,
            btc_real_rune_price=btc_price))

        await message.answer(price_text,
                             disable_web_page_preview=True,
                             disable_notification=True)

    @message_handler(commands='help', state='*')
    async def cmd_help(self, message: Message):
        await message.answer(self.loc.help_message(),
                             disable_web_page_preview=True,
                             disable_notification=True)

    @message_handler(filters.RegexpCommandsFilter(regexp_commands=[r'/.*']), state='*')
    async def on_unknown_command(self, message: Message):
        await message.answer(self.loc.unknown_command(), disable_notification=True)

    @message_handler(state=MainStates.MAIN_MENU)
    async def on_main_menu(self, message: Message):
        if message.text == self.loc.BUTTON_MM_PRICE:
            await self.cmd_price(message)
        elif message.text == self.loc.BUTTON_MM_CAP:
            await self.cmd_cap(message)
        elif message.text == self.loc.BUTTON_MM_MY_ADDRESS:
            message.text = ''
            await StakeDialog(self.loc, self.data, self.deps).on_enter(message)
        elif message.text == self.loc.BUTTON_MM_SETTINGS:
            await SettingsDialog(self.loc, self.data, self.deps).on_enter(message)
        else:
            return False
