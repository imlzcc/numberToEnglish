# TextFormatter Release Notes

## Version 2.0.0

### New Features
- **F5-TTS Integration**: Full integration with local F5-TTS API for voice generation
  - Reference audio upload (local file or remote URL)
  - Reference text input with auto-transcription support
  - Advanced parameters: speed, NFE steps, crossfade duration, remove silences
  - Random seed generation with 10-digit support
  - Automatic transcription of reference audio using Whisper
  - Save and open generated audio files
- **Settings Persistence**: Automatically saves and restores last-used settings
- **Debug Logging**: Comprehensive log section for troubleshooting

### Features
- **Number to English Conversion**: Converts numbers in text to English words
- **Year Recognition**: Special handling for years (1900-2099)
- **Suffix Support**: Handles numbers with suffixes (1991s, 4th, 1st, etc.)
- **Real-time Preview**: Side-by-side layout for easy comparison
- **Export Function**: Save processed text to file
- **Voice-over Friendly**: Prevents Chinese pronunciation in TTS systems
- **F5-TTS Voice Generation**: Generate high-quality voice using F5-TTS API

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.6+ (for source code)
- F5-TTS API server (for voice generation feature)

### Dependencies
- requests: For API communication
- tkinter: GUI framework (usually included with Python)

### File Size
- **TextFormatter.exe**: ~9.5 MB (compressed with UPX)
- **Original size**: ~10.1 MB

### Usage

#### Text Formatting
1. Double-click `TextFormatter.exe` to run
2. Enter text in the left input area
3. View processed results in the right preview area
4. Click "Export" to save the processed text

#### Voice Generation (F5-TTS)
1. Configure F5-TTS server URL (default: http://127.0.0.1:7860)
2. Upload or provide reference audio (local file or URL)
3. Optionally enter reference text (or leave empty for auto-transcription)
4. Enter or use processed text for generation
5. Adjust advanced parameters as needed
6. Click "生成语音" (Generate Speech)
7. Save or open the generated audio file

### Improvements in v2.0.0
- Fixed JSON message parsing for Gradio API event streams
- Improved Windows path handling in API requests
- Better error handling and logging
- Enhanced UI with debug log section

## Version 1.0.0

### Features
- **Number to English Conversion**: Converts numbers in text to English words
- **Year Recognition**: Special handling for years (1900-2099)
- **Suffix Support**: Handles numbers with suffixes (1991s, 4th, 1st, etc.)
- **Real-time Preview**: Side-by-side layout for easy comparison
- **Export Function**: Save processed text to file
- **Voice-over Friendly**: Prevents Chinese pronunciation in TTS systems

### System Requirements
- Windows 10/11 (64-bit)
- No additional dependencies required

### File Size
- **TextFormatter.exe**: ~9.5 MB (compressed with UPX)
- **Original size**: ~10.1 MB

### Usage
1. Double-click `TextFormatter.exe` to run
2. Enter text in the left input area
3. View processed results in the right preview area
4. Click "Export" to save the processed text

### Example Conversion
**Input:**
```
On December 4th, 1991s, after 64 years of circling the globe.
```

**Output:**
```
On December fourth, nineteen ninety-ones, after sixty-four years of circling the globe.
```

### Build Information
- Built with PyInstaller 6.13.0
- Compressed with UPX 4.2.1
- Python 3.11.9
- tkinter GUI framework
