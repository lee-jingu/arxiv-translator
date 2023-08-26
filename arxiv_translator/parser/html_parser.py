import re
from urllib.request import FancyURLopener as Opener
import webbrowser

from bs4 import BeautifulSoup


class ArxivParser:
    def __init__(self):
        self.opener = Opener({})

    def check_url(self, url: str) -> bool:
        if url.startswith("https://arxiv.org/abs/"):
            return True
        elif url.startswith("https://arxiv.org/pdf/"):
            return True
        else:
            return False

    def parse(self, url: str):
        if not self.check_url(url):
            raise ValueError("Invalid url")
        file = self.opener.open(
            url.replace(
                "https://arxiv.org/abs/", "https://ar5iv.labs.arxiv.org/html/"
            ).replace("https://arxiv.org/pdf/", "https://ar5iv.labs.arxiv.org/html/")
        )
        content = file.read()
        if response.status_code != 200:
            raise ValueError("Invalid url")
        self.soup = BeautifulSoup(response.text, "html.parser")
        return self.soup

    @property
    def title(self):
        res = self.soup.find("h1", "ltx_title ltx_title_document")
        return res.text.replace("\n", "").strip() if res is not None else ""

    @property
    def author_notes(self):
        ret = self.soup.find("span", "ltx_title ltx_title_document")
        return ret.text.replace("\n", "").strip() if ret is not None else ""

    @property
    def abstract(self):
        ret = self.soup.find("blockquote", "abstract mathjax")
        return ret.text.replace("\n", "").strip() if ret is not None else ""

    @property
    def authors(self):
        ret = self.soup.find("div", "ltx_authors")
        if ret is not None:
            # \n\n -> \n
            ret = re.sub(r"\n\n", "\n", ret.text.strip())
            return ret
        else:
            return ""

    @property
    def author_notes(self):
        ret = self.soup.find("div", "ltx_author_notes")
        return ret.text.replace("\n", "").strip() if ret is not None else ""

    @property
    def abstract(self):
        ret = self.soup.find("div", "ltx_abstract")
        return ret.text.replace("\n", "").strip() if ret is not None else ""

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(self.soup))

    def __iter__(self):
        for tag in self.soup.find_all("p", "ltx_p"):
            yield tag.text.replace("\n", "").strip()

    def __call__(self, url: str):
        pass


if __name__ == "__main__":
    parser = ArxivParser()
    parser.parse("https://arxiv.org/abs/1706.03762")
    for text in parser:
        print(text)
