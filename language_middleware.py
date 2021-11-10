from aiogram.contrib.middlewares.i18n import I18nMiddleware
from config import I18N_DOMAIN, LOCALES_DIR

i18n = I18nMiddleware(I18N_DOMAIN, LOCALES_DIR)