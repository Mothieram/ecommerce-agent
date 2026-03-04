from langchain_huggingface import HuggingFaceEmbeddings

class Embedder:
    def __init__(self):
        self._model = None

    def get(self):
        if not self._model:
            self._model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"}
            )
        return self._model

embedder = Embedder()