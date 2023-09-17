from default_data import dp
from data import elli_bot
import interface as ei

from aiogram.utils import executor
from aiogram.types import ContentTypes


def main():
    elli_bot.startLoadChatInfo()

    dp.register_message_handler(ei.elliBuySubscribeHandler, commands=["buy"])
    dp.register_pre_checkout_query_handler(ei.elliProcessPaymentHandler)
    dp.register_message_handler(ei.elliSuccessfulPaymentHandler, content_types=ContentTypes.SUCCESSFUL_PAYMENT)
    dp.register_message_handler(ei.startHandler, commands=["start"])
    dp.register_message_handler(ei.helpHandler, commands=["help"])
    dp.register_message_handler(ei.elliClearHandler, commands=["clear"])
    dp.register_message_handler(ei.elliChangeHandler, commands=["change"])
    dp.register_message_handler(ei.elliDefaultHandler, commands=["default"])
    dp.register_message_handler(ei.profileHandler, commands=["profile"])
    dp.register_message_handler(ei.elliGiveSubscribeHandler, commands=["give"])
    dp.register_message_handler(ei.botSendAllMessage, commands=["message_all"])
    dp.register_message_handler(ei.botSendTestMessage, commands=["message_test"])
    dp.register_message_handler(ei.statisticHandler, commands=["statistic"])
    dp.register_message_handler(ei.elliAudioHandler, content_types=["audio", "voice"])
    dp.register_message_handler(ei.botGiftHandler, commands=["gift"])
    dp.register_message_handler(ei.botClearGiftHandler, commands=["clear_gift"])
    dp.register_message_handler(ei.elliHandler)

    while True:
        executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
