from apex_churn_defense.models.trouble_ticket_models import TroubleTicketCreate
import asyncio
import httpx
import structlog

log = structlog.get_logger()

async def main():
    tickets =[
         {
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
        },
        {
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
        }]

    url = "http://localhost:8080/tmf-api/troubleTicket/v5/troubleTicket"
    
    try:
        for turn in tickets:
            ticket = TroubleTicketCreate.model_validate(turn) 
            payload = ticket.model_dump(by_alias=True, exclude_none=True)
            log.info(f" ticket payload for subscriber {ticket}")


            async with httpx.AsyncClient(timeout=240) as client:

                response = await client.post(url, json=ticket.model_dump())
                response.raise_for_status()
                data = response.json()
                log.info(f"response: {data}")
    except Exception as e:
        log.exception("Failed on call to create troubleticket.")
        
    

if __name__ == "__main__":

    asyncio.run(main())