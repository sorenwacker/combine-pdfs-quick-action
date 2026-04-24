#!/Users/sdrwacker/.local/share/combine-pdfs-venv/bin/python
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


def add_pdf_pages(context, pdf_path, target_rect):
    """Add all pages from a PDF, normalized to target size."""
    url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, pdf_path.encode(), len(pdf_path), False
    )
    pdf_doc = Quartz.CGPDFDocumentCreateWithURL(url)

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

        def draw_page():
            Quartz.CGContextTranslateCTM(
                context, -media_box.origin.x, -media_box.origin.y
            )
            Quartz.CGContextDrawPDFPage(context, page)

        draw_scaled_centered(
            context, media_box.size.width, media_box.size.height, draw_page
        )
        Quartz.CGContextEndPage(context)

    return page_count


def add_image_page(context, image_path, target_rect):
    """Add an image as a page, normalized to target size."""
    url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, image_path.encode(), len(image_path), False
    )
    source = Quartz.CGImageSourceCreateWithURL(url, None)

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

    def draw_image():
        rect = Quartz.CGRectMake(0, 0, width, height)
        Quartz.CGContextDrawImage(context, rect, image)

    draw_scaled_centered(context, width, height, draw_image)
    Quartz.CGContextEndPage(context)

    return 1


def combine_files(input_paths, output_path):
    """Combine files into one PDF with normalized page sizes."""
    url = Quartz.CFURLCreateFromFileSystemRepresentation(
        None, output_path.encode(), len(output_path), False
    )
    target_rect = Quartz.CGRectMake(0, 0, TARGET_WIDTH, TARGET_HEIGHT)
    context = Quartz.CGPDFContextCreateWithURL(url, target_rect, None)

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
