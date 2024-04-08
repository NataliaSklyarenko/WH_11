from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Contact, Base
from schemas import ContactCreate, ContactUpdate, Contact
from datetime import date, timedelta

SQLALCHEMY_DATABASE_URL = "postgresql://username:password@localhost/contacts_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/contacts/", response_model=Contact)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/", response_model=list[Contact])
def get_contacts(db: Session = Depends(get_db), search: str = None):
    if search:
        return db.query(Contact).filter(Contact.first_name.ilike(f"%{search}%") | 
                                       Contact.last_name.ilike(f"%{search}%") |
                                       Contact.email.ilike(f"%{search}%")).all()
    return db.query(Contact).all()

@app.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    return db.query(Contact).filter(Contact.id == contact_id).first()

@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact:
        for key, value in contact.dict().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
        return db_contact
    raise HTTPException(status_code=404, detail="Contact not found")

@app.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
        return db_contact
    raise HTTPException(status_code=404, detail="Contact not found")

@app.get("/contacts/birthdays/", response_model=list[Contact])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    today = date.today()
    end_date = today + timedelta(days=7)
    return db.query(Contact).filter(today <= Contact.birth_date, Contact.birth_date <= end_date).all()
