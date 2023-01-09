"""
`ocr/evaluation` performs a double evaluation of ocr outputs against given groundtruth data.

1. **Bag-of-word evaluation**: computes errors by matching words which have the minimal edit distance in a bag of groundtruth and in a a bag of predicted word.
2. **Coordinate based evaluation**: computes errors by matching words with overlapping coordinates.
"""

import os
from pathlib import Path

import Levenshtein
import pandas as pd
from tqdm import tqdm
from typing import List, Dict, Tuple, Union, Optional
from ajmc.commons.variables import ORDERED_OLR_REGION_TYPES
from ajmc.commons.arithmetic import safe_divide
from ajmc.commons.geometry import is_bbox_within_bbox, are_bboxes_overlapping_with_threshold
from ajmc.ocr.evaluation.utils import initialize_soup, count_errors_by_charset, record_editops, \
    insert_text_in_soup, write_error_counts, write_editops_record
from ajmc.ocr.utils import count_chars_by_charset, harmonise_unicode
from ajmc.text_processing.ocr_classes import OcrPage, OcrCommentary
from ajmc.commons.miscellaneous import get_custom_logger

logger = get_custom_logger(__name__)


# todo 👁️ add fuzzy eval
def bag_of_word_evaluation(gt_bag: List[str],
                           pred_bag: List[str],
                           error_counts: Optional[Dict[str, Union[int, float]]] = None,
                           ) -> Dict[str, Union[int, float]]:
    """Performs a bag-of-word evaluation of `pred_bag` against `groundtruth_bag`.

    Args:
        gt_bag: The list of groundtruth words
        pred_bag: The list of ocr-predicted words
        error_counts: A dict with results (pass it if you want to evaluate multiple pages)

    Returns:
        Error statistics (dict)
    """

    if not error_counts:
        error_counts = {'gt_words': 0, 'pred_words': 0, 'true_words': 0,
                        'chars': 0, 'distance': 0, }

    pred_bag_ = pred_bag.copy()

    error_counts['gt_words'] += len(gt_bag)
    error_counts['pred_words'] += len(pred_bag_)
    error_counts['chars'] += sum([len(w) for w in gt_bag])

    for gt_word in gt_bag:  # iterate over w in gt_string

        if pred_bag_:  # If there are still words in `ocr_bag_`...

            distances = [Levenshtein.distance(pred_word, gt_word) for pred_word in pred_bag_]

            min_distance = min(distances)

            # Records `min_distance` and removes word
            if min_distance == 0:
                error_counts['true_words'] += 1
            error_counts['distance'] += min_distance
            del pred_bag_[distances.index(min_distance)]

        else:  # If `ocr_bag_` is empty, add the distance of unrecognized gt_words
            error_counts['distance'] += len(gt_word)

    if pred_bag_:  # If `ocr_bag_` still contains words after the end of the loop
        error_counts['distance'] += sum([len(w) for w in pred_bag_])

    error_counts['precision'] = safe_divide(error_counts['true_words'], error_counts['pred_words'])
    error_counts['recall'] = safe_divide(error_counts['true_words'], error_counts['gt_words'])
    error_counts['f1'] = safe_divide((2 * error_counts['precision'] * error_counts['recall']), (
            error_counts['precision'] + error_counts['recall']))
    error_counts['cwr'] = safe_divide(error_counts['true_words'], error_counts['gt_words'])
    error_counts['ccr'] = 1 - safe_divide(error_counts['distance'], error_counts['chars'])

    return error_counts


def simple_coordinates_based_evaluation(gt_words: List[Union['CanonicalWord','OcrWord']],
                                        pred_words: List[Union['CanonicalWord','OcrWord']],
                                        overlap_threshold: float = 0.8) -> float:
    """Computes edit distance between spacially overlapping words and returns the CER.

     "Simple" means that this method does NOT deal with word-boxes related issues. It only evaluates gt-words which
     overlap to `overlap_threshold` with a predicted word and vice-versa. If no predicted word is found
     (e.g. with crummy groundtruth- or preds-boxes), the word is left out and not counted in the final result.

     Args:
         gt_words: The list of ground truth words (e.g. coming from `OcrPage.children.words`)
         pred_words: The list of predicted words (e.g. coming from `OcrPage.children.words`)
         overlap_threshold: The minimal overlap-proportion.

     Returns:
         float: the character error rate
    """

    pred_words_ = pred_words.copy()
    matched_words = 0
    total_characters = 0
    total_edit_distance = 0

    for gt_word in gt_words:

        for i, pred_word in enumerate(pred_words_):
            if are_bboxes_overlapping_with_threshold(pred_word.bbox.bbox,
                                                     gt_word.bbox.bbox,
                                                     overlap_threshold):
                total_characters += len(gt_word.text)
                total_edit_distance += Levenshtein.distance(pred_word.text, gt_word.text)
                matched_words += 1
                del pred_words_[i]
                break

    logger.info(f"""Evaluating on {matched_words} words, for a total of {len(gt_words)} words.""")

    return total_edit_distance / total_characters


