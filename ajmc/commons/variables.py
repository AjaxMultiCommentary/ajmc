import os
import re
from typing import Tuple

# ======================================================================================================================
#                                                 TYPES
# ======================================================================================================================
BoxType = Tuple[Tuple[int, int], Tuple[int, int]]

# ======================================================================================================================
#                                                 PATHS
# ======================================================================================================================

# Todo change paths
EXEC_ENV = 'cluster' #cluster or drive or local

PATHS = {
    'local_base_dir': '/Users/sven/drive/_AJAX/AjaxMultiCommentary/data/commentaries/commentaries_data',
    'drive_base_dir': '/content/drive/MyDrive/_AJAX/AjaxMultiCommentary/data/commentaries/commentaries_data',
    'cluster_base_dir': '/mnt/ajmcdata1/drive_cached/AjaxMultiCommentary/data/commentaries/commentaries_data',
    'schema': 'ajmc/data/templates/page.schema.json',
    'groundtruth': 'ocr/groundtruth',
    'png': 'images/png',
    'via_path': 'olr/via_project.json',
    'json': 'canonical',
    'xmi': 'ner/annotation',
    'typesystem': 'ajmc/data/templates/TypeSystem.xml',
    'olr_initiation': 'olr/annotation/project_initiation',
    'ocr': 'ocr/runs',
    'canonical': 'canonical/v2',
    'annotations': 'ner/entities',
    'ajmc_ne_corpus': '/Users/sven/drive/_AJAX/AjaxMultiCommentary/data/AjMC-NE-corpus',
    'ocr_gt_file_pairs': 'ocr/gt_file_pairs',
}
PATHS['base_dir'] = PATHS[f'{EXEC_ENV}_base_dir']
# PATHS['temp_dir'] = os.getenv('TMPDIR')

# Sheet names corresponds to the dictionary's keys
SPREADSHEETS = {
    'metadata': '1jaSSOF8BWij0seAAgNeGe3Gtofvg9nIp_vPaSj5FtjE',
    'olr_gt': '1_hDP_bGDNuqTPreinGS9-ShnXuXCjDaEbz-qEMUSito',
    'ocr_gt': '1RsJQTgM4oO-ds0cK3rstx-iBxsvxjwCSVRWS63NvQrQ'
}

FOLDER_STRUCTURE_PATHS = {
    # Only relative paths
    # Placeholder pattern are between []
    'ocr_outputs_dir': '[commentary_id]/ocr/runs/[ocr_run]/outputs',
    'canonical_json': '[commentary_id]/canonical/v2/[json]'
}

# ======================================================================================================================
#                                                 COMMENTARIES
# ======================================================================================================================

ALL_COMMENTARY_IDS = ['Colonna1975', 'DeRomilly1976', 'Ferrari1974', 'Finglass2011', 'Garvie1998', 'Kamerbeek1953',
                      'Paduano1982', 'Untersteiner1934', 'Wecklein1894', 'bsb10234118', 'cu31924087948174',
                      'lestragdiesdeso00tourgoog', 'sophoclesplaysa05campgoog', 'sophokle1v3soph', 'thukydides02thuc',
                      'pvergiliusmaroa00virggoog', 'annalsoftacitusp00taci']

EXTERNAL_COMMENTARY_IDS = ['thukydides02thuc', 'pvergiliusmaroa00virggoog', 'annalsoftacitusp00taci']

PD_COMMENTARY_IDS = ['bsb10234118', 'cu31924087948174', 'sophoclesplaysa05campgoog', 'sophokle1v3soph', 'Wecklein1894']

SAMPLE_PAGES = ['bsb10234118_0096', 'sophokle1v3soph_0126', 'cu31924087948174_0063', 'cu31924087948174_0063',
                'Wecklein1894_0087']

