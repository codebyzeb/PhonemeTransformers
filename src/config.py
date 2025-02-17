"""Defines the set of hyperparameters to be specified in the config file."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from omegaconf import MISSING


@dataclass
class ExperimentParams:
    seed: int

    # Name of the experiment - needs to be set at runtime
    name: str = MISSING

    # Name of the group that the current experiment belongs to
    # analogous to 'project' in wandb
    group: str = MISSING

    # whether to run a minimal version of the experiment
    dry_run: bool = False

    # whether to run the experiment only offline
    offline_run: bool = False

    # Whether to evaluate the segmentation task
    evaluate_segmentation: bool = True

    # Use a fixed subsample of tokens for the segmentation task
    # (good for when different datasets are used)
    segmentation_subsample: Optional[int] = None

    # Whether to evaluate the babyslm tasks
    evaluate_babyslm: bool = False

    # Which tasks to evaluate for BLIMP
    blimp_tasks: Optional[str] = None

    # Optional checkpoint path to resume training from
    resume_checkpoint_path: Optional[str] = None

    # If resume_checkpoint_path is not None and we are logging to wandb,
    # we need to specify the run_id of the run we are resuming from
    resume_run_id: Optional[str] = None


@dataclass
class DatasetParams:
    # name of the dataset on huggingface
    name: str

    # subconfig e.g. English, German, etc.
    subconfig: str

    # Which column from the loaded dataset to use for training
    text_column: str

    # Whether the data consists of phonemes
    is_phonemes: bool = False

    # Max age of child (in months)
    max_age: Optional[int] = None

    # Remove utterances from the dataset produced by children
    remove_child_utterances: Optional[bool] = None

    valid_size: Optional[int] = 10000


@dataclass
class TokenizerParams:
    # tokenizer parameters
    name: str


@dataclass
class DataPreprocessingParams:
    # params for preprocessing the dataset (i.e. tokenization)
    max_input_length: int

    # Either "dynamic" or "static" or None. Determines how utterances are collated.
    join_utts: Optional[str] = None

    # Whether to remove word boundaries from the input
    remove_word_boundaries: bool = True

    # Subsample the dataset to a certain number of examples/words/tokens
    subsample: Optional[int] = None

    # Whether to subsample the dataset using words, tokens or examples
    subsample_type: Optional[str] = None


@dataclass
class ModelParams:
    # model parameters
    name: str

    # Model kwargs to pass to the model class. Set name_or_path here to load from a pretrained model
    model_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainerParams:
    batch_size: int
    lr: float
    num_warmup_steps: int
    max_training_steps: int
    logging_steps: Optional[int] = None
    save_steps: Optional[int] = None
    eval_steps: Optional[int] = None


### Container for entire config ###


@dataclass
class TransformerSegmentationConfig:
    experiment: ExperimentParams
    dataset: DatasetParams
    tokenizer: TokenizerParams
    data_preprocessing: DataPreprocessingParams
    model: ModelParams
    trainer: TrainerParams
