import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document
from fsspec import AbstractFileSystem
from docx2txt.docx2txt import xml2text


def process(docx):
    """Slightly modified from docx2txt.process to handle docx files from Word Online."""

    text = ""

    # unzip the docx in memory
    with zipfile.ZipFile(docx) as zipf:
        filelist = zipf.namelist()

        # get header text
        # there can be 3 header files in the zip
        header_xmls = "word/header[0-9]*.xml"
        for fname in filelist:
            if re.match(header_xmls, fname):
                text += xml2text(zipf.read(fname))

        # get main text
        doc_xml = "word/document.xml"
        if doc_xml not in filelist:
            # Apparently Word Online makes these docx files with slightly different internal structure.
            doc_xml = "word/document2.xml"
        text += xml2text(zipf.read(doc_xml))

        # get footer text
        # there can be 3 footer files in the zip
        footer_xmls = "word/footer[0-9]*.xml"
        for fname in filelist:
            if re.match(footer_xmls, fname):
                text += xml2text(zipf.read(fname))

    return text.strip()


class DocxReader(BaseReader):
    """Docx parser."""

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        """Parse file."""
        if fs:
            with fs.open(file) as f:
                text = process(f)
        else:
            text = process(file)
        metadata = {"file_name": file.name}
        if extra_info is not None:
            metadata.update(extra_info)

        return [Document(text=text, metadata=metadata or {})]
