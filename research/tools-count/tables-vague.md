# Tables: vague names vs honest names (N = 50, 100)

Honest = the original runs (phase `full`); vague = the same tools, descriptions, schemas and tasks under the names in `vague-names.json` (phase `vague`, `TC_NAMES=vague`). 18 tasks × 2 reps per cell. Scored by canonical operation.

## Accuracy and wrong picks

| lane | tools | names | runs | fully correct | 95% CI | runs with a wrong tool executed | runs with any wrong pick (executed or failed) | wrong picks | first mutating pick wrong | failed calls/run | calls/run | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-search | 50 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.53 | ok 36 |
| claude-search | 50 | vague | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.58 | ok 36 |
| claude-search | 100 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.50 | ok 36 |
| claude-search | 100 | vague | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.47 | ok 36 |
| claude | 50 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.39 | ok 36 |
| claude | 50 | vague | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.39 | ok 36 |
| claude | 100 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.39 | ok 36 |
| claude | 100 | vague | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.36 | ok 36 |
| gemini | 50 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.53 | 1.81 | ok 36 |
| gemini | 50 | vague | 36 | 36/36 (100%) | 90%–100% | 0 | 4 | 9 | 1 | 0.42 | 1.64 | ok 36 |
| gemini | 100 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.61 | 1.97 | ok 36 |
| gemini | 100 | vague | 36 | 36/36 (100%) | 90%–100% | 0 | 6 | 7 | 4 | 0.33 | 1.61 | ok 36 |
| codex | 50 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.56 | ok 36 |
| codex | 50 | vague | 30 | 30/30 (100%) | 89%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.60 | ok 30 |
| codex | 100 | honest | 36 | 36/36 (100%) | 90%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.72 | ok 36 |
| codex | 100 | vague | 30 | 30/30 (100%) | 89%–100% | 0 | 0 | 0 | 0 | 0.00 | 1.43 | ok 30 |

## Schema loading

claude-search: `ToolSearch` calls; keyword = free-text search (not `select:` by exact name); loaded = distinct tools returned by the searches; extra = loaded tools that are neither needed nor read-only; first load wrong = the first search returned no needed tool. gemini: reads of the lazy schema files; skipped = runs that read no schema at all.

| lane | tools | names | ToolSearch calls/run | keyword searches/run | runs with a keyword search | schema reads/run | distinct schemas loaded/run | extra (not needed) loaded/run | runs whose first load was wrong | runs that never loaded a needed tool | runs with no schema read |
|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-search | 50 | honest | 1.00 | 0.00 | 0/36 | – | 1.72 | 0.06 | 0 | 0 | – |
| claude-search | 50 | vague | 1.14 | 0.44 | 15/36 | – | 5.36 | 3.81 | 3 | 0 | – |
| claude-search | 100 | honest | 1.00 | 0.00 | 0/36 | – | 1.58 | 0.03 | 0 | 0 | – |
| claude-search | 100 | vague | 1.39 | 0.94 | 28/36 | – | 7.61 | 6.00 | 5 | 0 | – |
| gemini | 50 | honest | – | – | – | 0.83 | 0.83 | 0.00 | 0 | – | 10/36 |
| gemini | 50 | vague | – | – | – | 3.11 | 3.11 | 1.78 | 15 | – | 0/36 |
| gemini | 100 | honest | – | – | – | 0.94 | 0.94 | 0.06 | 0 | – | 7/36 |
| gemini | 100 | vague | – | – | – | 3.69 | 3.69 | 2.33 | 19 | – | 1/36 |

## Tokens, calls, time

| lane | tools | names | first-call input | input/run | output/run | model calls/run | wall s | $/run (list) |
|---|---|---|---|---|---|---|---|---|
| claude-search | 50 | honest | 4.6k | 17.4k | 338 | 3.44 | 11.0 | 0.041 |
| claude-search | 50 | vague | 4.5k | 19.9k | 340 | 3.64 | 9.9 | 0.046 |
| claude-search | 100 | honest | 5.4k | 19.9k | 331 | 3.42 | 9.4 | 0.047 |
| claude-search | 100 | vague | 5.2k | 24.1k | 344 | 3.72 | 8.6 | 0.056 |
| claude | 50 | honest | 11.7k | 27.9k | 198 | 2.36 | 6.2 | 0.030 |
| claude | 50 | vague | 11.6k | 28.0k | 197 | 2.39 | 7.9 | 0.032 |
| claude | 100 | honest | 20.2k | 48.6k | 188 | 2.39 | 6.7 | 0.038 |
| claude | 100 | vague | 20.0k | 47.5k | 187 | 2.36 | 8.4 | 0.034 |
| gemini | 50 | honest | 4.1k | 20.5k | 1057 | 4.06 | 23.0 |  |
| gemini | 50 | vague | 4.0k | 19.4k | 1181 | 3.56 | 24.4 |  |
| gemini | 100 | honest | 4.3k | 18.6k | 808 | 3.69 | 19.9 |  |
| gemini | 100 | vague | 4.2k | 25.7k | 1603 | 4.17 | 28.5 |  |
| codex | 50 | honest | 13.2k | 61.4k | 142 | 3.47 | 14.2 |  |
| codex | 50 | vague | 13.2k | 60.2k | 142 | 3.40 | 14.8 |  |
| codex | 100 | honest | 13.2k | 78.2k | 151 | 3.69 | 13.8 |  |
| codex | 100 | vague | 13.2k | 73.2k | 142 | 3.47 | 13.3 |  |

