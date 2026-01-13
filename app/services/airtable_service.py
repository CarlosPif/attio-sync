import os
from dotenv import load_dotenv
import logging
from pyairtable import Api

logger = logging.getLogger("AttioWorker")

load_dotenv()
# Configuración
api = Api(os.getenv("AIRTABLE_TOKEN"))

# Base CRM
base_crm = api.base(os.getenv("AIRTABLE_BASE_CRM"))
table_crm = base_crm.table(os.getenv("AIRTABLE_TABLE_COMPANIES_ID"))

# Base Dealflow
base_dealflow = api.base(os.getenv("AIRTABLE_BASE_DEALFLOW"))
table_dealflow = base_dealflow.table(os.getenv("AIRTABLE_TABLE_DEALFLOW_ID"))

async def sync_company_to_airtable(c_map: dict):
    """Replica el nodo 'Create or update a record based on attio_id'"""
    try:
        # Traducimos el mapa de Postgres al mapa exacto de Airtable (según tu n8n)
        at_data = {
            "attio_id": c_map["id_attio"],
            "Startup name": c_map["name"],
            "website": c_map["domains"],
            "One liner": c_map["one_liner"],
            "stage_$startup": c_map["stage"],
            "Round_Size": c_map["round_size"],
            "PH1_current_valuation_$startups": c_map["current_valuation"],
            "deck_URL": c_map["deck_url"],
            "PH1_reference_$startups": c_map["reference"],
            "PH1_reference_other_$startups": c_map["reference_explanation"],
            "date_sourced": c_map["date_sourced"],
            "IM Lead": c_map["responsible"],
            "Company Type": [c_map["company_type"]] if c_map["company_type"] else [],
            "Dealflow_Fund": c_map["fund"],
            "PH1_business_model_$startups": c_map["business_model"],
            "PH1_Constitution_Location": c_map["constitution_location"],
            "ph1_business_type_$startups": c_map["business_type"],
            "Comments ": c_map["comments"]
        }
        table_crm.upsert([at_data], key_fields=["attio_id"])
        logger.info(f"🚀 Airtable CRM: Sincronizada {c_map['name']}")
    except Exception as e:
        logger.error(f"❌ Error Airtable CRM: {e}")

async def sync_fasttrack_to_airtable(event_type: str, ft_map: dict):
    """Replica la lógica de Switch1 del n8n (Created vs Updated)"""
    try:
        # Campos de FastTrack (mapeo del nodo de n8n)
        at_ft_data = {
            "attio_entry_id": ft_map["entry_id"],
            "Kill Reasons": ft_map["kill_reasons"],
            "Contact_Stage": ft_map["contact_status"],
            "first_videocall_done": ft_map["first_videocall_done"],
            "Risk": ft_map["risk"],
            "Urgency": ft_map["urgency"],
            "Next Steps": ft_map["next_steps"],
            "Deadline": ft_map["deadline"],
            "Extra Notes": ft_map["notes"],
            "Potential_Program": ft_map["potential_program"],
            "Last Contacted": ft_map["last_contacted"],
            "Date_First_Contact": ft_map["date_first_contact"],
            "Stage": ft_map["fast_track_status"]
        }

        if "created" in event_type:
            # 1. Marcar check en CRM (Nodo 'Put it in fast tracks')
            table_crm.upsert([{"attio_id": ft_map["parent_record_id"], "Dealflow_Fasttrack": True}], key_fields=["attio_id"])
            
            # 2. Buscar en Dealflow por parent_record_id (Nodo 'Search records')
            formula = f"{{parent_record_id}} = '{ft_map['parent_record_id']}'"
            existing = table_dealflow.all(formula=formula)
            
            if existing:
                # 3. Actualizar el registro encontrado (Nodo 'Update a record based on record_id')
                record_id = existing[0]["id"]
                table_dealflow.update(record_id, at_ft_data)
                logger.info(f"✅ Airtable Dealflow: Registro vinculado y actualizado {ft_map['entry_id']}")
        
        else:
            # Lógica de Update (Nodo 'Update a record based on attio_entry_id')
            table_dealflow.upsert([at_ft_data], key_fields=["attio_entry_id"])
            logger.info(f"✅ Airtable Dealflow: Registro actualizado {ft_map['entry_id']}")

    except Exception as e:
        logger.error(f"❌ Error Airtable Dealflow: {e}")