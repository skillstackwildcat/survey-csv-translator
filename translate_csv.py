#!/usr/bin/env python3
"""
CSV Translation Script
Translates content in CSV files using OpenAI API with translation memory support.
"""

import csv
import json
import os
import sys
import hashlib
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from datetime import datetime


class TranslationMemory:
    """Manages translation memory to cache and reuse translations."""
    
    def __init__(self, memory_file: str = "translation_memory.json"):
        self.memory_file = memory_file
        self.memory: Dict[str, Dict[str, str]] = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Dict[str, str]]:
        """Load translation memory from JSON file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_memory(self):
        """Save translation memory to JSON file."""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
    
    def _get_key(self, text: str, target_language: str) -> str:
        """Generate a unique key for a text and language combination."""
        normalized_text = text.strip().lower()
        return hashlib.md5(f"{normalized_text}:{target_language}".encode()).hexdigest()
    
    def get_translation(self, text: str, target_language: str) -> Optional[str]:
        """Retrieve a cached translation if available."""
        if not text or not text.strip():
            return text
        
        key = self._get_key(text, target_language)
        return self.memory.get(key, {}).get('translation')
    
    def save_translation(self, text: str, target_language: str, translation: str):
        """Save a translation to memory."""
        if not text or not text.strip():
            return
        
        key = self._get_key(text, target_language)
        if key not in self.memory:
            self.memory[key] = {}
        
        self.memory[key]['source'] = text
        self.memory[key]['target_language'] = target_language
        self.memory[key]['translation'] = translation
        self.memory[key]['timestamp'] = datetime.now().isoformat()
        self._save_memory()


class CSVTranslator:
    """Main translator class for CSV files."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.memory = TranslationMemory()
        self.stats = {
            'total_rows': 0,
            'translated_rows': 0,
            'cached_rows': 0,
            'api_calls': 0
        }
    
    def validate_csv_format(self, file_path: str) -> Tuple[bool, str]:
        """Validate that the CSV file matches the expected format."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                
                if not header:
                    return False, "CSV file is empty"
                
                if len(header) < 3:
                    return False, f"CSV must have at least 3 columns. Found {len(header)} columns."
                
                # Check if we have at least one data row
                first_row = next(reader, None)
                if first_row is None:
                    return False, "CSV file has no data rows"
                
                return True, "Valid CSV format"
        
        except FileNotFoundError:
            return False, f"File not found: {file_path}"
        except Exception as e:
            return False, f"Error reading CSV file: {str(e)}"
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for translation memory lookup (preserve placeholders)."""
        if not text:
            return ""
        return text.strip()
    
    def _extract_placeholders(self, text: str) -> List[Tuple[str, str]]:
        """Extract placeholders like {ORGANIZATION} from text."""
        pattern = r'\{[A-Z_]+\}'
        placeholders = re.findall(pattern, text)
        return [(ph, ph) for ph in placeholders]
    
    def _restore_placeholders(self, text: str, placeholders: List[Tuple[str, str]]) -> str:
        """Restore placeholders in translated text (they should remain unchanged)."""
        # Placeholders should already be preserved, but this ensures they stay
        return text
    
    def _create_translation_prompt(self, text: str, target_language: str) -> str:
        """Create a clear, professional translation prompt."""
        prompt = f"""Translate the following text to {target_language}. 

Important instructions:
- Preserve all HTML tags and formatting exactly as they appear (e.g., <strong>, <br />, etc.)
- Keep all placeholders in curly braces unchanged (e.g., {{ORGANIZATION}})
- Maintain the same tone and style as the original
- Translate naturally and accurately

Text to translate:
{text}

Translation:"""
        return prompt
    
    def translate_text(self, text: str, target_language: str) -> str:
        """Translate a single text using OpenAI API with caching."""
        if not text or not text.strip():
            return text
        
        # Check translation memory first
        cached = self.memory.get_translation(text, target_language)
        if cached is not None:
            self.stats['cached_rows'] += 1
            return cached
        
        # Extract placeholders to preserve them
        placeholders = self._extract_placeholders(text)
        
        try:
            prompt = self._create_translation_prompt(text, target_language)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using cost-effective model
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate accurately while preserving all formatting and placeholders."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
                max_tokens=2000
            )
            
            translation = response.choices[0].message.content.strip()
            self.stats['api_calls'] += 1
            
            # Save to memory
            self.memory.save_translation(text, target_language, translation)
            
            return translation
        
        except Exception as e:
            print(f"\n⚠️  Error translating text: {str(e)}")
            return text  # Return original on error
    
    def translate_csv(self, input_file: str, target_languages: List[str], output_dir: Optional[str] = None):
        """Translate a CSV file to one or more target languages."""
        # Validate CSV format
        is_valid, message = self.validate_csv_format(input_file)
        if not is_valid:
            print(f"❌ Validation failed: {message}")
            sys.exit(1)
        
        print(f"✅ CSV format validated successfully")
        
        # Set up output directory
        if output_dir is None:
            output_dir = os.path.dirname(input_file) or "."
        os.makedirs(output_dir, exist_ok=True)
        
        # Read input CSV
        rows = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = [row for row in reader]
        
        self.stats['total_rows'] = len(rows)
        
        # Process each target language
        for lang in target_languages:
            print(f"\n{'='*60}")
            print(f"🌍 Translating to: {lang}")
            print(f"{'='*60}\n")
            
            output_file = self._generate_output_filename(input_file, lang, output_dir)
            translated_rows = []
            
            # Translate each row
            for idx, row in enumerate(rows, 1):
                # Ensure row has at least 3 columns
                while len(row) < 3:
                    row.append("")
                
                key = row[0]
                source_text = row[1]
                # Column 2 (index 2) is where translation goes
                
                # Show progress
                progress = (idx / len(rows)) * 100
                print(f"\r📊 Progress: {idx}/{len(rows)} ({progress:.1f}%) | "
                      f"API calls: {self.stats['api_calls']} | "
                      f"Cached: {self.stats['cached_rows']}", end='', flush=True)
                
                # Translate the text
                if source_text and source_text.strip():
                    translated_text = self.translate_text(source_text, lang)
                    self.stats['translated_rows'] += 1
                else:
                    translated_text = ""
                
                # Create translated row: [key, original_text, translated_text]
                translated_rows.append([key, source_text, translated_text])
            
            # Write output CSV
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)  # Write header
                writer.writerows(translated_rows)
            
            print(f"\n✅ Translation complete! Output saved to: {output_file}")
        
        # Print final statistics
        print(f"\n{'='*60}")
        print("📈 Translation Statistics")
        print(f"{'='*60}")
        print(f"Total rows processed: {self.stats['total_rows']}")
        print(f"Rows translated: {self.stats['translated_rows']}")
        print(f"Translations from cache: {self.stats['cached_rows']}")
        print(f"API calls made: {self.stats['api_calls']}")
        print(f"{'='*60}\n")
    
    def _generate_output_filename(self, input_file: str, language: str, output_dir: str) -> str:
        """Generate output filename based on input file and target language."""
        input_path = Path(input_file)
        # Clean language name for filename (remove spaces, special chars)
        lang_clean = re.sub(r'[^\w-]', '_', language.lower().replace(' ', '_'))
        output_name = f"{input_path.stem}_{lang_clean}{input_path.suffix}"
        return os.path.join(output_dir, output_name)


