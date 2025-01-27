""" 
This script will run the BabySLM evaluation pipeline to return a lexical and syntactic score for the model. Instead of running their
load_stimuli_text function, we have already saved the stimuli in a csv file in data/babyslm. This script loads the stimuli and 
runs the model to get a score for each stimuli. It then calls the BabySLM evaluation function to get the final score.

"""

import logging
import sys
from pathlib import Path

import pandas as pd
import torch
import tqdm

sys.path.append("submodules")

from BabySLM.scripts.metrics import compute_lexical, compute_syntactic

LEXICAL_STIMULI = "evaluation_data/babyslm/lexical/test/lexical_stimuli.csv"
SYNTACTIC_STIMULI_ORTHO = "evaluation_data/babyslm/syntactic/test/syntactic_stimuli_ortho.csv"
SYNTACTIC_STIMULI_PHONEMIZED = "evaluation_data/babyslm/syntactic/test/syntactic_stimuli_phono.csv"
LEXICAL_GOLD_DATA = "evaluation_data/babyslm/lexical/test/gold.csv"
SYNTACTIC_GOLD_DATA = "evaluation_data/babyslm/syntactic/test/gold.csv"


def extract_probabilities(examples, model, tokenizer, batch_size=32):
    tokenized = tokenizer(examples, return_tensors="pt", padding=True, truncation=True)
    probabilities = []
    for i in tqdm.tqdm(range(0, len(examples), batch_size)):
        size = min(batch_size, len(examples) - i)
        input_ids = tokenized["input_ids"][i : i + size].to(model.device)
        attention_mask = tokenized["attention_mask"][i : i + size].to(model.device)
        with torch.no_grad():
            outputs = model(input_ids, attention_mask=attention_mask, labels=input_ids, return_dict=True)
        shift_logits = outputs.logits[..., :-1, :].contiguous()
        shift_labels = input_ids[..., 1:].contiguous()
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none", ignore_index=tokenizer.pad_token_id)
        loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        loss = loss.view(input_ids.size(0), input_ids.size(1) - 1)  # Reshape to get loss for each token in each sequence
        loss = loss.sum(dim=1) / (loss != 0).sum(dim=1)  # Normalize by number of non-padding tokens
        probabilities.extend(-loss.cpu().numpy())

    return probabilities


def write_probabilities(seq_names, probabilities, out_file):
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, "w") as f:
        for filename, prob in zip(seq_names, probabilities):
            f.write(f"{filename} {prob}\n")


def babyslm_evaluation(model, tokenizer, model_path, type, batch_size, is_phonemized=False):
    """
    Returns either the lexical or syntactic score for the model.

    Args:
        model: The model to be evaluated
        tokenizer: The tokenizer for the model
        model_path: The path to the model checkpoint
        type: The type of evaluation to be done. Either 'lexical' or 'syntactic'
        batch_size: The batch size to be used for evaluation
        is_phonemized: Whether to use the phonemized stimuli or not
    """

    if type == "lexical":
        stimuli = pd.read_csv(LEXICAL_STIMULI)
    elif type == "syntactic":
        if is_phonemized:
            stimuli = pd.read_csv(SYNTACTIC_STIMULI_PHONEMIZED)
        else:
            stimuli = pd.read_csv(SYNTACTIC_STIMULI_ORTHO)
    else:
        raise ValueError("type must be either lexical or syntactic")

    logging.info(f"Running BabySLM evaluation for {type} stimuli")

    # Some slight adjustments needed for the stimuli
    stimuli["transcription"] = stimuli["transcription"].str.replace("tʃ", "t̠ʃ")
    stimuli["transcription"] = stimuli["transcription"].str.replace("dʒ", "d̠ʒ")

    # Get probabilities for each example and write to a file
    examples = stimuli["transcription"].tolist()
    probabilities = extract_probabilities(examples, model, tokenizer, batch_size)
    seq_names = stimuli["filename"].tolist()
    out_file = model_path / "babyslm" / f"{type}.txt"
    write_probabilities(seq_names, probabilities, out_file)

    # Run evaluation script on computed probabilities
    if type == "lexical":
        gold_file = Path(LEXICAL_GOLD_DATA)
        _, by_pair, _, _ = compute_lexical.evaluate(gold_file, out_file, is_text=True)
        accuracy = by_pair["score"].mean()
        logging.info(f"Lexical accuracy: {accuracy}")
    else:
        gold_file = Path(SYNTACTIC_GOLD_DATA)
        _, by_pair, _ = compute_syntactic.evaluate(gold_file, out_file, is_text=True)
        accuracy = by_pair["score"].mean()
        logging.info(f"Syntactic accuracy: {accuracy}")

    return accuracy
