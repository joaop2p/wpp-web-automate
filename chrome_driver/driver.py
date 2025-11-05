import logging
from time import time
from typing import List
from typing_extensions import Literal
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.common.exceptions import NoSuchElementException as NSEE
from selenium.webdriver.remote.webelement import WebElement
from ..ui.element import Element as UIElement


class Driver:
    _driver: Chrome
    _printOptions: PrintOptions  
    __version__ = "1.5"
    _started: bool = False

    def __str__(self) -> str:
        return f"WebDriver Chrome {self.__version__}"

    def __init__(self, driver_path: str, headless: bool = False) -> None:
        self.logger = logging.getLogger(self.__str__())
        self._start(driver_path=driver_path, headless=headless)

    def is_started(self) -> bool:
        return self._started

    def start(self, driver_path: str, headless: bool = False) -> None:
        self._start(headless, driver_path)
        self._started = True
        self.logger.info("Driver inicializado com sucesso.")

    def _setOptionsPrint(self) -> PrintOptions:
        print_options = PrintOptions()
        print_options.orientation = "landscape"
        print_options.background = True
        print_options.page_width = 29.7
        print_options.page_height = 42.0
        return print_options

    def _setOptionsDriver(self, *args) -> ChromeOptions:
        option = ChromeOptions()
        for arg in args:
            option.add_argument(arg)
        return option

    def _start(self, headless: bool, driver_path: str) -> None:
        self._started = True
        options = self._setOptionsDriver(
                f"--user-data-dir={driver_path}"
            )
        if headless:
            options.add_argument("--headless")
        self._driver = Chrome(options=options)
        if self._driver is None:
            self._started = False
            raise Exception("Falha ao iniciar o WebDriver.")
        if len(self._driver.window_handles) != 1:
            for handle in self._driver.window_handles[1:]:
                self._driver.switch_to.window(handle)
                self._driver.close()
            self._driver.switch_to.window(self._driver.window_handles[0])
        self._printOptions = self._setOptionsPrint()
        
    def getPrintOptions(self) -> PrintOptions:
        return self._printOptions

    def find_element(self, element: UIElement, multiples: bool = False, area: WebElement|None = None) -> WebElement | List[WebElement] | None:
        area_s = self._driver if area is None else area
        finder = area_s.find_element if not multiples else area_s.find_elements
        try:
            return finder(by=element.getSelector, value=element.getElement)
        except NSEE:
            return None
        
    def await_element(self, element:UIElement, wait = True, area: WebElement|None = None, multiples: bool = False)  -> WebElement | List[WebElement] | None:
        element_obj = None
        start = time()
        while element_obj is None:
            element_obj = self.find_element(element=element, area=area, multiples=multiples)
            if not wait and time() - start >= 10:
                break
        return element_obj
    
    @property
    def driver(self):
        return self._driver

    def kill(self) -> None:
        self._driver.quit()