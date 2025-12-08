import json
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import mimetypes
import os

# Настройка логирования
logger = logging.getLogger(__name__)


class EvolutionAPIError(Exception):
    """Класс для ошибок Evolution API"""
    pass


class EvolutionMailTool:
    """
    Класс для работы с Evolution API (Cloud.ru) для отправки писем.
    """

    def __init__(
            self,
            api_key: str,
            base_url: str = "https://api.evolution-mail.ru/v1",
            default_sender: Optional[str] = None
    ):
        """
        Инициализация клиента Evolution API.

        Args:
            api_key: API ключ от Cloud.ru Evolution
            base_url: Базовый URL API (по умолчанию официальный)
            default_sender: Email отправителя по умолчанию
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_sender = default_sender
        self.session = None

        # Заголовки для всех запросов
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        logger.info(f"EvolutionMailTool инициализирован с базовым URL: {base_url}")

    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекста"""
        if self.session:
            await self.session.close()

    def _create_session_if_needed(self):
        """Создает сессию если она не существует (для синхронного использования)"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None

    def _encode_attachment(self, file_path: str) -> Dict[str, str]:
        """
        Кодирует файл в base64 для вложения.

        Args:
            file_path: Путь к файлу

        Returns:
            Словарь с данными вложения
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        # Определяем MIME тип
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Читаем и кодируем файл
        with open(file_path, 'rb') as f:
            file_data = f.read()

        encoded_data = base64.b64encode(file_data).decode('utf-8')

        # Получаем имя файла
        filename = os.path.basename(file_path)

        return {
            "filename": filename,
            "content": encoded_data,
            "mime_type": mime_type
        }

    async def send_email(
            self,
            to: List[str],
            subject: str,
            body: str,
            sender: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            reply_to: Optional[str] = None,
            attachments: Optional[List[str]] = None,
            html_body: Optional[str] = None,
            importance: str = "normal",  # "high", "normal", "low"
            track_opens: bool = False,
            track_clicks: bool = False
    ) -> Dict[str, Any]:
        """
        Отправляет email через Evolution API.

        Args:
            to: Список email получателей
            subject: Тема письма
            body: Текст письма (plain text)
            sender: Email отправителя (если None, используется default_sender)
            cc: Список email для копии

Nastya хакатон AI Devtools Hack, [08.12.2025 17:07]
bcc: Список email для скрытой копии
            reply_to: Email для ответа
            attachments: Список путей к файлам для вложений
            html_body: HTML версия письма (если нужна)
            importance: Важность письма
            track_opens: Трекинг открытий
            track_clicks: Трекинг кликов

        Returns:
            Ответ от API с деталями отправки

        Raises:
            EvolutionAPIError: Если произошла ошибка API
        """
        if not sender and not self.default_sender:
            raise ValueError("Не указан отправитель. Укажите sender или установите default_sender")

        sender_email = sender or self.default_sender

        try:
            # Подготовка данных письма
            email_data = {
                "from": sender_email,
                "to": to,
                "subject": subject,
                "text": body
            }

            # Добавляем опциональные поля
            if cc:
                email_data["cc"] = cc
            if bcc:
                email_data["bcc"] = bcc
            if reply_to:
                email_data["reply_to"] = reply_to
            if html_body:
                email_data["html"] = html_body

            # Настройки письма
            email_data["importance"] = importance
            email_data["track_opens"] = track_opens
            email_data["track_clicks"] = track_clicks

            # Обработка вложений
            if attachments:
                encoded_attachments = []
                for attachment_path in attachments:
                    try:
                        encoded_att = self._encode_attachment(attachment_path)
                        encoded_attachments.append(encoded_att)
                    except Exception as e:
                        logger.warning(f"Не удалось закодировать вложение {attachment_path}: {e}")
                        continue

                if encoded_attachments:
                    email_data["attachments"] = encoded_attachments

            # Создаем сессию если нужно
            self._create_session_if_needed()

            # Отправляем запрос
            async with self.session.post(
                    f"{self.base_url}/send",
                    json=email_data
            ) as response:
                result = await response.json()

                if response.status == 200:
                    logger.info(f"Письмо отправлено. ID: {result.get('message_id', 'unknown')}")
                    return result
                else:
                    error_msg = result.get('error', result.get('message', 'Unknown error'))
                    logger.error(f"Ошибка отправки письма: {error_msg}")
                    raise EvolutionAPIError(f"Evolution API error: {error_msg}")

        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка при отправке письма: {e}")
            raise EvolutionAPIError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке письма: {e}")
            raise EvolutionAPIError(f"Unexpected error: {str(e)}")

    async def send_template_email(
            self,
            template_id: str,
            to: List[str],
            template_data: Dict[str, Any],
            sender: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Отправляет письмо используя шаблон.

        Args:
            template_id: ID шаблона в Evolution
            to: Список получателей
            template_data: Данные для заполнения шаблона
            sender: Email отправителя
            cc: Список для копии
            bcc: Список для скрытой копии

        Returns:
            Ответ от API
        """
        sender_email = sender or self.default_sender

        email_data = {
            "from": sender_email,
            "to": to,
            "template_id": template_id,
            "template_data": template_data
        }

        if cc:
            email_data["cc"] = cc
        if bcc:
            email_data["bcc"] = bcc

        self._create_session_if_needed()

        async with self.session.post(
                f"{self.base_url}/send/template",
                json=email_data
        ) as response:
            return await response.json()

    async def get_delivery_status(
            self,
            message_id: str
    ) -> Dict[str, Any]:
        """
        Получает статус доставки письма.

        Args:
            message_id: ID письма

        Returns:
            Статус доставки
        """
        self._create_session_if_needed()

        async with self.session.get(
                f"{self.base_url}/status/{message_id}"
        ) as response:
            return await response.json()

    async def validate_email(
            self,
            email: str
    ) -> Dict[str, Any]:
        """
        Валидирует email адрес.

        Args:
            email: Email для валидации

        Returns:
            Результат валидации
        """
        self._create_session_if_needed()

        async with self.session.post(
                f"{self.base_url}/validate",
                json={"email": email}
        ) as response:
            return await response.json()


# Экспортируемые инструменты для MCP-сервера

async def send_email_tool(
        to_emails: str,
        subject: str,
        body: str,
        sender_email: Optional[str] = None,
        cc_emails: Optional[str] = None,
        bcc_emails: Optional[str] = None,
        attachments: Optional[str] = None,
        api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Инструмент для отправки email через Evolution API.

    Args:
        to_emails: Email получателей (через запятую)
        subject: Тема письма
        body: Текст письма
        sender_email: Email отправителя
        cc_emails: Email для копии (через запятую)
        bcc_emails: Email для скрытой копии (через запятую)
        attachments: Пути к файлам вложений (через запятую)
        api_key: API ключ (если не передан, берется из переменных окружения)

    Returns:
        Результат отправки
    """
    if not api_key:
        from ml.config import get_evolution_api_key
        api_key = get_evolution_api_key()

    if not api_key:
        return {"error": "API ключ не найден. Установите EVOLUTION_API_KEY в переменных окружения."}

    # Парсинг email списков
    to_list = [email.strip() for email in to_emails.split(',')]
    cc_list = None
    bcc_list = None
    attachments_list = None

    if cc_emails:
        cc_list = [email.strip() for email in cc_emails.split(',')]
    if bcc_emails:
        bcc_list = [email.strip() for email in bcc_emails.split(',')]
    if attachments:
        attachments_list = [path.strip() for path in attachments.split(',')]

    # Создание клиента и отправка
    client = EvolutionMailTool(api_key=api_key)
    async with client:
        try:
            result = await client.send_email(
                to=to_list,
                subject=subject,
                body=body,
                sender=sender_email,
                cc=cc_list,
                bcc=bcc_list,
                attachments=attachments_list
            )
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }
        except EvolutionAPIError as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


