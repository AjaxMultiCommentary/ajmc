"""Train or evaluate tesseract"""
import argparse

from ajmc.commons.miscellaneous import get_custom_logger
from ajmc.ocr.preprocessing import data_preparation
from ajmc.ocr.tesseract.experiments import make_experiments
from ajmc.ocr.tesseract.models import make_models

logger = get_custom_logger(__name__)

# Argument parsing
parser = argparse.ArgumentParser()

# Models
parser.add_argument('--make_models', action='store_true')
parser.add_argument('--model_ids', nargs='+', type=str, default=None,
                    help='The ids of the models to build, leave empty to build all models')

# Datasets
parser.add_argument('--make_datasets', action='store_true')
parser.add_argument('--dataset_ids', nargs='+', type=str, default=None,
                    help='The ids of the datasets to make, leave empty to make all datasets')

# Experiments
parser.add_argument('--make_experiments', action='store_true')
parser.add_argument('--experiment_ids', nargs='+', type=str, default=None,
                    help='The ids of the experiments to make, leave empty to make all experiments')

parser.add_argument('--overwrite', action='store_true')

if __name__ == '__main__':
    args = parser.parse_args()
    print(args)

    if args.make_datasets:
        logger.info('Making datasets')
        data_preparation.make_datasets(dts_ids=args.dataset_ids)

    if args.make_models:
        logger.info('Making models')
        make_models(models_ids=args.model_ids, overwrite=args.overwrite)


    if args.make_experiments:
        logger.info('Making experiments')
        make_experiments(experiment_ids=args.experiment_ids, overwrite=args.overwrite)
