#!/usr/bin/env python3
"""Combine PDFs and images into a single document with normalized page sizes."""

import os
import sys
from datetime import datetime

import Quartz

# US Letter size in points (8.5 x 11 inches)
TARGET_WIDTH = 612.0
TARGET_HEIGHT = 792.0

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif', '.bmp', '.heic'}
PDF_EXTENSIONS = {'.pdf'}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS


def add_pdf_pages(context, pdf_path, target_rect):
    """Add all pages from a PDF file to the context.

    Args:
        context: The PDF context to draw into.
        pdf_path: Path to the PDF file.
        target_rect: Target rectangle for page size.
    """
    pdf_document = Quartz.CGPDFDocumentCreateWithURL(
        Quartz.CFURLCreateFromFileSystemRepresentation(
            None, pdf_path.encode(), len(pdf_path), False
        )
    )

    if pdf_document is None:
        print(f"Warning: Skipping unreadable PDF {pdf_path}", file=sys.stderr)
        return

    page_count = Quartz.CGPDFDocumentGetNumberOfPages(pdf_document)

    for page_num in range(1, page_count + 1):
        page = Quartz.CGPDFDocumentGetPage(pdf_document, page_num)
        if page:
            Quartz.CGContextBeginPage(context, target_rect)

            media_box = Quartz.CGPDFPageGetBoxRect(page, Quartz.kCGPDFMediaBox)
            src_width = media_box.size.width
            src_height = media_box.size.height

            scale_x = TARGET_WIDTH / src_width
            scale_y = TARGET_HEIGHT / src_height
            scale = min(scale_x, scale_y)

            scaled_width = src_width * scale
            scaled_height = src_height * scale
            offset_x = (TARGET_WIDTH - scaled_width) / 2
            offset_y = (TARGET_HEIGHT - scaled_height) / 2

            Quartz.CGContextTranslateCTM(context, offset_x, offset_y)
            Quartz.CGContextScaleCTM(context, scale, scale)
            Quartz.CGContextTranslateCTM(
                context, -media_box.origin.x, -media_box.origin.y
            )

            Quartz.CGContextDrawPDFPage(context, page)
            Quartz.CGContextEndPage(context)


def add_image_page(context, image_path, target_rect):
    """Add an image as a page to the context.

    Args:
        context: The PDF context to draw into.
        image_path: Path to the image file.
        target_rect: Target rectangle for page size.
    """
    image_url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, image_path.encode(), len(image_path), False
    )

    image_source = Quartz.CGImageSourceCreateWithURL(image_url, None)
    if image_source is None:
        print(f"Warning: Skipping unreadable image {image_path}", file=sys.stderr)
        return

    image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
    if image is None:
        print(f"Warning: Skipping invalid image {image_path}", file=sys.stderr)
        return

    src_width = Quartz.CGImageGetWidth(image)
    src_height = Quartz.CGImageGetHeight(image)

    Quartz.CGContextBeginPage(context, target_rect)

    scale_x = TARGET_WIDTH / src_width
    scale_y = TARGET_HEIGHT / src_height
    scale = min(scale_x, scale_y)

    scaled_width = src_width * scale
    scaled_height = src_height * scale
    offset_x = (TARGET_WIDTH - scaled_width) / 2
    offset_y = (TARGET_HEIGHT - scaled_height) / 2

    draw_rect = Quartz.CGRectMake(offset_x, offset_y, scaled_width, scaled_height)
    Quartz.CGContextDrawImage(context, draw_rect, image)

    Quartz.CGContextEndPage(context)


def combine_files(input_paths, output_path):
    """Combine PDFs and images into one PDF with normalized page sizes.

    All pages are scaled to fit within US Letter size while preserving
    aspect ratio and centering on the page.

    Args:
        input_paths: List of paths to PDF or image files.
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

    for file_path in input_paths:
        ext = os.path.splitext(file_path)[1].lower()

        if ext in PDF_EXTENSIONS:
            add_pdf_pages(context, file_path, target_rect)
        elif ext in IMAGE_EXTENSIONS:
            add_image_page(context, file_path, target_rect)

    Quartz.CGPDFContextClose(context)


def main():
    if len(sys.argv) < 2:
        print("Usage: combine_pdfs.py file1.pdf image1.png ...", file=sys.stderr)
        sys.exit(1)

    input_files = sys.argv[1:]

    # Filter to supported files and sort alphabetically
    supported_files = sorted([
        f for f in input_files
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ])

    if len(supported_files) < 2:
        print("Error: Need at least 2 files to combine", file=sys.stderr)
        sys.exit(1)

    # Generate output filename: YYMMDD-combined.pdf
    output_dir = os.path.dirname(supported_files[0]) or '.'
    datestamp = datetime.now().strftime('%y%m%d')
    output_path = os.path.join(output_dir, f'{datestamp}-combined.pdf')

    combine_files(supported_files, output_path)
    print(f"Created: {output_path}")


if __name__ == '__main__':
    main()
