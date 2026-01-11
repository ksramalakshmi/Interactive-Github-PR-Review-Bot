from abc import ABC, abstractmethod

class ReviewAgent(ABC):
    name: str
    system_prompt: str

    @abstractmethod
    def analyze(self, file, line, code):
        pass