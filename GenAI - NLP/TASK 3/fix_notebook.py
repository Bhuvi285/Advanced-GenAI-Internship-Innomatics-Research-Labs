import json

file_path = "Build_a_Chatbot_using_Hugging_Face_Transformers.ipynb"

with open(file_path, "r", encoding="utf-8") as f:
    notebook = json.load(f)

# Remove widget metadata
if "widgets" in notebook["metadata"]:
    del notebook["metadata"]["widgets"]

# Clean outputs
for cell in notebook["cells"]:
    if "outputs" in cell:
        cell["outputs"] = []
    if "execution_count" in cell:
        cell["execution_count"] = None

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print("✅ Fixed successfully")