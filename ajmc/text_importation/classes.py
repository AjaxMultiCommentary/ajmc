import copy
import re
import json
import os
from time import strftime
from typing import Dict, Optional, List, Union, Any
import bs4.element
from ajmc.commons.miscellaneous import lazy_property, get_custom_logger
from ajmc.commons.docstrings import docstring_formatter
from ajmc.commons import variables
from ajmc.commons.geometry import (
    Shape,
    is_rectangle_within_rectangle_with_threshold,
    get_bounding_rectangle_from_points,
    is_rectangle_within_rectangle, are_rectangles_overlapping,
    adjust_to_included_contours
)
from ajmc.commons.image import Image
from ajmc.olr.utils.region_processing import sort_to_reading_order, get_page_region_dicts_from_via
import jsonschema
from ajmc.text_importation.markup_processing import parse_markup_file, get_element_coords, \
    get_element_text, find_all_elements
from ajmc.commons.file_management.utils import verify_path_integrity, parse_ocr_path, get_path_from_id, guess_ocr_format

logger = get_custom_logger(__name__)


class Commentary:
    """`Commentary` objects reprensent a single ocr run of a commentary."""

    def __init__(self,
                 commentary_id: str = None,
                 ocr_dir: str = None,
                 via_path: str = None,
                 image_dir: str = None,
                 groundtruth_dir: str = None,
                 _base_dir: str = None,  # Only useful for Commentary.from_ajmc_structure()

                 ):
        """Default constructor.

        Args:
            commentary_id: The id of the commentary
            ocr_dir: Absolute path to an ocr output folder.
            via_path:
            image_dir:
            groundtruth_dir:
        """
        self.id = commentary_id
        self.paths = {'ocr_dir': ocr_dir,
                      'via_path': via_path,
                      'image_dir': image_dir,
                      'groundtruth_dir': groundtruth_dir,
                      'base_dir': _base_dir}

    @classmethod
    @docstring_formatter(output_dir_format=variables.FOLDER_STRUCTURE_PATHS['ocr_outputs_dir'])
    def from_ajmc_structure(cls, ocr_dir: str):
        """Use this method to construct a `Commentary`-object using ajmc's folder structure.

        Args:
            ocr_dir: Path to the directory in which ocr-outputs are stored. It should end with
            {output_dir_format}.
            commentary_id: for dev purposes only, do not use :)
        """

        verify_path_integrity(path=ocr_dir, path_pattern=variables.FOLDER_STRUCTURE_PATHS['ocr_outputs_dir'])
        base_dir, commentary_id, ocr_run = parse_ocr_path(path=ocr_dir)

        return cls(commentary_id=commentary_id,
                   ocr_dir=ocr_dir,
                   via_path=os.path.join(base_dir, commentary_id, variables.PATHS['via_path']),
                   image_dir=os.path.join(base_dir, commentary_id, variables.PATHS['png']),
                   groundtruth_dir=os.path.join(base_dir, commentary_id, variables.PATHS['groundtruth']),
                   _base_dir=base_dir)

    @classmethod
    @docstring_formatter()
    def from_custom_paths(cls,
                          commentary_id: str = None,
                          ocr_dir: str = None,
                          via_path: str = None,
                          image_dir: str = None,
                          groundtruth_dir: str = None,
                          ):
        """Construct a `Commentary`-object using custom paths.

        This is usefull when you want to instantiate a `Commentary` without using `ajmc`'s folder structure. Note that
        only the requested paths must be provided. For instance, the object will be created if you do not provided the
        path to the images. But logically, you won't be able to access fonctionnalities that requires it (for instance
        `Commentary.pages[0].image`).

        Args:
            commentary_id:
            ocr_dir: Path to the directory in which ocr-outputs are stored.
            via_path:
            image_dir:
            groundtruth_dir:

        """

        return cls(commentary_id=commentary_id,
                   ocr_dir=ocr_dir,
                   via_path=via_path,
                   image_dir=image_dir,
                   groundtruth_dir=groundtruth_dir)

    @classmethod
    def from_canonical(cls, canonical_path: str):
        """Constructs a `Commentary` object from a canonical json."""

        # Read json
        with open(canonical_path, 'r') as file:
            canonical = json.load(file)

        # Create object distribute attributes
        # todo : continue to distribute objects here (words etc)
        return cls(commentary_id=canonical['id'],
                   pages=[Page.from_canonical(p) for p in canonical['pages']])

    @lazy_property
    def pages(self) -> List['Page']:
        """The pages contained in the commentaries"""
        pages = []
        for file in [f for f in os.listdir(self.paths['ocr_dir']) if f[-4:] in ['.xml', 'hocr', 'html']]:
            pages.append(Page(ocr_path=os.path.join(self.paths['ocr_dir'], file),
                              page_id=file.split('.')[0],
                              groundtruth_path=get_path_from_id(file.split('.')[0], self.paths['groundtruth_dir']),
                              image_path=get_path_from_id(file.split('.')[0], self.paths['image_dir']),
                              via_path=self.paths['via_path'],
                              commentary=self))

        return sorted(pages, key=lambda x: x.id)

    @lazy_property
    def ocr_groundtruth_pages(self) -> Union[List['Page'], list]:
        """The commentary's pages which have a groundtruth file in `self.paths['groundtruth']`."""
        pages = []
        for file in [f for f in os.listdir(self.paths['groundtruth_dir']) if f.endswith('.html')]:
            pages.append(Page(ocr_path=os.path.join(self.paths['groundtruth_dir'], file),
                              page_id=file.split('.')[0],
                              groundtruth_path=None,
                              image_path=get_path_from_id(file.split('.')[0], self.paths['image_dir']),
                              via_path=self.paths['via_path'],
                              commentary=self))

        return sorted(pages, key=lambda x: x.id)

    @lazy_property
    def regions(self):
        return [r for p in self.pages for r in p.regions]

    @lazy_property
    def lines(self):
        return [l for p in self.pages for l in p.lines]

    @lazy_property
    def words(self):
        return [w for p in self.pages for w in p.words]

    @lazy_property
    def via_project(self) -> dict:
        with open(self.paths['via_path'], 'r') as file:
            return json.load(file)

    def to_canonical(self):

        for page in self.pages:
            pass


