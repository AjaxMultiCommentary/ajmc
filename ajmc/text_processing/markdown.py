import ajmc.text_processing.canonical_classes as cc
import ajmc.text_processing.exportable_commentary as export
import ajmc.text_processing.zotero as zotero
import json
import os
import regex
import requests

from ajmc.commons.miscellaneous import get_ajmc_logger

logger = get_ajmc_logger(__name__)

# note that the `U` and `UNICDOE` flags are redundant
# https://docs.python.org/3/library/re.html#flags
REFERENCE_REGEX = regex.compile(r"(\w+)(?:\[(\d+)\])?", regex.IGNORECASE)

PASSAGE_REGEX = regex.compile(
    r"tei-l@n=(?P<first_line_n>\d+)\[(?P<first_line_offset>\d+)\]:tei-l@n=(?P<last_line_n>\d+)\[(?P<last_line_offset>\d+)\]",
    regex.IGNORECASE,
)

ALPHA_REGEX = regex.compile(r"[a-zA-Z]", regex.UNICODE)
SCOPE_ANCHOR_REPLACEMENT_REGEX = regex.compile(r"\.")


class CTS_URN:
    """
    Some methods in this class were borrowed
    from/inspired by
    https://github.com/Capitains/MyCapytain/blob/dev/MyCapytain/common/reference/_capitains_cts.py
    """

    prefix: str
    protocol: str
    namespace: str
    text_group: str | None
    work: str | None
    version: str | None
    exemplar: str | None
    references: str | None
    citations: list[str] | None
    subsections: list[str] | None
    indexes: list[str] | None

    def __init__(self, urn: str) -> None:
        self.__urn = None

        self.__parse__(urn)

    def __parse__(self, urn_s: str):
        self.__urn = urn_s.split("#")[0]

        urn = self.__urn.split(":")

        if isinstance(urn, list) and len(urn) > 2:
            self.prefix = urn[0]
            self.protocol = urn[1]
            self.namespace = urn[2]

            if len(urn) == 5:
                self.references = urn[4]
        else:
            raise ValueError(f"Invalid URN {urn_s}")

    def parse(self, s: str):
        return s.split(":")

    def passage_component(self) -> str:
        if self.citations is None:
            return ""

        if self.subsections is None:
            return f"{'-'.join(self.citations)}"

        if self.indexes is None:
            return f"{self.citations[0]}@{self.subsections[0]}-{self.citations[1]}@{self.subsections[1]}"

        return f"{self.citations[0]}@{self.subsections[0]}[{self.indexes[0]}]-{self.citations[1]}@{self.subsections[1]}[{self.indexes[1]}]"

    def work_component(self) -> str:
        if self.text_group is None:
            return ""

        if self.work is None:
            return f"{self.text_group}"

        if self.version is None:
            return f"{self.text_group}.{self.work}"

        if self.exemplar is None:
            return f"{self.text_group}.{self.work}.{self.version}"

        return f"{self.text_group}.{self.work}.{self.version}.{self.exemplar}"


def calculate_overlays(
    pages: list[cc.CanonicalPage],
    lemma: cc.CanonicalLemma,
    glossa_words: list[cc.CanonicalWord],
):
    all_words = lemma.children.words + glossa_words
    overlays = []

    for page in pages:
        page_words = [
            w
            for w in all_words
            if page.word_range[0] < w.index and w.index <= page.word_range[1]
        ]
        bboxes = [word.bbox for word in page_words]

        if len(bboxes) > 0:
            xs = [bbox.xmin for bbox in bboxes] + [bbox.xmax for bbox in bboxes]
            ys = [bbox.ymin for bbox in bboxes] + [bbox.ymax for bbox in bboxes]

            left_most = min(xs)
            right_most = max(xs)
            top_most = min(ys)
            bottom_most = max(ys)

            overlays.append(
                dict(
                    page_id=page.id,
                    px=left_most,
                    py=top_most,
                    width=(right_most - left_most),
                    height=(bottom_most - top_most),
                )
            )

    return overlays


def get_citations_from_selector(matches: regex.Match[str]):
    first_line_n = matches.group("first_line_n")
    first_line_offset = matches.group("first_line_offset")
    last_line_n = matches.group("last_line_n")
    last_line_offset = matches.group("last_line_offset")

    cleaned_first_line_n = ALPHA_REGEX.sub("", first_line_n)
    cleaned_last_line_n = ALPHA_REGEX.sub("", last_line_n)

    if int(cleaned_first_line_n) > int(cleaned_last_line_n):
        p = first_line_n
        first_line_n = last_line_n
        last_line_n = p
        p = first_line_offset
        first_line_offset = last_line_offset
        last_line_offset = p

    return dict(
        first_line_n=first_line_n,
        first_line_offset=int(first_line_offset),
        last_line_n=last_line_n,
        last_line_offset=int(last_line_offset),
    )


