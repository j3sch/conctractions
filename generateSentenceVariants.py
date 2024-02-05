import re
import spacy
import json

nlp = spacy.load("en_core_web_sm")

def replace_at(sentence, word, replacement):
    return re.sub(r'\b' + word + r'\b', replacement, sentence, flags=re.IGNORECASE)

def get_abbreviation(word):
    parts = word.split("'")
    if len(parts) > 1:
        return "'" + parts[1]
    else:
        return None
    
def add_new_sentence_to_array(new_variants, new_sentence_variant):
    if new_sentence_variant not in new_variants:
        # capitaliyze first letter of the sentence
        new_variant_capilized = new_sentence_variant[0].upper() + new_sentence_variant[1:]
        new_variants.append(new_variant_capilized)
    
def check_subject_in_third_person_singular(doc, contraction_index):
    for token in reversed(list(doc)[:contraction_index]):
        # Überprüfen, ob das Token ein Subjekt ist
        if "subj" in token.dep_:
            # spaCy stellt grammatikalische Merkmale wie Person und Zahl zur Verfügung
            person = token.morph.get("Person")
            number = token.morph.get("Number")
            
            # Überprüfen, ob das Subjekt in der dritten Person Singular steht
            if person == ['3'] and number == ['Sing']:
                return True
    return False

has_indicators = ["got", "been", "done", "seen", "heard", "eaten"]

def find_word_before_contractions(sentence, contractionEnd):
    words = sentence.split()
    words_before_contractions = [word[:-2] for word in words if word.endswith(contractionEnd)]
    return words_before_contractions

def find_closest_verb(doc, contraction_index):
    closest_verb = None
    verb_distance = float('inf')
    for token in doc:
        if token.pos_ == "VERB":
            distance = abs(token.i - contraction_index)
            if distance < verb_distance:
                closest_verb = token
                verb_distance = distance
    return closest_verb, verb_distance

def find_next_verb(doc, contraction_index):
    for token in doc[contraction_index+1:]:
        if token.pos_ == "VERB":
            return token
    return None

def does_sentence_express_possibility_wish_condition_hypothesis(doc):

    keywords = {
        # Modalverben, die Möglichkeiten oder hypothetische Situationen ausdrücken
        "could", "would", "should", "might", 
        
        # Ausdrücke, die Wünsche oder Sehnsüchte darstellen
        "wish", "want", "hope", "dream", "desire", "long for",
        
        # Konjunktionen und Phrasen, die Bedingungen oder Voraussetzungen ausdrücken
        "if", "in case", "provided that", "assuming that", "supposing", "on the condition that",
        
        # Ausdrücke, die Spekulationen oder potenzielle Möglichkeiten darstellen
        "maybe", "perhaps", "possibly", "potentially",
        
        # Ausdrücke, die Hypothesen oder Annahmen ausdrücken
        "assume", "suppose", "speculate", "think", "believe", "imagine",
        
        # Ausdrücke, die Unsicherheit oder Zweifel ausdrücken
        "uncertain", "not sure", "doubtful", "questionable",
        
        # Ausdrücke, die Bedauern oder Reue ausdrücken
        "regret", "lament",
        
        # Ausdrücke, die Fähigkeit oder Kapazität ausdrücken
        "can", "able to", "capable of",
    }


    for token in doc:
        if token.lemma_ in keywords:
            return True
    return False

    
def expand_contraction(sentence, contraction, alt_abbreviations):
    doc = nlp(sentence)
    abbreviation = get_abbreviation(contraction)
    for token in doc:
        # Finde das Token, das der Kontraktion entspricht
        if token.text.lower() == abbreviation:
            # Überprüfe das nächste Token im Satz
            contraction_index = token.i
            next_token_index = token.i + 1
            if next_token_index < len(doc):
                next_token = doc[next_token_index]
                # Entscheide für "he's"
                if abbreviation == "'s":
                    is_third_person_singular = check_subject_in_third_person_singular(doc, contraction_index)
                    if (next_token.tag_ == "VBN" or (next_token.dep_ == "aux" and next_token.head.tag_ == "VBN")) and is_third_person_singular:    
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # has
                    elif next_token.text.lower() in has_indicators and is_third_person_singular:
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # has
                    elif next_token.tag_ == "VBG":
                        return replace_at(sentence, contraction, alt_abbreviations[0]) # is
                    else:
                        # Suche das nächstgelegene Verb zur Kontraktion
                        closest_verb, verb_distance = find_closest_verb(doc, contraction_index)
                        if closest_verb:
                            if closest_verb.tag_ in ["VBD", "VBN"] and verb_distance <= 3: # Begrenze den Abstand für relevante Fälle
                                return replace_at(sentence, contraction, alt_abbreviations[1]) # has
                            elif closest_verb.tag_ == "VBG" and verb_distance <= 3:
                                return replace_at(sentence, contraction, alt_abbreviations[0]) # is
                        return replace_at(sentence, contraction, alt_abbreviations[0]) # is

                
                # Entscheide für "you'd"
                elif abbreviation == "'d":
                    if next_token.tag_ == 'VBN':  # next word == Partizip Perfekt
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # had
                    next_verb = find_next_verb(doc, contraction_index)
                    if next_verb and next_verb.tag_ == 'VBN':  # next verb == Partizip Perfekt
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # had
                    if next_token.tag_ == 'VB':  # Infinitiv
                        return replace_at(sentence, contraction, alt_abbreviations[0]) # would
                    if next_token.text.lower() in ["have", "'ve", "prefer", "like", "love", "hate"]:
                        return replace_at(sentence, contraction, alt_abbreviations[0])  # would
                    is_possible_wish_condition_hypothesis = does_sentence_express_possibility_wish_condition_hypothesis(doc)
                    if is_possible_wish_condition_hypothesis: # Satz eine Möglichkeit, einen Wunsch, eine Bedingung oder eine Hypothese ausdrückt
                        return replace_at(sentence, contraction, alt_abbreviations[0])  # would
                    
                    return replace_at(sentence, contraction, alt_abbreviations[0]) # else
    return sentence  # Falls die Kontraktion nicht gefunden wurde, gib den Originalsatz zurück