async def send_hr_email_tool(
        candidate_email: str,
        candidate_name: str,
        position: str,
        email_template: str = "interview_invitation",
        api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Специализированный инструмент для отправки HR писем.

    Args:
        candidate_email: Email кандидата

Nastya хакатон AI Devtools Hack, [08.12.2025 17:07]
candidate_name: Имя кандидата
        position: Название позиции
        email_template: Тип шаблона письма
        api_key: API ключ Evolution

    Returns:
        Результат отправки
    """
    if not api_key:
        from ml.config import get_evolution_api_key
        api_key = get_evolution_api_key()

    # Шаблоны писем
    templates = {
        "interview_invitation": {
            "subject": f"Приглашение на собеседование на позицию {position}",
            "body": f"""Уважаемый(ая) {candidate_name},

Мы рассмотрели Ваше резюме и приглашаем Вас на собеседование на позицию {position}.

Будем рады обсудить детали сотрудничества.

С уважением,
HR отдел"""
        },
        "offer": {
            "subject": f"Офер на позицию {position}",
            "body": f"""Уважаемый(ая) {candidate_name},

Мы рады предложить Вам позицию {position} в нашей компании.

Детали офера будут отправлены отдельно.

С уважением,
HR отдел"""
        },
        "rejection": {
            "subject": f"Отклик на позицию {position}",
            "body": f"""Уважаемый(ая) {candidate_name},

Благодарим Вас за интерес к позиции {position} и время, уделенное нашему отбору.

К сожалению, на данный момент мы не можем предложить Вам сотрудничество, но сохраним Ваше резюме в нашей базе.

Желаем успехов в поиске работы!

С уважением,
HR отдел"""
        }
    }

    template = templates.get(email_template, templates["interview_invitation"])

    return await send_email_tool(
        to_emails=candidate_email,
        subject=template["subject"],
        body=template["body"],
        api_key=api_key
    )


async def validate_email_tool(
        email: str,
        api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Инструмент для валидации email адреса.

    Args:
        email: Email для валидации
        api_key: API ключ Evolution

    Returns:
        Результат валидации
    """
    if not api_key:
        from ml.config import get_evolution_api_key
        api_key = get_evolution_api_key()

    client = EvolutionMailTool(api_key=api_key)
    async with client:
        try:
            result = await client.validate_email(email)
            return {
                "email": email,
                "valid": result.get("valid", False),
                "details": result.get("details", {}),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "email": email,
                "valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Словарь с доступными инструментами для MCP-сервера
EVOLUTION_TOOLS = {
    "send_email": {
        "function": send_email_tool,
        "description": "Отправляет email через Evolution API (Cloud.ru)",
        "parameters": {
            "to_emails": {
                "type": "string",
                "description": "Email адреса получателей (через запятую)"
            },
            "subject": {
                "type": "string",
                "description": "Тема письма"
            },
            "body": {
                "type": "string",
                "description": "Текст письма"
            },
            "sender_email": {
                "type": "string",
                "description": "Email отправителя (опционально)",
                "optional": True
            },
            "cc_emails": {
                "type": "string",
                "description": "Email адреса для копии (через запятую, опционально)",
                "optional": True
            },
            "bcc_emails": {
                "type": "string",
                "description": "Email адреса для скрытой копии (через запятую, опционально)",
                "optional": True
            },
            "attachments": {
                "type": "string",
                "description": "Пути к файлам вложений (через запятую, опционально)",
                "optional": True
            }
        }
    },
    "send_hr_email": {
    "function": send_hr_email_tool,
    "description": "Отправляет HR письмо кандидату через Evolution API",
    "parameters": {
    "candidate_email": {
        "type": "string",
        "description": "Email кандидата"
    },
    "candidate_name": {
        "type": "string",
        "description": "Имя кандидата"
    },
    "position": {
        "type": "string",
        "description": "Название позиции"
    },
    "email_template": {
        "type": "string",
        "description": "Тип письма: interview_invitation, offer, rejection",
        "default": "interview_invitation",
        "optional": True
    }
}
},
"validate_email": {
    "function": validate_email_tool,
    "description": "Валидирует email адрес через Evolution API",
    "parameters": {
        "email": {
            "type": "string",
            "description": "Email адрес для валидации"
        }
    }
}
}

def get_evolution_tools() -> Dict[str, Dict]:
    """
    Возвращает словарь с инструментами Evolution для MCP-сервера.

    Returns:
        Словарь с описанием инструментов
    """
    return EVOLUTION_TOOLS


if name == "__main__":
    # Тестовый пример использования
    import asyncio


    async def test_send_email():
        """Тестовая функция отправки письма"""
        # Замените на ваш API ключ
        TEST_API_KEY = "your_test_api_key_here"

        if TEST_API_KEY == "your_test_api_key_here":
            print("Пожалуйста, укажите ваш API ключ для тестирования")
            return

        client = EvolutionMailTool(api_key=TEST_API_KEY)

        try:
            result = await client.send_email(
                to=["test@example.com"],
                subject="Тестовое письмо от Evolution API",
                body="Это тестовое письмо, отправленное через Evolution API.",
                sender="noreply@yourdomain.com"
            )
            print(f"Письмо отправлено: {result}")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            await client.close()


    # Запуск теста
    asyncio.run(test_send_email())
