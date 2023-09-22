from ChemNER.processors import Entity, Processor, Normalizer
import spacy
from spacy.tokens import Doc
from spacy.language import Language

def split_into_paragraphs(document):
    start = 0
    for token in document:
        if "\n\n" in token.text:
            yield document[start:token.i].text
            start = token.i
    yield document[start:].text


def process(doc, entities):
    offset = 0
    for paragraph in split_into_paragraphs(doc):
        NER_processor.set_sequence(str(paragraph))
        results = NER_processor.predict()
        entities.add_entities(results)
        entities.remove_non_entities()
        offset += len(str(paragraph))
        NER_processor.set_offset(offset)

    NER_processor.set_offset(0, restart=True)


    
@Language.factory("ner_custom")
def create_custom_ner(nlp: Language, name: str):
    return CustomNERComponent()

class CustomNERComponent:
    def __call__(self, doc: Doc) -> Doc:
        entities = Entity(doc)
        process(doc, entities)
        entities.postprocess_entities()
        return doc

try:
    NER_processor = Processor('alvaroalon2/biobert_chemical_ner')
    
    spacy_pipe = spacy.load("en_core_sci_sm", exclude=["tok2vec", "lemmatizer"])
    spacy_pipe.replace_pipe('ner','ner_custom')

except Exception as error:
    print(repr(error))