class Page:
    """A class representing a commentary page."""

    def __init__(self,
                 page_id: str,
                 ocr_path: str,
                 commentary: Commentary = None,
                 groundtruth_path: Optional[str] = None,
                 image_path: Optional[str] = None,
                 words: Optional[str] = None):  # todo finish this with all the requested blabla
        """Default constructor.

        Args:
            ocr_path: Absolute path to an OCR output file
            commentary: The commentary to which the page belongs.
        """

        self.id = page_id
        self.commentary = commentary
        self.paths = {
            'ocr_path': ocr_path,
            'groundtruth_path': groundtruth_path,
            'image_path': image_path,
        }

    # Todo : implement
    @classmethod
    def from_ocr(cls, ocr_path):
        raise NotImplementedError

    # Todo : implement
    @classmethod
    def from_canonical(cls, canonical_path):
        raise NotImplementedError

    @lazy_property
    def ocr_format(self) -> str:
        return guess_ocr_format(self.paths['ocr_path'])

    @lazy_property
    def regions(self):
        """Gets page regions, removing empty regions and reordering them."""
        return [Region(r, self) for r in get_page_region_dicts_from_via(self.id, self.commentary.via_project)]

    @lazy_property
    def lines(self) -> List['Line']:
        return [Line(markup=line, page=self, ocr_format=self.ocr_format)
                for line in find_all_elements(self.markup, 'lines', self.ocr_format)]

        # todo : this belongs in central page coords optim.
        # return [l for l in lines if re.sub(r'\s+', '', l.text) != '']  # Remove empty words

    @lazy_property
    def words(self) -> List['Word']:
        return [w for l in self.lines for w in l.words]

    @lazy_property
    def image(self) -> Image:
        return Image(path=self.paths['image_path'])

    @lazy_property
    def text(self) -> str:
        return '\n'.join([line.text for line in self.lines])

    @lazy_property
    def markup(self) -> bs4.BeautifulSoup:
        return parse_markup_file(self.paths['ocr_path'])

    @lazy_property
    def canonical_data(self) -> Dict[str, Any]:
        data = {'id': self.id,
                'iiif': 'None',
                'cdate': strftime('%Y-%m-%d %H:%M:%S'),
                'regions': []}

        for r in self.regions:
            r_dict = {'region_type': r.region_type,
                      'coords': r.coords.xywh,
                      'lines': [
                          {
                              'coords': line.coords.xywh,
                              'words': [
                                  {
                                      'coords': word.coords.xywh,
                                      'text': word.text
                                  } for word in line.words
                              ]

                          } for line in r.lines
                      ]
                      }
            data['regions'].append(r_dict)

        return data

    def to_json(self, output_dir: str, schema_path: str = variables.PATHS['schema']):
        """Validate `self.canonical_data` & serializes it to json."""

        with open(schema_path, 'r') as file:
            schema = json.loads(file.read())

        jsonschema.validate(instance=self.canonical_data, schema=schema)

        with open(os.path.join(output_dir, self.id + '.json'), 'w') as f:
            json.dump(self.canonical_data, f, indent=4, ensure_ascii=False)

    def readjust_coords(self, word_inclusion_threshold):
        # This assumes we are starting from the untouched OCR output

        # Process lines and words
        lines = []
        for l in self.lines:
            l._words = [w for w in l.words if re.sub(r'\s+', '', w.text) != '']  # Remove empty words
            if l.words:  # Removes empty lines
                for w in l.words:  # Adjust word boxes
                    w._coords = adjust_to_included_contours(w.coords.bounding_rectangle, self.image.contours)
                # adjust line boxes
                l._coords = Shape.from_points([xy for w in l.words for xy in w.coords.bounding_rectangle])
                lines.append(l)
        self._lines = lines

        # Process regions
        # Readjust region coords with contained words
        for r in self.regions:
            words = [w for w in self.words
                     if is_rectangle_within_rectangle_with_threshold(contained=w.coords.bounding_rectangle,
                                                                     container=r.coords.bounding_rectangle,
                                                                     threshold=word_inclusion_threshold)]

            # resize region
            words_points = [xy for w in words for xy in w.coords.bounding_rectangle]
            r._coords = Shape(get_bounding_rectangle_from_points(words_points)) if words_points else r.coords

        self._regions = [r for r in self.regions if not (r.region_type == 'undefined' and not r.words)]
        self._regions = sort_to_reading_order(regions=self.regions)


        # Cut lines according to regions
        for r in self.regions:
            if r.region_type not in ['undefined', 'line_number_commentary']:
                r._lines = []

                for l in self.lines:
                    # If the line is entirely in the region, append it
                    if is_rectangle_within_rectangle(contained=l.coords.bounding_rectangle,
                                                     container=r.coords.bounding_rectangle):
                        r._lines.append(l)

                    # If the line is only partially in the region, handle the line splitting problem.
                    elif any([is_rectangle_within_rectangle(w.coords.bounding_rectangle, r.coords.bounding_rectangle)
                              for w in l.words]):

                        # Create the new line and append it both to region and page lines
                        l_ = copy.copy(l)
                        l_._words = [w for w in l.words if is_rectangle_within_rectangle(w.coords.bounding_rectangle,
                                                                                         r.coords.bounding_rectangle)]
                        l_._coords = Shape.from_points([xy for w in l_.words for xy in w.coords.bounding_rectangle])
                        r._lines.append(l_)
                        self._lines.append(l_)

                        # Actualize the old line
                        l._words = [w for w in l.words if w not in l_]
                        l._coords = Shape.from_points([xy for w in l.words for xy in w.coords.bounding_rectangle])

        # Actualize reading order
        self._lines = sort_to_reading_order(self.lines)
        self._words = [w for l in self.lines for w in l.words]