def coord_based_page_evaluation(gt_page: 'OcrPage',
                                pred_page: 'OcrPage',
                                word_overlap_threshold: Optional[float] = 0.8,
                                error_counts: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None,
                                editops_record: Optional[Dict[Tuple[str, str, str], int]] = None
                                ) -> Tuple[dict, dict, 'BeautifulSoup']:
    """Performs a regional and coordinates-based evaluation.

    This function returns extremely detailed counts, with word counts, caracter counts by charsets (latin, greek,
    numbers and punctuation) and correct rate (`cr`, corresponding to the normalized levenshtein distance) for
    each of these elements and for each olr region (commentary, primary text...).

    How to read the results? `cr`or `ccr`/`cwr` (correct character/word rate respectively) very straightforward. They
    correspond to the number of correct elements divided by the total number of elements.

    Note:
        Coordinate-based means that evaluation does not process documents in a linear manner, which is prone to
        alignement error when document layouts are complex. Instead, this matches overlapping words in groundtruth and
        ocr-data. More formally, for each groundtruth word :
            - find the predicted word which coordinates overlap the with groundtruth word to `word_overlap_threshold`
                - if found, calculate Levenshtein distance between the two
                - if not found, do not evaluate this word

    Args:
        gt_page: The groundtruth page
        pred_page: The predicted page
        word_overlap_threshold: The threshold to find overlaping words
        error_counts: A dict of counts (pass in if you want to evaluate multiple pages at once)
        editops_record: A dict of edit operations (pass in if you want to evaluate multiple pages at once)

    Returns:
        error_counts, editops_record, soup
    """

    soup = initialize_soup(img_width=gt_page.image.width, img_height=gt_page.image.height)  # Initialize html output
    charsets = ['latin', 'greek', 'punctuation', 'numbers']
    pred_words_ = pred_page.children.words.copy()

    if not error_counts:
        error_counts = {region:
                            {level:
                                 {count: 0 for count in ['total', 'evaluated', 'false']}
                             for level in ['words', 'chars'] + charsets}
                        for region in ['global'] + ORDERED_OLR_REGION_TYPES}

    if not editops_record:
        editops_record = {}

    for gt_word in gt_page.children.words:

        # Find `gt_word`'s regions
        gt_word_regions = ['global'] + [r.region_type for r in gt_page.children.regions if
                                        is_bbox_within_bbox(gt_word.bbox.bbox,
                                                            r.bbox.bbox)]

        for region in gt_word_regions:
            error_counts[region]['words']['total'] += 1
            error_counts[region]['chars']['total'] += len(gt_word.text)
            for charset in charsets:
                error_counts[region][charset]['total'] += count_chars_by_charset(gt_word.text, charset)

        # Find the corresponding ocr_word
        for i, pred_word in enumerate(pred_words_):
            if are_bboxes_overlapping_with_threshold(pred_word.bbox.bbox,
                                                     gt_word.bbox.bbox, word_overlap_threshold):
                distance = Levenshtein.distance(pred_word.text, gt_word.text)

                for region in gt_word_regions:

                    # Count evaluated words and false words
                    error_counts[region]['words']['evaluated'] += 1
                    error_counts[region]['words']['false'] += min(1, distance)

                    # Count evaluated chars and errors
                    error_counts[region]['chars']['evaluated'] += len(gt_word.text)
                    error_counts[region]['chars']['false'] += distance

                    # Count evaluated chars and errors by charset
                    for charset in charsets:
                        error_counts[region][charset]['evaluated'] += count_chars_by_charset(gt_word.text, charset)
                        error_counts[region][charset]['false'] += count_errors_by_charset(gt_word.text, pred_word.text,
                                                                                          charset)

                # Record edit operations
                editops_record = record_editops(gt_word=gt_word.text,
                                                ocr_word=pred_word.text,
                                                editops=Levenshtein.editops(pred_word.text, gt_word.text),
                                                editops_record=editops_record)

                # Actualize soup
                soup = insert_text_in_soup(soup=soup, word=gt_word, is_gt=True, is_false=bool(distance))
                soup = insert_text_in_soup(soup=soup, word=pred_word, is_gt=False, is_false=bool(distance))

                del pred_words_[i]
                break

    # Compute error rates
    for region in ['global'] + ORDERED_OLR_REGION_TYPES:
        for level in ['words', 'chars'] + charsets:
            error_counts[region][level]['cr'] = 1 - safe_divide(error_counts[region][level]['false'],
                                                                error_counts[region][level]['evaluated'])

    return editops_record, error_counts, soup


