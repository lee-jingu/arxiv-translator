import deepl
from omegaconf import DictConfig


class DeeplTranslator:
    @staticmethod
    def from_config(config: str):
        api_key = DictConfig.load(config)["deepl"]
        return DeeplTranslator(api_key)

    def __init__(self, api_key: str):
        self.translator = deepl.Translator(api_key)

    def translate(self, text: str, target_lang: str = "KO"):
        try:
            text = self.translator.translate_text(text, target_lang=target_lang)
        except Exception as e:
            print(e)
            text = ""
        return text

    def __call__(self, text: str, target_lang: str = "KO"):
        return self.translate(text, target_lang)
