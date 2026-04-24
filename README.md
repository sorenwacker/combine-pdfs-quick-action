# macOS Combine PDFs Quick Action

A Finder Quick Action to combine multiple PDFs and images into a single document with normalized page sizes.

## Features

- Combine PDFs and images into one document
- All pages normalized to US Letter size (8.5 x 11 inches)
- Preserves aspect ratio, centers content
- Supports: PDF, PNG, JPG, TIFF, GIF, BMP, HEIC
- Output: `YYMMDD-combined.pdf` in the same folder

## Installation

```bash
git clone https://github.com/sdrwacker/macos-fixes.git
cd macos-fixes
./install.sh
```

The installer will:
1. Create a Python virtual environment with required dependencies
2. Install the Quick Action to `~/Library/Services/`

## Usage

1. Select multiple PDFs or images in Finder
2. Right-click and choose **Quick Actions > Combine PDFs**
3. The combined file appears in the same folder

## Requirements

- macOS 10.14 (Mojave) or later
- Python 3.8+

## Uninstall

```bash
rm -rf ~/Library/Services/Combine\ PDFs.workflow
rm -rf ~/.local/bin/combine_pdfs
rm -rf ~/.local/share/combine-pdfs-venv
```
