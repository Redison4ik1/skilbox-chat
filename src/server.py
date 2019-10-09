#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver


class Handler(LineOnlyReceiver):
    """
    Класс для обработки подключений клиентов
    """

    factory: 'Server'  # свойство для доступа к серверу (фабрике)
    login: str  # тут мы будем хранить логин клиента (при успешном получении команды login:USER_LOGIN)

    def connectionLost(self, reason=connectionDone):
        """
        Метод для обработки отключения клиента (разрыв соединения, ручное отключение)
        :param reason:
        :return:
        """
        self.factory.clients.remove(self)  # удаляем клиента из списка подключенных
        print("Disconnected")  # выводим в терминал сообщение об отключении

    def connectionMade(self):
        """
        Метод для обработки успешного подключения клиента
        :return:
        """
        self.login = None  # сбрасываем логин на начальное (пустое) значение
        self.factory.clients.append(self)  # добавим клиента в список подключенных
        print("Connected")  # выведем в терминал уведомление о новом подключении

    def lineReceived(self, line: bytes):
        """
        Метод обработки нового сообщения от клиента
        :param line:
        :return:
        """
        message = line.decode()  # декодируем байты в строку

        # если у клиента уже настроен логин (прошел авторизацию)
        if self.login is not None:
            # формируем сообщение для пересылки другим клиентам
            message = f"<{self.login}>: {message}"
            self.factory.add_history(message)
            # циклически отправляем остальным клиентам (кроме текущего) TODO: смотри `send_message_to_client`
            self.factory.send_message_to_client(self, message)

        # если у клиента еще нет логина (первый раз зашел)
        else:
            # проверяем, что прислал правильную команду (например - login:admin)
            if message.startswith("login:"):
                # убираем начальную часть
                login = message.replace("login:", "")

                # записываем логин
                self.login = login
                # TODO: пометка для ДЗ (задание №1)
                logins = [user.login for user in self.factory.clients if user is not self]
                if self.login in logins:
                    self.sendLine(f"Логин {login} занят, попробуйте другой".encode())
                    self.transport.loseConnection()
                else:
                    # выводим уведомление в консоль
                    print(f"New user: {login}")
                    # отправляем клиенту приветственное сообщение
                    self.sendLine("Welcome!!!".encode())
                    # TODO: пометка для ДЗ (задание №2)
                    self.factory.send_history(self)
            # если прислал неправильную команду
            else:
                # отправим клиенту текст с ошибкой
                self.sendLine("Неверный логин".encode())


class Server(ServerFactory):
    """
    Класс для работы сервера и создания новых подключений
    """

    protocol = Handler  # тип протокола для подключения
    clients: list  # список активных клиентов
    history: list = []
    _history_length: int = 10

    def __init__(self):
        """
        Конструктор сервера (инициализация пустого списка клиентов)
        """
        self.clients = []

    def startFactory(self):
        """
        Метод для обработки запуска сервера в режиме ожидания подключений
        :return:
        """
        print("Server started...")

    def send_message_to_client(self, current_client, message):
        """
        Метод для отправки сообщений всем клиентам
        :param message:
        :return:
        """
        for client in self.clients:
            if client is not current_client:
                client.sendLine(message.encode())  # кодируем снова строку в байты

    def send_history(self, client):
        """
        Метод для отправки истории
        :param count:
        :return:
        """
        # TODO: пометка для ДЗ (задание №2)
        if self.history:
            client.sendLine('\n'.join(self.history).encode())

    def add_history(self, message):
        if len(self.history) >= self._history_length:
            del self.history[0]
        self.history.append(message)


# указание конфигурации реактора (порт и тип сервера)
reactor.listenTCP(
    7410, Server()
)
# запуск реактора в работу
reactor.run()
