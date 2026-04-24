#!/usr/bin/env python3
"""Merge multiple PDF files into a single document using macOS Quartz framework."""

import os
import sys
from datetime import datetime

import Quartz


def merge_pdfs(input_paths, output_path):
    """Merge multiple PDF files into one.

    Args:
        input_paths: List of paths to PDF files to merge.
        output_path: Path for the merged output PDF.
    """
    pdf_document = Quartz.CGPDFDocumentCreateWithURL(
        Quartz.CFURLCreateFromFileSystemRepresentation(
            None, input_paths[0].encode(), len(input_paths[0]), False
        )
    )

    if pdf_document is None:
        print(f"Error: Could not open {input_paths[0]}", file=sys.stderr)
        sys.exit(1)

    output_url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, output_path.encode(), len(output_path), False
    )

    context = Quartz.CGPDFContextCreateWithURL(output_url, None, None)

    if context is None:
        print(f"Error: Could not create output PDF at {output_path}", file=sys.stderr)
        sys.exit(1)

    for pdf_path in input_paths:
        pdf_document = Quartz.CGPDFDocumentCreateWithURL(
            Quartz.CFURLCreateFromFileSystemRepresentation(
                None, pdf_path.encode(), len(pdf_path), False
            )
        )

        if pdf_document is None:
            print(f"Warning: Skipping unreadable file {pdf_path}", file=sys.stderr)
            continue

        page_count = Quartz.CGPDFDocumentGetNumberOfPages(pdf_document)

        for page_num in range(1, page_count + 1):
            page = Quartz.CGPDFDocumentGetPage(pdf_document, page_num)
            if page:
                media_box = Quartz.CGPDFPageGetBoxRect(page, Quartz.kCGPDFMediaBox)
                Quartz.CGContextBeginPage(context, media_box)
                Quartz.CGContextDrawPDFPage(context, page)
                Quartz.CGContextEndPage(context)

    Quartz.CGPDFContextClose(context)


def main():
    if len(sys.argv) < 2:
        print("Usage: merge_pdfs.py file1.pdf file2.pdf ...", file=sys.stderr)
        sys.exit(1)

    input_files = sys.argv[1:]

    # Filter to only PDF files and sort alphabetically
    pdf_files = sorted([f for f in input_files if f.lower().endswith('.pdf')])

    if len(pdf_files) < 2:
        print("Error: Need at least 2 PDF files to merge", file=sys.stderr)
        sys.exit(1)

    # Generate output filename with timestamp in same directory as first file
    output_dir = os.path.dirname(pdf_files[0]) or '.'
    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'Merged_{timestamp}.pdf')

    merge_pdfs(pdf_files, output_path)
    print(f"Created: {output_path}")


if __name__ == '__main__':
    main()
