from rag.retriever import retrieve_context
from rag.llm import ask_llm

print("="*60)
print("FemCare AI")
print("="*60)

while True:

    question = input("\nAsk : ")

    if question.lower()=="exit":
        break

    context = retrieve_context(question)

    answer = ask_llm(
        question,
        context
    )

    print("\n")
    print(answer)