# Number to English Converter

A Python GUI tool that converts numbers in text to their English word equivalents, designed specifically for voice-over and text-to-speech applications.

## Features

- **Real-time Preview**: Automatically displays processed results as you type
- **Smart Number Recognition**: 
  - Year detection: 1947 → nineteen forty-seven
  - Other numbers: 123 → one hundred twenty-three
  - Suffix support: 1991s → nineteen ninety-ones, 4th → fourth
- **Export Function**: Save processed text to file
- **Side-by-side Layout**: Easy comparison between input and output
- **Voice-over Friendly**: Prevents Chinese pronunciation in TTS systems

## Usage

1. Run the program:
   ```bash
   python text_formatter.py
   ```

2. Enter text containing numbers in the left input area

3. The right preview area will show the processed results in real-time

4. Click "Export" to save the processed text to a file

## Number Conversion Rules

- **Four-digit Numbers (1000-9999) - Year Format**:
  - 1733 → seventeen thirty-three
  - 1947 → nineteen forty-seven
  - 2001 → two thousand one
  - 2023 → two thousand twenty-three
  - 1234 → twelve thirty-four
  - 5678 → fifty-six seventy-eight

- **Other Numbers**:
  - 1-20: Direct word mapping
  - 21-99: Combined form (e.g., 25 → twenty-five)
  - 100-999: Full English expression (e.g., 123 → one hundred twenty-three)
  - 10000+: Full English expression (e.g., 12345 → twelve thousand three hundred forty-five)

- **Numbers with Suffixes**:
  - 1991s → nineteen ninety-ones
  - 4th → fourth
  - 1st → first
  - 2nd → second
  - 3rd → third

## System Requirements

- Python 3.6+
- tkinter (usually included with Python)

## Interface Description

- **Input Text Area**: Enter text to be processed
- **Preview Area**: Shows processed results
- **Process Text**: Manually trigger processing
- **Export**: Save processed text to file
- **Clear**: Clear all text content

## Example

**Input:**
```
On December 4th, 1991s, after 64 years of circling the globe, Pan American World Airways ran out of money. The year 1733 was also significant.
```

**Output:**
```
On December fourth, nineteen ninety-ones, after sixty-four years of circling the globe, Pan American World Airways ran out of money. The year seventeen thirty-three was also significant.
```
