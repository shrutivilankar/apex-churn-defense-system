from langraph.graph import StateGraph
import re
from enum import StrEnum



TICKET_CLASSIFICATION = StrEnum("TICKET_CLASSIFICATION", ["billing", "outage", "QoS", "other"])

def classify_ticket(state: ChurnDefenseState):
    ticket = state["ticket"]
    print(f"Classifying ticket: {ticket.id}")
    desc = ticket.description.lower()

    if re.search(r"billing|invoice|payment", desc):
        state["ticket_classification"] = TICKET_CLASSIFICATION.billing
    elif re.search(r"outage|down|service interruption", desc):
        state["ticket_classification"] = TICKET_CLASSIFICATION.outage
    elif re.search(r"slow|latency",desc):
        state["ticket_classification"] = TICKET_CLASSIFICATION.QoS
    else:
        state["ticket_classification"] = TICKET_CLASSIFICATION.other


def run_churn_defence_workflow(ticket: TroubleTicketCreate):
    # Create new workflow
    workflow = StateGraph(ChurnDefenseState)
    state["ticket"] = ticket

    workflow.add_node("classify_ticket", classify_ticket)
    workflow.add_node("score_subscriber_value", score_subscriber_value)
    workflow.add_node("score_churn_risk", score_churn_risk)


    print (f"Running Churn Defence Workflow for ticket: {ticket.id}")

    
run_churn_defence_workflow(TroubleTicketCreate(id = "111"))



class ChurnDefenseState:
    ticket: TroubleTicketCreate
    ticket_classification: TICKET_CLASSIFICATION
