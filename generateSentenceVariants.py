import re
import spacy

nlp = spacy.load("en_core_web_sm")

def replace_at(sentence, word, replacement):
    return re.sub(r'\b' + word + r'\b', replacement, sentence, flags=re.IGNORECASE)

def get_abbreviation(word):
    parts = word.split("'")
    if len(parts) > 1:
        return "'" + parts[1]
    else:
        return None
    
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
                        print("has")
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # has
                    elif next_token.text.lower() in has_indicators and is_third_person_singular:
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # has
                    elif next_token.tag_ == "VBG":
                        print("is")
                        return replace_at(sentence, contraction, alt_abbreviations[0]) # is
                    else:
                        # Suche das nächstgelegene Verb zur Kontraktion
                        closest_verb, verb_distance = find_closest_verb(doc, contraction_index)
                        if closest_verb:
                            if closest_verb.tag_ in ["VBD", "VBN"] and verb_distance <= 3: # Begrenze den Abstand für relevante Fälle
                                print("has (nächstes Verb)")
                                return replace_at(sentence, contraction, alt_abbreviations[1]) # has
                            elif closest_verb.tag_ == "VBG" and verb_distance <= 3:
                                print("is (nächstes Verb)")
                                return replace_at(sentence, contraction, alt_abbreviations[0]) # is
                        return replace_at(sentence, contraction, alt_abbreviations[0]) # is

                
                # Entscheide für "you'd"
                elif abbreviation == "'d":
                    print("you'd")
                    if next_token.tag_ == 'VBN':  # Partizip Perfekt
                        return replace_at(sentence, contraction, alt_abbreviations[1]) # had
                    elif next_token.tag_ == 'VB':  # Infinitiv
                        return replace_at(sentence, contraction, alt_abbreviations[0]) # would
                    # Hier könnte eine komplexere Logik oder Kontextanalyse notwendig sein
                    else:
                        return replace_at(sentence, contraction, "you would")

    return sentence  # Falls die Kontraktion nicht gefunden wurde, gib den Originalsatz zurück


def add_variants_for_word(sentence_variants, abbreviation, alt_abbreviations):
    new_variants = []
    for variant in sentence_variants:
        print('variant', variant)
        if abbreviation.endswith(("'d'", "'s")) and len(alt_abbreviations)> 1:
            new_sentence_variant = expand_contraction(variant, abbreviation, alt_abbreviations)
            print('new_sentence_variant', new_sentence_variant)
            if (new_sentence_variant not in sentence_variants) and (new_sentence_variant not in new_variants):
                new_variants.append(new_sentence_variant)
        elif abbreviation.endswith(("had", "would", "is", "has")): # Use first alternative 'd, 's
            new_sentence_variant = replace_at(variant, abbreviation, alt_abbreviations[0])
            if (new_sentence_variant not in sentence_variants) and (new_sentence_variant not in new_variants):
                new_variants.append(new_sentence_variant)
        else:
            for alt_abbreviation in alt_abbreviations:
                new_sentence_variant = replace_at(variant, abbreviation, alt_abbreviation)
                if (new_sentence_variant not in sentence_variants) and (new_sentence_variant not in new_variants):
                    new_variants.append(new_sentence_variant)     
    return new_variants

def generate_sentence_variants(sentence, abbreviations):

    if not sentence:
        return []
    
    variants = [sentence]

    for group in abbreviations:
        for abbreviation in group:
            if abbreviation in sentence.lower():
                variants += add_variants_for_word(variants, abbreviation, [item for item in group if item != abbreviation])

    return variants

en_abbreviations = [
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

original_sentence = "John's coming over tonight."
all_variants = generate_sentence_variants(original_sentence, en_abbreviations)

print(all_variants)