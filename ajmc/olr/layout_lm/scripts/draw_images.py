import os
import pandas as pd
from ajmc.olr.utils import get_olr_split_page_ids
from ajmc.text_processing.canonical_classes import CanonicalCommentary
from transformers import LayoutLMv2TokenizerFast, LayoutLMv2ForTokenClassification, LayoutLMv2FeatureExtractor
from ajmc.olr.layout_lm.config import create_olr_config
from ajmc.olr.layout_lm.layoutlm import draw_pages
from ajmc.commons.variables import PATHS



base_path = '/Users/sven/drive/layout_lm_tests/first_region_token_only'

results = pd.DataFrame()

for fname in next(os.walk(base_path))[1]:  # Walk in dirs only
    if not fname.startswith('z') and not fname == 'all_tokens_b_ents':

        config = create_olr_config(os.path.join(base_path, fname, 'config.json'), PATHS['base_dir'] )

        model_name_or_path = os.path.join(base_path, fname, 'model')

        pages = []
        old_prefix = '/content/drive/MyDrive/'
        new_prefix = '/Users/sven/drive/'
        for dict_ in config['data']['eval']:
            ocr_dir = os.path.join(new_prefix, dict_['path'][len(old_prefix):])
            output_dir = os.path.join(new_prefix, config['predictions_dir'][len(old_prefix):])
            commentary = CanonicalCommentary.from_json(ocr_dir)
            pages += [p for p in commentary.children['page']
                      if p.id in get_olr_split_page_ids(commentary.id, dict_['split'])]

        tokenizer = LayoutLMv2TokenizerFast.from_pretrained(model_name_or_path)
        model = LayoutLMv2ForTokenClassification.from_pretrained(model_name_or_path)
        feature_extractor = LayoutLMv2FeatureExtractor.from_pretrained(model_name_or_path)

        draw_pages(pages,
                   rois=config['rois'],
                   labels_to_ids=config['labels_to_ids'],
                   ids_to_labels=config['ids_to_labels'],
                   regions_to_coarse_labels=config['region_types_to_labels'],
                   tokenizer=tokenizer,
                   feature_extractor=feature_extractor,
                   model=model,
                   output_dir=output_dir)

