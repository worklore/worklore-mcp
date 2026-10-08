#!/usr/bin/env python3
"""Fake file/document MCP server for the tool-count experiment (stdio, stdlib only).

Every tool is FAKE: it touches no files. It returns a plausible deterministic result
and appends {tool, op, args, result} to the call log at $TC_LOG.

Environment:
  TC_VARIANT  "5".."50" (separate tools) or "GROUPED" (7 noun tools covering the same 50 ops)
  TC_NEED     comma-separated tools the task needs; always exposed (the runner sets it from tasks.json,
              so the server never sees the answer key's path)
  TC_TASK     (alternative to TC_NEED) task id; needed tools are read from tasks.json
  TC_TASKS    path to tasks.json (default: next to this file)
  TC_LOG      path of the JSONL call log (default: none)
  TC_SEED     seed for the distractor order (default 20261007)
  TC_NAMES    "vague": expose the same tools (same descriptions and schemas) under the vague names in
              vague-names.json; calls are mapped back to the honest name for logging and scoring.
              Unset (default): honest names, byte-identical to the original runs. Ignored for GROUPED.

Exposed set for separate variant N: the task's needed tools, then distractors taken in a fixed
seeded order of the whole pool, until N tools. So the set for N is a superset of the set for N-5.
"""
import json, os, random, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))

def S(props, required):
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}

F = {"type": "string", "description": "Input file name (relative to the working folder)."}
FL = {"type": "array", "items": {"type": "string"}, "description": "Input file names, in order."}
OUT = {"type": "string", "description": "Optional output file name. A name is generated if omitted."}
PAGES = {"type": "string", "description": "Page range, e.g. \"1-3,5\"."}
PW = {"type": "string", "description": "Password."}

