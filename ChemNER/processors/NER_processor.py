import torch
from transformers import pipeline

class Processor:
    def __init__(self, model_name):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = pipeline(
            "ner",
            model=model_name,
            tokenizer=model_name,
            aggregation_strategy="simple",
            device=self.device
        )
        self.sequence = ''
        self.offset = 0
        self.results = []

    def set_sequence(self, sequence):
        self.sequence = sequence

    def set_offset(self, offset, restart=False):
        if restart:
            self.offset = 0
        else:
            self.offset = offset

    def predict(self):
        results = self.pipeline(self.sequence)
        if self.offset > 0:
            for result in results:
                result['start'] += self.offset
                result['end'] += self.offset
        self.results = results
        return self.results