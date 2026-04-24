#!/usr/bin/env COMBINE_PDFS_VENV/bin/python
"""Combine PDFs and images into a single document with normalized page sizes."""

import os
import subprocess
import sys
from datetime import datetime

import Quartz

# US Letter size in points (8.5 x 11 inches at 72 DPI)
TARGET_WIDTH = 612.0
TARGET_HEIGHT = 792.0

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif', '.bmp', '.heic'}
PDF_EXTENSIONS = {'.pdf'}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS


def notify(message, title="Combine PDFs"):
    """Show macOS notification."""
    subprocess.run([
        'osascript', '-e',
        f'display notification "{message}" with title "{title}"'
    ], capture_output=True)


def draw_scaled_centered(context, width, height, draw_func):
    """Scale and center content to fit target page size."""
    scale_x = TARGET_WIDTH / width
    scale_y = TARGET_HEIGHT / height
    scale = min(scale_x, scale_y)

    scaled_width = width * scale
    scaled_height = height * scale
    offset_x = (TARGET_WIDTH - scaled_width) / 2
    offset_y = (TARGET_HEIGHT - scaled_height) / 2

    Quartz.CGContextSaveGState(context)
    Quartz.CGContextTranslateCTM(context, offset_x, offset_y)
    Quartz.CGContextScaleCTM(context, scale, scale)
    draw_func()
    Quartz.CGContextRestoreGState(context)


def create_file_url(path):
    """Create a CFURLRef from a file path."""
    return Quartz.CFURLCreateFromFileSystemRepresentation(
        None, path.encode(), len(path), False
    )


def add_pdf_pages(context, pdf_path, target_rect):
    """Add all pages from a PDF, normalized to target size."""
    pdf_doc = Quartz.CGPDFDocumentCreateWithURL(create_file_url(pdf_path))

    if pdf_doc is None:
        print(f"Warning: Cannot read {pdf_path}", file=sys.stderr)
        return 0

    page_count = Quartz.CGPDFDocumentGetNumberOfPages(pdf_doc)

    for i in range(1, page_count + 1):
        page = Quartz.CGPDFDocumentGetPage(pdf_doc, i)
        if not page:
            continue

        media_box = Quartz.CGPDFPageGetBoxRect(page, Quartz.kCGPDFMediaBox)
        Quartz.CGContextBeginPage(context, target_rect)

        def draw_page(p=page, mb=media_box):
            Quartz.CGContextTranslateCTM(context, -mb.origin.x, -mb.origin.y)
            Quartz.CGContextDrawPDFPage(context, p)

        draw_scaled_centered(
            context, media_box.size.width, media_box.size.height, draw_page
        )
        Quartz.CGContextEndPage(context)

    return page_count


def add_image_page(context, image_path, target_rect):
    """Add an image as a page, normalized to target size."""
    source = Quartz.CGImageSourceCreateWithURL(create_file_url(image_path), None)

    if source is None:
        print(f"Warning: Cannot read {image_path}", file=sys.stderr)
        return 0

    image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
    if image is None:
        print(f"Warning: Invalid image {image_path}", file=sys.stderr)
        return 0

    width = Quartz.CGImageGetWidth(image)
    height = Quartz.CGImageGetHeight(image)

    Quartz.CGContextBeginPage(context, target_rect)

    def draw_image(img=image, w=width, h=height):
        rect = Quartz.CGRectMake(0, 0, w, h)
        Quartz.CGContextDrawImage(context, rect, img)

    draw_scaled_centered(context, width, height, draw_image)
    Quartz.CGContextEndPage(context)

    return 1


def combine_files(input_paths, output_path):
    """Combine files into one PDF with normalized page sizes."""
    target_rect = Quartz.CGRectMake(0, 0, TARGET_WIDTH, TARGET_HEIGHT)
    context = Quartz.CGPDFContextCreateWithURL(
        create_file_url(output_path), target_rect, None
    )

    if context is None:
        print(f"Error: Cannot create {output_path}", file=sys.stderr)
        return False

    total_pages = 0
    for path in input_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext in PDF_EXTENSIONS:
            total_pages += add_pdf_pages(context, path, target_rect)
        elif ext in IMAGE_EXTENSIONS:
            total_pages += add_image_page(context, path, target_rect)

    Quartz.CGPDFContextClose(context)
    return total_pages > 0


def main():
    # Read file paths from stdin or command line
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = [line.strip() for line in sys.stdin if line.strip()]

    # Filter and sort supported files
    supported = sorted([
        f for f in files
        if os.path.isfile(f) and os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ])

    if len(supported) < 2:
        notify("Need at least 2 files to combine")
        print("Error: Need at least 2 supported files", file=sys.stderr)
        sys.exit(1)

    # Generate output path
    output_dir = os.path.dirname(supported[0]) or '.'
    datestamp = datetime.now().strftime('%y%m%d')
    output_path = os.path.join(output_dir, f'{datestamp}-combined.pdf')

    if combine_files(supported, output_path):
        notify(f"Created: {os.path.basename(output_path)}")
        print(f"Created: {output_path}")
    else:
        notify("Failed to create PDF")
        sys.exit(1)


if __name__ == '__main__':
    main()
