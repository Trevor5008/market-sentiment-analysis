from ppath import PROJECT_ROOT
import json
import re

patterns = {
    "read_csv":r"read_csv",
    "dropna": r"\.dropna",
    "loc_filter" : r"\.loc\[", 
    "groupby": r"\.groupby",
    "notna": r"\.notna",
    "query": r"\.query",
    "comparision": r"\]\s*(==|!=|>=|<=|>|<)"

}
# TODO: determine syntax for neutral filter
# TODO: expand detection to other methods like masks

for nb in (PROJECT_ROOT/"docs"/"eda").rglob("*.ipynb"):

    try:
        with open(nb, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Error reading: ",nb, e)
        continue

    code = "\n".join(
        "".join(cell["source"])
        for cell in data["cells"]
        if cell["cell_type"] == "code"
    )
    print("\n", nb)

    for check, pattern in patterns.items():
        if re.search(pattern, code):
            print(check, ": FOUND")
        else:
            print(check, ": ")
