from loaders.loader_factory import load_source
from chunking.text_splitter import split_documents

documents = load_source("fsd.pdf")
chunks = split_documents(documents)

print("Documents:", len(documents))
print("Chunks:", len(chunks))
print(chunks[0].page_content[:1000])