def commentary_evaluation(commentary: 'OcrCommentary',
                          write_files: bool = True,
                          output_dir: Optional[str] = None,
                          word_overlap_threshold: float = 0.8):
    """Evaluates all the pages of a `OcrCommentary` that have groundtruth.

    Args:
        commentary: The `OcrCommentary` object to evaluate.
        write_files: Whether to write the files or not
        output_dir: Leave to none if you want to write files to the default dir
        word_overlap_threshold: See `coord_based_page_evaluation`.
    """

    bow_error_counts, coord_error_counts, editops = None, None, None
    soups = []

    for gt_page in tqdm(commentary.ocr_groundtruth_pages, desc='Evaluating commentary pages'):
        pred_page = [p for p in commentary.children.pages if p.id == gt_page.id][0]

        bow_error_counts = bag_of_word_evaluation(gt_bag=[w.text for w in gt_page.children.words],
                                                  pred_bag=[w.text for w in pred_page.children.words],
                                                  error_counts=bow_error_counts)

        editops, coord_error_counts, soup = coord_based_page_evaluation(gt_page=gt_page,
                                                                        pred_page=pred_page,
                                                                        word_overlap_threshold=word_overlap_threshold,
                                                                        error_counts=coord_error_counts,
                                                                        editops_record=editops)
        soups.append(soup)

    if write_files:
        if not output_dir:
            output_dir = os.path.join(commentary.ocr_dir, os.pardir, 'evaluation')

        os.makedirs(output_dir, exist_ok=True)

        for i, soup in enumerate(soups):
            with open(os.path.join(output_dir, commentary.ocr_groundtruth_pages[i].id + ".html"), "w",
                      encoding="utf-8") as html_file:
                html_file.write(str(soup))

        write_editops_record(editops_record=editops, output_dir=output_dir)
        write_error_counts(bow_error_counts, coord_error_counts, output_dir)

    return bow_error_counts, coord_error_counts, editops


def line_by_line_evaluation(gt_dir: Path,
                            ocr_dir: Path,
                            gt_suffix: str = '.gt.txt',
                            ocr_suffix: str = '.txt',
                            error_record: dict = None,
                            editops_record: dict = None,
                            write_to_file: bool = True,
                            normalize: bool = True) -> Tuple[dict, dict]:
    """Evaluates all the text files in `ocr_dir` against the corresponding text files in `gt_dir`.

    Args:
        gt_dir: The directory containing the groundtruth files.
        ocr_dir: The directory containing the OCR files.
        gt_suffix: The suffix of the groundtruth files.
        ocr_suffix: The suffix of the OCR files.
        error_record: The error record to update (pass only if you want to aggregate multiple evaluations).
        editops_record: The editops record to update (pass only if you want to aggregate multiple evaluations).
        write_to_file: Whether to write the error record and editops record to file.
        normalize: Whether to harmonise the unicode of the groundtruth and OCR files.
    """

    error_record = error_record if error_record else {k: [] for k in ['id', 'gt', 'ocr',
                                                                      'chars', 'chars_distance',
                                                                      'words', 'words_distance']}
    editops_record = editops_record if editops_record else {}

    for ocr_path in ocr_dir.glob(f'*{ocr_suffix}'):
        gt_path = gt_dir / ocr_path.with_suffix(gt_suffix).name
        gt_text = gt_path.read_text(encoding='utf-8')
        ocr_text = ocr_path.read_text(encoding='utf-8')

        # Postprocess the OCR text
        if normalize:
            ocr_text = ocr_text.strip('\n')
            ocr_text = ocr_text.strip()
            ocr_text = harmonise_unicode(ocr_text)
            gt_text = gt_text.strip(' ')
            gt_text = harmonise_unicode(gt_text)

        # compute distance
        error_record['id'].append(ocr_path.stem)
        error_record['gt'].append(gt_text)
        error_record['ocr'].append(ocr_text)
        error_record['chars'].append(len(gt_text))
        error_record['chars_distance'].append(Levenshtein.distance(gt_text, ocr_text))
        error_record['words'].append(len(gt_text.split(' ')))
        error_record['words_distance'].append(Levenshtein.distance(gt_text.split(), ocr_text.split()))

        # Record edit operations
        editops_record = record_editops(gt_word=gt_text,
                                        ocr_word=ocr_text,
                                        editops=Levenshtein.editops(ocr_text, gt_text),
                                        editops_record=editops_record)

    cer = round(safe_divide(sum(error_record['chars_distance']), sum(error_record['chars'])), 3)
    wer = round(safe_divide(sum(error_record['words_distance']), sum(error_record['words'])), 3)

    logger.info(f'Character Error Rate: {cer}')
    logger.info(f'Word Error Rate: {wer}')

    # Write files
    if write_to_file:
        eval_dir = ocr_dir.parent / 'evaluation'
        os.makedirs(eval_dir, exist_ok=True)

        editops_record = {k: v for k, v in sorted(editops_record.items(), key=lambda item: item[1], reverse=True)}
        write_editops_record(editops_record=editops_record, output_dir=eval_dir)

        pd.DataFrame.from_dict(error_record, orient='columns').to_csv(os.path.join(eval_dir, 'error_record.tsv'),
                                                                      sep='\t',
                                                                      index=False)

        with open(os.path.join(eval_dir, 'results.txt'), 'w') as f:
            f.write(f'cer\twer\n{cer}\t{wer}')

    return error_record, editops_record