COMMENTARY_IDS_TO_LANG = {
    'Colonna1975': 'ita',
    'DeRomilly1976': 'fra',
    'Ferrari1974': 'ita',
    'Finglass2011': 'eng',
    'Garvie1998': 'eng',
    'Kamerbeek1953': 'eng',
    'Paduano1982': 'ita',
    'Untersteiner1934': 'ita',
    'Wecklein1894': 'deu',
    'bsb10234118': 'deu',
    'cu31924087948174': 'eng',
    'lestragdiesdeso00tourgoog': 'fra',
    'sophoclesplaysa05campgoog': 'eng',
    'sophokle1v3soph': 'deu',
    'thukydides02thuc': 'deu',
    'pvergiliusmaroa00virggoog': 'deu',
    'annalsoftacitusp00taci': 'eng'
}
# ======================================================================================================================
#                                                 LAYOUT
# ======================================================================================================================

ORDERED_OLR_REGION_TYPES = ['commentary',
                            'primary_text',
                            'preface',
                            'translation',
                            'introduction',
                            'line_number_text',
                            'line_number_commentary',
                            'page_number',
                            'appendix',
                            'app_crit',
                            'bibliography',
                            'footnote',
                            'index',
                            'running_header',
                            'table_of_contents',
                            'title',
                            'printed_marginalia',
                            'handwritten_marginalia',
                            'other',
                            'undefined',
                            'line_region',  # added only to make sure every word has a region
                            ]

EXCLUDED_REGION_TYPES = ['line_number_commentary', 'handwritten_marginalia', 'undefined', 'line_region']
ROIS = [rt for rt in ORDERED_OLR_REGION_TYPES if rt not in EXCLUDED_REGION_TYPES]

REGION_TYPES_TO_COARSE_LABELS = {
    # Commentary
    'commentary': 'commentary',
    # Primary text
    'primary_text': 'primary_text',
    # Footnotes
    'footnote': 'footnote',
    # Running header
    'running_header': 'running_header',
    # Paratext
    'preface': 'paratext',
    'introduction': 'paratext',
    'appendix': 'paratext',
    # Numbers
    'line_number_text': 'numbers',
    'line_number_commentary': 'numbers',
    'page_number': 'numbers',
    # App Crit
    'app_crit': 'app_crit',
    # Others
    'translation': 'others',
    'bibliography': 'others',
    'index': 'others',
    'table_of_contents': 'others',
    'title': 'others',
    'printed_marginalia': 'others',
    'handwritten_marginalia': 'others',
    'other': 'others',
    'undefined': 'others',
    'line_region': 'others'
}

REGION_TYPES_TO_FINE_LABELS = {k: k for k in REGION_TYPES_TO_COARSE_LABELS.keys()}

VIA_CSV_DICT_TEMPLATE = {'filename': [],
                         'file_size': [],
                         'file_attributes': [],
                         'region_count': [],
                         'region_id': [],
                         'region_shape_attributes': [],
                         'region_attributes': []}

REGION_TYPES_TO_SEGMONTO = {
    'commentary': 'MainZone:commentary',
    'primary_text': 'MainZone:primaryText',
    'preface': 'MainZone:preface',
    'translation': 'MainZone:translation',
    'introduction': 'MainZone:introduction',
    'line_number_text': 'NumberingZone:textNumber',
    'line_number_commentary': '',
    'page_number': 'NumberingZone:pageNumber',
    'appendix': 'MainZone:appendix',
    'app_crit': 'MarginTextZone:criticalApparatus',
    'bibliography': 'MainZone:bibliography',
    'footnote': 'MarginTextZone:footnote',
    'index_siglorum': 'MainZone:index',
    'running_header': 'RunningTitleZone',
    'table_of_contents': 'MainZone:ToC',
    'title': 'TitlePageZone',
    'printed_marginalia': 'MarginTextZone:printedNote',
    'handwritten_marginalia': 'MarginTextZone:handwrittenNote',
    'other': 'CustomZone:other',
    'undefined': 'CustomZone:undefined',
    'line_region': 'CustomZone:line_region'
}

