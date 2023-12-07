from pymongo import MongoClient
from langchain.document_loaders.mongodb import MongodbLoader
import os
import csv
# collection.find_one({"name":"name1"})
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
import json
import ast


client = MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=30000)
# client = MongoClient('hostname', 27017, serverSelectionTimeoutMS=30000)
database_name = "sample_data3"
collection_name = "data3"
db = client[database_name]

# Access the specified collection
collection = db[collection_name]
# print(collection)
# res={"total_bedrooms": {"$gt": (800)}}

with open("C:/Users/kashi/Downloads/example.csv","r") as file:
    reader = csv.DictReader(file)
    data = list(reader)
    # Insert converted data into MongoDB
    collection.insert_many(data)
# print(res)


os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"



template = """

Your role involves specifying the criteria to effectively filter a database. When faced with a query, your goal is to identify the unique value within a specific column crucial for the filtering process. This analysis should solely rely on the provided column descriptions. It's important to highlight that the filtering criteria you generate are meant for MongoDB queries, requiring adherence to MongoDB query conventions.

Always remember, when providing the output, enclose the column name in double quotation marks.In situations where a distinct value for filtering isn't apparent, your response should explicitly state 'WHOLE TABLE IS REQUIRED.' It's crucial to keep in mind that if the specified column is absent in the table or doesn't align with any description, the output should be 'I DON'T KNOW.' Ensure that the output follows the provided rules and is logically sound. 

For example:
Query: What are the bakery items available for Bronx?
Output= filter_criteria = "borough": "Bronx", "cuisine": "Bakery"

Query: What are the bakery items available for nothing?
Output= I DON'T KNOW

Now, please provide the output for the following:
Query: {quest}
Descriptions: {desc}

"""

llm = ChatOpenAI(temperature=0)

prompt = ChatPromptTemplate.from_template(template
)
agent = (
    {
        "quest": lambda x : x["quest"],
        "desc": lambda x : x["desc"]
    }
    | prompt
    | llm
)

res=agent.invoke(

        {"quest":"How many houses hav longitude greater than -100 and latitude less than 33",
        "desc" : """
longitude=A measure of how far west a house is; a more negative value is farther west.Longitude values range from -180 to +180
latitude=A measure of how far north a house is; a higher value is farther north.Latitude values range from -90 to +90
housing_median_age=Median age of a house within a block; a lower number is a newer building	
total_rooms=Total number of rooms within a block	
total_bedrooms=Total number of bedrooms within a block	
population=Total number of people residing within a block	
households=Total number of households, a group of people residing within a home unit, for a block	
median_income=Median income for households within a block of houses (measured in tens of thousands of US Dollars)	
median_house_value=Median house value for households within a block (measured in US Dollars)"""
}
        
)
# print(res)
# print(str(res))

if(str(res).find("I DON'T KNOW")!=-1):
    print("Sorry the question asked cannot be identified. Try to be more clear!")
else:
    filter_criteria_string=str(res).split('=')[2].strip()
    filter_dict = json.loads(filter_criteria_string)
    # filter_criteria_dict={}
    # for i in filter_criteria_string.split(','):
    #     print(i)
    #     filter_criteria_dict[i.split(':')[0].split('{')[0].strip()]=i.split(':')[1].strip()
    print(filter_dict)
    loader = MongodbLoader(
    connection_string="mongodb://localhost:27017/",
    db_name="sample_data3",
    collection_name="data3",
    # filter_criteria={"borough": "Bronx", "cuisine": "Bakery"},
    filter_criteria=filter_dict
    )
    print(loader.load())

    my_string = '\n'.join(map(str, loader.load()))
    # print(my_string)
    template1 = """
   Your task involves leveraging provided documents, presented in JSON format but sourced from CSV datasets, to address questions posed. The dataset may have undergone prior filtration based on specified terms within the question. Your role is to intelligently analyze these documents to generate conclusive outputs without the necessity of re-segmenting the data. If the question includes parameters for potential dataset filtering, presume that the provided Documents list has already been filtered. Your goal is to comprehensively examine the documents and derive a definitive solution.
   The question at hand is: {ques}. 
   The available Documents for analysis are: {docs}.

    """ 

    prompt = ChatPromptTemplate.from_template(template1)
    
    agent = (
        {
            "ques": lambda x : x["ques"],
            "docs" : lambda x :x["docs"]
        }
        | prompt
        | llm
    )
    sol=agent.invoke(

        {"ques":"what is the average value of population?",
        "docs" : my_string}
        
    )
    print(sol)