## Confusions with vague names (wrong tool picked, all lanes)

| task | needed (vague name ← honest) | picked instead (vague name ← honest op) | executed | failed attempt | lanes |
|---|---|---|---|---|---|
| t10 | `read_image` ← ocr_image | `extract_content` ← pdf_to_txt | 0 | 1 | gemini 1 |
| t01 | `optimize_file` ← pdf_compress | `optimize_document` ← pdf_optimize | 0 | 1 | gemini 1 |
| t05 | `export_data` ← xlsx_to_csv | `convert_file` ← pptx_to_pdf | 0 | 1 | gemini 1 |
| t17 | `edit_pages` ← pdf_delete_pages | `adjust_pages` ← pdf_crop | 0 | 1 | gemini 1 |
| t13 | `combine_files` ← pdf_merge, `secure_file` ← pdf_protect | `run_pdf_job` ← pdf_flatten | 0 | 1 | gemini 1 |
| t17 | `edit_pages` ← pdf_delete_pages | `handle_pages` ← pdf_split | 0 | 1 | gemini 1 |
| t14 | `convert_file` ← pptx_to_pdf, `optimize_file` ← pdf_compress | `convert_document` ← doc_to_pdf | 0 | 1 | gemini 1 |
| t02 | `adjust_image` ← image_resize | `transform_image` ← image_rotate | 0 | 1 | gemini 1 |
| t08 | `build_document` ← pdf_from_images | `combine_files` ← pdf_merge | 0 | 1 | gemini 1 |
| t17 | `edit_pages` ← pdf_delete_pages | `manage_pages` ← pdf_reorder_pages | 0 | 1 | gemini 1 |
| t02 | `adjust_image` ← image_resize | `process_image` ← image_compress | 0 | 1 | gemini 1 |
| t07 | `process_image` ← image_compress | `optimize_image` ← image_optimize_web | 0 | 1 | gemini 1 |
| t09 | `convert_document` ← doc_to_pdf | `convert_file` ← pptx_to_pdf | 0 | 1 | gemini 1 |
| t02 | `adjust_image` ← image_resize | `edit_image` ← image_remove_background | 0 | 1 | gemini 1 |
| t08 | `build_document` ← pdf_from_images | `pack_files` ← zip_create | 0 | 1 | gemini 1 |
| t14 | `convert_file` ← pptx_to_pdf, `optimize_file` ← pdf_compress | `optimize_document` ← pdf_optimize | 0 | 1 | gemini 1 |

## First schema loaded was not a needed tool (vague runs)

| lane | task | first loaded (vague ← honest) | runs |
|---|---|---|---|
| claude-search | t08 | `combine_files` ← pdf_merge | 4 |
| gemini | t01 | `optimize_document` ← pdf_optimize | 4 |
| gemini | t08 | `combine_files` ← pdf_merge | 4 |
| gemini | t14 | `convert_document` ← doc_to_pdf | 4 |
| gemini | t02 | `edit_image` ← image_remove_background | 3 |
| gemini | t05 | `convert_file` ← pptx_to_pdf | 3 |
| gemini | t16 | `sanitize_document` ← pdf_redact | 3 |
| claude-search | t07 | `optimize_image` ← image_optimize_web | 2 |
| gemini | t07 | `optimize_image` ← image_optimize_web | 2 |
| gemini | t07 | `optimize_file` ← pdf_compress | 2 |
| claude-search | t07 | `convert_image` ← image_convert | 1 |
| claude-search | t18 | `handle_pdf` ← pdf_sign | 1 |
| gemini | t02 | `process_image` ← image_compress | 1 |
| gemini | t04 | `open_archive` ← seven_zip_extract | 1 |
| gemini | t05 | `convert_data` ← json_to_csv | 1 |
| gemini | t10 | `scan_image` ← qr_read | 1 |
| gemini | t11 | `image_utils` ← image_annotate | 1 |
| gemini | t11 | `process_image` ← image_compress | 1 |
| gemini | t11 | `sanitize_document` ← pdf_redact | 1 |
| gemini | t17 | `manage_pages` ← pdf_reorder_pages | 1 |
| gemini | t18 | `edit_pages` ← pdf_delete_pages | 1 |