SEGMONTO_TO_VALUE_IDS = {
    'MainZone:commentary': 'BT01',
    'MainZone:primaryText': 'BT02',
    'MainZone:preface': 'BT03',
    'MainZone:translation': 'BT04',
    'MainZone:introduction': 'BT05',
    'NumberingZone:textNumber': 'BT06',
    'NumberingZone:pageNumber': 'BT07',
    'MainZone:appendix': 'BT08',
    'MarginTextZone:criticalApparatus': 'BT09',
    'MainZone:bibliography': 'BT10',
    'MarginTextZone:footnote': 'BT11',
    'MainZone:index': 'BT12',
    'RunningTitleZone': 'BT13',
    'MainZone:ToC': 'BT14',
    'TitlePageZone': 'BT15',
    'MarginTextZone:printedNote': 'BT16',
    'MarginTextZone:handwrittenNote': 'BT17',
    'CustomZone:other': 'BT18',
    'CustomZone:undefined': 'BT19',
    'CustomZone:line_region': 'BT20',
    'CustomZone:weird': 'BT21',
}

# ======================================================================================================================
#                                                 TEXT CONTAINERS
# ======================================================================================================================

TEXTCONTAINER_TYPES = ['commentary',
                       'section',
                       'page',
                       'region',
                       'sentence',
                       'line',
                       'hyphenation',
                       'entity',
                       'word']

TC_TYPES_TO_CHILD_TYPES = {t: t + 's' if t[-1] != 'y' else t[:-1] + 'ies' for t in TEXTCONTAINER_TYPES}

CHILD_TYPES = list(TC_TYPES_TO_CHILD_TYPES.values())

# ======================================================================================================================
#                                                 ANNOTATIONS
# ======================================================================================================================

MINIREF_PAGES = [
    'cu31924087948174_0035',
    'cu31924087948174_0063',
    'sophoclesplaysa05campgoog_0014',
    'sophoclesplaysa05campgoog_0146',
    'sophoclesplaysa05campgoog_0288',
    'Wecklein1894_0007',
    'Wecklein1894_0016',
    'Wecklein1894_0080',
    'Wecklein1894_0087',
    'sophokle1v3soph_0017',
    'sophokle1v3soph_0049',
    'sophokle1v3soph_0085',
    'sophokle1v3soph_0125',
]

LINKAGE_MINIREF_PAGES = [
    'annalsoftacitusp00taci_0210',
    'annalsoftacitusp00taci_0211',
    'bsb10234118_0090',
    'bsb10234118_0115',
    'cu31924087948174_0063',
    'cu31924087948174_0152',
    'DeRomilly1976_0032',
    'DeRomilly1976_0088',
    'Ferrari1974_0050',
    'Ferrari1974_0115',
    'Garvie1998_0224',
    'Garvie1998_0257',
    'Kamerbeek1953_0098',
    'Kamerbeek1953_0099',
    'lestragdiesdeso00tourgoog_0113',
    'lestragdiesdeso00tourgoog_0120',
    'Paduano1982_0195',
    'Paduano1982_0214',
    'pvergiliusmaroa00virggoog_0199',
    'pvergiliusmaroa00virggoog_0200',
    'sophoclesplaysa05campgoog_0094',
    'sophoclesplaysa05campgoog_0095',
    'sophokle1v3soph_0047',
    'sophokle1v3soph_0062',
    'thukydides02thuc_0009',
    'thukydides02thuc_0011',
    'Untersteiner1934_0104',
    'Untersteiner1934_0105',
    'Wecklein1894_0016',
    'Wecklein1894_0024',
]

IDS_TO_RUNS = {  # Maps commentary_ids to the ocr_run_id used as a base in the annotation campaign.
    'cu31924087948174': '1bm0b3_tess_final',
    'lestragdiesdeso00tourgoog': '21i0dA_tess_hocr',
    'sophokle1v3soph': '1bm0b5_tess_final',
    'sophoclesplaysa05campgoog': '15o0dN_lace_retrained_sophoclesplaysa05campgoog-2021-05-24-08-15-12-porson-with-sophoclesplaysa05campgoog-2021-05-23-22-17-38',
    'Wecklein1894': '1bm0b6_tess_final'
}
IDS_TO_REGIONS = {  # Maps commentary_ids to the region_types used in the annotation campaign.
    'cu31924087948174': ['commentary', 'introduction', 'preface'],
    'Wecklein1894': ['commentary', 'introduction', 'preface'],
    'sophokle1v3soph': ['commentary', 'introduction', 'preface'],
    'sophoclesplaysa05campgoog': ['commentary', 'introduction', 'preface', 'footnote'],
    'lestragdiesdeso00tourgoog': ['commentary', 'introduction', 'preface', 'footnote']
}

