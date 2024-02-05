import spacy

nlp = spacy.load("en_core_web_sm")

sentences = [
    "I ain't needed around here anymore.",  # am not
    # "This old computer ain't needed since we got the new one", # is not
    # "They ain't needed an excuse to celebrate; any reason is good for them!" # have not
    # "You ain't needed your old books, right?",  # haven't needed
    # "You ain't allowed to talk during the exam.",  # are not
    # "I ain't going to the party tonight.",  # am not
    # "He ain't got any money left.",  # has not
    # "You ain't seen nothing yet!",  # have not
    # "They ain't ready for the test.",  # are not
    # "She ain't interested in the offer.",  # is not
    # "It ain't raining anymore.",  # is not
    # "We ain't been to Paris before.",  # have not
    # "That ain't the way to do it.",  # is not
    # "They ain't got a clue about what happened."  # have not
]

for sentence in sentences:
    doc = nlp(sentence)
    for token in doc:
        if token.dep_ == "auxpass" or token.dep_ == "pass":
            print(f"{token.text} ist Teil einer passiven Konstruktion.")
        else:
            print(f"{token.text} ist NICHT Teil einer passiven Konstruktion.")
            # print(f"Sentence: \"{sentence}\" | Verb: {token.text} | POS: {token.pos_} | Tag: {token.tag_} | Dep: {token.dep_}")
            
    print("\n")