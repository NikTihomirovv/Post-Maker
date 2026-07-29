# copy_debug.py
import os
import sys

# Расширения текстовых файлов
TEXT_EXTENSIONS = {
    '.js', '.ts', '.jsx', '.tsx', '.html', '.htm', '.css', '.scss', '.less',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.md', '.markdown', '.txt', '.log', '.csv', '.tsv',
    '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs',
    '.php', '.rb', '.sh', '.bash', '.zsh', '.fish', '.ps1',
    '.sql', '.r', '.swift', '.kt', '.dart', '.lua', '.pl', '.pm',
    '.vue', '.svelte', '.astro', '.mjs', '.cjs', '.mts', '.cts'
}

# Папки для исключения
EXCLUDE_DIRS = {
    'node_modules', '.git', '.venv', 'venv', 'env', '.env',
    '.vscode', '.idea', 'dist', 'build', 'target',
    'coverage', '.nyc_output', '__pycache__', '.pytest_cache',
    '.cache', '.next', '.nuxt', '.output', '.serverless',
    '.terraform', '.vs', '.gradle', '.mvn', '.hg',
    'logs', 'tmp', 'temp', '.temp', '.tmp'
}

def get_text_files(directory):
    """Рекурсивно собирает все текстовые файлы"""
    text_files = []
    
    for root, dirs, files in os.walk(directory):
        # Удаляем исключенные папки из поиска
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in TEXT_EXTENSIONS:
                file_path = os.path.join(root, file)
                text_files.append(file_path)
    
    return text_files

def read_file_safely(file_path):
    """Безопасно читает файл с попыткой разных кодировок"""
    encodings = ['utf-8', 'cp1251', 'latin-1', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except:
            continue
    
    return None

def main():
    # Устанавливаем кодировку для консоли Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    current_dir = os.getcwd()
    print(f"[INFO] Current directory: {current_dir}")
    print("=" * 80)
    
    all_files = get_text_files(current_dir)
    all_files.sort()
    
    print(f"[INFO] Found {len(all_files)} text files")
    print("=" * 80)
    
    success_count = 0
    fail_count = 0
    total_chars = 0
    
    for file_path in all_files:
        relative_path = os.path.relpath(file_path, current_dir)
        content = read_file_safely(file_path)
        
        if content is not None:
            print(f"\n[FILE] {relative_path}")
            print("-" * 80)
            print(content)
            print("-" * 80)
            print(f"[OK] Copied ({len(content)} chars)")
            
            total_chars += len(content)
            success_count += 1
        else:
            print(f"\n[WARN] Cannot read: {relative_path}")
            fail_count += 1
    
    print("\n" + "=" * 80)
    print("[STATS]")
    print(f"  OK: {success_count} files")
    print(f"  FAIL: {fail_count} files")
    print(f"  TOTAL CHARS: {total_chars}")
    print(f"  TOTAL KB: {total_chars / 1024:.2f} KB")
    print("=" * 80)
    print("[DONE] All files copied!")

if __name__ == "__main__":
    main()