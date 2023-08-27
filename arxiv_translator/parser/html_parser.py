from __future__ import annotations
import os
import re
from pathlib import Path

import requests
from tqdm import tqdm

from bs4 import BeautifulSoup


class ArxivParser:
    def __init__(self):
        self.soup = None
        self.image_dir = None

        self.references = {}
        self.fucntions = {}
        self.links = {}

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
        response = requests.get(
            url.replace(
                "https://arxiv.org/abs/", "https://ar5iv.labs.arxiv.org/html/"
            ).replace("https://arxiv.org/pdf/", "https://ar5iv.labs.arxiv.org/html/")
        )
        if response.status_code != 200:
            raise ValueError("Invalid url")
        self.soup = BeautifulSoup(response.text, "html.parser")

        self.image_dir = (
            Path(__file__).parent.parent.parent / "outputs" / self.title / "images"
        )
        if not self.image_dir.exists():
            self.image_dir.mkdir(parents=True)
        return self.soup

    @property
    def title(self):
        res = self.soup.find("h1", "ltx_title ltx_title_document")
        return (
            res.text.replace("\n", "").strip().replace(" ", "_")
            if res is not None
            else ""
        )

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

    def get_all_sections(self):
        sections = self.soup.find_all("section", "ltx_section")
        sections = []

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(self.soup))

    def figure_content_to_markdown(self, content):
        markdown = ""
        fig_captions = content.find_all("figcaption")
        imgs = content.find_all("img")
        for img in imgs:
            basename = Path(img.attrs["src"]).name.replace(" ", "_")
            # download image
            img_path = self.image_dir / basename
            with open(img_path, "wb") as f:
                f.write(
                    requests.get(
                        "https://ar5iv.labs.arxiv.org/" + img.attrs["src"]
                    ).content
                )
            markdown += f"![{img.attrs['alt']}]({img_path})"

        captions = ""
        for fig_caption in fig_captions:
            captions += fig_caption.text
        markdown += f"\n{captions}\n"

        return markdown

    def title_content_to_markdown(self, content):
        markdown = ""
        if content.name == "h1":
            markdown += "# "
        elif content.name == "h2":
            markdown += "## "
        elif content.name == "h3":
            markdown += "### "
        else:
            markdown += "#### "
        for sub_content in content.contents:
            if isinstance(sub_content, str):
                markdown += sub_content.strip()
            else:
                markdown += sub_content.text
        return markdown

    def table_content_to_markdown(self, content):
        def is_next_contents(cheked_contents):
            try:
                temp = cheked_contents.contents
                return True if temp is not None else False
            except:
                return False

        markdown = ""
        # TODO: table caption
        return markdown

    def contents_to_markdown(self, content):
        if isinstance(content, str):
            return content.strip()
        elif content.name == "figure":
            return self.figure_content_to_markdown(content)
        elif content.name.startswith("h"):
            return self.title_content_to_markdown(content)
        elif content.name == "cite":
            ref_name = f"nvlink_{len(self.references)}"
            self.references[ref_name] = {
                "text": content.text,
                "href": content.find("a").attrs["href"],
            }
            return f" {ref_name}"
        elif content.name == "math":
            func_name = f"britz_{len(self.fucntions)}"
            self.fucntions[func_name] = f' ${content.attrs["alttext"]}$ '
            return f" {func_name}"
        elif content.name == "a":
            link_name = f"lg_{len(self.links)}"
            self.links[link_name] = content.attrs["href"]
            return f" {link_name}"
        elif content.name in ("div", "p"):
            outputs = ""
            for sub_content in content.contents:
                outputs += f" {self.contents_to_markdown(sub_content)}"
            return outputs
        elif content.name == "p" and "ltx_p" in content.attrs["class"]:
            output = ""
            for sub_content in content.contents:
                output += f" {self.contents_to_markdown(sub_content)}"
            return output
        elif content.name == "table":
            return self.table_content_to_markdown(content)
        else:
            return ""

    def get_contents_markdown(self):
        sections = self.soup.find_all("section")
        all_mds = []
        for section in tqdm(sections):
            for content in section.contents:
                temp = self.contents_to_markdown(content)
                temp = re.sub(r"\s{2,}", " ", temp)
                # {space}. -> .
                temp = re.sub(r"\s\.", ".", temp)
                temp = re.sub(r"\s,", ",", temp)
                temp = temp.strip()
                if temp != "":
                    all_mds.append(temp)
        return all_mds

    def get_origin_text(self, text: str):
        """
        TODO: change name
        """
        for ref_name, ref in self.references.items():
            text = text.replace(ref_name, f"[{ref['text']}]({ref['href']})")
        for func_name, func in self.fucntions.items():
            ko_ref_name = func_name.replace("britz", "브리츠")
            text = text.replace(ko_ref_name, f" {func} ").replace(
                func_name, f" {func} "
            )
        for link_name, link in self.links.items():
            text = text.replace(link_name, link)
        return text

    def __call__(self, url: str):
        self.parse(url)
        return self.get_contents_markdown()


if __name__ == "__main__":
    parser = ArxivParser()
    texts = parser("https://arxiv.org/abs/1706.03762")
    temp = 0
