# Number to English Converter & F5-TTS Voice Generator

A Python GUI tool that converts numbers in text to their English word equivalents and integrates with F5-TTS for voice generation, designed specifically for voice-over and text-to-speech applications.

## Features

### Text Formatting
- **Real-time Preview**: Automatically displays processed results as you type
- **Smart Number Recognition**: 
  - Year detection: 1947 → nineteen forty-seven
  - Other numbers: 123 → one hundred twenty-three
  - Suffix support: 1991s → nineteen ninety-ones, 4th → fourth
- **Export Function**: Save processed text to file
- **Side-by-side Layout**: Easy comparison between input and output
- **Voice-over Friendly**: Prevents Chinese pronunciation in TTS systems

### F5-TTS Voice Generation
- **Reference Audio Support**: Upload local files or provide remote URLs
- **Reference Text Input**: Manually enter or auto-transcribe reference audio
- **Advanced Parameters**:
  - Playback speed (0.1 - 2.0)
  - NFE steps
  - Cross-fade duration
  - Remove silences
  - Random seed generation (10-digit)
- **Settings Persistence**: Automatically saves and restores last-used settings
- **Debug Logging**: Comprehensive log section for troubleshooting

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

- Python 3.6+ (for source code)
- tkinter (usually included with Python)
- requests library (for F5-TTS integration)
- F5-TTS API server (for voice generation feature)

## Interface Description

### Text Formatting Section
- **Input Text Area**: Enter text to be processed
- **Preview Area**: Shows processed results
- **Process Text**: Manually trigger processing
- **Export**: Save processed text to file
- **Clear**: Clear all text content

### F5-TTS Section
- **Server URL**: F5-TTS API server address
- **Reference Audio**: Upload or provide URL for reference audio
- **Reference Text**: Manually enter or leave empty for auto-transcription
- **Generation Text**: Text to be converted to speech
- **Advanced Settings**: Speed, NFE steps, crossfade, remove silences, seed
- **Generate Speech**: Trigger voice generation
- **Save Audio**: Save generated audio file
- **Open Audio**: Open generated audio file
- **Debug Log**: View detailed logs for troubleshooting

## Example

**Input:**
```
On December 4th, 1991s, after 64 years of circling the globe, Pan American World Airways ran out of money. The year 1733 was also significant.
```

**Output:**
```
On December fourth, nineteen ninety-ones, after sixty-four years of circling the globe, Pan American World Airways ran out of money. The year seventeen thirty-three was also significant.
```
