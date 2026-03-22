from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

#Creating a pydantic class
class Patient(BaseModel):
    id:Annotated[str,Field(...,description='ID of the patient',example='P001')]
    name:Annotated[str,Field(...,description='Name of the Patient')]
    city:Annotated[str,Field(...,description='City where the patient is living')]
    age:Annotated[int,Field(...,gt=0,lt=120,description='Age of the patient')]
    gender:Annotated[Literal['Male','Female','Others'],Field(...,description='Gender of the patient')]
    height:Annotated[float,Field(...,gt=0,description='Height of the patient in mtrs')]
    weight:Annotated[float,Field(...,gt=0,description='Weight of the patient in kgs')]
   
   
    
    @computed_field
    @property
    def bmi(self) -> float:
     if self.height and self.weight:
        return round(self.weight / (self.height ** 2), 2)
     return None

    @computed_field
    @property
    def verdict(self)-> str:
     if self.bmi < 18.5:
        return 'Underweight'
     elif self.bmi<30:
        return 'Normal'
     else:
        return 'Obese'
    
#Creating a pydantic class to update patient record
class PatientUpdate(BaseModel):
    id:Annotated[Optional[str],Field(default=None)]
    name:Annotated[Optional[str],Field(default=None)]
    city:Annotated[Optional[str],Field(default=None)]
    age:Annotated[Optional[int],Field(default=None,gt=0)]
    gender:Annotated[Optional[Literal['Male','Female']],Field(default=None)]
    height:Annotated[Optional[float],Field(default=None,gt=0)]
    weight:Annotated[Optional[float],Field(default=None,gt=0)]
        

def load_data():
    with open("patient.json", "r") as f: 
        return json.load(f)
   
    
def save_data(data):
    with open('patient.json','w') as f:
        json.dump(data, f)
        
@app.get("/")
def hello():
    return {"message": "Patient Management System API"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}

@app.get("/view")
def view():
    return load_data()

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str=Path(...,description="ID of the patient in DB",example='P001')):
    data = load_data()
    
    if patient_id in data:
        return data[patient_id]

    raise HTTPException(status_code=404,detail="Patient ID not found")

@app.get('/sort')
def sort_Patient(sort_by:str=Query(...,description='Sort on the basis of weight and bmi'),order:str=Query('asc',description='sort in ascending or descending order')):
    valid_fields=['height','weight','bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail=f'Invalid field select from {valid_fields}')
    if order not in['asc','desc']:
        raise HTTPException(status_code=400,detail=f'Invalid Order select between asc and desc')
    
    data=load_data()
    
    sort_order= True if order=='desc' else False
    
    sorted_data=sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse=sort_order)
    
    return sorted_data
    
#Endpoint for POST Method
@app.post('/create')
def create_patient(patient:Patient):#pydantic object(patient)
    #load existing data
    data=load_data()#Python dictionary
    print(data)
    
    #check if patient already exist
    if patient.id in data:
        raise HTTPException(status_code=400,detail='Patient exist already')
    
    #If not exist add to the Db
    data[patient.id]=patient.model_dump(exclude=['id'])
    
    #save into the json file
    save_data(data)
    return JSONResponse(status_code=201,content={'message':'patient created successfully'})
    
 #Update endpoint   
@app.put('/edit/{patient_id}')
def update_patient(patient_id:str,patient_update:PatientUpdate):
     
  data=load_data()
  if patient_id not in data:
      raise HTTPException(status_code=404,detail='patient not found')
  
  existing_patient_info=data[patient_id]
  updated_patient_info = patient_update.model_dump(exclude_unset=True)
  
  for key,value in updated_patient_info.items():
      existing_patient_info[key]=value
  
  #existing_patinet_info -> pydantic object -> updated bmi + verdict
  existing_patient_info['id']=patient_id
  patient_patient_obj=Patient(**existing_patient_info)
  #-> pydantic object ->dict
  existing_patient_info=patient_patient_obj.model_dump(exclude='id')
   #add this dictionary to data 
  data[patient_id]=existing_patient_info
  
  #save data
  save_data(data)
  return JSONResponse(status_code=200,content={'message':'patient updated'})
  
@app.delete('/delete/{patient_id}') 
def delete_patient(patient_id:str):
    #load data
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail='Patient not found')
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'patient deleted'})