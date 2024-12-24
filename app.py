from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from langchain_community.document_loaders import PyPDFLoader
from fastapi.responses import JSONResponse
import os
import json
import pandas as pd
from PyPDF2 import PdfReader  # To handle PDF files
from pydantic import BaseModel
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
#KEY = os.getenv("OPENAI_API_KEY")
KEY=" "
# LangChain Model
llm = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo", temperature=0.5)



import requests
import boto3
def get_session():

    ACCESS_KEY = ' '
    SECRET_KEY = ' '
    REGION_NAME = 'us-east-1'
    session = boto3.Session(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION_NAME
    )
    return session
session = get_session()
ssm = session.client('ssm')
parameter_name = '/unrealinput/bluecollar'



app = FastAPI()

# File content storage
TEXT_DATA = ""
SECTIONS_DATA = ""
QUIZ_DATA = {}


# Templates
TEMPLATE = """
Text:{text}
You are an expert MCQ maker. Given the above text, it is your job to \
create a quiz of {number} multiple choice questions for {subject} students in {tone} tone. 
Make sure the questions are not repeated and check all the questions to conform to the text.
Make sure to format your response like RESPONSE_JSON below and use it as a guide. \
Ensure to make {number} MCQs
### RESPONSE_JSON
{response_json}
"""


TEMPLATE_SECTION_HEADING = """
Text:{text}
You are an expert content summarizer and organizer. Given the above text, your task is to:
1. Divide the text into meaningful sections.
2. Create an appropriate heading for each section.
3. Ensure the sections and headings logically follow the structure and content of the text.

Make sure to format your response like RESPONSE_JSON below and use it as a guide:
### RESPONSE_JSON
{response_json}
"""

heading_generation_prompt = PromptTemplate(
    input_variables=["text", "response_json"],
    template=TEMPLATE_SECTION_HEADING,
)

heading_generation_chain = LLMChain(llm=llm, prompt=heading_generation_prompt, output_key="sections", verbose=True)

quiz_generation_prompt = PromptTemplate(
    input_variables=["text", "number", "subject", "tone", "response_json"],
    template=TEMPLATE,
)

quiz_chain = LLMChain(llm=llm, prompt=quiz_generation_prompt, output_key="quiz", verbose=True)


class MCQRequest(BaseModel):
    number: int
    subject: str
    tone: str


class AnswerRequest(BaseModel):
    question_id: str
    answer: str

class QuestionNumber(BaseModel):
    question_id: str
    



