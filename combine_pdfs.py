#!/bin/bash
# Combine PDFs and images into a single document with normalized page sizes.
# Uses macOS built-in tools: sips for images, join for combining.
# Reads file paths from stdin (one per line) or command line arguments.

# Log for debugging
exec 2>>/tmp/combine_pdfs_debug.log
echo "=== $(date) ===" >&2
echo "Args: $@" >&2
echo "Arg count: $#" >&2

set -e

# Collect input files from stdin or arguments
FILES=()
if [ $# -gt 0 ]; then
    echo "Reading from arguments" >&2
    for f in "$@"; do
        FILES+=("$f")
    done
else
    echo "Reading from stdin" >&2
    while IFS= read -r line; do
        [ -n "$line" ] && FILES+=("$line")
    done
fi

echo "Files collected: ${#FILES[@]}" >&2
printf '%s\n' "${FILES[@]}" >&2

if [ ${#FILES[@]} -lt 2 ]; then
    osascript -e 'display notification "Need at least 2 files to combine" with title "Combine PDFs"'
    echo "Error: Need at least 2 files to combine" >&2
    exit 1
fi

# Get output directory from first file
OUTPUT_DIR="$(dirname "${FILES[0]}")"
DATESTAMP="$(date +%y%m%d)"
OUTPUT_FILE="$OUTPUT_DIR/$DATESTAMP-combined.pdf"

# Create temp directory
TEMP_DIR="$(mktemp -d)"
trap "rm -rf '$TEMP_DIR'" EXIT

# US Letter size in pixels at 72 DPI
PAGE_WIDTH=612
PAGE_HEIGHT=792

convert_to_pdf() {
    local input="$1"
    local output="$2"
    local ext="${input##*.}"
    ext="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"

    case "$ext" in
        pdf)
            cp "$input" "$output"
            ;;
        png|jpg|jpeg|tiff|tif|gif|bmp|heic)
            # Get image dimensions
            local img_width img_height
            img_width=$(sips -g pixelWidth "$input" 2>/dev/null | tail -1 | awk '{print $2}')
            img_height=$(sips -g pixelHeight "$input" 2>/dev/null | tail -1 | awk '{print $2}')

            # Calculate scale to fit US Letter while preserving aspect ratio
            local scale_x scale_y scale
            scale_x=$(echo "scale=6; $PAGE_WIDTH / $img_width" | bc)
            scale_y=$(echo "scale=6; $PAGE_HEIGHT / $img_height" | bc)

            if (( $(echo "$scale_x < $scale_y" | bc -l) )); then
                scale="$scale_x"
            else
                scale="$scale_y"
            fi

            # Calculate new dimensions
            local new_width new_height
            new_width=$(echo "scale=0; $img_width * $scale / 1" | bc)
            new_height=$(echo "scale=0; $img_height * $scale / 1" | bc)

            # Create resized image and convert to PDF
            local temp_img="$TEMP_DIR/temp_$(basename "$input")"
            sips --resampleHeightWidth "$new_height" "$new_width" "$input" --out "$temp_img" >/dev/null 2>&1
            sips -s format pdf "$temp_img" --out "$output" >/dev/null 2>&1
            ;;
        *)
            echo "Warning: Skipping unsupported file $input" >&2
            return 1
            ;;
    esac
}

# Convert all inputs to PDFs
PDF_LIST=()
counter=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        temp_pdf="$TEMP_DIR/$(printf '%04d' $counter).pdf"
        if convert_to_pdf "$file" "$temp_pdf"; then
            PDF_LIST+=("$temp_pdf")
        fi
        ((counter++))
    fi
done

echo "PDFs to combine: ${#PDF_LIST[@]}" >&2

if [ ${#PDF_LIST[@]} -lt 2 ]; then
    osascript -e 'display notification "Need at least 2 valid files" with title "Combine PDFs"'
    echo "Error: Need at least 2 valid files to combine" >&2
    exit 1
fi

# Combine PDFs using macOS built-in join tool
"/System/Library/Automator/Combine PDF Pages.action/Contents/MacOS/join" -o "$OUTPUT_FILE" "${PDF_LIST[@]}"

osascript -e "display notification \"Created: $(basename "$OUTPUT_FILE")\" with title \"Combine PDFs\""
echo "Created: $OUTPUT_FILE" >&2
