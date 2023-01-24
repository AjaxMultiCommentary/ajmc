"""
`basic_rebuild`, `get_iiif_url`, `compute_image_links`, `get_cas`, `rebuild_to_xmi`, `export_commentaries_to_xmi` are
legacy but functional.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from cassis import Cas, load_cas_from_xmi, load_typesystem
from cassis.typesystem import FeatureStructure
from tqdm import tqdm

from ajmc.commons import variables
from ajmc.commons.arithmetic import compute_interval_overlap
from ajmc.commons.miscellaneous import aligned_print, get_custom_logger

logger = get_custom_logger(__name__)


# Todo : See how to handle the three 'coords' (instead of bbox) keys. change all the existing canonical ?
def basic_rebuild(page: dict,
                  region_types: Union[List[str], str] = "all",
                  string: str = "") -> dict:
    # todo 👁️ a light version of this function computing only what you actually need
    """Basic rebuild function"""

    coordinates = {"regions": [], "lines": [], "words": []}
    offsets = {"regions": [], "lines": [], "words": []}
    texts = {"regions": [], "lines": [], "words": []}

    for region in page["regions"]:

        if region_types == "all" or region["region_type"] in region_types:

            region_text = ""
            region_offsets = [len(string)]

            for line in region["lines"]:
                line_text = ""
                line_offsets = [len(string)]

                for n, word in enumerate(line['words']):
                    word_offsets = [len(string)]

                    region_text += word["text"] + " "
                    line_text += word["text"] + " "
                    string += word["text"] + " "

                    word_offsets.append(len(string) - 1)

                    texts["words"].append(word["text"] + " ")
                    offsets['words'].append(word_offsets)
                    coordinates['words'].append(word['bbox'])

                line_offsets.append(len(string) - 1)
                offsets["lines"].append(line_offsets)
                coordinates['lines'].append(line['bbox'])
                texts["lines"].append(line_text)

            region_offsets.append(len(string) - 1)
            coordinates['regions'].append(region['bbox'])
            offsets["regions"].append(region_offsets)
            texts["regions"].append(region_text)

    return {"id": page["id"], "fulltext": string, "bbox": coordinates, "offsets": offsets, "texts": texts}


def get_iiif_url(page_id: str,
                 box: List[int],
                 base: str = "http://lorem_ipsum.com/ajax",
                 iiif_manifest_uri: str = None,
                 pct: bool = False,
                 ) -> str:
    """ Returns impresso iiif url given a page id and a box

    Args:
        page_id (str): page id
        box (List[int]): iiif box coordinates (x, y, w, h)
        base (str): base url
        iiif_manifest_uri (str): iiif manifest uri
        pct (bool): if True, returns pct coordinates
    """
    prefix = "pct:" if pct else ""
    suffix = "full/0/default.jpg"

    box = ",".join(str(x) for x in box)

    if iiif_manifest_uri is None:
        return os.path.join(base, page_id, prefix + box, suffix)
    else:
        return os.path.join(iiif_manifest_uri.replace('/info.json', ''), prefix + box, suffix)


def compute_image_links(page: dict,
                        padding: int = 20,
                        iiif_endpoint: str = None,
                        iiif_links: Dict[str, str] = None,
                        pct: bool = False, ):
    image_links = []

    for line_coords, line_offsets in zip(page["bbox"]["lines"], page["offsets"]["lines"]):

        if iiif_links is None:
            iiif_link = get_iiif_url(page["id"], box=line_coords, pct=pct)
        else:
            iiif_link = get_iiif_url(page["id"], box=line_coords, iiif_manifest_uri=iiif_links[page["id"]], pct=pct)
        image_links.append((iiif_link, line_offsets[0], line_offsets[1]))

    for word_coords, word_offsets in zip(page["bbox"]["words"], page["offsets"]["words"]):

        if iiif_links is None:
            iiif_link = get_iiif_url(page["id"], box=word_coords, pct=pct)
        else:
            iiif_link = get_iiif_url(page["id"], box=word_coords, iiif_manifest_uri=iiif_links[page["id"]], pct=pct)
        image_links.append((iiif_link, word_offsets[0], word_offsets[1]))

    return image_links


def rebuild_to_xmi(page: dict,
                   output_dir: Path,
                   typesystem_path: Path = variables.TYPESYSTEM_PATH,
                   iiif_mappings=None,
                   pct_coordinates=False):
    """
    Converts a rebuild-dict into Apache UIMA/XMI format.

    The resulting file will be named after the page ID, adding
    the `.xmi` extension.

    Args:
        page (dict): a page dict as returned by `basic_rebuild`
        output_dir (Path): path to the output directory
        typesystem_path (Path): path to the typesystem file
        iiif_mappings (dict): a dict mapping page IDs to IIIF manifest URIs
        pct_coordinates (bool): if True, coordinates are expressed in percentage
    """

    with open(str(typesystem_path), "rb") as f:
        typesystem = load_typesystem(f)  # object for the type system

    cas = Cas(typesystem=typesystem)
    cas.sofa_string = page["fulltext"]  # str # `ft` field in the rebuild CI
    cas.sofa_mime = 'text/plain'

    sentence = typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence')
    word = typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token')

    img_link_type = 'webanno.custom.AjMCImages'
    image_link = typesystem.get_type(img_link_type)

    # create sentence-level annotations
    for offsets in page["offsets"]["lines"]:
        cas.add_annotation(sentence(begin=offsets[0], end=offsets[1]))

    for offsets in page["offsets"]["words"]:
        cas.add_annotation(word(begin=offsets[0], end=offsets[1]))

    iiif_links = compute_image_links(page, iiif_links=iiif_mappings, pct=pct_coordinates)

    # inject the IIIF links into
    for iiif_link, start, end in iiif_links:
        cas.add_annotation(image_link(begin=start, end=end, link=iiif_link))

    cas.to_xmi((output_dir / f'{page["id"]}.xmi'), pretty_print=True)


# todo 👁️ This should rely on ocr outputs dirs
def export_commentary_to_xmis(commentary: Type['Commentary'],
                              make_jsons: bool,
                              make_xmis: bool,
                              json_dir: Optional[Path] = None,
                              xmi_dir: Optional[Path] = None,
                              region_types: Union[List[str], str] = 'all'):
    """
    Main function for the pipeline.
    
    Args:
        commentary:
        json_dir: Absolute path to the directory in which to write the json files or take them from.
        xmi_dir: Absolute path to the directory in which to write the xmi files.
        make_jsons: Whether to create canonical jsons. If false, jsons are grepped from json_dir.
        make_xmis: Whether to create xmis.
        region_types: The desired regions to convert to xmis, eg `introduction, preface, commentary, footnote`.   
    """

    # Create paths
    json_dir = json_dir if json_dir else variables.COMMS_DATA_DIR / commentary.id / 'canonical' /commentary.ocr_run
    xmi_dir = xmi_dir if xmi_dir else variables.get_comm_xmi_dir(commentary.id) / commentary.ocr_run

    if make_jsons and make_xmis:
        json_dir.mkdir(parents=True, exist_ok=True)
        xmi_dir.mkdir(parents=True, exist_ok=True)

        for page in tqdm(commentary.children.pages, desc=f'Building jsons and xmis for {commentary.id}'):
            page.to_json(output_dir=json_dir)
            rebuild = basic_rebuild(page.to_canonical_v1(), region_types)
            if len(rebuild['fulltext']) > 0:  # handles the empty-page case
                rebuild_to_xmi(rebuild, xmi_dir)

    elif make_jsons:
        json_dir.mkdir(parents=True, exist_ok=True)
        for page in tqdm(commentary.children.pages, desc=f'Creating jsons for {commentary.id}'):
            logger.debug('Canonizing page  ' + page.id)
            page.to_json(output_dir=json_dir)

    elif make_xmis:
        xmi_dir.mkdir(parents=True, exist_ok=True)

        for json_path in tqdm(json_dir.glob('*.json'), desc=f'Building xmis for {commentary.id}'):
            logger.debug('Xmi-ing page  ' + page['id'])
            page = json.loads(json_path.read_text(encoding='utf-8'))  # Why can't this be done directly from commentary ?
            rebuild = basic_rebuild(page, region_types)
            if len(rebuild['fulltext']) > 0:  # handles the empty-page case
                rebuild_to_xmi(rebuild, xmi_dir)


def get_cas(xmi_path: Path, xml_path: Path) -> 'cassis.Cas':
    typesystem = load_typesystem(xml_path)
    cas = load_cas_from_xmi(xmi_path, typesystem=typesystem)
    return cas


def align_cas_annotation(cas_annotation, rebuild, verbose: bool = False):
    # We define an empty dict to store the annotation.
    bboxes, shifts, warnings = [], [], []

    # We get the annotation's surrounding text
    text_window = f"""{cas_annotation.sofa.sofaString[cas_annotation.begin - 10:cas_annotation.begin]}|\
    {cas_annotation.sofa.sofaString[cas_annotation.begin:cas_annotation.end]}|\
    {cas_annotation.sofa.sofaString[cas_annotation.end:cas_annotation.end + 10]}"""

    # We then find the words included in the annotation and retrieve their bboxes
    ann_words = [{'bbox': bbox, 'offsets': offsets}
                 for bbox, offsets in zip(rebuild['bbox']['words'], rebuild['offsets']['words'])
                 if compute_interval_overlap((cas_annotation.begin, cas_annotation.end), offsets) > 0]

    # If the annotation words are not found in the page dictionary. This is a problem, should not happen
    if not ann_words:
        logger.error(f"""Annotation has no words: {text_window}""")
        warnings = ['no words']

    else:
        bboxes = [ann_word['bbox'] for ann_word in ann_words]
        shifts = [cas_annotation.begin - ann_words[0]['offsets'][0],
                  cas_annotation.end - ann_words[-1]['offsets'][1]]

        if verbose:
            aligned_print(rebuild["fulltext"][ann_words[0]['offsets'][0]:ann_words[-1]['offsets'][1]],
                          cas_annotation.sofa.sofaString[cas_annotation.begin:cas_annotation.end])

    return bboxes, shifts, text_window, warnings


def import_page_rebuild(page_id: str):
    comm_id = page_id.split('_')[0]
    json_path = variables.get_comm_canonical_v1_dir(comm_id) / variables.IDS_TO_RUNS[comm_id]/ (page_id + '.json')
    if comm_id == 'sophoclesplaysa05campgoog' and page_id in variables.MINIREF_PAGES:
        json_path = variables.get_comm_canonical_v1_dir(comm_id) / '1bm0b4_tess_final'/ (page_id + '.json')

    return basic_rebuild(page=json.loads(json_path.read_text('utf-8')), region_types=variables.IDS_TO_REGIONS[comm_id])


def import_page_cas(page_id: str,
                    ajmc_ne_corpus_path: Path = variables.NE_CORPUS_DIR):

    xml_path = ajmc_ne_corpus_path / 'data/preparation/TypeSystem.xml'

    candidate_xmi_paths = list(ajmc_ne_corpus_path.glob(f'data/preparation/corpus/*/curated/{page_id}.xmi'))
    if candidate_xmi_paths:
        xmi_path = candidate_xmi_paths[0]
        return get_cas(xmi_path, xml_path)


def safe_import_page_annotations(page_id,
                                 cas,
                                 rebuild,
                                 annotation_layer: str,
                                 manual_safe_check: bool = False) -> List[FeatureStructure]:

    if manual_safe_check and cas.sofa_string != rebuild['fulltext']:
        print(f'Alignment error, skipping: {page_id}')
        print('REBUILD**************************')
        print(rebuild['fulltext'])
        print('CAS**************************')
        print(cas.sofa_string)
        input('Press enter to continue')

    return cas.select(annotation_layer)

