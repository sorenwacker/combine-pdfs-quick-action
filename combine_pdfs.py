#!/usr/bin/env python3
"""Combine multiple PDF files into a single document with normalized page sizes."""

import os
import sys
from datetime import datetime

import Quartz

# US Letter size in points (8.5 x 11 inches)
TARGET_WIDTH = 612.0
TARGET_HEIGHT = 792.0


def combine_pdfs(input_paths, output_path):
    """Combine multiple PDF files into one with normalized page sizes.

    All pages are scaled to fit within US Letter size while preserving
    aspect ratio and centering on the page.

    Args:
        input_paths: List of paths to PDF files to combine.
        output_path: Path for the combined output PDF.
    """
    output_url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, output_path.encode(), len(output_path), False
    )

    target_rect = Quartz.CGRectMake(0, 0, TARGET_WIDTH, TARGET_HEIGHT)
    context = Quartz.CGPDFContextCreateWithURL(output_url, target_rect, None)

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
                Quartz.CGContextBeginPage(context, target_rect)

                media_box = Quartz.CGPDFPageGetBoxRect(page, Quartz.kCGPDFMediaBox)
                src_width = media_box.size.width
                src_height = media_box.size.height

                # Calculate scale to fit while preserving aspect ratio
                scale_x = TARGET_WIDTH / src_width
                scale_y = TARGET_HEIGHT / src_height
                scale = min(scale_x, scale_y)

                # Calculate centering offset
                scaled_width = src_width * scale
                scaled_height = src_height * scale
                offset_x = (TARGET_WIDTH - scaled_width) / 2
                offset_y = (TARGET_HEIGHT - scaled_height) / 2

                # Apply transformation: translate to center, then scale
                Quartz.CGContextTranslateCTM(context, offset_x, offset_y)
                Quartz.CGContextScaleCTM(context, scale, scale)
                Quartz.CGContextTranslateCTM(
                    context, -media_box.origin.x, -media_box.origin.y
                )

                Quartz.CGContextDrawPDFPage(context, page)
                Quartz.CGContextEndPage(context)

    Quartz.CGPDFContextClose(context)


def main():
    if len(sys.argv) < 2:
        print("Usage: combine_pdfs.py file1.pdf file2.pdf ...", file=sys.stderr)
        sys.exit(1)

    input_files = sys.argv[1:]

    # Filter to only PDF files and sort alphabetically
    pdf_files = sorted([f for f in input_files if f.lower().endswith('.pdf')])

    if len(pdf_files) < 2:
        print("Error: Need at least 2 PDF files to combine", file=sys.stderr)
        sys.exit(1)

    # Generate output filename with timestamp in same directory as first file
    output_dir = os.path.dirname(pdf_files[0]) or '.'
    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'Combined_{timestamp}.pdf')

    combine_pdfs(pdf_files, output_path)
    print(f"Created: {output_path}")


if __name__ == '__main__':
    main()
