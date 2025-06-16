import pandas as pd
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter

df = pd.read_csv("nike_data_2022_09.csv")
docs = []

for i, row in df.iterrows():
    text = f"Product: {row['name']}\nSubtitle: {row['sub_title']}\nBrand: {row['brand']}\nModel: {row['model']}\nColor: {row['color']}\nPrice: {row['price']} {row['currency']}\nAvailability: {row['availability']}\nSizes: {row['available_sizes']}\nRating: {row['avg_rating']} ({row['review_count']} reviews)\nDescription: {row['raw_description']}"
    docs.append(text)

embeddings = OpenAIEmbeddings()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
texts = text_splitter.create_documents(docs)
db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
db.save_local("faiss_index")