## Keyword ToolSearch queries with vague names (claude-search)

| tools | task | rep | queries | loaded (honest) | success |
|---|---|---|---|---|---|
| 50 | t01 | 1 | `compress pdf optimize` | pdf_optimize, pdf_to_docx, pdf_sign, pdf_compress, pdf_flatten | True |
| 50 | t01 | 2 | `compress pdf optimize` | pdf_optimize, pdf_to_docx, pdf_sign, pdf_compress, pdf_flatten | True |
| 50 | t02 | 1 | `resize image width` | image_resize, image_convert, image_remove_background, image_upscale, image_crop | True |
| 50 | t02 | 2 | `resize image` | image_resize, image_convert, image_remove_background, image_upscale, image_crop | True |
| 50 | t06 | 1 | `linearize pdf fast web view` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_optimize, pdf_crop | True |
| 50 | t06 | 2 | `linearize pdf fast web view` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_optimize, pdf_crop | True |
| 50 | t07 | 1 | `compress optimize image png|select:mcp__filekit__optimize_file,mcp__filekit__process_image,mcp__filekit__transform_image,mcp__filekit__update_image,mcp__filekit__inspect_image` | image_convert, image_resize, image_remove_background, image_upscale, image_crop, pdf_compress, image_compress, image_rotate, image_strip_metadata, image_info | True |
| 50 | t08 | 1 | `images to pdf combine|image to PDF convert jpg|select:mcp__filekit__build_document,mcp__filekit__pack_files,mcp__filekit__render_document,mcp__filekit__render_file,mcp__filekit__layout_pages,mcp__filekit__scan_image,mcp__filekit__export_pages,mcp__filekit__process_image,mcp__filekit__transform_image,mcp__filekit__handle_pages` | pdf_merge, pdf_sign, pdf_to_docx, pdf_flatten, pdf_extract_pages, image_convert, doc_to_pdf, pptx_to_pdf, image_grayscale, image_resize, json_to_csv, pdf_from_images, zip_create, html_to_pdf, epub_to_pdf, pdf_add_page_numbers, qr_read, pdf_to_images, image_compress, image_rotate, pdf_split | True |
| 50 | t08 | 2 | `images to pdf combine|select:mcp__filekit__convert_image,mcp__filekit__build_document,mcp__filekit__convert_file,mcp__filekit__scan_image` | pdf_merge, pdf_sign, pdf_to_docx, pdf_flatten, pdf_extract_pages, image_convert, pdf_from_images, pptx_to_pdf, qr_read | True |
| 50 | t11 | 1 | `image metadata exif strip remove` | image_strip_metadata, image_info, image_remove_background, image_resize, image_convert, image_upscale, image_crop, image_watermark | True |
| 50 | t11 | 2 | `image metadata exif strip remove|select:mcp__filekit__inspect_image` | image_strip_metadata, image_info, image_remove_background, image_resize, image_convert, image_upscale, image_crop, image_watermark | True |
| 50 | t16 | 1 | `pdf metadata author title` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_metadata_set, pdf_info, pdf_crop, pdf_from_images, pdf_merge | True |
| 50 | t16 | 2 | `pdf metadata author title` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_metadata_set, pdf_info, pdf_crop, pdf_from_images, pdf_merge | True |
| 50 | t18 | 1 | `rotate pdf page` | pdf_sign, pdf_flatten, pdf_to_docx, pdf_extract_pages, pdf_to_images, pdf_split, pdf_add_page_numbers, pdf_rotate | True |
| 50 | t18 | 2 | `rotate pdf page` | pdf_sign, pdf_flatten, pdf_to_docx, pdf_extract_pages, pdf_to_images, pdf_split, pdf_add_page_numbers, pdf_rotate | True |
| 100 | t01 | 1 | `compress pdf optimize size` | pdf_optimize, pdf_compress, pdf_to_docx, pdf_sign, pdf_flatten | True |
| 100 | t01 | 2 | `compress pdf optimize` | pdf_optimize, pdf_to_docx, pdf_sign, pdf_compress, pdf_flatten | True |
| 100 | t02 | 1 | `resize image width` | image_resize, image_optimize_web, image_collage, image_convert, image_remove_background | True |
| 100 | t02 | 2 | `resize image width` | image_resize, image_optimize_web, image_collage, image_convert, image_remove_background | True |
| 100 | t06 | 1 | `linearize pdf fast web view` | pdf_to_docx, pdf_sign, pdf_flatten, image_thumbnail, pdf_optimize | True |
| 100 | t06 | 2 | `linearize pdf fast web view` | pdf_to_docx, pdf_sign, pdf_flatten, image_thumbnail, pdf_optimize | True |
| 100 | t07 | 1 | `select:mcp__filekit__optimize_image,mcp__filekit__inspect_image|compress png image file size lossless` | image_optimize_web, image_info, image_collage, image_compress, svg_to_png, image_convert, image_to_ico, image_resize, image_remove_background | True |
| 100 | t07 | 2 | `select:mcp__filekit__optimize_image|compress png lossless image size` | image_optimize_web, image_collage, image_convert, image_to_ico, image_info, image_compress, svg_to_png, image_resize, image_remove_background | True |
| 100 | t08 | 1 | `images to pdf combine|convert images jpg into a PDF|select:mcp__filekit__bundle_files,mcp__filekit__pack_files,mcp__filekit__export_image,mcp__filekit__build_document,mcp__filekit__bundle_document,mcp__filekit__scan_image,mcp__filekit__render_image,mcp__filekit__export_pages` | pdf_merge, pdf_sign, xlsx_merge, pdf_to_docx, pdf_flatten, csv_merge, pdf_extract_pages, pdf_compress, csv_to_xlsx, json_to_csv, image_convert, doc_to_pdf, pptx_to_pdf, md_to_docx, image_collage, tar_create, zip_create, image_to_ico, pdf_from_images, pdf_attach_file, qr_read, svg_to_png, pdf_to_images | True |
| 100 | t08 | 2 | `images to pdf combine|convert images jpg to pdf|select:mcp__filekit__build_document,mcp__filekit__bundle_files,mcp__filekit__pack_files,mcp__filekit__export_image,mcp__filekit__scan_image,mcp__filekit__bundle_document,mcp__filekit__render_image,mcp__filekit__build_image` | pdf_merge, pdf_sign, xlsx_merge, pdf_to_docx, pdf_flatten, csv_merge, pdf_extract_pages, pdf_compress, doc_to_pdf, pptx_to_pdf, image_convert, json_to_csv, odt_to_docx, md_to_docx, csv_to_xlsx, pdf_from_images, tar_create, zip_create, image_to_ico, qr_read, pdf_attach_file, svg_to_png, image_collage | True |
| 100 | t09 | 1 | `convert docx to pdf` | pdf_to_docx, doc_to_pdf, odt_to_docx, pptx_to_pdf, md_to_docx | True |
| 100 | t09 | 2 | `docx to pdf convert document` | doc_to_pdf, pdf_to_docx, md_to_docx, docx_to_markdown, pdf_to_pdfa, odt_to_docx, pptx_to_pdf, doc_word_count | True |
| 100 | t10 | 1 | `ocr text from image` | ocr_image, image_annotate, image_watermark, image_strip_metadata, image_resize | True |
| 100 | t10 | 2 | `ocr image text extract` | ocr_image, image_annotate, image_watermark, image_resize, image_collage | True |
| 100 | t11 | 1 | `image metadata exif strip remove|select:mcp__filekit__inspect_image` | image_strip_metadata, image_info, image_optimize_web, image_remove_background, image_resize, image_collage, image_convert, image_upscale | True |
| 100 | t11 | 2 | `image metadata exif strip remove` | image_strip_metadata, image_info, image_optimize_web, image_remove_background, image_resize, image_collage, image_convert, image_upscale | True |
| 100 | t12 | 1 | `pdf password remove decrypt unlock` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_unlock, pdf_optimize, pdf_protect, pdf_crop, pdf_to_pdfa | True |
| 100 | t12 | 2 | `remove pdf password decrypt` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_unlock, pdf_optimize | True |
| 100 | t13 | 1 | `merge pdf password protect|combine multiple PDF files into one` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_unlock, pdf_protect, pdf_crop, pdf_to_pdfa, pdf_from_images, pdf_merge, xlsx_merge, csv_merge, tar_create, zip_create | True |
| 100 | t13 | 2 | `merge pdf password protect|combine multiple PDFs into one` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_unlock, pdf_protect, pdf_crop, pdf_to_pdfa, pdf_from_images, xlsx_merge, pdf_merge, csv_merge, pdf_split, image_collage, image_resize, pdf_compare | True |
| 100 | t15 | 1 | `select:mcp__filekit__convert_image,mcp__filekit__sanitize_document,mcp__filekit__transform_image,mcp__filekit__modify_image,mcp__filekit__clean_document|image metadata strip EXIF remove|resize image width pixels` | image_convert, pdf_redact, image_rotate, image_flip, pdf_remove_annotations, image_strip_metadata, image_info, image_optimize_web, image_remove_background, image_resize, image_collage | True |
| 100 | t15 | 2 | `select:mcp__filekit__convert_image,mcp__filekit__transform_image,mcp__filekit__clean_document,mcp__filekit__modify_image,mcp__filekit__process_image|image metadata strip exif remove|resize image width pixels` | image_convert, image_rotate, pdf_remove_annotations, image_flip, image_compress, image_strip_metadata, image_info, image_optimize_web, image_remove_background, image_resize, image_collage | True |
| 100 | t16 | 1 | `pdf metadata author title` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_metadata_set, pdf_info, pdf_crop, pdf_to_pdfa, pdf_from_images | True |
| 100 | t16 | 2 | `pdf metadata author title` | pdf_to_docx, pdf_sign, pdf_flatten, pdf_metadata_set, pdf_info | True |
| 100 | t17 | 1 | `remove delete pages pdf` | pdf_delete_pages, pdf_crop, pdf_reorder_pages, pdf_stamp, pdf_rotate, pdf_to_docx, pdf_to_images, pdf_resize_pages | True |
| 100 | t17 | 2 | `delete remove pages pdf` | pdf_delete_pages, pdf_crop, pdf_reorder_pages, pdf_stamp, pdf_rotate, pdf_to_docx, pdf_to_images, pdf_resize_pages | True |
| 100 | t18 | 1 | `rotate pdf pages` | pdf_rotate, pdf_crop, pdf_delete_pages, pdf_reorder_pages, pdf_stamp, pdf_to_docx, pdf_to_images, pdf_resize_pages | True |
| 100 | t18 | 2 | `rotate pdf page|select:mcp__filekit__adjust_pages,mcp__filekit__edit_pages,mcp__filekit__manage_pages,mcp__filekit__transform_pages,mcp__filekit__mark_pages` | pdf_sign, pdf_flatten, pdf_to_docx, pdf_extract_pages, pdf_to_images, pdf_resize_pages, pdf_split, pdf_add_page_numbers, pdf_crop, pdf_delete_pages, pdf_reorder_pages, pdf_rotate, pdf_stamp | True |