# name: (description, schema, result-extras)
POOL = {
 # ---------------- PDF (22) ----------------
 "pdf_merge": ("Combine several PDF files into one PDF, in the given order.",
     S({"files": FL, "output": OUT}, ["files"]), {"pages": 12}),
 "pdf_split": ("Split a PDF into several PDFs, one per page range (or one file per page if no ranges are given).",
     S({"file": F, "ranges": {"type": "array", "items": {"type": "string"}, "description": "Page ranges, one output file each."}}, ["file"]), {"parts": 3}),
 "pdf_compress": ("Reduce a PDF's file size by downsampling and recompressing embedded images and fonts. Use when a PDF is too big to email or upload.",
     S({"file": F, "level": {"type": "string", "enum": ["low", "medium", "high"], "description": "Compression strength (default medium)."}, "output": OUT}, ["file"]), {"size_before_kb": 8420, "size_after_kb": 1960}),
 "pdf_optimize": ("Optimize a PDF's internal structure for fast web viewing: linearize it so the first page shows before the whole file downloads, and remove unused objects. Does not recompress images, so the size barely changes.",
     S({"file": F, "output": OUT}, ["file"]), {"linearized": True, "size_before_kb": 8420, "size_after_kb": 8105}),
 "pdf_rotate": ("Rotate pages of a PDF by 90, 180 or 270 degrees.",
     S({"file": F, "degrees": {"type": "integer", "enum": [90, 180, 270]}, "pages": PAGES, "output": OUT}, ["file", "degrees"]), {}),
 "pdf_protect": ("Encrypt a PDF with a password so it cannot be opened without it.",
     S({"file": F, "password": PW, "output": OUT}, ["file", "password"]), {"encrypted": True}),
 "pdf_unlock": ("Remove password protection from a PDF, given its current password.",
     S({"file": F, "password": {"type": "string", "description": "The PDF's current password."}, "output": OUT}, ["file", "password"]), {"encrypted": False}),
 "pdf_to_images": ("Render each page of a PDF as an image (PNG or JPG).",
     S({"file": F, "format": {"type": "string", "enum": ["png", "jpg"]}, "dpi": {"type": "integer"}}, ["file"]), {"images": 12}),
 "pdf_from_images": ("Build one PDF from one or more image files (JPG, PNG, HEIC), one image per page.",
     S({"files": FL, "output": OUT}, ["files"]), {}),
 "pdf_extract_text": ("Extract the embedded text layer from a PDF (does not OCR scanned images).",
     S({"file": F, "pages": PAGES}, ["file"]), {"text": "Quarterly report. Revenue grew 14%..."}),
 "pdf_extract_pages": ("Copy selected pages of a PDF into a new PDF.",
     S({"file": F, "pages": PAGES, "output": OUT}, ["file", "pages"]), {}),
 "pdf_delete_pages": ("Delete selected pages from a PDF.",
     S({"file": F, "pages": PAGES, "output": OUT}, ["file", "pages"]), {}),
 "pdf_reorder_pages": ("Reorder the pages of a PDF.",
     S({"file": F, "order": {"type": "array", "items": {"type": "integer"}, "description": "New page order, 1-based."}, "output": OUT}, ["file", "order"]), {}),
 "pdf_watermark": ("Stamp a text watermark on every page of a PDF.",
     S({"file": F, "text": {"type": "string"}, "opacity": {"type": "number"}, "output": OUT}, ["file", "text"]), {}),
 "pdf_add_page_numbers": ("Add page numbers to the footer of each page of a PDF.",
     S({"file": F, "position": {"type": "string", "enum": ["left", "center", "right"]}, "output": OUT}, ["file"]), {}),
 "pdf_sign": ("Add a visible signature image to a PDF page.",
     S({"file": F, "signature_image": {"type": "string"}, "page": {"type": "integer"}, "output": OUT}, ["file", "signature_image"]), {}),
 "pdf_info": ("Show a PDF's page count, page size, file size, encryption status and metadata.",
     S({"file": F}, ["file"]), {"pages": 12, "size_kb": 8420, "encrypted": False, "title": "Report"}),
 "pdf_metadata_set": ("Set or clear a PDF's document metadata (title, author, subject, keywords).",
     S({"file": F, "title": {"type": "string"}, "author": {"type": "string"}, "clear": {"type": "boolean", "description": "Remove all existing metadata."}, "output": OUT}, ["file"]), {}),
 "pdf_to_docx": ("Convert a PDF into an editable Word (.docx) document.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "pdf_redact": ("Black out every occurrence of the given text in a PDF.",
     S({"file": F, "terms": {"type": "array", "items": {"type": "string"}}, "output": OUT}, ["file", "terms"]), {"redactions": 4}),
 "pdf_flatten": ("Flatten form fields and annotations of a PDF into static page content.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "pdf_crop": ("Crop the margins of PDF pages.",
     S({"file": F, "margins_mm": {"type": "number"}, "pages": PAGES, "output": OUT}, ["file"]), {}),
 # ---------------- Images (13) ----------------
 "image_resize": ("Resize an image to a new width and/or height in pixels (keeps aspect ratio if only one is given).",
     S({"file": F, "width": {"type": "integer"}, "height": {"type": "integer"}, "output": OUT}, ["file"]), {}),
 "image_compress": ("Reduce an image's file size by re-encoding at a lower quality, keeping its pixel dimensions.",
     S({"file": F, "quality": {"type": "integer", "description": "1-100, default 75."}, "output": OUT}, ["file"]), {"size_before_kb": 2310, "size_after_kb": 540}),
 "image_convert": ("Convert an image to another format (jpg, png, webp, gif, tiff).",
     S({"file": F, "format": {"type": "string", "enum": ["jpg", "png", "webp", "gif", "tiff"]}, "output": OUT}, ["file", "format"]), {}),
 "image_strip_metadata": ("Remove EXIF and other metadata (GPS location, camera model, timestamps) from an image.",
     S({"file": F, "output": OUT}, ["file"]), {"removed": ["GPS", "Make", "Model", "DateTimeOriginal"]}),
 "image_remove_background": ("Remove the background of an image, leaving the main subject on transparency.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "image_crop": ("Crop an image to a rectangle.",
     S({"file": F, "x": {"type": "integer"}, "y": {"type": "integer"}, "width": {"type": "integer"}, "height": {"type": "integer"}, "output": OUT}, ["file", "width", "height"]), {}),
 "image_rotate": ("Rotate an image by 90, 180 or 270 degrees.",
     S({"file": F, "degrees": {"type": "integer", "enum": [90, 180, 270]}, "output": OUT}, ["file", "degrees"]), {}),
 "image_watermark": ("Overlay a text watermark on an image.",
     S({"file": F, "text": {"type": "string"}, "output": OUT}, ["file", "text"]), {}),
 "image_info": ("Show an image's format, dimensions, file size and EXIF metadata.",
     S({"file": F}, ["file"]), {"format": "jpeg", "width": 4032, "height": 3024, "size_kb": 2310, "exif": {"GPS": "48.85,2.35", "Model": "iPhone 15"}}),
 "image_grayscale": ("Convert an image to black and white (grayscale).",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "image_upscale": ("Upscale an image 2x or 4x with AI super-resolution.",
     S({"file": F, "factor": {"type": "integer", "enum": [2, 4]}, "output": OUT}, ["file"]), {}),
 "ocr_image": ("Recognize and return the text in an image (photo, scan or screenshot) using OCR.",
     S({"file": F, "language": {"type": "string", "description": "ISO language code, default en."}}, ["file"]), {"text": "ACME STORE\nTotal: 42.50"}),
 "qr_read": ("Decode a QR code found in an image and return its content.",
     S({"file": F}, ["file"]), {"data": "https://example.com"}),
 # ---------------- Documents & data (11) ----------------
 "doc_to_pdf": ("Convert a Word or OpenDocument text document (.docx, .doc, .odt, .rtf) to PDF.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "docx_read": ("Read the text content of a Word (.docx) document.",
     S({"file": F}, ["file"]), {"text": "This agreement is made between..."}),
 "html_to_pdf": ("Render an HTML file or URL to PDF.",
     S({"source": {"type": "string", "description": "HTML file name or URL."}, "output": OUT}, ["source"]), {}),
 "md_to_docx": ("Convert a Markdown file to a Word (.docx) document.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "pptx_to_pdf": ("Convert a PowerPoint presentation (.pptx, .ppt) to PDF.",
     S({"file": F, "output": OUT}, ["file"]), {"pages": 18}),
 "epub_to_pdf": ("Convert an EPUB e-book to PDF.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "xlsx_to_csv": ("Export a sheet of an Excel workbook (.xlsx) to CSV.",
     S({"file": F, "sheet": {"type": "string", "description": "Sheet name; the first sheet if omitted."}, "output": OUT}, ["file"]), {"rows": 240}),
 "xlsx_read": ("Read cell values from an Excel workbook (.xlsx).",
     S({"file": F, "sheet": {"type": "string"}, "range": {"type": "string"}}, ["file"]), {"cells": [["Item", "Cost"], ["Rent", 1200]]}),
 "csv_to_json": ("Convert a CSV file to a JSON array of objects.",
     S({"file": F, "output": OUT}, ["file"]), {"records": 240}),
 "json_to_csv": ("Convert a JSON array of objects to CSV.",
     S({"file": F, "output": OUT}, ["file"]), {"rows": 240}),
 "doc_word_count": ("Count words, characters and pages in a document (.docx, .pdf, .txt, .md).",
     S({"file": F}, ["file"]), {"words": 5321, "characters": 31877}),
 # ---------------- Archives & codes (5) ----------------
 "qr_make": ("Generate a QR code image (PNG) that encodes the given text or URL.",
     S({"data": {"type": "string", "description": "Text or URL to encode."}, "size": {"type": "integer", "description": "Pixels, default 512."}, "output": OUT}, ["data"]), {}),
 "zip_create": ("Create a ZIP archive from files.",
     S({"files": FL, "output": OUT}, ["files"]), {}),
 "zip_extract": ("Extract all files from a ZIP archive into the working folder.",
     S({"file": F, "destination": {"type": "string", "description": "Folder to extract into; the working folder if omitted."}}, ["file"]), {"extracted": ["notes.txt", "data.csv", "img/logo.png"]}),
 "zip_list": ("List the files inside a ZIP archive without extracting them.",
     S({"file": F}, ["file"]), {"entries": ["notes.txt", "data.csv", "img/logo.png"]}),
}
assert len(POOL) == 50, len(POOL)
BASE_NAMES = frozenset(POOL)

# ---------------- Extension pool (added for the N = 75 / 100 sweep): 50 more tools ----------------
# Same honest style; many deliberate look-alikes of the base tools. They are APPENDED after the base
# distractor order, so every N <= 50 exposes exactly the same tools as before.
LANG = {"type": "string", "description": "Target language, ISO code (e.g. es, de)."}
POOL_EXT = {
 # PDF (14)
 "pdf_stamp": ("Place an image stamp (e.g. APPROVED, a logo or a seal) at a position on chosen PDF pages.",
     S({"file": F, "stamp_image": {"type": "string"}, "pages": PAGES, "position": {"type": "string", "enum": ["top-left", "top-right", "center", "bottom-left", "bottom-right"]}, "output": OUT}, ["file", "stamp_image"]), {}),
 "pdf_compare": ("Compare two PDFs and report the text differences page by page.",
     S({"file_a": F, "file_b": F}, ["file_a", "file_b"]), {"pages_changed": [2, 7], "changes": 5}),
 "pdf_ocr": ("Add a searchable, selectable text layer to a scanned PDF by running OCR on its pages. Produces a new PDF.",
     S({"file": F, "language": {"type": "string"}, "output": OUT}, ["file"]), {"pages_processed": 12}),
 "pdf_fill_form": ("Fill the interactive form fields of a PDF with the given values.",
     S({"file": F, "fields": {"type": "object", "description": "Field name -> value."}, "output": OUT}, ["file", "fields"]), {"filled": 6}),
 "pdf_extract_images": ("Save every embedded image of a PDF as a separate image file.",
     S({"file": F, "format": {"type": "string", "enum": ["png", "jpg"]}}, ["file"]), {"images": 9}),
 "pdf_resize_pages": ("Change the page size of a PDF (e.g. Letter to A4), scaling the content to fit.",
     S({"file": F, "size": {"type": "string", "enum": ["A4", "A5", "Letter", "Legal"]}, "output": OUT}, ["file", "size"]), {}),
 "pdf_add_bookmarks": ("Add an outline (bookmarks) to a PDF from a list of titles and page numbers.",
     S({"file": F, "bookmarks": {"type": "array", "items": {"type": "object"}}, "output": OUT}, ["file", "bookmarks"]), {}),
 "pdf_attach_file": ("Embed another file as an attachment inside a PDF.",
     S({"file": F, "attachment": {"type": "string"}, "output": OUT}, ["file", "attachment"]), {}),
 "pdf_repair": ("Try to repair a damaged or corrupted PDF that will not open, rebuilding its cross-reference table.",
     S({"file": F, "output": OUT}, ["file"]), {"repaired": True}),
 "pdf_to_pdfa": ("Convert a PDF to PDF/A for long-term archiving (embeds fonts, removes encryption and JavaScript).",
     S({"file": F, "level": {"type": "string", "enum": ["1b", "2b", "3b"]}, "output": OUT}, ["file"]), {}),
 "pdf_grayscale": ("Convert all pages of a PDF to black and white (grayscale).",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "pdf_remove_annotations": ("Delete all comments, highlights and other annotations from a PDF.",
     S({"file": F, "output": OUT}, ["file"]), {"removed": 14}),
 "pdf_header_footer": ("Add a text header and/or footer to every page of a PDF.",
     S({"file": F, "header": {"type": "string"}, "footer": {"type": "string"}, "output": OUT}, ["file"]), {}),
 "pdf_to_txt": ("Save the text layer of a PDF as a plain .txt file.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 # Images (11)
 "image_blur_faces": ("Detect faces in a photo and blur them.",
     S({"file": F, "strength": {"type": "integer"}, "output": OUT}, ["file"]), {"faces": 3}),
 "image_sharpen": ("Sharpen a blurry image.",
     S({"file": F, "amount": {"type": "number"}, "output": OUT}, ["file"]), {}),
 "image_add_border": ("Add a solid-color border around an image.",
     S({"file": F, "width_px": {"type": "integer"}, "color": {"type": "string"}, "output": OUT}, ["file"]), {}),
 "image_collage": ("Arrange several images side by side or in a grid into ONE image file (PNG/JPG).",
     S({"files": FL, "layout": {"type": "string", "enum": ["row", "column", "grid"]}, "output": OUT}, ["files"]), {}),
 "image_to_ico": ("Convert an image into a multi-size .ico favicon.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "image_thumbnail": ("Create a small square thumbnail (crop to square, then scale down) for previews.",
     S({"file": F, "size": {"type": "integer", "description": "Side in pixels, default 256."}, "output": OUT}, ["file"]), {}),
 "image_optimize_web": ("Prepare an image for the web: convert to WebP, cap the width at 1920 px and strip metadata. Dimensions and format may change.",
     S({"file": F, "output": OUT}, ["file"]), {"format": "webp"}),
 "image_flip": ("Mirror an image horizontally or vertically.",
     S({"file": F, "direction": {"type": "string", "enum": ["horizontal", "vertical"]}, "output": OUT}, ["file", "direction"]), {}),
 "image_color_adjust": ("Adjust brightness, contrast and saturation of an image.",
     S({"file": F, "brightness": {"type": "number"}, "contrast": {"type": "number"}, "saturation": {"type": "number"}, "output": OUT}, ["file"]), {}),
 "image_annotate": ("Draw arrows, boxes or text labels on an image.",
     S({"file": F, "shapes": {"type": "array", "items": {"type": "object"}}, "output": OUT}, ["file", "shapes"]), {}),
 "svg_to_png": ("Render an SVG vector file to a PNG image.",
     S({"file": F, "width": {"type": "integer"}, "output": OUT}, ["file"]), {}),
 # Documents & data (14)
 "doc_compare": ("Compare two Word documents and report the tracked differences.",
     S({"file_a": F, "file_b": F}, ["file_a", "file_b"]), {"insertions": 12, "deletions": 4}),
 "translate_doc": ("Translate a document (.docx, .pdf, .txt, .md) into another language, keeping its layout. Produces a new file.",
     S({"file": F, "target_language": LANG, "output": OUT}, ["file", "target_language"]), {}),
 "summarize_doc": ("Return a short summary of a document's content.",
     S({"file": F, "max_words": {"type": "integer"}}, ["file"]), {"summary": "The report covers Q3 revenue growth of 14% and..."}),
 "docx_to_markdown": ("Convert a Word (.docx) document to Markdown.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "docx_find_replace": ("Find and replace text throughout a Word (.docx) document.",
     S({"file": F, "find": {"type": "string"}, "replace": {"type": "string"}, "output": OUT}, ["file", "find", "replace"]), {"replacements": 7}),
 "odt_to_docx": ("Convert an OpenDocument text file (.odt) to Word (.docx).",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "txt_to_pdf": ("Typeset a plain-text (.txt) file as a PDF.",
     S({"file": F, "font_size": {"type": "integer"}, "output": OUT}, ["file"]), {}),
 "xlsx_merge": ("Combine several Excel workbooks into one workbook, one sheet per input.",
     S({"files": FL, "output": OUT}, ["files"]), {"sheets": 3}),
 "csv_merge": ("Concatenate several CSV files with the same columns into one CSV.",
     S({"files": FL, "output": OUT}, ["files"]), {"rows": 720}),
 "csv_dedupe": ("Remove duplicate rows from a CSV file.",
     S({"file": F, "columns": {"type": "array", "items": {"type": "string"}}, "output": OUT}, ["file"]), {"removed": 18}),
 "csv_sort": ("Sort a CSV file by one or more columns.",
     S({"file": F, "by": {"type": "array", "items": {"type": "string"}}, "descending": {"type": "boolean"}, "output": OUT}, ["file", "by"]), {}),
 "csv_to_xlsx": ("Convert a CSV file into an Excel workbook (.xlsx).",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "xlsx_add_chart": ("Insert a chart into an Excel sheet from a cell range.",
     S({"file": F, "range": {"type": "string"}, "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]}, "output": OUT}, ["file", "range"]), {}),
 "json_validate": ("Check that a JSON file is valid and optionally matches a JSON Schema.",
     S({"file": F, "schema": {"type": "string"}}, ["file"]), {"valid": True}),
 # Archives & codes (7)
 "tar_create": ("Create a .tar.gz archive from files.",
     S({"files": FL, "output": OUT}, ["files"]), {}),
 "tar_extract": ("Extract all files from a .tar, .tar.gz or .tgz archive.",
     S({"file": F, "destination": {"type": "string"}}, ["file"]), {"extracted": ["a.txt", "b.txt"]}),
 "gzip_compress": ("Compress a single file with gzip (.gz).",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "zip_protect": ("Create a password-protected (AES) ZIP archive from files.",
     S({"files": FL, "password": PW, "output": OUT}, ["files", "password"]), {}),
 "barcode_make": ("Generate a 1D barcode image (Code128, EAN-13) for the given value.",
     S({"data": {"type": "string"}, "symbology": {"type": "string", "enum": ["code128", "ean13"]}, "output": OUT}, ["data"]), {}),
 "file_hash": ("Compute the SHA-256 (or MD5) checksum of a file.",
     S({"file": F, "algorithm": {"type": "string", "enum": ["sha256", "md5"]}}, ["file"]), {"hash": "9f2c1a7e5b0d..."}),
 "seven_zip_extract": ("Extract all files from a .7z archive.",
     S({"file": F, "destination": {"type": "string"}}, ["file"]), {"extracted": ["x.bin"]}),
 # Email / calendar / contacts exports (4)
 "eml_to_pdf": ("Render an email message file (.eml) to PDF, including headers and attachments list.",
     S({"file": F, "output": OUT}, ["file"]), {}),
 "ics_to_csv": ("Export the events of a calendar file (.ics) to CSV.",
     S({"file": F, "output": OUT}, ["file"]), {"events": 42}),
 "vcf_to_csv": ("Export the contacts of a vCard file (.vcf) to CSV.",
     S({"file": F, "output": OUT}, ["file"]), {"contacts": 130}),
 "mbox_export": ("Export the messages of an .mbox mailbox to individual .eml files.",
     S({"file": F, "destination": {"type": "string"}}, ["file"]), {"messages": 380}),
}
assert len(POOL_EXT) == 50, len(POOL_EXT)
assert not (set(POOL_EXT) & BASE_NAMES)
POOL.update(POOL_EXT)

READONLY = {"pdf_info", "image_info", "pdf_extract_text", "docx_read", "xlsx_read", "doc_word_count", "zip_list", "qr_read", "ocr_image",
            "pdf_compare", "doc_compare", "summarize_doc", "json_validate", "file_hash"}

# ---------------- GROUPED variant: 7 noun tools covering the same 50 ops ----------------
PDF_OPS = ["merge", "split", "compress", "optimize", "rotate", "protect", "unlock", "extract_pages", "delete_pages",
           "reorder_pages", "watermark", "add_page_numbers", "sign", "set_metadata", "redact", "flatten", "crop"]
IMG_OPS = ["resize", "compress", "convert", "strip_metadata", "remove_background", "crop", "rotate", "watermark", "upscale", "grayscale"]
READ_KINDS = ["text", "ocr", "qr", "cells", "word_count", "image_info"]
GROUPED = {
 "pdf_edit": ("Edit PDF files. operation: merge (files -> one PDF), split, compress (shrink file size by recompressing images), "
              "optimize (linearize for fast web view; size barely changes), rotate, protect (add password), unlock (remove password, needs current password), "
              "extract_pages, delete_pages, reorder_pages, watermark, add_page_numbers, sign, set_metadata, redact, flatten, crop.",
     S({"operation": {"type": "string", "enum": PDF_OPS}, "file": F, "files": {**FL, "description": "Input PDFs (merge only)."},
        "password": PW, "pages": PAGES, "degrees": {"type": "integer", "enum": [90, 180, 270]}, "text": {"type": "string", "description": "Watermark text."},
        "order": {"type": "array", "items": {"type": "integer"}}, "terms": {"type": "array", "items": {"type": "string"}},
        "level": {"type": "string", "enum": ["low", "medium", "high"]}, "options": {"type": "object", "description": "Other operation-specific options."}, "output": OUT},
       ["operation"])),
 "pdf_info": ("Show a PDF's page count, page size, file size, encryption status and metadata.", S({"file": F}, ["file"])),
 "image_edit": ("Edit an image. operation: resize (width/height in px), compress (smaller file, same dimensions), convert (to another format), "
                "strip_metadata (remove EXIF/GPS), remove_background, crop, rotate, watermark, upscale, grayscale.",
     S({"operation": {"type": "string", "enum": IMG_OPS}, "file": F, "width": {"type": "integer"}, "height": {"type": "integer"},
        "quality": {"type": "integer"}, "format": {"type": "string", "enum": ["jpg", "png", "webp", "gif", "tiff"]}, "degrees": {"type": "integer", "enum": [90, 180, 270]},
        "text": {"type": "string"}, "factor": {"type": "integer", "enum": [2, 4]}, "x": {"type": "integer"}, "y": {"type": "integer"}, "output": OUT},
       ["operation", "file"])),
 "doc_read": ("Read content from a document or image. kind: text (PDF text layer, .docx text), ocr (recognize text in an image), qr (decode a QR code in an image), "
              "cells (Excel values), word_count, image_info (dimensions and EXIF).",
     S({"file": F, "kind": {"type": "string", "enum": READ_KINDS}, "pages": PAGES, "sheet": {"type": "string"}, "range": {"type": "string"}}, ["file", "kind"])),
 "doc_convert": ("Convert files between formats: .docx/.doc/.odt/.rtf -> pdf, .pptx -> pdf, .epub -> pdf, .html/URL -> pdf, images -> one pdf (pass files), "
                 "pdf -> docx, pdf -> png/jpg pages, .md -> docx, .xlsx -> csv, .csv -> json, .json -> csv.",
     S({"file": F, "files": {**FL, "description": "Several inputs (images -> one PDF)."}, "to": {"type": "string", "enum": ["pdf", "docx", "csv", "json", "png", "jpg"]},
        "sheet": {"type": "string"}, "output": OUT}, ["to"])),
 "qr_make": ("Generate a QR code image (PNG) that encodes the given text or URL.",
     POOL["qr_make"][1]),  # identical to the separate tool, so cached schemas never differ
 "archive": ("Work with ZIP archives. operation: create (from files), extract (all files), list (show contents).",
     S({"operation": {"type": "string", "enum": ["create", "extract", "list"]}, "file": F, "files": FL, "destination": {"type": "string"}, "output": OUT}, ["operation"])),
}

def ext(name):
    return os.path.splitext(str(name or ""))[1].lower().lstrip(".")

def canonical(tool, a):
    """Map a GROUPED call to the equivalent separate tool name."""
    op = a.get("operation")
    if tool == "pdf_edit":
        return {"extract_pages": "pdf_extract_pages", "delete_pages": "pdf_delete_pages", "reorder_pages": "pdf_reorder_pages",
                "add_page_numbers": "pdf_add_page_numbers", "set_metadata": "pdf_metadata_set"}.get(op, f"pdf_{op}")
    if tool == "image_edit":
        return f"image_{op}"
    if tool == "doc_read":
        k = a.get("kind")
        if k == "ocr": return "ocr_image"
        if k == "qr": return "qr_read"
        if k == "cells": return "xlsx_read"
        if k == "word_count": return "doc_word_count"
        if k == "image_info": return "image_info"
        return "docx_read" if ext(a.get("file")) in ("docx", "doc") else "pdf_extract_text"
    if tool == "doc_convert":
        to = a.get("to"); src = a.get("file") or (a.get("files") or [None])[0]; e = ext(src)
        if a.get("files") and to == "pdf" and e in ("jpg", "jpeg", "png", "heic", "webp", "gif", "tiff"): return "pdf_from_images"
        if to == "pdf":
            return {"pptx": "pptx_to_pdf", "ppt": "pptx_to_pdf", "epub": "epub_to_pdf", "html": "html_to_pdf", "htm": "html_to_pdf",
                    "jpg": "pdf_from_images", "jpeg": "pdf_from_images", "png": "pdf_from_images", "heic": "pdf_from_images"}.get(e, "doc_to_pdf")
        if to == "docx": return "md_to_docx" if e == "md" else "pdf_to_docx"
        if to == "csv": return "json_to_csv" if e == "json" else "xlsx_to_csv"
        if to == "json": return "csv_to_json"
        if to in ("png", "jpg"): return "pdf_to_images" if e == "pdf" else "image_convert"
        return "doc_convert?"
    if tool == "archive":
        return f"zip_{op}"
    return tool  # pdf_info, qr_make

def canonical_args(tool, a):
    a = dict(a)
    if tool == "doc_convert" and a.get("to") in ("png", "jpg") and ext(a.get("file")) != "pdf":
        a["format"] = a["to"]
    return a

OUTNAME = {
 "pdf_merge": "merged.pdf", "pdf_compress": "{stem}-compressed.pdf", "pdf_optimize": "{stem}-optimized.pdf", "pdf_protect": "{stem}-protected.pdf",
 "pdf_unlock": "{stem}-unlocked.pdf", "pdf_from_images": "images.pdf", "doc_to_pdf": "{stem}.pdf", "pptx_to_pdf": "{stem}.pdf", "epub_to_pdf": "{stem}.pdf",
 "html_to_pdf": "page.pdf", "md_to_docx": "{stem}.docx", "pdf_to_docx": "{stem}.docx", "xlsx_to_csv": "{stem}.csv", "csv_to_json": "{stem}.json",
 "json_to_csv": "{stem}.csv", "qr_make": "qr.png", "zip_create": "archive.zip", "image_convert": "{stem}.{format}",
}

def fake_result(op, a):
    src = a.get("file") or a.get("source") or (a.get("files") or [""])[0]
    stem = os.path.splitext(os.path.basename(str(src)))[0] or "output"
    res = {"ok": True}
    extras = POOL.get(op, (None, None, {}))[2]
    if op not in READONLY and op not in ("pdf_split", "pdf_to_images", "zip_extract"):
        out = a.get("output")
        if not out:
            tmpl = OUTNAME.get(op)
            if tmpl:
                out = tmpl.format(stem=stem, format=a.get("format", "jpg"))
            else:
                e = ext(src) or "out"
                out = f"{stem}-{op.split('_', 1)[1].replace('_', '-')}.{e}"
        res["output"] = out
    if op == "pdf_split": res["outputs"] = [f"{stem}-part{i}.pdf" for i in (1, 2, 3)]
    if op == "pdf_to_images": res["outputs"] = [f"{stem}-p{i}.{a.get('format', 'png')}" for i in (1, 2, 3)]
    res.update(extras)
    # Stateful file properties, so info tools agree with what earlier calls did (one server process per run).
    IMG = ("jpg", "jpeg", "png", "heic", "webp", "gif", "tiff")
    def props(f):
        k = norm_name(f)
        if k not in STATE:
            e = ext(k)
            if e in IMG:
                STATE[k] = {"format": "jpeg" if e in ("jpg", "jpeg") else e, "width": 4032, "height": 3024, "size_kb": 2310,
                            "exif": {"GPS": "48.85,2.35", "Make": "Apple", "Model": "iPhone 15"}}
            else:
                pages = {"a.pdf": 5, "b.pdf": 7}.get(k, 12)
                STATE[k] = {"pages": pages, "size_kb": 700 * pages, "encrypted": k == "statement.pdf", "linearized": False,
                            "title": "Q3 Report", "author": "J. Smith"}
        return dict(STATE[k])
    if op in ("pdf_info", "image_info"):
        p = props(src)
        keys = ("pages", "size_kb", "encrypted", "linearized", "title", "author", "page_rotation") if op == "pdf_info" else ("format", "width", "height", "size_kb", "exif")
        res.update({k: p[k] for k in keys if k in p})
        return res
    if "output" in res:
        p = props(src)
        if op == "pdf_merge":
            ps = [props(f) for f in (a.get("files") or [])]
            p["pages"] = sum(x.get("pages", 0) for x in ps) or 12; p["size_kb"] = sum(x.get("size_kb", 0) for x in ps) or 8400
            res["pages"] = p["pages"]
        elif op == "pdf_compress": p["size_kb"] = round(p.get("size_kb", 8400) * 0.23); res["size_before_kb"], res["size_after_kb"] = props(src).get("size_kb"), p["size_kb"]
        elif op == "pdf_optimize": p["linearized"] = True; p["size_kb"] = round(p.get("size_kb", 8400) * 0.96); res["size_before_kb"], res["size_after_kb"] = props(src).get("size_kb"), p["size_kb"]
        elif op == "pdf_metadata_set":
            m = {**a, **(a.get("options") or {})}
            if m.get("clear"):
                p["title"] = None; p["author"] = None
            for k in ("title", "author"):
                if k in m: p[k] = m[k] or None
        elif op in ("pdf_delete_pages", "pdf_extract_pages", "pdf_rotate"):
            sel = pageset(a.get("pages"), p.get("pages", 12))
            if op == "pdf_delete_pages": p["pages"] = max(0, p.get("pages", 12) - len(sel)); res["pages"] = p["pages"]
            elif op == "pdf_extract_pages": p["pages"] = len(sel); res["pages"] = p["pages"]
            else:
                rot = dict(p.get("page_rotation") or {})
                for i in sel: rot[str(i)] = (rot.get(str(i), 0) + int(a.get("degrees") or 0)) % 360
                p["page_rotation"] = rot; res["rotated_pages"] = sorted(sel)
        elif op == "pdf_protect": p["encrypted"] = True
        elif op == "pdf_unlock": p["encrypted"] = False
        elif op == "image_resize":
            w0, h0 = p.get("width", 4032), p.get("height", 3024)
            w = a.get("width"); h = a.get("height")
            if w and not h: h = round(h0 * w / w0)
            if h and not w: w = round(w0 * h / h0)
            w = w or w0; h = h or h0
            p["width"], p["height"] = w, h; p["size_kb"] = max(40, round(p.get("size_kb", 2310) * (w * h) / (w0 * h0)))
            res["width"], res["height"] = w, h
        elif op == "image_compress": p["size_kb"] = round(p.get("size_kb", 2310) * 0.25); res["size_before_kb"], res["size_after_kb"] = props(src).get("size_kb"), p["size_kb"]
        elif op == "image_convert": p["format"] = "jpeg" if a.get("format") in ("jpg", "jpeg") else a.get("format")
        elif op == "image_strip_metadata": p["exif"] = {}
        elif op in ("doc_to_pdf", "pptx_to_pdf", "epub_to_pdf", "html_to_pdf", "pdf_from_images"):
            n = len(a.get("files") or []) or extras.get("pages", 6)
            p = {"pages": n, "size_kb": 900 * n, "encrypted": False, "linearized": False, "title": stem}
            if op == "pptx_to_pdf": p["size_kb"] = 14200
        STATE[norm_name(res["output"])] = p
    return res

STATE = {}
def pageset(x, total):
    if x in (None, "", "all"): return set(range(1, total + 1))
    if isinstance(x, int): return {x}
    if isinstance(x, list): return {int(i) for i in x if str(i).isdigit()}
    out = set()
    for part in str(x).replace(" ", "").split(","):
        try:
            if "-" in part:
                lo, hi = part.split("-", 1); out |= set(range(int(lo), int(hi) + 1))
            elif part: out.add(int(part))
        except ValueError:
            pass
    return out

def norm_name(f):
    return os.path.basename(str(f or "").strip().lstrip("./")).lower()

# ---------------- MCP plumbing ----------------
def load_tasks():
    p = os.environ.get("TC_TASKS") or os.path.join(HERE, "tasks.json")
    with open(p) as f:
        return {t["id"]: t for t in json.load(f)["tasks"]}

def distractor_order(seed):
    # base 50 in the original seeded order (unchanged), then the 50 extension tools in their own seeded order
    names = sorted(BASE_NAMES)
    random.Random(seed).shuffle(names)
    ext = sorted(POOL_EXT)
    random.Random(seed + 1).shuffle(ext)
    return names + ext

def exposed_tools(variant, task_id, seed=20261007, need=None):
    if variant == "GROUPED":
        return list(GROUPED)
    n = int(variant)
    needed = [x for x in (need or "").split(",") if x]
    if task_id and not needed:
        for step in load_tasks()[task_id]["expected"]:
            if step["tool"] not in needed:
                needed.append(step["tool"])
    names = list(needed)
    for name in distractor_order(seed):
        if len(names) >= n: break
        if name not in names: names.append(name)
    return names

def tool_defs(variant, names):
    src = GROUPED if variant == "GROUPED" else POOL
    return [{"name": n, "description": src[n][0], "inputSchema": src[n][1]} for n in names]

def vague_names():
    """honest name -> vague name (TC_NAMES=vague)."""
    with open(os.path.join(HERE, "vague-names.json")) as f:
        return json.load(f)["names"]

def log(entry):
    p = os.environ.get("TC_LOG")
    if p:
        with open(p, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main():
    variant = os.environ.get("TC_VARIANT", "50")
    task_id = os.environ.get("TC_TASK")
    seed = int(os.environ.get("TC_SEED", "20261007"))
    names = exposed_tools(variant, task_id, seed, os.environ.get("TC_NEED"))
    defs = tool_defs(variant, names)
    vague = os.environ.get("TC_NAMES") == "vague" and variant != "GROUPED"
    honest_of = {}
    if vague:
        vn = vague_names()
        honest_of = {vn[n]: n for n in names}
        defs = [{**d, "name": vn[d["name"]]} for d in defs]
    schemas = {d["name"]: d["inputSchema"] for d in defs}
    if vague:
        log({"event": "start", "variant": variant, "task": task_id, "tools": names, "names": "vague", "exposed": [d["name"] for d in defs]})
    else:
        log({"event": "start", "variant": variant, "task": task_id, "tools": names})
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        mid = msg.get("id"); method = msg.get("method")
        if mid is None:
            continue  # notification
        if method == "initialize":
            pv = (msg.get("params") or {}).get("protocolVersion") or "2025-06-18"
            result = {"protocolVersion": pv, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "filekit", "version": "1.0.0"}}
        elif method == "tools/list":
            log({"event": "tools/list"})
            result = {"tools": defs}
        elif method == "tools/call":
            p = msg.get("params") or {}
            tool = p.get("name"); a = p.get("arguments") or {}
            if tool not in schemas:
                result = {"isError": True, "content": [{"type": "text", "text": json.dumps({"ok": False, "error": f"unknown tool {tool}"})}]}
                log({"event": "call", "tool": tool, "op": None, "args": a, "result": None, "error": "unknown tool"})
            else:
                missing = [r for r in schemas[tool].get("required", []) if r not in a]
                op = canonical(tool, a) if variant == "GROUPED" else honest_of.get(tool, tool)
                ca = canonical_args(tool, a) if variant == "GROUPED" else a
                if missing:
                    res = {"ok": False, "error": f"missing required argument(s): {', '.join(missing)}"}
                    err = True
                elif op not in POOL:
                    res = {"ok": False, "error": f"unsupported operation for {tool}"}
                    err = True
                elif variant == "GROUPED" and [r for r in POOL[op][1].get("required", []) if r not in ca]:
                    # grouped schemas can only require 'operation'; the operation itself still needs its inputs
                    miss = [r for r in POOL[op][1].get("required", []) if r not in ca]
                    res = {"ok": False, "error": f"missing required argument(s) for this operation: {', '.join(miss)}"}
                    err = True
                else:
                    res = fake_result(op, ca); err = False
                log({"event": "call", "tool": tool, "op": op, "args": a, "result": res, "error": res.get("error")})
                result = {"content": [{"type": "text", "text": json.dumps(res)}], "isError": err}
        elif method == "ping":
            result = {}
        else:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}) + "\n")
            sys.stdout.flush(); continue
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        v = sys.argv[2] if len(sys.argv) > 2 else "50"; t = sys.argv[3] if len(sys.argv) > 3 else None
        print("\n".join(exposed_tools(v, t)))
    else:
        main()
