import csv
import json

input_file = 'ingredients.csv'  # Ваш файл CSV
output_file = 'ingredients_fix.json'  # Выходной JSON

model_name = 'recipes.ingredient'  # Название модели (app_name.ModelName)

with open(input_file, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    data = []
    for row in reader:
        data.append({
            "model": model_name,
            "fields": {
                "name": row['name'],
                "measurement_unit": row['measurement_unit'],
            }
        })

with open(output_file, 'w', encoding='utf-8') as jsonfile:
    json.dump(data, jsonfile, ensure_ascii=False, indent=2)

print(f'JSON data written to {output_file}')
