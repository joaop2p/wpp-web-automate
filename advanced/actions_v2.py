import base64
import logging
from os import makedirs
import random
from os.path import join, exists
from time import sleep, time
from typing import Literal, Optional
from warnings import deprecated

from ..ui.seletores import Selectors, Element
from ..chrome_driver.driver import Driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

class ActionsConfig:
    """Configurações para a classe Actions."""
    repository_path: str
    cache_path: str
    headless: bool
    driver_path: str
    
    def __init__(self, repository_path: str = 'repository', cache_path: str = 'cache', headless: bool = False, driver_path: str = './cache') -> None:
        self.repository_path = repository_path
        self.cache_path = cache_path
        self.headless = headless
        self.driver_path = driver_path


class WhatsAppNotStartedException(Exception):
    """Exceção lançada quando uma ação é tentada sem o WhatsApp estar iniciado."""
    pass

class NoElementFoundException(Exception):
    """Exceção lançada quando um elemento esperado não é encontrado na página."""
    pass


class Actions:
    """
    Classe para automação de tarefas no WhatsApp Web.
    
    Fornece funcionalidades para enviar mensagens, arquivos, realizar buscas,
    criar enquetes e capturar screenshots/PDFs de conversas.
    """
    
    # Constantes de tempo (em segundos)
    WHATSAPP_LOAD_TIMEOUT = 300  # 5 minutos
    LOGIN_TIMEOUT = 500  # ~8 minutos
    DEFAULT_MIN_DELAY = 1
    DEFAULT_MAX_DELAY = 3
    SEARCH_MIN_DELAY = 4
    SEARCH_MAX_DELAY = 5
    MAX_RETRY_ATTEMPTS = 3
    
    _wpp_started: bool = False
    _started: bool = False
    webdriver: Driver
    _config: ActionsConfig

    def __init__(self, config: Optional[ActionsConfig] = None) -> None:
        """Inicializa a classe Actions com WebDriver e logger."""
        self._safe_search = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self._config = config or ActionsConfig()

    def __str__(self) -> str:
        """Retorna o nome da classe para fins de logging."""
        return f'{self.__class__.__name__}(WebDriver={self.webdriver}, WhatsAppStarted={self._wpp_started}, )'
    
    @property
    def wpp_started(self) -> bool:
        """Verifica se o WhatsApp Web foi iniciado."""
        return self._wpp_started
    
    def _ensure_whatsapp_started(self) -> None:
        """
        Garante que o WhatsApp está iniciado antes de executar ações.
        
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
        """
        if not self._wpp_started:
            raise WhatsAppNotStartedException(
                "WhatsApp Web não foi iniciado. Execute start_whatsapp() primeiro."
            )
    
    def _random_delay(self, min_seconds: int = None, max_seconds: int = None) -> None:
        """
        Aplica um delay aleatório para simular comportamento humano.
        
        Args:
            min_seconds: Tempo mínimo de espera (padrão: DEFAULT_MIN_DELAY)
            max_seconds: Tempo máximo de espera (padrão: DEFAULT_MAX_DELAY)
        """
        min_val = min_seconds or self.DEFAULT_MIN_DELAY
        max_val = max_seconds or self.DEFAULT_MAX_DELAY
        sleep(random.randint(min_val, max_val))

    @deprecated("Passe uma instância de ActionsConfig na inicialização do objeto em vez disso.")
    def set_driver_config(self, headless: bool = False, driver_path: str = "./cache") -> None:
        """
        Define configurações do WebDriver.
        
        Args:
            headless: Se True, executa o navegador em modo headless
            driver_path: Caminho onde o driver será armazenado
        """
        return

    @deprecated("Passe uma instância de ActionsConfig na inicialização do objeto em vez disso.")
    def set_path_config(self, repository: str = "repository") -> None:
        """
        Define configurações de caminhos para arquivos.
        
        Args:
            repository: Diretório onde screenshots e PDFs serão salvos
        """
        return
    
    def start_driver(self) -> None:
        """Inicia o WebDriver com as configurações definidas."""
        self.logger.info('Iniciando WebDriver...')
        self.webdriver = Driver(driver_path=self._config.driver_path, headless=self._config.headless)

    def delivered(self) -> bool:
        """
        Verifica se a última mensagem foi entregue para o contato.
        
        Returns:
            True se a mensagem foi entregue, False caso contrário
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
        """
        self._ensure_whatsapp_started()
        
        messages = self.webdriver.find_element(element=Selectors.MESSAGES_AREA, multiples=True)
        if isinstance(messages, list) and messages:
            final_message = messages[-1]
            is_delivered = self.webdriver.await_element(
                element=Selectors.CHECK, 
                area=final_message, 
                wait=False
            ) is not None
            self.logger.debug('Status de entrega: %s', is_delivered)
            return is_delivered
        return False
    
    def send_survey(self, options: list[str]) -> None:
        """
        Envia uma enquete com as opções fornecidas.
        
        Args:
            options: Lista de opções para a enquete
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
            ValueError: Se a lista de opções estiver vazia
        """
        self._ensure_whatsapp_started()
        
        if not options:
            raise ValueError("A lista de opções não pode estar vazia.")
        
        self.logger.info('Enviando enquete com %d opções', len(options))
        
        self._input_buttons()
        sleep(1)
        
        vote_menu_button = self.webdriver.await_element(element=Selectors.MENU_ITEM)
        if not isinstance(vote_menu_button, WebElement):
            raise NoElementFoundException("Botão de enquete não encontrado")
        vote_menu_button.click()
        sleep(1)
        
        fields = self.webdriver.await_element(element=Selectors.FIELDS, multiples=True)
        if not isinstance(fields, list):
            raise NoElementFoundException("Campos de enquete não encontrados")

        for index, field in enumerate(fields):
            if index >= len(options):
                break
            input_field = field.find_element(
                Selectors.INPUT_FIELDS_ENQUETE.getSelector, 
                Selectors.INPUT_FIELDS_ENQUETE.getElement
            )
            input_field.send_keys(options[index])
            self.logger.debug('Opção %d preenchida', index + 1)
            sleep(1)
        
        button = self.webdriver.await_element(element=Selectors.SWITCH)
        if isinstance(button, WebElement):
            button.click()
        
        button_send = self.webdriver.await_element(element=Selectors.SEND_BUTTON_ENQUETE)
        if not isinstance(button_send, WebElement):
            raise NoElementFoundException("Botão de envio não encontrado.")
        button_send.click()
        self.logger.info('Enquete enviada com sucesso')
        self._random_delay()
    
    def start_whatsapp(self) -> None:
        """
        Abre o WhatsApp Web no navegador controlado pelo WebDriver.
        
        Aguarda até 5 minutos para o WhatsApp carregar completamente.
        Se o usuário não estiver logado, aguarda até ~8 minutos para login.
        
        Raises:
            Exception: Se timeout ao carregar ou usuário não logar no tempo esperado
        """
        if not self._started:
            self.start_driver()
            
        self.logger.info('Abrindo WhatsApp Web...')
        self.webdriver.driver.get("https://web.whatsapp.com/")
        start_time = time()
        
        while not self.webdriver.find_element(Selectors.LOGGED_FLAG):
            elapsed = time() - start_time
            
            if elapsed > self.WHATSAPP_LOAD_TIMEOUT:
                raise Exception('Timeout ao inicializar o WhatsApp Web. Verifique sua conexão.')
            
            if self.webdriver.find_element(Selectors.NO_LOGGED_FLAG):
                self.logger.info('Aguardando login do usuário...')
                login_start = time()
                
                while time() - login_start < self.LOGIN_TIMEOUT:
                    if self.webdriver.find_element(Selectors.LOGGED_FLAG):
                        self._wpp_started = True
                        self.logger.info('WhatsApp inicializado com sucesso após login.')
                        return
                    sleep(1)
                
                raise Exception("Timeout: usuário não logou no WhatsApp Web no tempo esperado.")
            
            self.logger.debug('Aguardando carregamento... (%.0fs)', elapsed)
            sleep(1)
        
        self._wpp_started = True
        self.logger.info('WhatsApp inicializado com sucesso.')

    def safe_search(self, number: int, enter: bool = True) -> None:
        """
        Realiza uma busca segura pelo número informado usando o campo de busca do WhatsApp Web.
        
        Args:
            number: Número para buscar
            enter: Se True, pressiona Enter após digitar
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
            Exception: Se a área de busca não for encontrada
        """
        self._ensure_whatsapp_started()
        self.logger.info('Buscando conversa com: %d', number)
        
        search_area = self.webdriver.await_element(Selectors.SAFE_SEARCH)
        if not isinstance(search_area, WebElement):
            raise NoElementFoundException("Área de busca não encontrada.")
        
        search_area.send_keys(str(number))
        if enter:
            search_area.send_keys(Keys.ENTER)
        
        self._safe_search = True
        self._random_delay(3, 5)

    @deprecated("Use exit_chat_from_search() em vez disso.")
    def cancel_safe_search(self, max_attempts: int = 3) -> None:
        """
        Cancela a busca segura caso esteja ativa, clicando no botão de cancelar.
        
        Args:
            max_attempts: Número máximo de tentativas (padrão: 3)
        """
        if not self._safe_search:
            self.logger.debug('Busca segura não está ativa, nada a cancelar.')
            return
            
        for attempt in range(max_attempts):
            try:
                cancel_button = self.webdriver.await_element(Selectors.CANCEL_SAFE_SEARCH, wait=True)
                if isinstance(cancel_button, WebElement):
                    cancel_button.click()
                    self.logger.info('Busca segura cancelada.')
                    self._random_delay()
                    self._safe_search = False
                    return
                else:
                    self.logger.warning('Botão cancelar não encontrado - Tentativa %d/%d', 
                                       attempt + 1, max_attempts)
            except Exception as e:
                self.logger.warning('Erro ao cancelar busca - Tentativa %d/%d: %s', 
                                   attempt + 1, max_attempts, str(e))
                if attempt < max_attempts - 1:
                    self._random_delay(1, 2)
                    
        self.logger.error('Falha ao cancelar busca após todas as tentativas.')
        self._safe_search = False
            
    def stop(self) -> None:
        """Finaliza o WebDriver, encerrando a automação do navegador."""
        self.logger.info('Finalizando WebDriver...')
        self.webdriver.kill()
        self._wpp_started = False

    def search(self, number: int) -> Optional[bool]:
        """
        Busca um contato pelo número informado no WhatsApp Web.
        
        Args:
            number: Número do contato para buscar
            
        Returns:
            True se encontrado, False se não encontrado, None se erro
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
        """
        self._ensure_whatsapp_started()
        self.logger.info('Procurando contato: %d', number)
        
        new_chat = self.webdriver.await_element(Selectors.NEW_CHAT)
        if not isinstance(new_chat, WebElement):
            self.logger.error('Botão de novo chat não encontrado')
            raise NoElementFoundException("Botão de novo chat não encontrado.")
        new_chat.click()
        
        search = self.webdriver.await_element(Selectors.SEARCH)
        if not isinstance(search, WebElement):
            self.logger.error('Campo de busca não encontrado')
            raise NoElementFoundException("Campo de busca não encontrado.")
        
        search.send_keys(str(number))
        self._random_delay(self.SEARCH_MIN_DELAY, self.SEARCH_MAX_DELAY)
        search.send_keys(Keys.ENTER)
        
        warning = self.webdriver.await_element(element=Selectors.NOT_HAS_CHAT, wait=False)
        message_box = self.webdriver.await_element(element=Selectors.MESSAGE_BOX, wait=False)
        
        if message_box is None or warning is not None:
            self.logger.warning('Número não encontrado: %d', number)
            self.exit_chat_from_search()
            return False
        
        self.logger.info('Contato encontrado: %d', number)
        self._random_delay()
        return True
    
    def _exit_chat(self, from_element: Element) -> None:
        """
        Sai do chat atual pressionando ESC no elemento especificado.
        
        Args:
            from_element: Elemento onde ESC será pressionado
        """
        element = self.webdriver.await_element(element=from_element, wait=False)
        if not isinstance(element, WebElement):
            self.logger.warning('Elemento para sair do chat não encontrado')
            raise NoElementFoundException("Elemento para sair do chat não encontrado.")
        
        self.logger.debug('Saindo do chat...')
        element.send_keys(Keys.ESCAPE)
        self._random_delay()

    def exit_chat_from_message_box(self) -> None:
        """
        Sai do chat atual pressionando ESC no campo de mensagem.
        
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
        """
        self._ensure_whatsapp_started()
        self._exit_chat(Selectors.MESSAGE_BOX)

    def exit_chat_from_search(self) -> None:
        """
        Sai do chat alternativo pressionando ESC no campo de busca.
        
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
        """
        self._ensure_whatsapp_started()
        if self._safe_search:
            self._exit_chat(Selectors.SAFE_SEARCH)
            self._safe_search = False
        else:
            self._exit_chat(Selectors.SEARCH)

    def _input_buttons(self) -> None:
        """
        Clica no botão de anexos para abrir opções de envio de arquivos.
        
        Raises:
            Exception: Se o botão de anexos não for encontrado
        """
        anexos = self.webdriver.await_element(element=Selectors.ATTACHMENTS)
        if not isinstance(anexos, WebElement):
            raise NoElementFoundException("Botão de anexos não encontrado.")
        anexos.click()
        self.logger.debug('Botão de anexos clicado.')
        self._random_delay()

    def _send_message(self, message: str, message_box: WebElement) -> None:
        """
        Envia uma mensagem simples para o contato.
        
        Args:
            message: Texto da mensagem
            message_box: Elemento da caixa de mensagem
        """
        message_box.send_keys(str(message))
        message_box.send_keys(Keys.ENTER)

    def _send_messages(self, message: str, message_box: WebElement) -> None:
        """
        Envia uma mensagem dividida em múltiplas linhas para o contato.
        
        Args:
            message: Texto da mensagem com múltiplas linhas
            message_box: Elemento da caixa de mensagem
        """
        messages = message.splitlines()
        for msg in messages:
            message_box.send_keys(str(msg))
            message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        message_box.send_keys(Keys.ENTER)

    def send_message(self, message: str, split_lines: bool = False) -> None:
        """
        Envia uma mensagem para o contato.
        
        Args:
            message: Texto da mensagem
            split_lines: Se True, envia linha a linha mantendo quebras
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
            Exception: Se a caixa de mensagem não for encontrada
        """
        self._ensure_whatsapp_started()
        
        message_box = self.webdriver.await_element(element=Selectors.MESSAGE_BOX)
        if not isinstance(message_box, WebElement):
            raise NoElementFoundException("Caixa de mensagem não encontrada.")
        
        if split_lines:
            self._send_messages(message, message_box)
        else:
            self._send_message(message, message_box)
        
        self.logger.info('Mensagem enviada com sucesso.')
        self._random_delay()

    def send_file(self, file_path: str, mode: Literal['image', 'video', '*'] = '*') -> None:
        """
        Envia um arquivo para o contato.
        
        Args:
            file_path: Caminho completo do arquivo
            mode: Tipo de arquivo ('image', 'video' ou '*' para qualquer)
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
            FileNotFoundError: Se o arquivo não existir
            Exception: Se falhar ao enviar
        """
        self._ensure_whatsapp_started()
        
        if not exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        self.logger.info('Enviando arquivo: %s (modo: %s)', file_path, mode)
        
        self._input_buttons()
        
        # Seleciona o input correto baseado no modo
        element_map = {
            'image': Selectors.FILE_INPUT_IMAGE,
            'video': Selectors.FILE_INPUT_VIDEO,
            '*': Selectors.FILE_INPUT_ALL
        }
        element = element_map.get(mode, Selectors.FILE_INPUT_ALL)
        
        file_input = self.webdriver.await_element(element=element)
        if not isinstance(file_input, WebElement):
            raise NoElementFoundException("Input de arquivo não encontrado.")
        
        file_input.send_keys(file_path)
        
        send_button = self.webdriver.await_element(element=Selectors.SEND_BUTTON, wait=False)
        if not isinstance(send_button, WebElement):
            send_button = self.webdriver.await_element(element=Selectors.SEND_BUTTON2, wait=False)
            if not isinstance(send_button, WebElement):
                raise NoElementFoundException("Botão de envio não encontrado.")
        
        send_button.click()
        self.logger.info('Arquivo enviado com sucesso.')
        self._random_delay()

    def screenshot(self, name: str | int) -> None:
        """
        Tira um screenshot da área principal do WhatsApp Web.
        
        Args:
            name: Nome do arquivo (sem extensão)
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
            Exception: Se falhar ao tirar screenshot
        """
        self._ensure_whatsapp_started()
        
        main = self.webdriver.await_element(element=Selectors.MAIN_AREA)
        if not isinstance(main, WebElement):
            raise NoElementFoundException("Área principal não encontrada.")
        
        repository_path = self._config.repository_path
        if not exists(repository_path):
            makedirs(repository_path)
        
        output_path = join(repository_path, f'{name}.png')
        
        if main.screenshot(output_path):
            self.logger.info('Screenshot salvo: %s', output_path)
        else:
            raise Exception('Falha ao tirar screenshot.')

    def print_page(self, name: str | int, n: int = 0) -> None:
        """
        Imprime a página atual do WhatsApp Web em PDF.
        
        Args:
            name: Nome do arquivo (sem extensão)
            n: Contador interno de tentativas (não usar externamente)
            
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
        """
        self._ensure_whatsapp_started()
        
        if n >= self.MAX_RETRY_ATTEMPTS:
            self.logger.error('Número máximo de tentativas atingido para impressão.')
            return

        repository_path = self._config.repository_path
        if not exists(repository_path):
            makedirs(repository_path)
        
        try:
            pdf = self.webdriver.driver.print_page(self.webdriver.getPrintOptions())
            pdf_decode = base64.b64decode(pdf)
            
            output_path = join(repository_path, f'{name}.pdf')
            with open(output_path, "wb") as file:
                file.write(pdf_decode)
            self.logger.info('PDF salvo: %s', output_path)
        except OSError as e:
            self.logger.warning('Falha ao salvar PDF (tentativa %d/%d): %s', 
                               n + 1, self.MAX_RETRY_ATTEMPTS, str(e))
            self._random_delay(1, 2)
            self.print_page(name, n + 1)

    def back(self) -> None:
        """
        Volta para a tela anterior do WhatsApp Web.
        
        Raises:
            WhatsAppNotStartedException: Se o WhatsApp não foi iniciado
            Exception: Se o botão voltar não for encontrado
        """
        self._ensure_whatsapp_started()
        
        back_button = self.webdriver.await_element(element=Selectors.BACK)
        if not isinstance(back_button, WebElement):
            raise NoElementFoundException("Botão voltar não encontrado.")
        
        back_button.click()
        self.logger.info('Navegação: voltou para tela anterior.')
        self._random_delay()

    # Experimental
    def __enter__(self) -> 'Actions':
        """Habilita o uso do gerenciador de contexto."""
        self.start_whatsapp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Desabilita o uso do gerenciador de contexto."""
        self.stop()