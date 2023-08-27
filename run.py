import os
import re
from argparse import Namespace, ArgumentParser

import gradio as gr
from tqdm import tqdm

from arxiv_translator import ArxivParser, DeeplTranslator

DEEPL_API_KEY_CONFIG = "./api-keys.yaml"

parser = ArxivParser()
translator = DeeplTranslator.from_config(DEEPL_API_KEY_CONFIG)


def translate(url: str):
    all_texts = parser(url)
    image_idx = []
    for i in tqdm(range(len(all_texts))):
        # ![] 가 있는 지 체크
        is_image = re.search(r"!\[.*\]\(.*\)", all_texts[i])
        if is_image:
            image_idx.append(i)
            continue
        is_title = re.search(r"^#.*", all_texts[i])
        if is_title:
            continue
        all_texts[i] = translator(all_texts[i]).text

    for i in range(len(all_texts)):
        all_texts[i] = parser.get_origin_text(all_texts[i])

    save_path = parser.image_dir.parent / "output.md"
    md = "\n".join(all_texts)
    md = md.replace(parser.image_dir.as_posix(), "images")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(md)
    return "\n".join(all_texts)


if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--cli", action="store_true")
    arg_parser.add_argument(
        "--url",
        type=str,
        default="",
        help="Arxiv url",
    )
    args = arg_parser.parse_args()

    if not args.cli:
        iface = gr.Interface(
            translate,
            inputs=gr.Textbox(
                max_lines=1, placeholder="https://arxiv.org/abs/xxxx.xxxxx"
            ),
            outputs=gr.Markdown(),
            title="Arxiv Translator",
        )
        iface.launch(debug=True)
    elif args.url:
        translate(args.url)
    else:
        raise ValueError("Invalid args")
