import requests
import time
import os
import telegram
import argparse
import logging
from logging.handlers import RotatingFileHandler
import traceback
from dotenv import load_dotenv


def main():
    load_dotenv()
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    bot = telegram.Bot(token=telegram_bot_token)
    chat_id_env = os.getenv('TELEGRAM_CHAT_ID')
    authorization_token = os.getenv('AUTHORIZATION_DEVMAN_TOKEN')
    parser = argparse.ArgumentParser(description='Получения chat_id пользователя в телеграме')
    parser.add_argument(
        'chat_id',
        type=str,
        nargs='?',
        help='ID пользователя в телеграм чате',
        default=None
    )
    args = parser.parse_args()
    chat_id = args.chat_id if args.chat_id is not None else chat_id_env
    header = {
        "Authorization": authorization_token
    }

    url = f'https://dvmn.org/api/long_polling/'

    last_timestamp = time.time()
    while True:
        try:
            params = {'timestamp': last_timestamp}
            response = requests.get(url, headers=header, params=params, timeout=90)
            response.raise_for_status()
            content_last_attempt = response.json()
            if content_last_attempt['status'] == 'found':
                last_timestamp = content_last_attempt['last_attempt_timestamp']    
                lesson_title = content_last_attempt['new_attempts'][0]['lesson_title']
                lesson_url = content_last_attempt['new_attempts'][0]['lesson_url']
                success_text = 'Работа по: "<a href=\'{lesson_url}\'>{lesson_title}</a>" принята.'.format(
                    lesson_title=lesson_title,
                    lesson_url=lesson_url,
                )
                error_text = 'Работа по: "<a href=\'{lesson_url}\'>{lesson_title}</a>" отправлена на доработку.'.format(
                    lesson_title=lesson_title,
                    lesson_url=lesson_url,
                )
                if not content_last_attempt['new_attempts'][0]['is_negative']:
                    bot.send_message(chat_id=chat_id, text=success_text, parse_mode=telegram.ParseMode.HTML)
                    logger.info(f"Сообщение успешно отправлено: {success_text}")
                else:
                    bot.send_message(chat_id=chat_id, text=error_text, parse_mode=telegram.ParseMode.HTML)
                    logger.info(f"Сообщение успешно отправлено: {error_text}")
        except requests.exceptions.ReadTimeout:
            time.sleep(5)
            continue
        except requests.exceptions.RequestException as error:
            logger.exception("Ошибка запроса:")
            error_message = f"Ошибка при выполнении запроса: {error}\n\n{traceback.format_exc()}"
            bot.send_message(chat_id=chat_id, text=error_message)
            time.sleep(5)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler('devman_bot.log', maxBytes=200*1024**2, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
    logger.critical('Critical message')
    main()