ANNOTATION_LAYERS = {
    'entities': 'webanno.custom.AjMCNamedEntity',
    'segments': 'de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence',
    'sentences': 'webanno.custom.GoldSentences',
    'hyphenations': 'webanno.custom.GoldHyphenation',
    'tokens': 'de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token',
}

# ======================================================================================================================
#                                                 AESTHETICS
# ======================================================================================================================

COLORS = {
    # https://coolors.co/b2001e-f02282-461e44-3b9ff1-37507d-125b4f-98e587-ffc802-af7159-b5a267
    'distinct': {
        'red': (178, 0, 30),
        'pink': (240, 34, 130),
        'blue': (59, 159, 241),
        'green': (152, 229, 135),
        'yellow': (255, 200, 2),
        'brown': (175, 113, 89),
        'dark_green': (18, 91, 79),
        'purple': (70, 30, 68),
        'dark_blue': (55, 80, 125),
        'ecru': (181, 162, 103),
    },
    # https://coolors.co/f72585-b5179e-7209b7-560bad-480ca8-3a0ca3-3f37c9-4361ee-4895ef-4cc9f0
    'hues': {
        'pink': (247, 37, 133),
        'byzantine': (181, 23, 158),
        'purple1': (114, 9, 183),
        'purple2': (86, 11, 173),
        'trypan_blue1': (72, 12, 168),
        'trypan_blue2': (58, 12, 163),
        'persian_blue': (63, 55, 201),
        'ultramarine_blue': (67, 97, 238),
        'dodger_blue': (72, 149, 239),
        'vivid_sky_blue': (76, 201, 240)
    }
    # Other color palettes
    # https://coolors.co/97dffc-93caf6-8eb5f0-858ae3-7364d2-613dc1-5829a7-4e148c-461177-3d0e61
    # https://coolors.co/b7094c-a01a58-892b64-723c70-5c4d7d-455e89-2e6f95-1780a1-0091ad
    # https://coolors.co/0081a7-00afb9-fdfcdc-fed9b7-f07167
}

TEXTCONTAINERS_TYPES_TO_COLORS = {
    'word': COLORS['hues']['pink'],
    'line': COLORS['hues']['byzantine'],
    'region': COLORS['hues']['purple1'],
    'page': COLORS['hues']['purple2'],
    'entity': COLORS['hues']['trypan_blue1'],
    'hyphenation': COLORS['hues']['trypan_blue2'],
    'sentence': COLORS['hues']['persian_blue'],
}

REGION_TYPES_TO_COLORS = {l: c for l, c in zip(ORDERED_OLR_REGION_TYPES,
                                               list(COLORS['distinct'].values()) + list(COLORS['hues'].values()))}

# ======================================================================================================================
#                                                 MISC
# ======================================================================================================================


PARAMETERS = {
    'ocr_region_inclusion_threshold': 0.7,
    'entity_inclusion_threshold': 0.8,
}

CHARSETS = {
    'latin': re.compile(r'([A-Za-z]|[\u00C0-\u00FF]|\u0152|\u0153)', re.UNICODE),
    'greek': re.compile(r'([\u0373-\u03FF]|[\u1F00-\u1FFF]|\u0300|\u0301|\u0313|\u0314|\u0345|\u0342|\u0308)',
                        re.UNICODE),
    'numbers': re.compile(r'([0-9])', re.UNICODE),
    'punctuation': re.compile(r'([\u0020-\u002F]|[\u003A-\u003F]|[\u005B-\u0060]|[\u007B-\u007E]|\u00A8|\u00B7)',
                              re.UNICODE)
}
