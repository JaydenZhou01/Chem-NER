from spacy import util

class Entity:
    def __init__(self, doc):
        self.doc = doc
        self.entities = []

    def count_entities(self):
        return len(self.doc.entities)

    def sort_entities(self):
        self.entities.sort(key=lambda k: k['start'])

    def add_entities(self, entities):
        self.entities.extend(entities)

    def remove_non_entities(self):
        self.entities = [ent for ent in self.entities if ent['entity_group'] != '0']

    def postprocess_entities(self):        
        
        def get_entity_spans():
            entity_spans = []
            for entity in self.entities:
                proposed_span = self.doc.char_span(entity['start'], entity['end'], entity['entity_group'])
                if proposed_span:
                    entity_spans.append(proposed_span)
            return entity_spans
        
        try:
            self.remove_non_entities()
            self.sort_entities()
            entity_spans = get_entity_spans()
            entity_spans = list(filter(None, entity_spans))
            filtered_spans = util.filter_spans(entity_spans)
            self.doc.set_ents(filtered_spans)
        except ValueError as error:
            print(repr(error))