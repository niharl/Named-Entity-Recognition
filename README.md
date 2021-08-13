# Named-Entity-Recognition
2 projects in the field of Named Entity Recognition (NER).

## 1. NER Recency Bias Experiment
* An experiment exploring the effect of training an NER model on the recognition of previously trained (or embedded entities)
* Spacy's NER model is pre-trained to recognise standard named entities in English text (e.g. dates, locations, names, organisations)
* We update this model by training on domain-specific data (aircraft incidents) to recognise new entities (e.g. failures, aircraft)
* We compare the success rate of the NER model before and after updated training at the recognition of standard entities in generic English text
* We find that training the model to recognise new entities almost entirely eliminates the recognition of previously trained entities
* After training, the NER model only picks up false positive in generic textual data

## 2. NER Annotation Tool
* A colour-based graphic application for annotation of textual data for NER training (built with PySimpleGui)
* An alternative to Spacy's Prodigy tool or tagging text files
* Input/output in the form of XML-style tagged text files which can be parsed for NER training

Screenshot:

<img src = "https://github.com/niharl/Named-Entity-Recognition/blob/main/NER%20Annotation%20App/Screenshot.png?raw=true" width = 800>
