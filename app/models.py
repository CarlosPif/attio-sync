from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import validates
from app.database import Base

# Definimos la clase de nuestra tabla de companies
class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    id_attio = Column(String, unique=True, index=True)
    name = Column(String)
    domains = Column(String)
    created_at = Column(String)
    one_liner = Column(String)
    stage = Column(String)
    round_size = Column(String)
    current_valuation = Column(String)
    deck_url = Column(String)
    reference = Column(String)
    reference_explanation = Column(String)
    date_sourced = Column(String)
    responsible = Column(String)
    company_type = Column(String)
    fund = Column(String)
    business_model = Column(ARRAY(String))
    constitution_location = Column(ARRAY(String))
    business_type = Column(ARRAY(String))
    comments = Column(String)

    # Limpiamos los arrays vacíos para los multi-select
    @validates('business_model', 'constitution_location', 'business_type')
    def empty_list_to_null(self, key, value):
        if isinstance(value, list) and len(value) == 0:
            return None
        return value

    class FastTrack(Base):
        __tablename__ = 'fast_tracks'

        id = Column(Integer, primary_key=True, index=True)
        entry_id = Column(String, unique=True, index=True)
        company_id = Column(Integer)
        parent_record_id = Column(String)
        name = Column(String)
        potential_program = Column(String)
        added_to_list_at = Column(String)
        kill_reasons = Column(String)
        contact_status = Column(String)
        first_videocall_done = Column(String)
        risk = Column(String)
        urgency = Column(String)
        next_steps = Column(String)
        deadline = Column(String)
        notes = Column(String)
        last_contacted = Column(String)
        last_modified = Column(String)
        date_first_contact = Column(String)
        fast_track_status = Column(String)
        signals_evaluations = Column(JSON)
        green_flags_summary = Column(String)
        red_flags_summary = Column(String)
        signal_comments = Column(String)

        @validates('signals_evaluations')
        def validate_json_empty(self, key, value):
            if isinstance(value, dict) and not value:
                return None

            if isinstance(value, list) and not value:
                return None
            
            if isinstance(value, str) and not value.strip():
                return None

            return value