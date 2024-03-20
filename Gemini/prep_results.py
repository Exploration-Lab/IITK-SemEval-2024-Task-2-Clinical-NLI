import json

labels = json.load(open('./Gemini_results.json'))

keys = list(labels.keys())

# function to add to JSON
def write_json(id, new_data, filename='./results.json'):
    with open(filename,'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data[id] = new_data
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)

for key in keys:
    if labels[key]["answer"].startswith("Yes") or labels[key]["answer"].startswith("**Yes"):
        write_json(key, {"Prediction": "Entailment"})
    elif labels[key]["answer"].startswith("No") or labels[key]["answer"].startswith("**No"):
        write_json(key, {"Prediction": "Contradiction"})