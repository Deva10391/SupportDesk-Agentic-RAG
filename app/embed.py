from fastembed import TextEmbedding

_m = TextEmbedding("BAAI/bge-small-en-v1.5")  # 384-dim, local, free
DIM = 384


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _m.embed(texts)]