# Todo : check that you select only words which are not empty
# Todo : check that you select only lines which are not empty
# Todo : check that you select only regions which are not empty


class Region:
    """A class representing OLR regions extracted from a via project.

    Attributes:
        via_dict (dict):
            The via-dict, as extracted from the commentary's via_project. It should look like :

                $ { 'shape_attributes': {'name': 'rect', 'x': 31, 'y': 54, 'width': 1230, 'height': 453},
                    'region_attributes': {'text': 'preface'} }

        region_type (str):
            The type of the region, e.g. 'page_number', 'introduction'...
        coords (Shape):
            The actualized coordinates of the region, corresponding to the bounding rectangle of included words.
        page:
            The `PageXmlCommentaryPage` object to which the region belongs
        words (List[ElementType]):
            The words included in the region.
    """

    def __init__(self, via_dict: Dict[str, dict], page: 'Page'):
        self.region_type = via_dict['region_attributes']['text']
        self.page = page
        self.markup = via_dict
        self._line_inclusion_threshold = 0.9
        self._word_inclusion_threshold = 0.7

    # =================== Parents and children ================
    @lazy_property
    def lines(self):
        # Todo : This should not be available for raw regions
        return [l for l in self.page.lines
                if is_rectangle_within_rectangle_with_threshold(contained=l.coords.bounding_rectangle,
                                                                container=self.coords.bounding_rectangle,
                                                                threshold=self._line_inclusion_threshold)]

    @lazy_property
    def words(self):
        return [w for w in self.page.words
                if is_rectangle_within_rectangle_with_threshold(contained=w.coords.bounding_rectangle,
                                                                container=self.coords.bounding_rectangle,
                                                                threshold=self._word_inclusion_threshold)]

    @lazy_property
    def coords(self):
        """Automatically readjusts the region coordinates, so that exactly fit the words contained in the region.

                This is done by :

                        1. Finding the words in the region's page which are contained in the region's initial via_coords.
                        This is done using `is_rectangle_partly_within_rectangle` with `word_inclusion_threshold`.
                        2. Actualizing the coords to fit the exact bounding rectangle of contained words."""
        return Shape.from_xywh(x=self.markup['shape_attributes']['x'],
                               y=self.markup['shape_attributes']['y'],
                               w=self.markup['shape_attributes']['width'],
                               h=self.markup['shape_attributes']['height'])

        # todo add this in central
        # included_words = [w for w in self.page.words
        #                   if is_rectangle_within_rectangle_with_threshold(w.coords.bounding_rectangle,
        #                                                                   raw_coords.bounding_rectangle,
        #                                                                   0.7)]
        # words_points = [xy for w in included_words for xy in w.coords.bounding_rectangle]
        #
        # return Shape(get_bounding_rectangle_from_points(words_points)) if words_points else raw_coords

    @lazy_property
    def image(self):
        return self.page.image.crop(self.coords.bounding_rectangle)

    @lazy_property
    def text(self):
        return '\n'.join([l.text for l in self.lines])

    # todo implement this centrally
    def get_readjusted_lines(self) -> List['Line']:
        """Readjusts region lines to fit only the words of a line that are actually contained within the region.

        Goes through page-level lines to find the lines that overlap with the region. If there is an overlap, makes a
        copy of the lines and finds the words in the line that are contained in the region, then shrinks the lines
        coordinates to fit only the contained words.

        Note:
            This is mostly used to circumvent the double-column lines issue. Please we aware that page.lines will then
            be different from `[region.lines for region in page.regions]`, as this procedure does not changes page
            lines."""

        region_lines = []
        for line in self.page.lines:
            if are_rectangles_overlapping(line.coords.bounding_rectangle, self.coords.bounding_rectangle):
                line_ = copy.copy(line)
                line_._words = []
                for word in line.words:
                    if is_rectangle_within_rectangle(word.coords.bounding_rectangle,
                                                     self.coords.bounding_rectangle):
                        line_._words.append(word)

                if line_._words:
                    line_points = [xy for w in line_._words for xy in w.coords.bounding_rectangle]
                    line_._coords = Shape(get_bounding_rectangle_from_points(line_points)) \
                        if line_points else Shape.from_points([(0, 0)])
                    region_lines.append(line_)

        return region_lines


