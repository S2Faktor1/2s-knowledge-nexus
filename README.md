# Overview

This Python application is used to prepare documents to be part of a semantic search database.  There are two Python data process, one for Word document
and the other for PDF.  They are separated because processing images and categorizing headers, sub-headers and sections is done one way for a word document
but must be approached differently with pdf files.

# Word Document Preparation

Metadata Extraction:

Extracts basic metadata such as title, author, creation date, and version from the Word document properties.
Sections and Headers:

Identifies sections based on heading styles (e.g., "Heading 1", "Heading 2").
The level of the heading determines the section hierarchy.
Content Types:

Paragraphs: Extracted as-is.
Lists: Detects lists based on style names (e.g., "List Bullet", "List Number").
Processing Directory:

Processes all .docx files in the specified directory if no specific filenames are provided.
If filenames are provided, only those files are processed.
Command-Line Arguments:

The script takes the directory path and optional list of filenames as arguments.

## To process all files in the document-sources
`python doc_prep.py document-sources`

## To process specific files in the document-sources
`python doc_prep.py document-sources\ShiftPlanning-Deployment-Guide.docx`

## Processed Data

The process data will be saved in the directory processed-data.  The filename format for processed data is original_filename_YYYYMMDD_HHMMSS.json. This makes it easy to track when the data was processed.

## To process run UI 
`python app.py`
