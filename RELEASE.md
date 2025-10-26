# TextFormatter Release Notes

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
