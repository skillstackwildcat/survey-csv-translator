# CSV Translation Tool

A Python script that translates content in CSV files using OpenAI's API. The tool supports multiple languages (including dialects), uses translation memory to reduce API costs, and preserves HTML formatting and placeholders.

## Features

- ✅ **Multiple Language Support**: Translate to one or more languages, including regional dialects (e.g., French Canada vs. French France)
- ✅ **Translation Memory**: Caches translations to reduce API calls and costs
- ✅ **Format Preservation**: Automatically preserves HTML tags, CSS, and placeholders like `{ORGANIZATION}`
- ✅ **CSV Validation**: Validates input file format before processing
- ✅ **Real-time Progress**: Shows translation progress with statistics
- ✅ **Separate Output Files**: Generates one CSV file per target language

## Prerequisites

- Python 3.7 or higher
- OpenAI API key
- Virtual environment (already set up)

## Installation

1. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key (choose one method):
   - **Option 1**: Set as environment variable:
     ```bash
     export OPENAI_API_KEY="your-api-key-here"
     ```
   - **Option 2**: Enter it when prompted by the script

## Usage

### Basic Usage

Run the script and follow the interactive prompts:

```bash
python translate_csv.py
```

The script will ask you for:
1. Path to the CSV file (if not provided as argument)
2. Target language(s) to translate to
3. Output directory (optional, defaults to input file directory)

### Command Line Arguments

You can also provide arguments directly:

```bash
python translate_csv.py <input_file.csv> <language1> <language2> ...
```

Examples:
```bash
# Single language
python translate_csv.py sample_file.csv "French (France)"

# Multiple languages
python translate_csv.py sample_file.csv "Spanish (Spain)" "French (Canada)" "German"

# With output directory
python translate_csv.py sample_file.csv "Spanish (Spain)" --output-dir ./translations
```

### CSV File Format

Your CSV file must follow this format:
- **Column 1**: Key/Metadata (ignored during translation)
- **Column 2**: English text to translate
- **Column 3**: Translation column (will be populated with translations)

Example:
```csv
Key,Default Text,Translation
q-1,Hello World,
q-2,How are you?,
```

## Supported Languages

The script includes a menu with common languages, but you can also enter any custom language name. Pre-configured options include:

- Spanish (Spain)
- Spanish (Latin America)
- French (France)
- French (Canada)
- German
- Italian
- Portuguese (Brazil)
- Portuguese (Portugal)
- Chinese (Simplified)
- Chinese (Traditional)
- Japanese
- Korean
- Arabic
- Russian
- Dutch
- Polish
- Custom languages (any language name)

## Translation Memory

The script automatically creates a `translation_memory.json` file that stores previously translated phrases. This helps:
- Reduce API costs by reusing translations
- Ensure consistency across multiple runs
- Speed up translation of similar content

The translation memory is saved automatically and persists between runs.

## Output Files

For each target language, the script generates a separate CSV file with the naming pattern:
```
<original_filename>_<language_name>.csv
```

For example:
- `sample_file.csv` → `sample_file_french_france.csv`
- `sample_file.csv` → `sample_file_spanish_spain.csv`

## Features in Detail

### Format Preservation
- HTML tags (e.g., `<strong>`, `<br />`) are preserved exactly
- Placeholders like `{ORGANIZATION}` remain unchanged
- CSS styling is maintained

### Progress Tracking
The script displays real-time progress including:
- Current row being processed
- Total rows
- Number of API calls made
- Number of translations retrieved from cache

### Error Handling
- Validates CSV format before processing
- Handles API errors gracefully
- Returns original text if translation fails

## Example Workflow

1. Prepare your CSV file with English content in column 2
2. Run the script:
   ```bash
   python translate_csv.py my_survey.csv
   ```
3. Select target languages from the menu (e.g., "1,3,5" for Spanish, French, German)
4. Wait for translation to complete
5. Find translated files in the output directory

## Troubleshooting

### "CSV format validation failed"
- Ensure your CSV has at least 3 columns
- Check that the file is not empty
- Verify the file encoding is UTF-8

### "OpenAI API key is required"
- Set the `OPENAI_API_KEY` environment variable, or
- Enter it when prompted by the script

### Translation errors
- Check your internet connection
- Verify your OpenAI API key is valid and has sufficient credits
- Check OpenAI API status

## Notes

- The script uses `gpt-4o-mini` model for cost-effective translations
- Translation memory is stored in `translation_memory.json` in the script directory
- Empty cells are preserved as empty in translations
- The script handles multi-line text and special characters

## License

This script is provided as-is for translation purposes.

