from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import datetime
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_database():
    CONNECTION_STRING = "mongodb+srv://alecbradyjensen:Texas1004!@teacherbirthdayscluster.zlq13.mongodb.net/test"
    from pymongo import MongoClient
    client = MongoClient(CONNECTION_STRING)
    return client['TeacherBirthdays']


db = get_database()
birthdays = db['birthdays']


class TeacherRequestModel(BaseModel):
    nameFirst: str
    nameLast: str
    date: str
    school: str


@app.get("/lookup")
@limiter.limit("2/second")
async def lookup(request: Request, nameFirst: str, nameLast: str):
    cursor = birthdays.find({"name": f"{nameFirst} {nameLast}"})
    ii = []
    for i in cursor:
        del i["requester"]
        ii.append(i)
    return {"lookupresult": str(ii)}


@app.get("/lookup/nameFirst")
@limiter.limit("2/second")
async def lookupNameFirst(request: Request, nameFirst: str):
    cursor = birthdays.find({"nameFirst": nameFirst})
    ii = []
    for i in cursor:
        del i["requester"]
        ii.append(i)
    return {"lookupresult": str(ii)}


@app.get("/lookup/nameLast")
@limiter.limit("2/second")
async def lookupNameLast(request: Request, nameLast: str):
    cursor = birthdays.find({"nameLast": nameLast})
    ii = []
    for i in cursor:
        del i["requester"]
        ii.append(i)
    return {"lookupresult": str(ii)}


@app.get("/lookup/school")
@limiter.limit("2/second")
async def lookupSchool(request: Request, school: str):
    cursor = birthdays.find({"school": school})
    ii = []
    for i in cursor:
        del i["requester"]
        ii.append(i)
    return {"lookupresult": str(ii)}


@app.post("/teacher")
@limiter.limit("2/second")
async def teacher(request: Request, item: TeacherRequestModel):
    try:
        try:
            dateInDatetime = datetime.datetime.strptime(item.date, '%Y-%m-%d')
        except ValueError:
            dateInDatetime = datetime.datetime.strptime(item.date, '%Y/%m/%d')
    except ValueError:
        return {"error": "Invalid time format. Please use YYYY-MM-DD"}
    if len(item.nameFirst) > 25:
        return {"error": "Value nameFirst too long (>25 char)"}
    if len(item.nameLast) > 25:
        return {"error": "Value nameLast too long (>25 char)"}
    if len(item.school) > 25:
        return {"error": "Value school too long (>25 char)"}
    name = f"{item.nameFirst} {item.nameLast}"
    teacherDict = {
        "name": name,
        "nameFirst": item.nameFirst,
        "nameLast": item.nameLast,
        "date": item.date,
        "dateInDatetime": dateInDatetime,
        "school": item.school,
        "requester": request.client.host
    }
    birthdays.insert_one(teacherDict)
    return {"recv": 1, "name": name, "nameFirst": item.nameFirst, "nameLast": item.nameLast, "date": item.date,
            "school": item.school, "dateInDatetime": dateInDatetime}