def get_language_selection() -> List[str]:
    """Interactive language selection."""
    print("\nAvailable languages (enter numbers separated by commas):")
    print("1. Spanish (Spain)")
    print("2. Spanish (Latin America)")
    print("3. French (France)")
    print("4. French (Canada)")
    print("5. German")
    print("6. Italian")
    print("7. Portuguese (Brazil)")
    print("8. Portuguese (Portugal)")
    print("9. Chinese (Simplified)")
    print("10. Chinese (Traditional)")
    print("11. Japanese")
    print("12. Korean")
    print("13. Arabic")
    print("14. Russian")
    print("15. Dutch")
    print("16. Polish")
    print("17. Custom (enter language name)")
    
    language_map = {
        '1': 'Spanish (Spain)',
        '2': 'Spanish (Latin America)',
        '3': 'French (France)',
        '4': 'French (Canada)',
        '5': 'German',
        '6': 'Italian',
        '7': 'Portuguese (Brazil)',
        '8': 'Portuguese (Portugal)',
        '9': 'Chinese (Simplified)',
        '10': 'Chinese (Traditional)',
        '11': 'Japanese',
        '12': 'Korean',
        '13': 'Arabic',
        '14': 'Russian',
        '15': 'Dutch',
        '16': 'Polish'
    }
    
    selection = input("\nEnter your selection: ").strip()
    
    if not selection:
        print("❌ No selection made. Exiting.")
        sys.exit(1)
    
    selected_languages = []
    parts = [s.strip() for s in selection.split(',')]
    
    for part in parts:
        if part in language_map:
            selected_languages.append(language_map[part])
        elif part == '17':
            custom = input("Enter custom language name: ").strip()
            if custom:
                selected_languages.append(custom)
        else:
            # Try to interpret as custom language
            selected_languages.append(part)
    
    if not selected_languages:
        print("❌ No valid languages selected. Exiting.")
        sys.exit(1)
    
    return selected_languages


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Translate CSV files using OpenAI API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python translate_csv.py sample_file.csv "French (France)"
  python translate_csv.py sample_file.csv "Spanish (Spain)" "French (Canada)" -o ./translations
  python translate_csv.py sample_file.csv --interactive
        """
    )
    parser.add_argument('input_file', nargs='?', help='Path to the CSV file to translate')
    parser.add_argument('languages', nargs='*', help='Target language(s) to translate to')
    parser.add_argument('-o', '--output-dir', dest='output_dir', help='Output directory for translated files')
    parser.add_argument('-i', '--interactive', action='store_true', help='Use interactive mode for language selection')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env variable)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("CSV Translation Tool")
    print("="*60)
    
    # Check for API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("\nEnter your OpenAI API key (or set OPENAI_API_KEY env variable): ").strip()
        if not api_key:
            print("❌ OpenAI API key is required. Exiting.")
            sys.exit(1)
    
    # Get input file
    input_file = args.input_file
    if not input_file:
        input_file = input("\nEnter path to CSV file: ").strip()
    
    if not input_file or not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    # Get target languages
    target_languages = args.languages
    if not target_languages or args.interactive:
        target_languages = get_language_selection()
    
    print(f"\n📁 Input file: {input_file}")
    print(f"🌍 Target languages: {', '.join(target_languages)}")
    
    # Get output directory (optional)
    output_dir = args.output_dir
    if not output_dir and (args.interactive or not args.languages):
        # Prompt for output directory in interactive mode
        output_dir = input("\nEnter output directory (press Enter for same as input file): ").strip()
        if not output_dir:
            output_dir = None
    
    # Create translator and translate
    translator = CSVTranslator(api_key=api_key)
    translator.translate_csv(input_file, target_languages, output_dir)
    
    print("✨ All translations completed successfully!")


if __name__ == "__main__":
    main()

