from apex_churn_defense.models.trouble_ticket_models import TroubleTicketCreate
import asyncio
import httpx
import structlog
from langfuse import Evaluation, get_client
from dotenv import load_dotenv

load_dotenv()

log = structlog.get_logger()
langfuse = get_client()

test_data = [
    {
        "input": {
            "id": "ticket1",
            "description": "Billed $145 in international roaming fees while traveling near the border without leaving the country or enabling data roaming.",
            "severity": "Major",
            "ticketType": "Complaint",
            "relatedParty": [
                {
                    "role": "customer",
                    "partyOrPartyRole": {"id": "sub-123", "@referredType": "Party"},
                }
            ],
        }
    },
    {
        "input":  {
            "id": "ticket2",
            "description": "5G mobile data speeds throttled below 1 Mbps during peak evening hours even with full signal bars and remaining high-speed allowance.",
            "severity": "Major",
            "ticketType": "Complaint",
            "relatedParty": [
                {
                    "role": "customer",
                    "partyOrPartyRole": {"id": "sub-456", "@referredType": "Party"},
                }
            ],
        }
    }
]

async def invoke_workflow(*, item, **kwargs):
    turn = item["input"]
    url = "http://localhost:8080/tmf-api/troubleTicket/v5/troubleTicket"
    ticket = TroubleTicketCreate.model_validate(turn) 
    payload = ticket.model_dump(by_alias=True, exclude_none=True)
    log.info(f" ticket payload for subscriber {ticket}")


    async with httpx.AsyncClient(timeout=240) as client:

        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        log.info(f"response: {data}")
        return data

 
def validate_churn_agent_output(*, output, **kwargs):

    has_recommended_offers = bool(output.get("recommended_offers"))
    has_recommended_refund = bool(output.get("recommended_refund"))
    has_recommendation_description = bool(output.get("recommendation_description"))
    if (has_recommended_offers or has_recommended_refund) and has_recommendation_description:
        score=1.0
    else:
        score=0.0
    
    return Evaluation(
        name="valid_agent_output",
        value= score,
        comment="LLM returned response"
    )

def run_evals():
    try:
       result = langfuse.run_experiment(
        name="TroubleTicket Churn Defence Evals",
        data=test_data,
        task=invoke_workflow,
        evaluators=[validate_churn_agent_output],
        max_concurrency=1

       )
       print(result.format())
           
    except Exception as e:
        log.exception("Failed on call to create troubleticket.")
    finally:
        langfuse.flush()
    

if __name__ == "__main__":

    run_evals()