import os
import zipfile
import glob

# Ім'я файлу архіву
archive_name = "ignored_files_archive.zip"

# Зчитування вмісту .gitignore
with open(".gitignore", "r") as gitignore_file:
    ignore_paths = [line.strip() for line in gitignore_file if line.strip() and not line.startswith("#")]

# Функція для додавання файлів до архіву
def add_to_zip(zip_file, path):
    for file in glob.glob(path, recursive=True):  # Додаємо підтримку шаблонів
        if os.path.isfile(file):
            zip_file.write(file)
        elif os.path.isdir(file):
            for root, _, files in os.walk(file):
                for f in files:
                    full_path = os.path.join(root, f)
                    zip_file.write(full_path)

# Створення архіву
with zipfile.ZipFile(archive_name, "w") as zip_file:
    for path in ignore_paths:
        matched_files = glob.glob(path, recursive=True)
        if matched_files:
            add_to_zip(zip_file, path)
        else:
            print(f"Попередження: {path} не знайдено")

print(f"Архів {archive_name} створено!")