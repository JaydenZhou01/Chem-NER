import pysolr
import re
import os

class Normalizer:
    def __init__(self):
        self.solr_url = os.getenv('SOLR_URL','http://localhost:8983/solr/')
        try:
            self.solr_engine = pysolr.Solr(self.solr_url+'ner_chem', timeout=20)
        except ConnectionError as error:
            print(repr(error))

    def normalize_entities(self, entities):
    
        def get_unique_terms(entities):
            unique_ents = set()
            ents = [item for item in entities if item.lower() not in unique_ents and len(item) > 1 and not unique_ents.add(item.lower())]
            return ents
        
        normalized_entities = []
        unique_entities = get_unique_terms(entities)
        for entity in unique_entities:
            label = str(entity)
            label_clean = re.sub(r'\W+', ' ', label)
            
            term_exact_match = f'term:"{label}"^100 or synonyms:"{label}"^10'
            term_fuzzy_match = f'term:{label}^100 or synonyms:{label}^10'
            syn_exact_match = f'term:"{label}"^10 or synonyms:"{label}"^100'
            syn_fuzzy_match = f'term:{label}^10 or synonyms:{label}^100'
            
            try:
                results_term_exact = self.solr_engine.search(term_exact_match, fl='*,score')
                results_term_fuzzy = self.solr_engine.search(term_fuzzy_match, fl='*,score')
                results_syn_exact = self.solr_engine.search(syn_exact_match, fl='*,score')
                results_syn_fuzzy = self.solr_engine.search(syn_fuzzy_match, fl='*,score')
            except Exception:
                try:
                    results_term_exact = self.solr_engine.search(f'term:"{label_clean}"^100 or synonyms:"{label_clean}"^10', fl='*,score')
                    results_term_fuzzy = self.solr_engine.search(f'term:{label_clean}^100 or synonyms:{label_clean}^10', fl='*,score')
                    results_syn_exact = self.solr_engine.search(f'term:"{label_clean}"^10 or synonyms:"{label_clean}"^100', fl='*,score')
                    results_syn_fuzzy = self.solr_engine.search(f'term:{label_clean}^10 or synonyms:{label_clean}^100', fl='*,score')
                except Exception:
                    continue

            if len(results_term_exact) < 1 and len(results_term_exact) < 1:
                compound = {'entity': label}
                normalized_entities.append(compound)
            else:
                score_term_exact = results_term_exact.docs[0]['score'] if results_term_exact else 0
                score_term_fuzzy = results_term_fuzzy.docs[0]['score'] if results_term_fuzzy else 0
                score_syn_exact = results_syn_exact.docs[0]['score'] if results_syn_exact else 0
                score_syn_fuzzy = results_syn_fuzzy.docs[0]['score'] if results_syn_fuzzy else 0                

                results_scores = {results_term_exact: score_term_exact, results_term_fuzzy: score_term_fuzzy,
                                  results_syn_exact: 0.8*score_syn_exact, results_syn_fuzzy: 0.8*score_syn_fuzzy}
                results = max(results_scores, key=results_scores.get)

                compound = {'entity': label}
                result = results.docs[0]
                if "term" in result:
                    compound["name"] = "".join(result["term"])
                if 'cid' in result:
                    compound['cid'] = result["cid"]
                if 'inchikey' in result:
                    compound['inchikey'] = result['inchikey']
                if 'chebi_id' in result:
                    compound['chebi_id'] = result["chebi_id"]
                normalized_entities.append(compound)
        return normalized_entities