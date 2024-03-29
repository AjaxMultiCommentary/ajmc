import os
import random

import numpy as np
import yaml

from ajmc.commons.image import AjmcImage
from ajmc.commons.miscellaneous import stream_handler
from ajmc.olr.layoutlm.layoutlm import create_olr_config
from ajmc.olr.utils import get_olr_splits_page_ids
from ajmc.text_processing import canonical_classes

stream_handler.setLevel(0)

base_data_dir = '/mnt/ajmcdata1/drive_cached/AjaxMultiCommentary/data/commentaries/commentaries_data'
base_xp_dir = '/scratch/sven/yolo'
configs_dir = '/scratch/sven/tmp/ajmc/data/yolo/configs'

configs_to_run = [  # '4D_segmonto_fine.json',
    '4E_segmonto_coarse.json'
]
DATASET_NAME = 'multiclass'

for config_name in os.listdir(configs_dir):
    if config_name.endswith('.json') and config_name in configs_to_run:
        print(f'******** Processing {config_name} *********')
        config = create_olr_config(os.path.join(configs_dir, config_name),
                                   prefix=base_data_dir)

        config_dir = os.path.join(base_xp_dir, f'datasets/{DATASET_NAME}', config_name[:-5])
        # Create folders
        abs_paths = {'images': {'train': os.path.join(config_dir, 'images/train'),
                                'eval': os.path.join(config_dir, 'images/eval')},
                     'labels': {'train': os.path.join(config_dir, 'labels/train'),
                                'eval': os.path.join(config_dir, 'labels/eval')}}
        for k, d in abs_paths.items():
            for k_, path in d.items():
                os.makedirs(path, exist_ok=True)

        # Write yaml dataset config :
        yolo_yaml = {
            'path': f'../datasets/{DATASET_NAME}/{config_name[:-5]}',
            'train': 'images/train',
            'val': 'images/eval',
            'nc': config['num_labels'],
            'names': sorted(list(config['labels_to_ids'].keys()))
        }

        with open(os.path.join(config_dir, 'config.yaml'), 'w') as file:
            documents = yaml.dump(yolo_yaml, file)

        for set_, dicts in config['data'].items():

            pages = []
            for dict_ in dicts:  # todo 👁️ why isn't this directly a get_data_dict_pages ?

                # You get the commentary to canonical
                comm = canonical_classes.CanonicalCommentary.from_json(dict_['path'])

                p_ids = get_olr_splits_page_ids(dict_['id'], [dict_['split']])
                pages += [p for p in comm.children.pages if p.id in p_ids]

            if config['sampling']:
                random.seed(42)
                pages = random.sample(pages, k=int(config['sampling'][set_] * len(pages)))

            for p in pages:
                # write page image
                img_name = p.image.path.split('/')[-1]
                p.image.write(os.path.join(abs_paths['images'][set_], img_name))
                # get page labels
                yolo_labels = []
                for r in p.children.regions:
                    if r.region_type in config['rois']:
                        r_coarse_label = config['region_types_to_labels'][r.region_type]
                        r_label_id = config['labels_to_ids'][r_coarse_label]
                        # r_label_id = 0
                        r_width = r.bbox.width / p.image.width
                        r_height = r.bbox.height / p.image.height
                        r_center_x = r.bbox.center[0] / p.image.width
                        r_center_y = r.bbox.center[1] / p.image.height
                        yolo_labels.append(f'{r_label_id} {r_center_x} {r_center_y} {r_width} {r_height}')

                # write page labesl
                with open(os.path.join(abs_paths['labels'][set_], p.image.id + '.txt'), 'w') as f:
                    f.write('\n'.join(yolo_labels))

        # write blank images
        num_blank_pages = 2
        for i in range(num_blank_pages):
            blank_img = AjmcImage(matrix=np.ones(p.image.matrix.shape))
            blank_img.write(os.path.join(abs_paths['images']['train'], f'blank_{i}.png'))
            # write page labels
            with open(os.path.join(abs_paths['labels']['train'], f'blank_{i}.txt'), 'w') as f:
                f.write('')