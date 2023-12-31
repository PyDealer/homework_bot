from http import HTTPStatus
import sys
import time
import logging
import os
import requests

from dotenv import load_dotenv
import telegram

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    virable_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    try:
        for virable in virable_list:
            all(virable)
    except Exception as error:
        logging.critical(
            f'Одной из переменных окружения не существует: {error}')
        sys.exit()


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    logging.info('Попытка отправить сообщение.')
    if message:
        logging.debug('Сообщение отправлено.')
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(timestamp):
    """Делает запрос эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            raise requests.exceptions.HTTPError(
                (f'Ошибка запроса, статус {response.status_code}'))
        data = response.json()
        return data
    except requests.RequestException as e:
        logging.error('Ошибка при выполнении запроса:', e)


def check_response(response):
    """Проверяет ответ API на соответствие документации из урока API."""
    if ('homeworks' not in response or not
            isinstance(response['homeworks'], list) or not
            isinstance(response, dict)):
        error_message = 'Неверный формат данных в ответе API'
        logging.error(error_message)
        raise TypeError(error_message)
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус проверенной работы."""
    try:
        status = homework['status']
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        raise KeyError('Не хватает ключа')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        filename='main.log',
        level=logging.INFO,
        encoding='utf-8',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        timestamp = int(time.time())
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response.get('homeworks')) != 0:
                message = parse_status(response['homeworks'][0])
                send_message(bot, message)
            else:
                logging.debug('Работа пока не проверена')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
