from aiogram.utils.callback_data import CallbackData


cb_menu = CallbackData('menu', 'menu')
cb_menu_page = CallbackData('menu_page', 'menu', 'page')
cb_item_id_action = CallbackData('item_id', 'item', 'id', 'action')

cb_lang = CallbackData('lang', 'action', 'data')
cb_balance = CallbackData('balance', 'action')

cb_cus = CallbackData('cus', '')
