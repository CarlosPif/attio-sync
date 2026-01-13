import os
from dotenv import load_dotenv
import logging
from pyairtable import Api

logger = logging.getLogger("AttioWorker")
load_dotenv()

api = Api(os.getenv("AIRTABLE_TOKEN"))

# Bases y Tablas
base_crm = api.base(os.getenv("AIRTABLE_BASE_CRM"))
table_crm = base_crm.table(os.getenv("AIRTABLE_TABLE_COMPANIES_ID"))

base_dealflow = api.base(os.getenv("AIRTABLE_BASE_DEALFLOW"))
table_dealflow = base_dealflow.table(os.getenv("AIRTABLE_TABLE_DEALFLOW_ID"))

def clean_for_airtable(data: dict):
    """Elimina nulos y asegura formatos correctos antes de enviar a Airtable"""
    return {k: v for k, v in data.items() if v is not None}

async def sync_company_to_airtable(c_map: dict):
    """Replica: 'Create or update a record based on attio_id'"""
    try:
        at_data = {
            "attio_id": c_map.get("id_attio"),
            "Startup name": c_map.get("name"),
            "website": c_map.get("domains"),
            "One liner": c_map.get("one_liner"),
            "stage_$startup": c_map.get("stage"),
            "Round_Size": float(c_map["round_size"]) if c_map.get("round_size") else None,
            "PH1_current_valuation_$startups": float(c_map["current_valuation"]) if c_map.get("current_valuation") else None,
            "deck_URL": c_map.get("deck_url"),
            "PH1_reference_$startups": c_map.get("reference"),
            "PH1_reference_other_$startups": c_map.get("reference_explanation"),
            "date_sourced": c_map.get("date_sourced"),
            "IM Lead": c_map.get("responsible"),
            "Company Type": [c_map["company_type"]] if c_map.get("company_type") else [], # Array 
            "Dealflow_Fund": c_map.get("fund"),
            "PH1_business_model_$startups": c_map.get("business_model") or [], # Array 
            "PH1_Constitution_Location": c_map.get("constitution_location") or [], # Array 
            "ph1_business_type_$startups": c_map.get("business_type") or [], # Array 
            "Comments ": c_map.get("comments")
        }
        
        payload = clean_for_airtable(at_data)
        # Upsert requiere attio_id como campo de texto en Airtable 
        table_crm.upsert([payload], key_fields=["attio_id"])
        logger.info(f"🚀 Airtable CRM: Sincronizada {c_map.get('name')}")
    except Exception as e:
        logger.error(f"❌ Error Airtable CRM: {e}")

async def sync_fasttrack_to_airtable(event_type: str, ft_map: dict):
    """Replica la lógica de Switch1: Created (Check + Link) vs Updated (Sync)"""
    try:
        at_ft_data = {
            "attio_entry_id": ft_map.get("entry_id"),
            "Kill Reasons": ft_map.get("kill_reasons"),
            "Contact_Stage": ft_map.get("contact_status"),
            "first_videocall_done": ft_map.get("first_videocall_done"),
            "Risk": ft_map.get("risk"),
            "Urgency": ft_map.get("urgency"),
            "Next Steps": ft_map.get("next_steps"),
            "Deadline": ft_map.get("deadline"),
            "Extra Notes": ft_map.get("notes"),
            "Potential_Program": ft_map.get("potential_program"),
            "Last Contacted": ft_map.get("last_contacted"),
            "Date_First_Contact": ft_map.get("date_first_contact"),
            "Stage": ft_map.get("fast_track_status")
        }
        
        payload = clean_for_airtable(at_ft_data)

        if "created" in event_type:
            # 1. Nodo 'Put it in fast tracks': Marcar check en CRM 
            table_crm.upsert([{"attio_id": ft_map["parent_record_id"], "Dealflow_Fasttrack": True}], key_fields=["attio_id"])
            
            # 2. Nodo 'Search records': Buscar por parent_record_id 
            formula = f"{{parent_record_id}} = '{ft_map['parent_record_id']}'"
            records = table_dealflow.all(formula=formula)
            
            if records:
                # 3. Nodo 'Update a record based on record_id' 
                # Accedemos a record['id'] para evitar el error de 'fields'
                table_dealflow.update(records[0]["id"], payload)
                logger.info(f"✅ Dealflow vinculado: {ft_map['entry_id']}")
        else:
            # Nodo 'Update a record based on attio_entry_id' 
            table_dealflow.upsert([payload], key_fields=["attio_entry_id"])
            logger.info(f"✅ Dealflow actualizado: {ft_map['entry_id']}")

    except Exception as e:
        logger.error(f"❌ Error Airtable Dealflow: {e}")