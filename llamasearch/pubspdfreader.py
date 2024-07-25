"""Read PDF files using PyMuPDF library."""

import string
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Union

import fitz
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document


WHITE = set(string.whitespace)
def is_white(text):
    return WHITE.issuperset(text)


class PubsPDFReader(BaseReader):
    """Read PDF files using PyMuPDF library.
    Attempt to remove header/footers, watermarks, reference lists using some heuristics."""

    def load_data(
        self,
        file_path: Union[Path, str],
        metadata: bool = True,
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        """Loads list of documents from PDF file and also accepts extra information in dict format."""
        return self.load(file_path, metadata=metadata, extra_info=extra_info)


    def get_title_authors(self, page, margin_top, margin_bottom, maxfontsize):
        clip = page.rect + (0, margin_top, 0, margin_bottom)
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_BLOCKS ^ fitz.TEXT_PRESERVE_LIGATURES, clip=clip)["blocks"]

        title = []
        authors = ""
        foundtitle = False
        authors_done = False
        titlefont = None
        titleflags = None
        authorsize = None
        authorfont = None
        authorflags = None

        for block in blocks:
            for line in block["lines"]:
                if line["dir"] != (1, 0):
                    # Non-horizontal text most likely not part of the main content.
                    continue
                if authorsize is None and any(round(span["size"]) == maxfontsize for span in line["spans"]):
                    if titlefont is None:
                        titlefont = line["spans"][0]["font"]
                    if titleflags is None:
                        titleflags = line["spans"][0]["flags"]
                    if titlefont == line["spans"][0]["font"] and titleflags == line["spans"][0]["flags"]:
                        foundtitle = True
                        title.append("".join(span["text"] for span in line["spans"]))
                        continue
                if foundtitle:
                    if authorsize is None:
                        authorsize = round(line["spans"][0]["size"])
                        authorfont = line["spans"][0]["font"]
                        authorflags = line["spans"][0]["flags"]
                    if any(round(span["size"]) == authorsize and span["font"] == authorfont and span["flags"] == authorflags for span in line["spans"]):
                        authors += "".join(span["text"] for span in line["spans"] if is_white(span["text"]) or (round(span["size"]) == authorsize and span["font"] == authorfont and span["flags"] == authorflags)) + "\n"
                        continue
                    authors_done = True
                    break
            if authors_done:
                break
        return " ".join(title), authors.strip()

    def get_blocks_text(self, page, margin_top, margin_bottom):
        clip = page.rect + (0, margin_top, 0, margin_bottom)

        # List of bitmap image bounding boxes.
        img_bboxes = [fitz.Rect(img["bbox"]) for img in page.get_image_info() if img["bbox"] in clip]

        # Make a list of table boundary boxes.
        # Must include the header bbox (which may exist outside tab.bbox)
        tabs = page.find_tables(clip=clip, strategy="lines_strict")
        tab_bboxes = [fitz.Rect(t.bbox) | fitz.Rect(t.header.bbox) for t in tabs]

        # Make a list of vector graphic bounding boxes.
        paths = [
            p
            for p in page.get_drawings()
            if p["rect"] in clip
            and p["rect"].width < clip.width
            and p["rect"].height < clip.height
        ]

        vector_bboxes = page.cluster_drawings(drawings=paths)

        def in_bbox(bb, bboxes):
            for bbox in bboxes:
                if bbox.intersects(bb):
                    return True
            return False

        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_BLOCKS ^ fitz.TEXT_PRESERVE_LIGATURES, clip=clip)["blocks"]
        clippedtext = ""
        for block in blocks:
            for line in block["lines"]:
                if line["dir"] != (1, 0):
                    # Non-horizontal text most likely not part of the main content.
                    continue
                if in_bbox(line["bbox"], tab_bboxes):
                    continue
                if in_bbox(line["bbox"], vector_bboxes):
                    continue
                if in_bbox(line["bbox"], img_bboxes):
                    continue

                joined = "".join(span["text"] for span in line["spans"]) + "\n"
                if "References" in joined:
                    return clippedtext.strip(), True
                clippedtext += joined
            clippedtext += "\n"
        return clippedtext.strip(), False

    def load(
        self,
        file_path: Union[Path, str],
        metadata: bool = True,
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        """Loads list of documents from PDF file and also accepts extra information in dict format.

        Args:
            file_path (Union[Path, str]): file path of PDF file (accepts string or Path).
            metadata (bool, optional): if metadata to be included or not. Defaults to True.
            extra_info (Optional[Dict], optional): extra information related to each document in dict format. Defaults to None.

        Raises:
            TypeError: if extra_info is not a dictionary.
            TypeError: if file_path is not a string or Path.

        Returns:
            List[Document]: list of documents.
        """
        # check if file_path is a string or Path
        if not isinstance(file_path, str) and not isinstance(file_path, Path):
            raise TypeError("file_path must be a string or Path.")

        # open PDF file
        doc = fitz.open(file_path)

        body_font_size, max_font_size = self.guess_fontsizes(doc)
        margin_top, margin_bottom = self.guess_header_margin(doc, body_font_size)

        title, authors = self.get_title_authors(doc[0], margin_top, margin_bottom, max_font_size)

        clipped_texts = []
        for page in doc:
            clippedtext, finished = self.get_blocks_text(page, margin_top, margin_bottom)

            clipped_texts.append(clippedtext)
            if finished:
                break

        # if extra_info is not None, check if it is a dictionary
        if extra_info:
            if not isinstance(extra_info, dict):
                raise TypeError("extra_info must be a dictionary.")

        # if metadata is True, add metadata to each document
        if metadata:
            if not extra_info:
                extra_info = {}
            extra_info["total_pages"] = len(doc)
            extra_info["file_path"] = str(file_path)
            extra_info["Title"] =  title
            extra_info["Authors"] = authors

            # return list of documents
            return [
                Document(
                    text=ct.encode("utf-8"),
                    extra_info=dict(
                        extra_info,
                        **{
                            "source": f"{page.number+1}",
                        },
                    ),
                    excluded_embed_metadata_keys=["file_path", "file_name", "file_type", "file_size", "creation_date", "last_modified_date", "total_pages", "source"],
                    excluded_llm_metadata_keys=["file_path", "file_name", "file_type", "file_size", "creation_date", "last_modified_date", "total_pages", "source"],
                    metadata_template="{key}:\n{value}\n",
                    text_template="{metadata_str}\n\nExcerpt:\n{content}",
                )
                for page, ct in zip(doc, clipped_texts)
            ]
        return [
            Document(
                text=ct.encode("utf-8"),
                extra_info=extra_info or {},
                excluded_embed_metadata_keys=["file_path", "file_name", "file_type", "file_size", "creation_date", "last_modified_date", "total_pages", "source"],
                excluded_llm_metadata_keys=["file_path", "file_name", "file_type", "file_size", "creation_date", "last_modified_date", "total_pages", "source"],
                metadata_template="{key}:\n{value}\n",
                text_template="{metadata_str}\n\nExcerpt:\n{content}",
            )
            for ct in clipped_texts
        ]


    def guess_fontsizes(self, doc):
        """Guess the body font size (most common) and title font size (largest, above a minimum count)"""
        fontsizes = defaultdict(int)
        for page in doc:
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
            for span in [  # look at all non-empty horizontal spans
                s
                for b in blocks
                for l in b["lines"]
                for s in l["spans"]
                if not is_white(s["text"]) and l["dir"] == (1, 0)
            ]:
                fontsz = round(span["size"])
                fontsizes[fontsz] += len(span["text"].strip())
        return max(fontsizes.items(), key=lambda x:x[1])[0], max((i for i in fontsizes.items() if i[1] > 1), key=lambda x:x[0])[0]


    def guess_header_margin(self, doc, body_font_size):
        """Guess top and bottom clip margins to remove header/footer text using some heuristics"""
        firsts = []
        lasts = []
        top = 0
        bottom = 0

        NUMERIC = "wholly numeric"
        def remove_digits(s): # Remove digits from a string so e.g. "Page 1 of 10" or "<page number> <header text>" match
            if s.isnumeric():
                return NUMERIC
            return "".join(c for c in s if not c.isnumeric())

        for page in doc:
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]

            first = blocks[0]["lines"][0]
            if first["spans"][0]["size"] > body_font_size: # Probably a title, skip this page
                continue
            first_text = "".join(s["text"] for s in first["spans"]).strip()
            if first_text:
                firsts.append((remove_digits(first_text), first["bbox"][3]))

            last = blocks[-1]["lines"][-1]
            last_text = "".join(s["text"] for s in last["spans"]).strip()
            if last_text:
                lasts.append((remove_digits(last_text), last["bbox"][1]))

        firstcount = Counter(f[0] for f in firsts)
        lastcount = Counter(l[0] for l in lasts)
        for repeated in firstcount.most_common():
            # hack: if page numbers are on the bottom they're probably more common and correct, and we're picking up numbers from figures/tables at the top.
            if repeated[0] == NUMERIC and NUMERIC in lastcount and lastcount[NUMERIC] > repeated[1]:
                continue
            if repeated[1] > 4:
                for text, coord in firsts:
                    if text == repeated[0]:
                        top = max(top, coord)
        for repeated in lastcount.most_common():
            if repeated[1] > 4:
                for text, coord in lasts:
                    if text == repeated[0]:
                        bottom = min(bottom, coord - page.rect.y1)
        return top, bottom
