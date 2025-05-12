import cv2
import iris
from pathlib import Path
from itertools import combinations

def load_template(img_path):
    return iris.IRISPipeline()(cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE), eye_side="left")['iris_template']

def process_templates(dataset_path, num_folders=3, threshold=0.37):
    templates = {}
    matcher = iris.HammingDistanceMatcher()
    
    # Load templates
    for folder in sorted(dataset_path.iterdir())[:num_folders]:
        if not folder.is_dir():
            continue
        templates[folder.name] = [load_template(p) for p in folder.glob("*.jpg") if load_template(p) is not None]
        print(f"{folder.name}: {len(templates[folder.name])} templates loaded")

    # Compare templates
    stats = {'false_diffs': 0, 'correct_matches': 0, 'false_matches': 0, 'correct_rejects': 0}
    
    # Within folder comparisons
    for name, tmpl_list in templates.items():
        for t1, t2 in combinations(tmpl_list, 2):
            d = matcher.run(t1, t2)
            if d < threshold:
                stats['correct_matches'] += 1
            else:
                stats['false_diffs'] += 1

    # Across folder comparisons
    for (name1, tmpl_list1), (name2, tmpl_list2) in combinations(templates.items(), 2):
        for t1, t2 in combinations(tmpl_list1 + tmpl_list2, 2):
            d = matcher.run(t1, t2)
            if d < threshold:
                stats['false_matches'] += 1
            else:
                stats['correct_rejects'] += 1

    return stats

if __name__ == "__main__":
    stats = process_templates(Path("dataset"))
    print("\nResults:")
    for key, value in stats.items():
        print(f"{key}: {value}")