## Every failed vague run

| lane | tools | task | rep | status | called (vague names) | canonical ops | why |
|---|---|---|---|---|---|---|---|

## Success by task, vague names (N = 50 and 100 pooled)

| task | kind | needed (vague) | claude-search | claude | gemini | codex |
|---|---|---|---|---|---|---|
| t01 | simple | optimize_file | 4/4 | 4/4 | 4/4 | 4/4 |
| t02 | simple | adjust_image | 4/4 | 4/4 | 4/4 | 4/4 |
| t03 | simple | generate_code | 4/4 | 4/4 | 4/4 | 4/4 |
| t04 | simple | handle_archive | 4/4 | 4/4 | 4/4 | 4/4 |
| t05 | simple | export_data | 4/4 | 4/4 | 4/4 | 4/4 |
| t06 | ambiguous | optimize_document | 4/4 | 4/4 | 4/4 | 4/4 |
| t07 | ambiguous | process_image | 4/4 | 4/4 | 4/4 | 4/4 |
| t08 | ambiguous | build_document | 4/4 | 4/4 | 4/4 | 4/4 |
| t09 | ambiguous | convert_document | 4/4 | 4/4 | 4/4 | 4/4 |
| t10 | ambiguous | read_image | 4/4 | 4/4 | 4/4 | 4/4 |
| t11 | ambiguous | update_image | 4/4 | 4/4 | 4/4 | 4/4 |
| t12 | ambiguous | secure_document | 4/4 | 4/4 | 4/4 | 4/4 |
| t13 | chain | combine_files, secure_file | 4/4 | 4/4 | 4/4 | 2/2 |
| t14 | chain | convert_file, optimize_file | 4/4 | 4/4 | 4/4 | 2/2 |
| t15 | chain | convert_image, update_image, adjust_image | 4/4 | 4/4 | 4/4 | 2/2 |
| t16 | ambiguous | update_document | 4/4 | 4/4 | 4/4 | 2/2 |
| t17 | ambiguous | edit_pages | 4/4 | 4/4 | 4/4 | 2/2 |
| t18 | ambiguous | transform_pages | 4/4 | 4/4 | 4/4 | 2/2 |
