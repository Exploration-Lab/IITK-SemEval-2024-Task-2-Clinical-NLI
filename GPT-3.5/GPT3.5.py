import os
import textwrap
from getpass import getpass

# import chromadb
import langchain
import openai
from langchain.chains import LLMBashChain, LLMChain, RetrievalQA, SimpleSequentialChain
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

import json

from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

#chat_gpt = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

data = json.load(open('./training_data/test.json'))
CT_files = os.listdir("./training_data/CT_json")
# CT_files.remove(".DS_Store")

CT_files_data = {}

for file in CT_files:
    if file == ".DS_Store":
        CT_files.remove(file)
        continue

    path = f"./training_data/CT_json/{file}".encode('latin-1')
    path = path.decode('utf-8')
    content = json.load(open(path))
    CT_files_data[file[:-5]] = content

# CT_files_data = {file[:-5]:json.load(open(f"./training_data/CT_json/{file}")) for file in CT_files}

data_expanded = []
for _id, value in data.items():
    temp = {}
    temp["id"] = _id
    p_nctid = value["Primary_id"]
    s_nctid = value.get("Secondary_id")
    section_id = value["Section_id"]
    statement = value["Statement"]
    primary_evidence = CT_files_data[p_nctid][section_id]
    temp["statement"] = statement
    temp["primary_evidence"] = primary_evidence
    # temp["label"] = value["Label"]

    if s_nctid is not None:
        secondary_evidence = CT_files_data[s_nctid][section_id]
        temp["secondary_evidence"] = secondary_evidence

    data_expanded.append(temp)

samples = []
for sample in data_expanded:
    primary_evidence = "".join(sample['primary_evidence'])
    sentence = f"For the primary trial participants, \n\n {primary_evidence}"
    secondary_evidence = sample.get("secondary_evidence")
    if secondary_evidence:
        secondary_evidence = "".join(sample['secondary_evidence'])
        sentence = f"{sentence}\n For the secondary trial participants, \n\n{secondary_evidence}"
    temp = {"id": sample['id'], "clinical_trial":sentence, "hypothesis":sample['statement']}
    samples.append(temp)

model_id = "gpt-3.5-turbo-1106"

# We call this function and pass the new question and the last messages
def GetMessageMemory(newQuestion, lastmessage):
  # Append the new question to the last message
  lastmessage.append({"role": "user", "content": newQuestion})

  msgcompletion = openai.ChatCompletion.create(
    model=model_id,
    messages=lastmessage
    )

  # Print the new answer
  msgresponse = msgcompletion.choices[0].message.content

  # We return the new answer
  return msgresponse

def get_question(context, question):
   template = f"""
    Act as a clinical expert.

    Imagine three different experts are answering this question.
    All experts will write down first step of their thinking, then share it with the group.
    Then all experts will go on to the next step of their thinking.
    If any expert realises they're wrong at any point then they leave.
    Continue till a definite conclusion is reached.

    Incorporate information from the context given below into the evaluation process. 
    Cross-reference the model's responses with relevant details from the context to 
    enhance the accuracy of interpretation.

    Give a final conclusion after assessing the logical consistency within the model's responses.

    CONTEXT: {context}

    HYPOTHESIS: {question}
    """
   return template

# function to add to JSON
def write_json(id, new_data, filename=f'./ChatGPT_Results.json'):
    with open(filename,'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data[id] = new_data
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)

import time

FINAL_QUESTION = '''
Based on the comprehensive evaluation of the model's responses, given context, and logical analysis, 
is the given hypothesis deemed to be true or false? Write one word answer.
'''
results = {}
count = 1800
for sample in samples[1800:]:
    count += 1
    print("\n############################################\n")
    print(f"-------Running for sample {count}--------\n")

    prediction = {}
    pred = {}
    answer = ''
    explanation = ''
    # try:
    messages = []

    question = get_question(sample['clinical_trial'], sample['hypothesis'])
    cresponse = GetMessageMemory(question, messages)
    explanation = cresponse
    print(f"The explanation for statement {sample['id']} is -\n{explanation}\n")

    time.sleep(25)

    # Append the answer in the messages so we can send this along for the new question for context
    messages.append({"role": "assistant", "content": cresponse})

    cresponse = GetMessageMemory(FINAL_QUESTION, messages)

    answer = cresponse
    print(f"The hypothesis for statement {sample['id']} is - {answer.upper()}")

    time.sleep(25)

    # except Exception as err:
    #     print(f"\nRateLimitError has occured: {err}\n")
    #     print("Sleeping for 1 minute ... \n")
    #     # Sleep for 10 minutes
    #     time.sleep(60)

    prediction["explanation"] = explanation
    prediction["answer"] = answer
    results[sample['id']] = prediction
    write_json(sample['id'], prediction)