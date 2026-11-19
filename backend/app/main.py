import os
from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, create_engine, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

engine=create_engine(os.getenv("DATABASE_URL","postgresql+psycopg://studynote:studynote@localhost:5432/studynote"),pool_pre_ping=True)
SessionLocal=sessionmaker(engine)
SECRET_KEY=os.getenv("SECRET_KEY","")
hashing=PasswordHash.recommended()
bearer=HTTPBearer()
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120))
    email:Mapped[str]=mapped_column(String(254),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String(255))
class Subject(Base):
    __tablename__="subjects"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    name:Mapped[str]=mapped_column(String(120))
    color:Mapped[str]=mapped_column(String(20),default="#ed9859")
class Note(Base):
    __tablename__="notes"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    subject_id:Mapped[int|None]=mapped_column(ForeignKey("subjects.id",ondelete="SET NULL"),nullable=True)
    title:Mapped[str]=mapped_column(String(180))
    content:Mapped[str]=mapped_column(Text,default="")
    summary:Mapped[str]=mapped_column(Text,default="")
    study_date:Mapped[date]=mapped_column(Date,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class RegisterIn(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    email:EmailStr
    password:str=Field(min_length=8,max_length=128)
class LoginIn(BaseModel):
    email:EmailStr
    password:str
class SubjectIn(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    color:str="#ed9859"
class NoteIn(BaseModel):
    title:str=Field(min_length=1,max_length=180)
    content:str=""
    summary:str=""
    subject_id:int|None=None
    study_date:date
class NotePatch(BaseModel):
    title:str|None=Field(default=None,min_length=1,max_length=180)
    content:str|None=None
    summary:str|None=None
    subject_id:int|None=None
    study_date:date|None=None
app=FastAPI(title="Note by SP API")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:5173").split(","),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def init_db():
    if len(SECRET_KEY)<32: raise RuntimeError("SECRET_KEY must contain at least 32 characters")
    Base.metadata.create_all(engine)
def db_session():
    with SessionLocal() as db: yield db
DB=Annotated[Session,Depends(db_session)]
def current_user(credentials:Annotated[HTTPAuthorizationCredentials,Depends(bearer)],db:DB):
    try:
        payload=jwt.decode(credentials.credentials,SECRET_KEY,algorithms=["HS256"])
        uid=int(payload["sub"])
    except (JWTError,KeyError,ValueError,TypeError):
        raise HTTPException(401,"Invalid or expired token")
    user=db.get(User,uid)
    if not user: raise HTTPException(401,"User not found")
    return user
Account=Annotated[User,Depends(current_user)]
def user_data(u):return {"id":u.id,"name":u.name,"email":u.email}
def subject_data(s):return {"id":s.id,"name":s.name,"color":s.color}
def note_data(n):return {"id":n.id,"title":n.title,"content":n.content,"summary":n.summary,"subject_id":n.subject_id,"study_date":n.study_date.isoformat(),"created_at":n.created_at.isoformat() if n.created_at else None}
def token(u): return {"access_token":jwt.encode({"sub":str(u.id),"exp":datetime.now(timezone.utc)+timedelta(days=7)},SECRET_KEY,algorithm="HS256"),"token_type":"bearer","user":user_data(u)}
@app.get("/api/health")
def health(): return {"status":"ok"}
@app.post("/api/auth/register",status_code=201)
def register(body:RegisterIn,db:DB):
    email=body.email.lower()
    if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,"Email already registered")
    u=User(name=body.name,email=email,password_hash=hashing.hash(body.password))
    db.add(u);db.commit();db.refresh(u)
    return token(u)
@app.post("/api/auth/login")
def login(body:LoginIn,db:DB):
    u=db.scalar(select(User).where(User.email==body.email.lower()))
    if not u or not hashing.verify(body.password,u.password_hash):raise HTTPException(401,"Incorrect email or password")
    return token(u)
@app.get("/api/auth/me")
def me(user:Account):return user_data(user)
@app.get("/api/subjects")
def subjects(user:Account,db:DB):return [subject_data(s) for s in db.scalars(select(Subject).where(Subject.user_id==user.id).order_by(Subject.id.desc()))]
@app.post("/api/subjects",status_code=201)
def add_subject(body:SubjectIn,user:Account,db:DB):
    s=Subject(user_id=user.id,**body.model_dump());db.add(s);db.commit();db.refresh(s);return subject_data(s)
@app.delete("/api/subjects/{subject_id}",status_code=204)
def delete_subject(subject_id:int,user:Account,db:DB):
    s=db.scalar(select(Subject).where(Subject.id==subject_id,Subject.user_id==user.id))
    if not s: raise HTTPException(404,"Subject not found")
    db.delete(s);db.commit()
def check_subject(subject_id,user,db):
    if subject_id is not None and not db.scalar(select(Subject).where(Subject.id==subject_id,Subject.user_id==user.id)):
        raise HTTPException(400,"Invalid subject")
@app.get("/api/notes")
def notes(user:Account,db:DB):return [note_data(n) for n in db.scalars(select(Note).where(Note.user_id==user.id).order_by(Note.study_date.desc(),Note.id.desc()))]
@app.post("/api/notes",status_code=201)
def add_note(body:NoteIn,user:Account,db:DB):
    check_subject(body.subject_id,user,db)
    n=Note(user_id=user.id,**body.model_dump());db.add(n);db.commit();db.refresh(n);return note_data(n)
@app.patch("/api/notes/{note_id}")
def edit_note(note_id:int,body:NotePatch,user:Account,db:DB):
    n=db.scalar(select(Note).where(Note.id==note_id,Note.user_id==user.id))
    if not n:raise HTTPException(404,"Note not found")
    data=body.model_dump(exclude_unset=True);check_subject(data.get("subject_id",n.subject_id),user,db)
    for k,v in data.items():setattr(n,k,v)
    db.commit();db.refresh(n);return note_data(n)
@app.delete("/api/notes/{note_id}",status_code=204)
def delete_note(note_id:int,user:Account,db:DB):
    n=db.scalar(select(Note).where(Note.id==note_id,Note.user_id==user.id))
    if not n:raise HTTPException(404,"Note not found")
    db.delete(n);db.commit()
@app.get("/api/dashboard")
def dashboard(user:Account,db:DB):
    ns=list(db.scalars(select(Note).where(Note.user_id==user.id)))
    count=db.scalar(select(func.count(Subject.id)).where(Subject.user_id==user.id))
    dates={n.study_date for n in ns};today=date.today();streak=0;day=today
    if day not in dates:day-=timedelta(days=1)
    while day in dates:streak+=1;day-=timedelta(days=1)
    return {"total_notes":len(ns),"total_subjects":count,"study_days":len(dates),"streak":streak,"recent_notes":[note_data(n) for n in sorted(ns,key=lambda n:(n.study_date,n.id),reverse=True)[:5]]}
