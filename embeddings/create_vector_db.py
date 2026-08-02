import os
import shutil
import pandas as pd

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# ==========================================================
# Paths
# ==========================================================

DATASET_PATH = "data/cleaned_dataset.csv"
KNOWLEDGE_FOLDER = "knowledge"
VECTOR_DB_PATH = "vectorstore/faiss_index"

# ==========================================================
# Load Dataset
# ==========================================================

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)
df.fillna("Unknown", inplace=True)

print(f"Loaded {len(df)} records.")

# ==========================================================
# Create Dataset Documents
# ==========================================================

documents = []

print("Creating dataset documents...")

for _, row in df.iterrows():

    text = f"""
Age: {row['age']} years
BMI: {row['bmi']}
State: {row['state']}

Cycle Length: {row['cycle_length_days']} days
Previous Cycle Length: {row['prev_cycle_length']} days
Cycle Phase: {row['cycle_phase']}

Flow Level: {row['flow_level']}
Pain Level: {row['pain_level']}/10
Stress Level: {row['stress_score_cycle']}/10

Sleep During Cycle: {row['sleep_hours_cycle']} hours
Average Sleep: {row['sleep_hours']} hours

Mood Score: {row['mood_score']}
Energy Level: {row['energy_level']}

PMS Symptoms: {row['pms_symptoms']}
Ovulation: {row['ovulation_result']}

Exercise: {row['exercise_frequency']}
Diet Quality: {row['diet_quality']}

PCOS Diagnosed: {row['pcos_diagnosed']}

Overall Health Score: {row['overall_health_score']}
"""

    documents.append(
        Document(
            page_content=text,
            metadata={
                "source": "dataset",
                "type": "clinical_record"
            }
        )
    )

print(f"Dataset documents : {len(documents)}")

# ==========================================================
# Load Medical Knowledge
# ==========================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

knowledge_docs = []

print("Loading medical knowledge...")

for filename in os.listdir(KNOWLEDGE_FOLDER):

    if filename.endswith(".txt"):

        if filename == "dataset_observations.txt":
            continue

        path = os.path.join(KNOWLEDGE_FOLDER, filename)

        with open(path, "r", encoding="utf-8") as f:

            text = f.read()

        chunks = splitter.split_text(text)

        for chunk in chunks:

            knowledge_docs.append(

                Document(

                    page_content=chunk,

                    metadata={
                        "source": filename,
                        "type": "medical_knowledge"
                    }

                )

            )

print(f"Knowledge chunks : {len(knowledge_docs)}")

# ==========================================================
# Merge
# ==========================================================

documents.extend(knowledge_docs)

print(f"Total documents : {len(documents)}")

# ==========================================================
# Embedding Model
# ==========================================================

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")

# ==========================================================
# Build FAISS in Batches
# ==========================================================

print("Building FAISS index...")

batch_size = 500

db = None

for i in range(0, len(documents), batch_size):

    batch = documents[i:i+batch_size]

    texts = [doc.page_content for doc in batch]
    metas = [doc.metadata for doc in batch]

    print(
        f"Batch {(i//batch_size)+1} / {(len(documents)-1)//batch_size+1}"
    )

    if db is None:

        db = FAISS.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metas
        )

    else:

        db.add_texts(
            texts=texts,
            metadatas=metas
        )

# ==========================================================
# Save
# ==========================================================

if os.path.exists(VECTOR_DB_PATH):
    shutil.rmtree(VECTOR_DB_PATH)

db.save_local(VECTOR_DB_PATH)

print()
print("=" * 50)
print("FAISS VECTOR DATABASE CREATED SUCCESSFULLY")
print("=" * 50)
print(f"Dataset Records : {len(df)}")
print(f"Knowledge Chunks: {len(knowledge_docs)}")
print(f"Total Documents : {len(documents)}")
print(f"Saved To        : {VECTOR_DB_PATH}")
print("=" * 50)