def find_subj(doc):

    subj = None
    is_subj_before_aint = True

    for token in doc:
        if token.text.lower() == 'ai':
            word_before = doc[token.i - 1]
            if "subj" in word_before.dep_:
                return word_before.text.lower()
            else: 
                is_subj_before_aint = False
                if subj:
                    return subj
        if "subj" in token.dep_:
            subj = token.text.lower()
            if is_subj_before_aint is False:
                return subj
    return subj

def detect_tense(input_sentence):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(input_sentence)

    tenses = {
        'past': ['VBD', 'VBN'],
        'present': ['VB', 'VBP', 'VBZ', 'VBG'],
        'future': ['MD']
    }
    state_verbs = ['allowed', 'required', 'supposed', 'needed', 'expected', 'permitted', 'prohibited', 'forbidden', 'obligated', 'entitled', 'encouraged', 'advised', 'recommended', 'compelled', 'asked', 'instructed', 'ordered', 'commanded', 'enabled', 'empowered', 'authorized', 'sanctioned', 'banned', 'barred', 'prevented', 'restricted', 'limited', 'constrained', 'discouraged', 'dissuaded', 'urged', 'implored', 'begged', 'appealed']

    aux_token = None
    state_verb_token = None

    def decide_tense(token):
        if token.tag_ in tenses['past']:
            return 'past'
        elif token.tag_ in tenses['present']:
            return 'present'
        elif token.tag_ in tenses['future']:
            return 'future'
        return None

    for token in doc:
        if token.text == "ai":
            continue
        if token.text in state_verbs:
            state_verb_token = token
            continue
        if token.pos_ == "VERB":
            return decide_tense(token)
        if (token.pos_ == "AUX"):
            aux_token = token

    if state_verb_token:
        return decide_tense(state_verb_token)
    if aux_token:
        return decide_tense(aux_token)

    return "present"

def get_constraction_index(doc, contraction):
    for token in doc:
        if token.text.lower() == contraction:
            return token.i
    return None


def expand_contration_aint(sentence):
    doc = nlp(sentence)

    contraction = "ain't"
    subj = find_subj(doc)
    tense = detect_tense(sentence)
    if (subj is None): return sentence

    if subj in ["i", "we", "you", "they"]:
        if tense == "past":
            return replace_at(sentence, contraction, "have not")
        else:
            if subj == "i": return replace_at(sentence, contraction, "am not") 
            return replace_at(sentence, contraction, "are not")
    elif (subj in ["he", "she", "it"]):
        if tense == "past":
            return replace_at(sentence, contraction, "has not")
        else:
            return replace_at(sentence, contraction, "is not")
    else: # subj is it but as a word (e.g. "the dog")
        if tense == "past":
            return replace_at(sentence, contraction, "has not")
        else:
            return replace_at(sentence, contraction, "is not")
    
    

def add_variants_for_constraction(sentence_variants, contraction, alt_contractions):
    new_variants = []
    for variant in sentence_variants:
        if contraction.endswith(("had", "would", "is", "has")): # Use first alternative 'd, 's
            new_sentence_variant = replace_at(variant, contraction, alt_contractions[0])
            add_new_sentence_to_array(new_variants, new_sentence_variant)
        else:
            for alt_abbreviation in alt_contractions:
                new_sentence_variant = replace_at(variant, contraction, alt_abbreviation)
                add_new_sentence_to_array(new_variants, new_sentence_variant)
    return new_variants

