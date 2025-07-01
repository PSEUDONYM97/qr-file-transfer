import re
import os
import sys

def parse_chunk_metadata(chunk_text):
    header_match = re.search(r"--BEGIN part_(\d+)_of_.*?file:\s*(.+?)--", chunk_text)
    footer_match = re.search(r"--END part_\d+--", chunk_text)

    if not header_match or not footer_match:
        return None, None, None

    part_num = int(header_match.group(1))
    filename = header_match.group(2).strip()
    start = header_match.end()
    end = footer_match.start()
    body = chunk_text[start:end]
    # Only remove leading/trailing newlines, preserve tabs and spaces
    body = body.strip('\n\r')
    # Convert tabs to 4 spaces
    body = body.expandtabs(4)
    return part_num, filename, body

def collect_chunks_from_folder(folder_path):
    chunks = []
    for fname in sorted(os.listdir(folder_path)):
        if fname.lower().endswith(".txt"):
            path = os.path.join(folder_path, fname)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                part_num, filename, body = parse_chunk_metadata(text)
                if part_num is not None:
                    chunks.append((part_num, filename, body))
                else:
                    print(f"Warning: Skipped invalid chunk in {fname}")
    return chunks

def main():
    if len(sys.argv) != 2:
        print("Usage: python qr_rebuild_spaces.py <folder_path>")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid folder.")
        sys.exit(1)

    print(f"Reading QR chunks from: {folder}")
    chunks = collect_chunks_from_folder(folder)

    if not chunks:
        print("No valid chunks found.")
        return

    chunks.sort(key=lambda x: x[0])
    output_filename = chunks[0][1] + "_spaces"
    combined = "\n".join(chunk[2] for chunk in chunks)

    with open(output_filename, "w", encoding="utf-8") as out:
        out.write(combined)

    print(f"Successfully rebuilt file with tabs converted to spaces: {output_filename}")

if __name__ == "__main__":
    main() 