@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file, save its content in a global variable, and return a success message.
    """
    global TEXT_DATA
    try:
        #TEXT_DATA = (await file.read()).decode("utf-8")
        #return {"message": "File uploaded and content saved successfully"}
    # Check the file type
        print("Debug1")
        if file.filename.endswith(".txt"):
            print("File is text")
            
            TEXT_DATA = (await file.read()).decode("utf-8")
        elif file.filename.endswith(".pdf"):
            print("File is pdf")
            #TEXT_DATA = extract_text_from_pdf(await file.read())           
            temp_file_path = f"/tmp/{file.filename}"  # Save file temporarily
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(await file.read())  # Write PDF content to a temporary file
            
            loader = PyPDFLoader(temp_file_path)  # Initialize loader
            
            pages = []
            async for page in loader.alazy_load():
                pages.append(page)
            TEXT_DATA = pages
            #pages[0].page_content
            print()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a .txt or .pdf file.")

        return {"message": "File uploaded and content saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/create-sections")
async def create_sections():
    """
    Generate sections from the uploaded file content stored in TEXT_DATA.
    """
    global TEXT_DATA, SECTIONS_DATA
    try:
        if not TEXT_DATA:
            raise HTTPException(status_code=400, detail="No file content found. Please upload a file first.")

        RESPONSE_JSON_SUMMARIZER = {
        "Section 1": "Heading for Section 1",
        "Section 2": "Heading for Section 2",
        "Section 3": "Heading for Section 3"
        }

        

        with get_openai_callback() as cb:
            response = heading_generation_chain(
                {
                    "text": TEXT_DATA,                   
                    "response_json": json.dumps(RESPONSE_JSON_SUMMARIZER),
                }
            )

        SECTIONS_DATA = json.loads(response.get("sections"))
        
        # filtered_response = {}
        # for question_id, data in QUIZ_DATA.items():
        #     filtered_response[question_id] = {key: value for key, value in data.items() if key != "correct"}

        return {"message": "Sections generated successfully..", "sections": SECTIONS_DATA}
        #questions = {key: value["mcq"] for key, value in QUIZ_DATA.items()}
        #return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sections: {str(e)}")


@app.post("/create-mcqs")
async def create_mcqs(mcq_request: MCQRequest):
    """
    Generate MCQs from the uploaded file content stored in TEXT_DATA.
    """
    global TEXT_DATA, QUIZ_DATA
    try:
        if not TEXT_DATA:
            raise HTTPException(status_code=400, detail="No file content found. Please upload a file first.")

        RESPONSE_JSON = {
            "1": {
                "mcq": "multiple choice question",
                "options": {
                    "a": "choice here",
                    "b": "choice here",
                    "c": "choice here",
                    "d": "choice here",
                },
                "correct": "correct answer",
            },
        }

        with get_openai_callback() as cb:
            response = quiz_chain(
                {
                    "text": TEXT_DATA,
                    "number": mcq_request.number,
                    "subject": mcq_request.subject,
                    "tone": mcq_request.tone,
                    "response_json": json.dumps(RESPONSE_JSON),
                }
            )

        QUIZ_DATA = json.loads(response.get("quiz"))
        
        filtered_response = {}
        for question_id, data in QUIZ_DATA.items():
            filtered_response[question_id] = {key: value for key, value in data.items() if key != "correct"}

        return {"message": "MCQs generated successfully..", "quiz": filtered_response}
        #questions = {key: value["mcq"] for key, value in QUIZ_DATA.items()}
        #return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating MCQs: {str(e)}")


from fastapi import Query


@app.post("/displayQuizData")
async def ask_question():
    return {"message": "MCQs generated successfully..", "quiz": QUIZ_DATA}
    

from fastapi import FastAPI, HTTPException

# app = FastAPI()

# Sample Quiz Data
RESPONSE_JSON = {
    "1": {
        "mcq": "What is the capital of France?",
        "options": {
            "a": "Berlin",
            "b": "Madrid",
            "c": "Paris",
            "d": "Rome",
        },
        "correct": "c",
    },
    "2": {
        "mcq": "What is 2 + 2?",
        "options": {
            "a": "3",
            "b": "4",
            "c": "5",
            "d": "6",
        },
        "correct": "b",
    },
}

@app.get("/get_question/{question_id}")
async def get_question(question_id: str):
    """
    Get a specific question and its options based on question ID.
    """
    question_data = QUIZ_DATA.get(question_id)

    if not question_data:
        raise HTTPException(status_code=404, detail="Question ID not found.")


    explanation_prompt = f"""
    You are an host, Ask question : {question_data["mcq"]}, options : {question_data["options"]}  in a way that the user will understand clearly.
    Dont tell the answer.    """

    
    print(explanation_prompt)
    # Use LLM to generate explanation for the correct answer
    explanation = llm.predict(explanation_prompt)


    tossm = '''{"language": "englishus", "input": "''' + explanation + '''" , "voiceid": "MatthewNeural"}'''

    response = ssm.put_parameter(
        Name=parameter_name,
        Value=tossm,
        Type='String',
        Overwrite=True  # Set to True to update an existing parameter
    )

    return explanation

    # Return only the question and options
    # return {
    #     "question_id": question_id,
    #     "question": question_data["mcq"],
    #     "options": question_data["options"],
    # }

# Run the FastAPI app with `uvicorn` as usual


@app.post("/quiz/")
async def ask_question(
    answer_request: AnswerRequest = None):
    """
    Display all questions or ask a specific question and evaluate the user's response.
    """
    global QUIZ_DATA

    if not QUIZ_DATA:
        raise HTTPException(status_code=400, detail="No quiz data found. Please generate a quiz first.")

    # questions = {key: value["mcq"] for key, value in QUIZ_DATA.items()}
    # print {"questions": questions}

    # Proceed with answering a specific question
    if not answer_request:
        raise HTTPException(status_code=400, detail="Please provide an answer request payload.")

    question_id = answer_request.question_id
    user_answer = answer_request.answer.lower()

    if question_id not in QUIZ_DATA:
        raise HTTPException(status_code=404, detail="Question ID not found in the quiz.")

    question = QUIZ_DATA[question_id]
    correct_answer = question["correct"].lower()
    explanation_prompt = f"""
    You are an expert teacher. Explain why the correct answer is "{correct_answer}" for the following question:
    {question['mcq']}
    Options: {question['options']}
    """
    
    
    if user_answer == correct_answer:
        explanation = "Veryyyy Goood Usher and, Mahi"
        tossm = '''{"language": "englishus", "input": "''' + explanation + '''" , "voiceid": "MatthewNeural"}'''


        response = ssm.put_parameter(
        Name=parameter_name,
        Value=tossm,
        Type='String',
        Overwrite=True  # Set to True to update an existing parameter
        )
        return tossm
        #return {"message": "Correct!", "question": question["mcq"], "answer": user_answer}
    

    # Use LLM to generate explanation for the correct answer
    explanation = llm.predict(explanation_prompt)

    explanation = "Sorry Usher and, Mahi, " +  explanation
    tossm = '''{"language": "englishus", "input": "''' + explanation + '''" , "voiceid": "MatthewNeural"}'''


    response = ssm.put_parameter(
    Name=parameter_name,
    Value=tossm,
    Type='String',
    Overwrite=True  # Set to True to update an existing parameter
    )
    return {
        "message": "Incorrect. Here is the correct answer and an explanation.",
        "question": question["mcq"],
        "your_answer": user_answer,
        "correct_answer": correct_answer,
        "explanation": explanation,
    }

import uvicorn

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "app:app",  # Replace 'app' with the name of your Python file if different
        host="0.0.0.0",
        port=8000,
        reload=True  # Enables auto-reload for development
    )
