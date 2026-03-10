import pickle
import sys
from pathlib import Path
import joblib

# Paths
MODEL_PATH = Path(__file__).resolve().parent.parent / "models"
MODEL_FILE = MODEL_PATH / "model.pkl"

def load_model():
    model = joblib.load(MODEL_FILE)
    return model

def extract_tree_structure(tree, tree_id):
    n_nodes = tree.tree_.node_count
    children_left = tree.tree_.children_left
    children_right = tree.tree_.children_right
    feature = tree.tree_.feature
    threshold = tree.tree_.threshold
    value = tree.tree_.value

    nodes = []

    for i in range(n_nodes):
        node = {
            'feature': int(feature[i]),
            'threshold': float(threshold[i]),
            'left': int(children_left[i]),
            'right': int(children_right[i]),
            'value': float(value[i][0][0]) if children_left[i] == -1 else 0.0  # leaf value
        }
        nodes.append(node)

    return nodes

def generate_c_code(model):
    
    trees = model.estimators_
    n_trees = len(trees)

    # Collect all tree structures
    all_trees = []
    max_nodes = 0

    for i, tree in enumerate(trees):
        tree_nodes = extract_tree_structure(tree, i)
        all_trees.append(tree_nodes)
        max_nodes = max(max_nodes, len(tree_nodes))

    # Generate C code
    code = []
    code.append("#ifndef RF_MODEL_H")
    code.append("#define RF_MODEL_H")
    code.append("")
    code.append("#include <stdint.h>")
    code.append("")
    code.append("// Random Forest Tree Node Structure")
    code.append("typedef struct {")
    code.append("    int feature;        // Feature index to split on (-1 for leaves)")
    code.append("    float threshold;     // Split threshold")
    code.append("    int left;           // Left child node index (-1 for leaves)")
    code.append("    int right;          // Right child node index (-1 for leaves)")
    code.append("    float value;        // Leaf prediction value")
    code.append("} rf_node_t;")
    code.append("")
    code.append(f"#define N_TREES {n_trees}")
    code.append(f"#define MAX_NODES {max_nodes}")
    code.append("")

    # Generate tree arrays
    for i, tree_nodes in enumerate(all_trees):
        code.append(f"// Tree {i}")
        code.append(f"static const rf_node_t tree_{i}[] = {{")
        for node in tree_nodes:
            code.append("    {" +
                       f"{node['feature']}, " +
                       f"{node['threshold']}f, " +
                       f"{node['left']}, " +
                       f"{node['right']}, " +
                       f"{node['value']}f" +
                       "},")
        code.append("};")
        code.append("")

    # Generate array of tree pointers
    code.append("// Array of tree pointers")
    code.append("static const rf_node_t* trees[] = {")
    for i in range(n_trees):
        code.append(f"    tree_{i},")
    code.append("};")
    code.append("")

    # Generate tree sizes
    code.append("// Number of nodes in each tree")
    code.append("static const int tree_sizes[] = {")
    for tree_nodes in all_trees:
        code.append(f"    {len(tree_nodes)},")
    code.append("};")
    code.append("")

    # Generate prediction function
    code.append("// Predict function for a single tree")
    code.append("static inline float predict_tree(const rf_node_t* tree, const float* features, int n_features) {")
    code.append("    int node_idx = 0;")
    code.append("    while (tree[node_idx].left != -1) {")
    code.append("        int feature = tree[node_idx].feature;")
    code.append("        if (feature < 0 || feature >= n_features) return 0.0f;")
    code.append("        if (features[feature] <= tree[node_idx].threshold) {")
    code.append("            node_idx = tree[node_idx].left;")
    code.append("        } else {")
    code.append("            node_idx = tree[node_idx].right;")
    code.append("        }")
    code.append("    }")
    code.append("    return tree[node_idx].value;")
    code.append("}")
    code.append("")

    code.append("// Predict function for the entire forest")
    code.append("static inline float predict_forest(const float* features, int n_features) {")
    code.append("    float prediction = 0.0f;")
    code.append("    for (int i = 0; i < N_TREES; i++) {")
    code.append("        prediction += predict_tree(trees[i], features, n_features);")
    code.append("    }")
    code.append("    return prediction / N_TREES;")
    code.append("}")
    code.append("")

    code.append("#endif // RF_MODEL_H")

    return "\n".join(code)

def main():
    """Main function to load model and generate C code."""
    try:
        print("Loading model from", MODEL_FILE)
        model = load_model()
        print(f"Model loaded: {type(model)}")
        print(f"Number of trees: {len(model.estimators_)}")

        print("Generating C code...")
        c_code = generate_c_code(model)

        # Write to file
        output_file = MODEL_PATH / "rf_model.h"
        with open(output_file, 'w') as f:
            f.write(c_code)

        print(f"C code generated and saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()