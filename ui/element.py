class Element:
    def __init__(self, selector: str, element: str) -> None:
        self._selector = selector
        self._element = element

    @property
    def getSelector(self) -> str:
        return self._selector

    @property
    def getElement(self) -> str:
        return self._element