def generate_sentence_variants(sentence, contractions):

    if not sentence:
        return []
    
    variants = [sentence]

    # could be contraction like who's, but also possessive like John's
    if "'s" in sentence:
        new_variants = []
        for variant in variants:
            words_before_contractions = find_word_before_contractions(variant, "'s")
            for word in words_before_contractions:
                if word.lower() == "let":
                    new_sentence_variant = replace_at(sentence, "let's", "let us")  # would
                    add_new_sentence_to_array(new_variants, new_sentence_variant)
                else:
                    new_sentence_variant = expand_contraction(variant, word + "'s", [word + " is", word + " has"])
                    add_new_sentence_to_array(new_variants, new_sentence_variant)
        variants += new_variants
    # looks 
    if "'d" in sentence:
        new_variants = []
        for variant in variants:
            word_before_contractions = find_word_before_contractions(variant, "'d")
            for word in word_before_contractions:
                new_sentence_variant = expand_contraction(variant, word + "'d", [word + " would", word + " had"])
                add_new_sentence_to_array(new_variants, new_sentence_variant)
        variants += new_variants
    if "ain't" in sentence:
        new_variants = []
        for variant in variants:
            new_sentence_variant = expand_contration_aint(variant)
            add_new_sentence_to_array(new_variants, new_sentence_variant)
        variants += new_variants
    for group in contractions:
        for contraction in group:
            if contraction.endswith(("'s", "'d")) or contraction == "ain't": # is handled above
                continue

            if contraction in sentence.lower():
                if contraction.startswith("he") and ("she is" in sentence.lower() or "she has" in sentence.lower() or "she will" in sentence.lower() or "she would" in sentence.lower() or "she had" in sentence.lower()):                    
                    continue
                variants += add_variants_for_constraction(variants, contraction, [item for item in group if item != contraction])

    return variants

en_contractions = [
 ["can't", 'cannot', 'can not'],
["won't", 'will not'],
["i'm", 'i am'],
["you're", 'you are'],
["he's", 'he is', 'he has'],
["she's", 'she is', 'she has'],
["it's", 'it is', "it has"],
["we're", 'we are'],
["they're", 'they are'],
["i'll", 'i will'],
["you'll", 'you will'],
["he'll", 'he will'],
["she'll", 'she will'],
["it'll", 'it will'],
["we'll", 'we will'],
["they'll", 'they will'],
["i'd", 'i would', 'i had'], 
["you'd", 'you would', 'you had'],
["he'd", 'he would', 'he had'], 
["she'd", 'she would', 'she had'], 
["it'd", 'it would', 'it had'], 
["we'd", 'we would', 'we had'],  
["they'd", 'they would', 'they had'], 
["i've", 'i have'],
["you've", 'you have'],
["we've", 'we have'],
["they've", 'they have'],
["isn't", 'is not'],
["aren't", 'are not'],
["wasn't", 'was not'],
["weren't", 'were not'],
["haven't", 'have not'],
["hasn't", 'has not'],
["hadn't", 'had not'],
["wouldn't", 'would not'],
["don't", 'do not'],
["doesn't", 'does not'],
["didn't", 'did not'],
["couldn't", 'could not'],
["shouldn't", 'should not'],
["mightn't", 'might not'],
["mustn't", 'must not'],
["what's", "what is", "what has"], 
["that's", "that is", "that has"], 
["who's", "who is", "who has"], 
["where's", "where is", "where has"], 
["when's", "when is", "when has"], 
["why's", "why is", "why has"], 
["how's", "how is", "how has"], 
["let's", "let us"], 
["there's", "there is", "there has"], 
["here's", "here is", 'here has'],
["what're", "what are"],
["who're", "who are"],
["where're", "where are"],
["when're", "when are"],
["why're", "why are"],
["how're", "how are"],
["that'll", "that will"],
["who'll", "who will"],
["where'll", "where will"],
["when'll", "when will"],
["why'll", "why will"],
["how'll", "how will"],
["that'd", "that would", "that had"], 
["who'd", "who would", "who had"], 
["where'd", "where would", "where had"], 
["when'd", "when would", "when had"], 
["why'd", "why would", "why had"], 
["how'd", "how would", "how had"], 
["there'd", "there would", "there had"], 
["there'll", "there will"],
["there've", "there have"],
["ain't", "am not", "are not", "is not", "has not", "have not"], 
["y'all", "you all"],
["could've", "could have"],
["might've", "might have"],
["must've", "must have"],
["should've", "should have"],
["would've", "would have"],
["not've", "not have"],
]

# original_sentence = "Let's try something."
# all_variants = generate_sentence_variants(original_sentence, en_contractions)
# print(all_variants)

def read_data_from_file(file_name):
    with open(file_name, "r") as file:
        data =  json.load(file)

    for item in data: 
        translations = item["translations"]
        new_translations = []
        for translation in translations:
            new_variants = generate_sentence_variants(translation, en_contractions)
            for new_variant in new_variants:
                add_new_sentence_to_array(new_translations, new_variant)
        item["translations"] = new_translations
    
    # write data to file
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)
            

read_data_from_file("deToEn.json")