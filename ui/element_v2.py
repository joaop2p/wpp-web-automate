from selenium.webdriver.common.by import By
from typing import Union
from dataclasses import dataclass

@dataclass(frozen=True)
class Element:
    """
    Representa um elemento da interface do usuário com seu seletor e tipo de elemento.
    
    Attributes:
        selector: Estratégia de localização (CSS_SELECTOR, XPATH, etc.)
        element: String do seletor para localizar o elemento
        
    Example:
        >>> btn = Element(By.CSS_SELECTOR, "button[type='submit']")
        >>> print(btn.getSelector)
        'css selector'
    """
    selector: str
    element: str

    def __post_init__(self):
        if not self.selector:
            raise ValueError("O seletor não pode ser vazio.")
        if not self.element:
            raise ValueError("O elemento não pode ser vazio.")

    @property
    def getSelector(self) -> str:
        return self.selector

    @property
    def getElement(self) -> str:
        return self.element
        
    def __str__(self) -> str:
        return f"Element(selector='{self.selector}', element='{self.element}')"
    
    def __repr__(self) -> str:
        return self.__str__()