class Line:
    """Class for lines."""

    def __init__(self, markup: 'bs4.element.Tag', page: Page, ocr_format: str):
        self.markup = markup
        self.page = page
        self.ocr_format = ocr_format

    @lazy_property
    def coords(self):  # Are readjusted to word bounding boxes, themselves readjusted to contours
        return get_element_coords(self.markup, self.ocr_format)

    @lazy_property
    def image(self):
        return self.page.image.crop(self.coords.bounding_rectangle)

    @lazy_property
    def words(self):
        return [Word(el, self.page, self.ocr_format)
                for el in find_all_elements(self.markup, 'words', self.ocr_format)]

    @lazy_property
    def text(self):
        return ' '.join([w.text for w in self.words])


class Word:
    """Class for Words."""

    def __init__(self, markup: 'bs4.element.Tag', page: Page, ocr_format: str):
        self.markup = markup
        self.page = page
        self.ocr_format = ocr_format

    @classmethod  # todo : implement
    def from_canonical(cls, canonical: dict):
        raise NotImplementedError

    @lazy_property
    def coords(self) -> Shape:
        return get_element_coords(self.markup, self.ocr_format)

    @lazy_property
    def image(self):
        return self.page.image.crop(self.coords.bounding_rectangle)

    @lazy_property
    def text(self):
        return get_element_text(self.markup, self.ocr_format)
