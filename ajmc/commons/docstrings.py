"""This file contains generic docstring chunks to be formatted using``docstring_formatter``."""


def docstring_formatter(**kwargs):
    """Decorator with arguments used to format the docstring of a functions.

    ``docstring_formatter`` is a decorator with arguments, which means that it takes any set of ``kwargs`` as argument and
    returns a decorator. It should therefore always be called with parentheses (unlike traditional decorators - see
    below). It follows the grammar of ``str.format()``, i.e. ``{my_format_value}``.
    grammar.

    Example:

        This code snippet:

        .. code-block:: Python

            @docstring_formatter(greeting = 'hello')
            def my_func():
                "A simple greeter that says {greeting}"
                # Do your stuff

        Is actually equivalent with :

        .. code-block:: Python

            def my_func():
                "A simple greeter that says {greeting}"
                # Do your stuff

            my_func.__doc__ = my_func.__doc__.format(greeting = 'hello')

    Note:
        Best practice is to name your arguments in compliance with ``docstrings.docstrings`` in order to simply call
        ``@doctring_formatter(**docstrings.docstrings)``.

    """

    def inner_decorator(func):
        func.__doc__ = func.__doc__.format(**kwargs)
        return func

    return inner_decorator


docstrings = dict()  # Creating docstrings on the fly in order to refer to previously declared elements.

docstrings['artifact_size_threshold'] = f"""Size-threshold under which contours are to be considered as artifacts and removed, expressed as a \
percentage of image height. Default is 0.003"""

docstrings['BatchEncoding'] = """The default ouput of HuggingFace's ``TokenizerFast``. As the \
`docs <https://huggingface.co/docs/transformers/v4.19.2/en/main_classes/tokenizer#transformers.BatchEncoding>`_ have it, *"This class is derived from \
a python dictionary and can be used as a dictionary. In addition, this class exposes utility methods to map from word/character space to token \
space"*. The object contains ``data`` and ``encodings``. Data is directly callable and has the form of a ``Dict[str, List[List[int]]]`` where keys \
are model inputs. Encodings is a list of example, containing notably the offsets. Please note that not using a ``TokenizerFast`` (i.e. using a \
``Tokenizer`` instead) can lead to the cumbersome situation in which ``self.encodings`` is set to ``None``.""",

docstrings['root_dir'] = """``commentaries_data`` root directory. Use variables.COMMS_DATA_DIR to access the default value."""

docstrings['bbox'] = """A tuple of two (x, y) tuples representing upper-left and lower-right coordinates."""

docstrings['children_type'] = """The type of children to get. Must be one of ``pages``, ``regions``, ``lines`` or ``words``."""

docstrings[
    'commentary_id'] = """The id of the commentary (e.g. sophoclesplaysa05campgoog). Ids are listed in ``ajmc.commons.variables.ALL_COMM_IDS``."""

docstrings['coords_single'] = 'A ``Shape`` object representing the coordinates of the object.'

docstrings['comms_root_dir'] = """The base directory a commentaries data, normally ``variables.COMMS_DATA_DIR / [comm_id]``. Use \
``variables.get_comm_root_dir()`` to retrieve it."""

docstrings['custom_dataset'] = """A dataset inheriting from ``torch.utils.data.Dataset``, implementing at least ``__len__`` and \
``__getitem__()``, where each item is a dict alike ``{{'model_input': tensor(), ...}}`` corresponding \
to a single example."""

docstrings['dilation_kernel_size'] = """Dilation kernel size, preferably an odd number. Tweak \
this parameter and ``dilation_iterations`` to improve automatic boxing. Starting with 25 is recommended."""

docstrings['dilation_iterations'] = 'Number of iterations in dilation, default 1'

docstrings['directory'] = 'The absolute path to the directory'

docstrings['do_debug'] = """Whether break loops after the first iteration."""

docstrings['groundtruth_dir'] = 'The absolute path to the directory containg groundtruth files.'

docstrings['ids_to_labels'] = """A dict mapping the label numbers (int) used by the model \
to the original label names (str), e.g. ``{{0: "O", 1: "B-PERS", ...}}``"""

docstrings['image_dir'] = 'The absolute path to the directory containing the images.'

docstrings['image_path'] = 'The absolute path to the image.'

docstrings['img_extension'] = """The extension of image files, including the ``.``, e.g. ``'.png'`` or ``'.jpg'``."""

docstrings['interval'] = 'A ``Tuple[int, int]`` defining the included boundaries of an interval, with start <= stop.'

docstrings['kwargs_for_properties'] = 'Use **kwargs to manually set or override properties.'

docstrings['labels_to_ids'] = 'A dict mapping label-names to their respective ids, e.g. ``{{"cat":0, "dog":1, ...}}``.'

docstrings['ocr_dir'] = 'The absolute path to the directory containing OCR outputs.'

docstrings['ocr_path'] = 'The absolute path to an ocr output file.'

docstrings['ocr_run_id'] = """The id of an ocr-run, e.g. '28o09e_tess_base', (generally follow the pattern \
'{get_62_based_datecode()}_{ocr_engine}_{ocr_model}')."""

docstrings['olr_region_type'] = """The type of the Region (i.e. ``'primary_text'`` or ``'commentary'``)."""

docstrings['parent_page'] = """"The ``RawPage`` containing the object"""

docstrings['parent_type'] = """"The type of the parent object. Must be one of ``commentary``, ``page``, ``region`` or ``line``."""

docstrings['path'] = 'The absolute path'

docstrings['point'] = 'Iterable containing x and y coordinates (e.g. ``(123, 87)``'

docstrings['points'] = f"""Iterable of iterable containing x-y points (e.g. ``[(12,8), (15,16), ...]``. """

docstrings['transformers_model'] = """A ``transformers.models``."""

docstrings['transformers_model_inputs_names'] = """The name of the inputs required by the model, e.g. ``['input_ids', 'attention_mask',...]``."""

docstrings['transformers_model_inputs'] = """A mapping to between the names of the model's requirements and ``torch.Tensor`` of size \
(max_length, batch_size).
    Example: 
        ``{'input_ids': torch.tensor([[int, int, ...], [int, int, ...]])``."""

docstrings['transformers_model_predictions'] = """``np.ndarray`` containing the predicted labels, so in the shape (number of exs, length of an ex)."""

docstrings['max_length'] = 'The maximum length of a sequence to be processed by the model.'

docstrings['sections_path'] = 'The absolute path to the sections json-file.'

docstrings['sheet_id'] = """The id of the spreadsheet, i.e. the part of the url after 'spreadsheets/d/'. Check ``commons.variables.SPREADSHEET_IDS`` \
for examples."""

docstrings['sheet_name'] = """The name of the sheet in the spreadsheet, for instance 'Sheet1' or ``olr_gt``."""

docstrings['special_tokens'] = """LEGACY. A dict containing the model's special token for sequence start, end and pad, for instance \
``{{'start': {{'input_ids':100, ...}}, ...}}``"""

docstrings['via_dict'] = """A via-json compliant dict. Should look like:

    .. code-block:: python
    
        { 'shape_attributes': {'name': 'rect', 'x': 31, 'y': 54, 'width': 1230, 'height': 453}, 
        'region_attributes': {'text': 'preface'} 
"""

docstrings['via_path'] = 'The absolute path to the via_project json.'

docstrings['via_project'] = """A dictionary resulting from the reading of a via_project JSON file. Visit \
https://www.robots.ox.ac.uk/~vgg/software/via/ for more information."""

docstrings['word_range'] = """A tuple of two ints representing the start and end of the object in the commentary's text."""
