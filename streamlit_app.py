import streamlit as st
import pandas as pd
import json
from io import StringIO
from spacy import displacy
from bs4 import BeautifulSoup
import time

from ChemNER import Entity, Processor, Normalizer
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

NER_processor = Processor('alvaroalon2/biobert_chemical_ner')
    
spacy_pipe = spacy.load("en_core_web_sm", exclude=["tok2vec", "lemmatizer"])
spacy_pipe.replace_pipe('ner','ner_custom')


def find_entity(ent_list, ent_name):
    for entity in ent_list:
        if entity['entity']==ent_name:
            return entity
    return {}


st.set_page_config(page_title="Chem-NER", page_icon=":test-tube:")

st.markdown('<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Poppins">',unsafe_allow_html=True)

with open('style.css') as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

st.title("Chemical Named Entity Recognition")

with st.expander("ℹ️ - About this app", expanded=False):

    st.write(
        """     
-   The **Chemical Named Entity Recognition** app is an easy-to-use interface built in Streamlit.
-   It finds chemical entities in the given document and provide PubChem and Chebi id for the entities if existed.
	    """
    )

st.markdown("## **📌 Paste or upload your document **")
st.markdown("")

with st.form("doc"):
    uploaded_file = st.file_uploader("Choose a document")
    text = st.text_area('Document to analyze', 
                            placeholder="Acetaminophen is a commonly used over-the-counter medication for pain relief..", 
                            height=400)
    if uploaded_file is not None:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        text = stringio.read()
        btn = True

    btn = st.form_submit_button("Submit")

if btn:
    st.markdown("## **🎈 Check & download results **")
    with st.spinner('Please wait...'):
        with st.expander("Labeled document", expanded=True):
            doc = spacy_pipe(text)
            ner_result = displacy.render(doc, style='ent',
                                        options={"ents": ["CHEMICAL"], "colors": {"CHEMICAL":"linear-gradient(45deg,#51a8dd,#A5DEE4)"}})
            
            entities = [f.text for f in doc.ents if f.label_ == 'CHEMICAL']
            normalizer = Normalizer()
            normalized_ents = normalizer.normalize_entities(entities)

            soup = BeautifulSoup(ner_result, 'html.parser')

            marks = soup.find_all('mark')

            for mark in marks:
                entity_text = mark.find_next(string=True).strip()
                entity_info = 'Information about {}'.format(entity_text)
                
                info_div = soup.new_tag('div', attrs={'class': 'entity-info'})
                info_div.string = entity_info
        
                table = soup.new_tag('table')
                table['style'] = 'width: 100%; margin-top: 10px'
                
                thead = soup.new_tag('thead')
                tr = soup.new_tag('tr')
                th1 = soup.new_tag('th')
                th1.string = 'Found name'
                th2 = soup.new_tag('th')
                th2.string = 'PubChem'
                th3 = soup.new_tag('th')
                th3.string = 'Chebi'
                tr.append(th1)
                tr.append(th2)
                tr.append(th3)
                thead.append(tr)
                
                ent = find_entity(normalized_ents, entity_text)
                tbody = soup.new_tag('tbody')
                tr = soup.new_tag('tr')
                td1 = soup.new_tag('td')
                td1.string = ent['name'] if 'name' in ent else '-'
                td2 = soup.new_tag('td')
                if 'cid' in ent: 
                    cid = str(ent['cid']) 
                    pubchem_link = soup.new_tag('a', href=f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}')
                    pubchem_link.string = cid
                else:
                    pubchem_link = soup.new_tag('span')
                    pubchem_link.string = '-'
                td2.append(pubchem_link)
                td3 = soup.new_tag('td') 
                if 'chebi_id' in ent:
                    chebi_id = str(ent['chebi_id'])
                    chebi_link = soup.new_tag('a', href=f'https://www.ebi.ac.uk/chebi/searchId.do?chebiId={chebi_id}')
                    chebi_link.string = chebi_id
                else:
                    chebi_link = soup.new_tag('span')
                    chebi_link.string = '-'
                td3.append(chebi_link)    
                tr.append(td1)
                tr.append(td2)
                tr.append(td3)
                tbody.append(tr)
                
                table.append(thead)
                table.append(tbody)
                
                info_div.append(table)
            
                mark.append(info_div) 

            modified_html = str(soup)
            st.markdown(modified_html, unsafe_allow_html=True)
            
        st.markdown("")

        c1, c2 = st.columns([1, 1])

        ent_df = pd.DataFrame(normalized_ents)
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode('utf-8')

        ent_csv = convert_df(ent_df)
        ent_json = json.dumps(normalized_ents)
        with c1:
            st.download_button("📥 Download (.csv)", ent_csv, "Data.csv")
        with c2:
            st.download_button("📥 Download (.json)",ent_json, "Data.json")

