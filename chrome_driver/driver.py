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

    def __version_(self) -> Literal['1.5']:
        return "1.5"

    def __str__(self) -> str:
        return f"WebDriver Chrome {self.__version_()}"
    
    def __init__(self, config) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__str__())

    def start(self):
        self._start(self.config.app.headless_mode)
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

    def _start(self, headless: bool) -> None:
        options = self._setOptionsDriver(
                f"--user-data-dir={self.config.path.cache}"
            )
        if headless:
            options.add_argument("--headless")
        self._driver = Chrome(options=options)
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
        
    def getDriver(self) -> Chrome:
        return self._driver

    def kill(self) -> None:
        self._driver.quit()