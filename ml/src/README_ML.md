concat_dataset.py :
Gets all the csv files in root/datasets and concatenates them.

split_dataset.py :
Splits dataset into train/val/test sublists.

preprocessing.py :
Uses one hot encoder for categorical variables and scales numerical variables. ML models require numbers only and bigger numbers create a bias, that's the reason we do preprocessing.

generate_profile.py :
Trains a decision tree on combined telemetry data and exports scheduler selection rules as a YAML profile in sample-profiles/generated_tester.yaml.

compiled_schedulers.yaml :
Manual YAML profile based on README descriptions of compiled schedulers, mapping them to telemetry conditions without ML training.


train.py :
A training script that uses Random Forest Classifier to guess the minimum load_avg_1.

evaluate.py :
Outputs percentiles and error rates which we will use in the scheduler_runtime.py.

pkl_converter.py :
Outputs the tree structure in json format. Stored in ml/model/scheduler_tree.json.

scheduler_runtime.py : (ŞİMDİLİK IGNORELA TAM ÇALIŞMIYOR LOGIC OTURMADI)
Additional file if json won't be enough. Uses percentiles to switch between schedulers.