def transcribe_lemma(lemma: cc.CanonicalLemma):
    if lemma.transcript is not None:  # type: ignore
        return lemma.transcript  # type: ignore

    return " ".join([w.text for w in lemma.children.words])


class Glossa:
    attributes: dict
    canonical_lemma: cc.CanonicalLemma
    content: str
    lemma_transcript: str
    start_line: str
    end_line: str
    start_offset: int | None
    end_offset: int | None
    urn: CTS_URN

    def __init__(
        self, canonical_lemma: cc.CanonicalLemma, glossa_words, pages, overlays
    ) -> None:
        self.canonical_lemma = canonical_lemma
        self.attributes = self.canonical_lemma.to_json()
        self.content = glossa_words
        self.lemma_transcript = transcribe_lemma(canonical_lemma)
        self.pages = pages
        self.overlays = overlays
        self.set_offsets()

    def set_offsets(self):
        if self.attributes.get("anchor_target") is not None:
            try:
                anchor_target = json.loads(self.attributes.get("anchor_target"))  # type: ignore
                selector = anchor_target.get("selector")
                matches = regex.search(PASSAGE_REGEX, selector)

                if matches is not None:
                    citations = get_citations_from_selector(matches)
                    start_line = citations.get("first_line_n")

                    assert isinstance(start_line, str)

                    self.start_line = start_line

                    end_line = citations.get("last_line_n")

                    assert isinstance(end_line, str)

                    self.end_line = end_line

                    self.start_offset = citations.get("first_line_offset")  # type: ignore
                    self.end_offset = citations.get("last_line_offset")  # type: ignore
            except:
                logger.warn(
                    f"Unable to parse anchor_target: {self.attributes.get('anchor_target')}"
                )
                pass
        elif self.attributes.get("scope-anchor") is not None:
            scope_anchor = self.lemma_transcript
            scope_anchor = SCOPE_ANCHOR_REPLACEMENT_REGEX.sub("", scope_anchor)

            try:
                scope_anchor = (
                    scope_anchor.replace("A", "4")
                    .replace("B", "8")
                    .replace("S", "5")
                    .strip()
                    .split("-")
                )

                # `scope_anchor` might only have one element, in which case
                # the length will be the same. This check is for normalizing
                # abbreviated citations like 160-1 to 160-161
                if len(scope_anchor[0]) < len(scope_anchor[-1]):
                    diff = len(scope_anchor[0]) - len(scope_anchor[-1])

                    scope_anchor = [
                        scope_anchor[0],
                        scope_anchor[0][0:diff] + scope_anchor[-1],
                    ]

                self.start_line = scope_anchor[0]
                self.end_line = scope_anchor[-1]
            except:
                logger.warn(f"Unable to parse scope_anchor: {scope_anchor}")
                pass

    def export(self):
        print(self.content)


class LabeledWord:
    def __init__(self, text, url) -> None:
        self.text = text
        self.url = url

    def append(self, text):
        self.text += f" {text}"

    def __str__(self):
        return f"[{self.text}]({self.url})"


