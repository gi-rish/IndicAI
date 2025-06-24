# setup_lang_index.py

import chromadb
from sentence_transformers import SentenceTransformer

# Connect to Chroma server
client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_or_create_collection("language_embeddings")

# Define sample phrases per language (in Latin script for now)
LANG_SAMPLES = {
    "kannada": [
        "neevu hegiddira", "haay", "idu ondu pareekshe", "nanna hesaru girish", "ondhu nimisha", "banni illi", "nanu hoguttiddene",
        "hege ide", "dayavittu", "naale sigona", "swalpa nillu", "nimage sahaya beka", "ninna hesaru enu", "idanna odhi", 
        "ivattu santoshadinda ide", "hotte tumbi hogide", "tumba chennagide", "nanna mane ellide", "nange artha aagilla", "illavalla"
    ],
    "hindi": [
        "aapka naam kya hai", "namaste", "yah ek pariksha hai", "aap kaise ho", "mera naam dev hai", "thoda ruk jao", "mujhe bhookh lagi hai",
        "tum kahan ja rahe ho", "yeh kya hai", "kripya dhyan dein", "aaj mausam accha hai", "kal milte hain", "aapka din shubh ho", "main samajh gaya",
        "kya aap madad karenge", "yeh galat hai", "kitne baje hue", "kya yeh sahi hai", "abhi tak nahi aaya", "bahut sundar"
    ],
    "marathi": [
        "tuze naav kaay aahe", "namaskar", "ha ek chaachani aahe", "tumhi kase aahat", "mala bhook lagli aahe", "mi gharat aahe", "krupaya thamba",
        "he kay aahe", "kal miluya", "majhe naav girish aahe", "majha ghar kuthe aahe", "ha changla ahe", "tumhala kahi pahije ka", "mi samajlo",
        "mi jato", "chaha hava ahe", "tumchi madat pahije", "thoda vel thaamb", "aat gharat ahe", "kaahi samajat nahi"
    ],
    "tamil": [
        "vanakkam", "un peyar enna", "ithu oru sothanai", "neenga eppadi irukeenga", "enna seiyringa", "naan saapittaen", "intha edam enge",
        "naan purinjuka matten", "konjam niruthunga", "unga peru enna", "neenga enga irukeenga", "idhu sari illa", "nalladhu nadakkum",
        "naan poittu varen", "kavalai padatheenga", "sirikka vaanga", "thaniyaa vidunga", "enga veedu enga irukku", "naan ungaluku udhavi seiven", "romba nalla irukku"
    ],
    "english": [
        "hello", "how are you", "this is a test", "my name is girish", "where are you going", "please wait", "thank you very much", "good morning",
        "what time is it", "can you help me", "this is incorrect", "i don't understand", "let's meet tomorrow", "everything is fine",
        "i am hungry", "you are welcome", "see you soon", "have a nice day", "what do you mean", "that's amazing"
    ],
}


# Load sentence transformer
model = SentenceTransformer("all-MiniLM-L6-v2")

# Build and add embeddings
texts, ids, metas = [], [], []
i = 0
for lang, phrases in LANG_SAMPLES.items():
    for phrase in phrases:
        texts.append(phrase)
        ids.append(f"{lang}_{i}")
        metas.append({"lang": lang})
        i += 1

embeddings = model.encode(texts).tolist()
collection.add(documents=texts, embeddings=embeddings, metadatas=metas, ids=ids)

print("✅ Language embedding index created.")
print("Total documents in collection:", collection.count())
