#!/usr/bin/env python3
"""
Generate notes.json from source.json by extracting docstrings.

Usage:
    python generate_notes.py <source_json_path> <notes_json_path>
"""
import sys
import json
from pathlib import Path
from docstring_extractor import extract_docstrings


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_notes.py <source_json_path> <notes_json_path>")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    notes_path = Path(sys.argv[2])

    # Read source.json
    if not source_path.exists():
        print(f"Error: {source_path} does not exist")
        sys.exit(1)

    with open(source_path, 'r', encoding='utf-8') as f:
        source_files = json.load(f)

    # Extract docstrings
    flat_notes = extract_docstrings(source_files)

    # Reorganize notes by file path
    # UI expects: {filepath: [note1, note2, ...]}
    notes_by_file = {}
    for key, note in flat_notes.items():
        filepath = note['path']
        if filepath not in notes_by_file:
            notes_by_file[filepath] = []
        notes_by_file[filepath].append(note)

    # If notes.json already exists, merge with existing manual notes
    existing_notes = {}
    if notes_path.exists():
        try:
            with open(notes_path, 'r', encoding='utf-8') as f:
                existing_notes = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Merge: For each file, combine auto-generated and manual notes
    final_notes = {}

    # Start with auto-generated notes
    for filepath, auto_note_list in notes_by_file.items():
        final_notes[filepath] = auto_note_list

    # Add manual notes (notes that don't have all the auto-generated fields)
    for filepath, note_list in existing_notes.items():
        if filepath not in final_notes:
            final_notes[filepath] = []

        # Keep only manual notes (those without the exact structure of auto-generated ones)
        for note in note_list:
            # Check if this is a manual note by seeing if it lacks the auto-generated marker
            # Auto-generated notes have specific titles like "## Module Documentation" or "## Class:"
            if 'note' in note:
                note_text = note.get('note', '')
                # Keep manual notes (those that don't start with our auto-generated patterns)
                if not (note_text.startswith('## Module Documentation') or
                        note_text.startswith('## Class:') or
                        note_text.startswith('## Function:')):
                    final_notes[filepath].append(note)

    # Write notes.json
    with open(notes_path, 'w', encoding='utf-8') as f:
        json.dump(final_notes, f, indent=2, ensure_ascii=False)

    total_auto = sum(len(notes_by_file.get(f, [])) for f in notes_by_file)
    total_final = sum(len(v) for v in final_notes.values())

    print(f"Generated {total_auto} notes from docstrings")
    print(f"Total: {total_final} notes written to {notes_path}")


if __name__ == "__main__":
    main()
