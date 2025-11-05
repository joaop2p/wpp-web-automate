import base64
import logging
from os import makedirs
import random
from os.path import join, exists
from time import sleep, time
from typing import Literal, Optional
from ..ui.seletores import Selectors, Element
from ..chrome_driver.driver import Driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from warnings import deprecated

class Actions:
    _wpp_started: bool = False
    webdriver: Driver
    _config: dict = {
        "path": {
            "repository": "repository",
            "cache": "cache"
        },
        "driver": {
            "headless": False,
            "driver_path": "./cache"
        }
    }

    def __init__(self) -> None:
        self._safe_search = False
        self.webdriver = Driver()
        self.logger = logging.getLogger(self.__str__())

    def __str__(self) -> str:
        """Retorna o nome da classe para fins de logging."""
        return "Action Automate"
    
    @property
    def wpp_started(self) -> bool:
        """Verifica se o WhatsApp Web foi iniciado."""
        return self._wpp_started

    def set_driver_config(self, headless: bool = False, driver_path: str = "./cache") -> None:
        """Configurações do driver."""
        self.logger.info('Configurando driver: headless=%s, driver_path=%s', headless, driver_path)
        self._config['driver']['headless'] = headless
        self._config['driver']['driver_path'] = driver_path

    def set_path_config(self, repository: str = "repository") -> None:
        """Configurações de caminhos."""
        self._config['path']['repository'] = repository
    
    def start_driver(self) -> None:
        self.webdriver.start(**self._config["driver"])

    def delivered(self) -> bool:
        """
        Verifica se a última mensagem foi entregue para o contato.
        Retorna True se entregue, False caso contrário.
        """
        messages = self.webdriver.find_element(element=Selectors.MESSAGES_AREA, multiples=True)
        if isinstance(messages, list):
            final_message = messages[-1]
            return self.webdriver.await_element(element=Selectors.CHECK, area=final_message, wait=False) is not None
        return False
    
    def send_survey(self, options: list[str]) -> None:
        self._input_buttons()
        sleep(1)
        vote_menu_button = self.webdriver.await_element(element=Selectors.MENU_ITEM)
        if not isinstance(vote_menu_button, WebElement):
            return
        vote_menu_button.click()
        sleep(1)
        fields = self.webdriver.await_element(element=Selectors.FIELDS, multiples=True)
        if not isinstance(fields, list):
            return
        for index, field in enumerate(fields):
            x = field.find_element(Selectors.INPUT_FIELDS_ENQUETE.getSelector, Selectors.INPUT_FIELDS_ENQUETE.getElement)
            x.send_keys(options[index])
            sleep(1)
        button = self.webdriver.await_element(element=Selectors.SWITCH)
        if not isinstance(button, WebElement):
            return
        button.click()
        button_send = self.webdriver.await_element(element=Selectors.SEND_BUTTON_ENQUETE)
        if not isinstance(button_send, WebElement):
            return
        button_send.click()
        sleep(random.randint(1, 3))
    
    def start_whatsapp(self) -> None:
        """
        Abre o WhatsApp Web no navegador controlado pelo WebDriver.
        Aguarda até 5 minutos para o WhatsApp carregar completamente.
        Se o usuário não estiver logado, aguarda até 2 minutos para login.
        """
        if not self.webdriver.is_started():
            self.start_driver()
        self.webdriver.driver.get("https://web.whatsapp.com/")
        start_time = time()
        while not self.webdriver.find_element(Selectors.LOGGED_FLAG):
            self.logger.info('Aguardando carregamento do WhatsApp Web...')
            if time() - start_time > 300:
                raise Exception('Timeout ao inicializar o WhatsApp Web. Verifique sua conexão.')
            elif self.webdriver.find_element(Selectors.NO_LOGGED_FLAG):
                self.logger.info('Aguardando login...')
                login_start = time()
                # Aguarda até 120 segundos para o usuário fazer login
                while time() - login_start < 500:
                    if self.webdriver.find_element(Selectors.LOGGED_FLAG):
                        self._wpp_started = True
                        self.logger.info('WhatsApp inicializado com sucesso.')
                        return
                raise Exception("Usuário não está logado no WhatsApp Web.")          
            sleep(1)
        self._wpp_started = True
        self.logger.info('WhatsApp inicializado com sucesso.')

    def safe_search(self, number: int, enter: bool = True) -> None:
        """
        Realiza uma busca segura pelo número informado, utilizando o campo de busca do WhatsApp Web.
        """
        self.logger.info('Procurando conversa com: %d', number)
        search_area = self.webdriver.await_element(Selectors.SAFE_SEARCH)
        if isinstance(search_area, WebElement):
            search_area.send_keys(str(number))
            if enter:
                search_area.send_keys(Keys.ENTER)
            self._safe_search = True
            sleep(random.randint(3, 5))
        else:
            raise Exception("Área de busca não encontrada.")

    @deprecated("Use exit_chat_from_search() em vez disso.")
    def cancel_safe_search(self, max_attempts: int = 3) -> None:
        """
        Cancela a busca segura caso esteja ativa, clicando no botão de cancelar.
        
        Args:
            max_attempts: Número máximo de tentativas (padrão: 3)
        """
        if not self._safe_search:
            return
            
        for attempt in range(max_attempts):
            try:
                cancel_button = self.webdriver.await_element(Selectors.CANCEL_SAFE_SEARCH, wait=True)
                if isinstance(cancel_button, WebElement):
                    cancel_button.click()
                    self.logger.info('Busca simples cancelada.')
                    sleep(random.randint(1, 3))
                    self._safe_search = False
                    return
                else:
                    self.logger.warning(f'Botão de cancelar não encontrado - Tentativa {attempt + 1}/{max_attempts}')
            except Exception as e:
                self.logger.warning(f'Erro ao cancelar busca segura - Tentativa {attempt + 1}/{max_attempts}: {str(e)}')
                if attempt < max_attempts - 1:
                    sleep(random.randint(1, 2))
                    
        self.logger.error('Falha ao cancelar busca segura após todas as tentativas.')
        self._safe_search = False  # Força reset do estado para evitar loops
            
    def stop(self) -> None:
        """
        Finaliza o WebDriver, encerrando a automação do navegador.
        """
        self.logger.info('Webdriver finalizado.')
        self.webdriver.kill()

    def search(self, number: int) -> Optional[bool]:
        """
        Busca um contato pelo número informado no WhatsApp Web.
        Retorna True se encontrado, False se não encontrado, None se erro.
        """
        self.logger.info('Procurando conversa com: %d', number)
        new_chat = self.webdriver.await_element(Selectors.NEW_CHAT)
        if not isinstance(new_chat, WebElement):
            return None
        new_chat.click()
        search = self.webdriver.await_element(Selectors.SEARCH)
        if not isinstance(search, WebElement):
            return None
        search.send_keys(str(number))
        sleep(random.randint(4, 5))
        search.send_keys(Keys.ENTER)
        warnning = self.webdriver.await_element(element=Selectors.NOT_HAS_CHAT, wait=False)
        message_box = self.webdriver.await_element(element=Selectors.MESSAGE_BOX, wait=False)
        if message_box is None or warnning is not None:
            self.logger.error('Número não encontrado: %d', number)
            self.exit_chat_from_search()
            return False
        sleep(random.randint(1, 3))
        return True
    
    def _exit_chat(self, from_element: Element):
        """
        Sai do chat atual pressionando ESC no elemento especificado.
        """
        element = self.webdriver.await_element(element=from_element, wait=False)
        if not isinstance(element, WebElement):
            return
        self.logger.info('Saindo do chat...')
        element.send_keys(Keys.ESCAPE)
        sleep(random.randint(1, 3))

    def exit_chat_from_message_box(self):
        """
        Sai do chat atual pressionando ESC no campo de mensagem.
        """
        self._exit_chat(Selectors.MESSAGE_BOX)

    def exit_chat_from_search(self):
        """
        Sai do chat alternativo pressionando ESC no campo de busca.
        """
        if self._safe_search:
            self._exit_chat(Selectors.SAFE_SEARCH)
            self._safe_search = False
        else:
            self._exit_chat(Selectors.SEARCH)

    def _input_buttons(self) -> None:
        """
        Clica no botão de anexos para abrir opções de envio de arquivos.
        """
        anexos = self.webdriver.await_element(element=Selectors.ATTACHMENTS)
        if not isinstance(anexos, WebElement):
            return
        anexos.click()
        self.logger.info('Botão de anexos clicado.')
        sleep(random.randint(1, 3))

    def _send_message(self, message: str, message_box: WebElement) -> None:
        """
        Envia uma mensagem simples para o contato.
        """
        message_box.send_keys(str(message))
        message_box.send_keys(Keys.ENTER)

    def _send_messages(self, message: str, message_box: WebElement) -> None:
        """
        Envia uma mensagem dividida em múltiplas linhas para o contato.
        """
        messages = message.splitlines()
        for message in messages:
            message_box.send_keys(str(message))
            message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        message_box.send_keys(Keys.ENTER)

    def send_message(self, message: str, split_lines: bool = False) -> None:
        """
        Envia uma mensagem para o contato. Se split_lines=True, envia linha a linha.
        """
        message_box = self.webdriver.await_element(element=Selectors.MESSAGE_BOX)
        if not isinstance(message_box, WebElement):
            return
        if split_lines:
            self._send_messages(message, message_box)
        else:
            self._send_message(message, message_box)
        self.logger.info('Mensagem enviada com sucesso.')
        sleep(random.randint(1, 3))

    def send_file(self, file_path: str, mode: Literal['image', 'video', '*'] = '*') -> None:
        """Envia um arquivo."""
        self._input_buttons()
        match mode:
            case 'image':
                element = Selectors.FILE_INPUT_IMAGE
            case 'video':
                element = Selectors.FILE_INPUT_VIDEO
            case '*':
                element = Selectors.FILE_INPUT_ALL
            case _:
                element = Selectors.FILE_INPUT_ALL
        file_input = self.webdriver.await_element(element=element)
        if not isinstance(file_input, WebElement):
            return
        file_input.send_keys(file_path)
        send_button = self.webdriver.await_element(element=Selectors.SEND_BUTTON, wait=False)
        if not isinstance(send_button, WebElement):
            send_button = self.webdriver.await_element(element=Selectors.SEND_BUTTON2, wait=False)
            if not isinstance(send_button, WebElement):
                return
        send_button.click()
        sleep(random.randint(1, 3))

    def screenshot(self, name: str | int) -> None:
        """
        Tira um screenshot da área principal do WhatsApp Web.
        """
        main = self.webdriver.await_element(element=Selectors.MAIN_AREA)
        if not isinstance(main, WebElement):
            return
        if main.screenshot(join(self._config['path']['repository'], f'{name}.png')):
            self.logger.info('Screenshot tirado com sucesso: %s', name)
        else:
            self.logger.error('Falha ao tirar screenshot.')

    def print_page(self, name: str | int, n: int = 0) -> None:
        """
        Imprime a página atual do WhatsApp Web em PDF.
        Tenta até 3 vezes em caso de erro.
        """
        if not exists(self._config['path']['repository']):
            makedirs(self._config['path']['repository'])
        pdf = self.webdriver.driver.print_page(self.webdriver.getPrintOptions())
        pdf_decode = base64.b64decode(pdf)
        with open(join(self._config['path']['repository'], f'{name}.pdf'), "wb") as file:
            try:
                file.write(pdf_decode)
                self.logger.info('Página impressa com sucesso: %s', name)
            except OSError:
                self.logger.error('Falha ao imprimir página.')
                self.print_page(name, n+1)

    def back(self) -> None:
        """
        Volta para a tela anterior do WhatsApp Web.
        """
        back_button = self.webdriver.await_element(element=Selectors.BACK)
        if not isinstance(back_button, WebElement):
            return
        back_button.click()
        self.logger.info('Botão voltar clicado.')
        sleep(random.randint(1, 3))