class MarkdownCommentary(export.ExportableCommentary):
    def __init__(self, ajmc_id, bibliographic_data) -> None:
        self.markdown = None

        super().__init__(ajmc_id, bibliographic_data)

    def frontmatter(self):
        creators = [
            dict(
                first_name=a["firstName"],
                last_name=a["lastName"],
                creator_type=a["creatorType"],
            )
            for a in self.bibliographic_data["creators"]
        ]
        edition = self.bibliographic_data["edition"]
        languages = self.bibliographic_data["language"].split(", ")
        place = self.bibliographic_data["place"]
        publication_date = self.bibliographic_data["date"]
        public_domain_year = self.bibliographic_data["extra"]["Public Domain Year"]
        publisher = self.bibliographic_data["publisher"]
        source_url = self.bibliographic_data["url"]
        title = self.bibliographic_data["title"]
        wikidata_qid = self.bibliographic_data["extra"]["QID"]
        urn = self.bibliographic_data["extra"]["URN"]
        zotero_id = self.bibliographic_data["key"]
        zotero_link = (
            self.bibliographic_data.get("links", {}).get("alternate", {}).get("href")
        )

        return dict(
            creators=creators,
            edition=edition,
            languages=languages,
            metadata=self.commentary.metadata,  # type: ignore
            pid=self.commentary.id,  # type: ignore
            place=place,
            publication_date=publication_date,
            public_domain_year=public_domain_year,
            publisher=publisher,
            source_url=source_url,
            title=title,
            urn=f"urn:cts:greekLit:{urn}",
            wikidata_qid=wikidata_qid,
            zotero_id=zotero_id,
            zotero_link=zotero_link,
        )

    def add_entities_to_words(self, words: list[cc.CanonicalWord]):
        labeled_words = []
        current_entity = None
        current_el = None

        for word in words:
            entity = self.get_entity_for_word(word)

            if entity is not None and (
                isinstance(entity, export.PrimaryFullEntity)
                or (
                    entity.label in export.EXPORTED_ENTITY_LABELS  # type: ignore
                    and entity.wikidata_id is not None  # type: ignore
                )
            ):
                if entity == current_entity and current_el is not None:
                    current_el.append(word.text)
                else:
                    current_entity = entity

                    if current_el is not None:
                        print("SDLKFJDKLFJKLDJFJKL")
                        labeled_words.append(str(current_el))

                    if isinstance(entity, export.PrimaryFullEntity):
                        current_el = LabeledWord(word.text, entity.url)
                    else:
                        current_el = LabeledWord(word.text, entity.wikidata_id)  # type: ignore
            else:
                labeled_words.append(word.text)

        return " ".join([str(w) for w in labeled_words])

    def get_pages_between_lemmas(
        self, lemma: cc.CanonicalLemma, next_lemma: cc.CanonicalLemma
    ):
        [_lemma_start, lemma_end] = lemma.word_range
        [next_lemma_start, _next_lemma_end] = next_lemma.word_range
        return [
            page
            for page in self.commentary.children.pages
            if page.word_range[0] > lemma_end and page.word_range[1] < next_lemma_start
        ]

    def get_pages_to_end(self, lemma):
        [_lemma_start, lemma_end] = lemma.word_range

        return [
            page
            for page in self.commentary.children.pages
            if page.word_range[0] > lemma_end
        ]

    def get_words_between_lemmas(
        self, lemma: cc.CanonicalLemma, next_lemma: cc.CanonicalLemma
    ):
        [_lemma_start, lemma_end] = lemma.word_range
        [next_lemma_start, _next_lemma_end] = next_lemma.word_range

        return [
            word
            for region in self.commentary.children.regions
            if region.region_type == "commentary"
            and region.word_range[0] > lemma_end
            and region.word_range[1] < next_lemma_start
            for word in region.children.words
        ]

    def get_words_to_end(self, lemma: cc.CanonicalLemma):
        [_lemma_start, lemma_end] = lemma.word_range

        return [
            word
            for region in self.commentary.children.regions
            if region.region_type == "commentary" and region.word_range[0] > lemma_end
            for word in region.children.words
        ]

    def glosses(self):
        glossae = []

        for i, lemma in enumerate(self.commentary.children.lemmas):
            if lemma.label in ["scope-anchor", "word-anchor"]:
                try:
                    next_lemma = self.commentary.children.lemmas[i + 1]
                    glossa_words = self.get_words_between_lemmas(lemma, next_lemma)
                    pages = self.get_pages_between_lemmas(lemma, next_lemma)
                    overlays = calculate_overlays(pages, lemma, glossa_words)

                    glossae.append(
                        Glossa(
                            lemma,
                            self.add_entities_to_words(glossa_words),
                            pages,
                            overlays,
                        )
                    )
                except IndexError:
                    glossa_words = self.get_words_to_end(lemma)
                    pages = self.get_pages_to_end(lemma)
                    overlays = calculate_overlays(pages, lemma, glossa_words)

                    glossae.append(
                        Glossa(
                            lemma,
                            self.add_entities_to_words(glossa_words),
                            pages,
                            overlays,
                        )
                    )

        return glossae

    def export(self):
        return [g.export() for g in self.glosses()]


if __name__ == "__main__":
    commentaries = requests.get(
        f"{os.getenv('AJMC_API_URL', 'https://ajmc.unil.ch/api')}/commentaries?public=true"
    )

    commentary = commentaries.json()["data"][2]
    zotero_data = zotero.get_zotero_data(commentary["zotero_id"])
    doc = MarkdownCommentary(commentary["pid"], zotero_data)
    doc.export()

    # for commentary in commentaries.json()["data"]:
    #     zotero_data = zotero.get_zotero_data(commentary["zotero_id"])
    #     doc = MarkdownCommentary(commentary["pid"], zotero_data)

    #     doc.export()