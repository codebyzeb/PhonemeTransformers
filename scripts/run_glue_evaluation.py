# python submodules/evaluation-pipeline-2024/finetune_classification.py --model_name_or_path $MODEL_PATH_FULL --output_dir results/finetune/$model_basename/$task/ --train_file evaluation_data/babylm_eval/glue_filtered/$TRAIN_NAME.train.jsonl --validation_file evaluation_data/babylm_eval/glue_filtered/$VALID_NAME.valid.jsonl --do_train $DO_TRAIN  --do_eval --do_predict  --use_fast_tokenizer False --max_seq_length 128 --per_device_train_batch_size 64 --learning_rate 5e-5 --num_train_epochs 10 --patience 3 --evaluation_strategy epoch --save_strategy epoch --overwrite_output_dir --trust_remote_code  --seed 12 --use_cpu True

import json
import os
import sys

import wandb

sys.path.append("submodules/evaluation-pipeline-2024")

import finetune_classification

TASKS = ["boolq", "cola", "mnli", "mnli-mm", "mrpc", "multirc", "qnli", "qqp", "rte", "sst2", "wsc"]
TASK_METRICS = {
    "boolq": "eval_accuracy",
    "cola": "eval_mcc",
    "mnli": "eval_accuracy",
    "mnli-mm": "eval_accuracy",
    "mrpc": "eval_f1",
    "multirc": "eval_accuracy",
    "qnli": "eval_accuracy",
    "qqp": "eval_f1",
    "rte": "eval_accuracy",
    "sst2": "eval_accuracy",
    "wsc": "eval_accuracy",
}


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/run_glue_evaluation.py <checkpoint_path> <resume_run_id>")
        sys.exit(1)

    checkpoint_path = sys.argv[1]
    resume_run_id = sys.argv[2]

    wandb_entity = os.environ.get("WANDB_ENTITY")
    group = checkpoint_path.split("/")[1]
    name = checkpoint_path.split("/")[2]

    evaluation_folder = "evaluation_data/babylm_eval_phonemized/glue_filtered" if "phoneme" in checkpoint_path else "evaluation_data/babylm_eval/glue_filtered"

    task_results = {}

    for task in TASKS:

        out_dir = f"checkpoints/finetune/{group}/{name}/{task}/"
        model_path = f"checkpoints/finetune/{group}/{name}/mnli" if task == "mnli-mm" else checkpoint_path
        train_file = f"{evaluation_folder}/mnli.train.jsonl" if task == "mnli-mm" else f"{evaluation_folder}/{task}.train.jsonl"
        valid_file = f"{evaluation_folder}/{task}.valid.jsonl"
        do_train = "False" if task == "mnli-mm" else "True"

        args = [
            "submodules/evaluation-pipeline-2024/finetune_classification.py",
            "--model_name_or_path",
            model_path,
            "--output_dir",
            f"{out_dir}",
            "--train_file",
            train_file,
            "--validation_file",
            valid_file,
            "--do_train",
            do_train,
            "--do_eval",
            "--do_predict",
            "--max_seq_length",
            "128",
            "--per_device_train_batch_size",
            "64",
            "--learning_rate",
            "5e-5",
            "--num_train_epochs",
            "10",
            "--patience",
            "3",
            "--evaluation_strategy",
            "epoch",
            # "--save_strategy",
            # "epoch",
            "--overwrite_output_dir",
            "--trust_remote_code",
            "--seed",
            "12",
            # "--use_cpu",
            # "True",
        ]

        # Only run evaluation if it hasn't been run yet
        if not os.path.exists(out_dir + "eval_results.json"):
            sys.argv = args
            finetune_classification.main()

        # Read json results
        with open(out_dir + "eval_results.json", "r") as f:
            results = json.load(f)

        task_results[f"eval/glue_{task}"] = results[TASK_METRICS[task]]
        wandb.finish()

    glue_macro = sum([task_results[f"eval/glue_{task}"] for task in TASKS]) / len(TASKS)
    task_results["eval/glue_macro"] = glue_macro

    print("Full task results:")
    print(task_results)

    # Log results to wandb
    api = wandb.Api()
    run = api.run(f"{wandb_entity}/{group}/{resume_run_id}")
    config = run.config
    wandb.init(
        entity=wandb_entity,
        project=group,
        name=name,
        config=config,
        resume="allow",
        id=resume_run_id,
    )

    wandb.log(task_results)


if __name__ == "__main__":
    main()
