
import re
from enum import StrEnum
from apex_churn_defense.models.trouble_ticket_models import TroubleTicket
from apex_churn_defense.risk.risk_profile_service import evaluate_risk_profile
from apex_churn_defense.risk.risk_scoring_service import score_risk_profile
from apex_churn_defense.risk.risk_models import RiskScore, SubscriberRiskProfile
from apex_churn_defense.catalog.catalog_service import get_sellable_offers

from langgraph.graph import StateGraph, START, END

from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langfuse import get_client
from langfuse.langchain import CallbackHandler

import sqlite3
from dotenv import load_dotenv
import os
from pathlib import Path
import structlog
from typing import TypedDict
from pydantic import BaseModel

load_dotenv()
log = structlog.get_logger()
langfuse = get_client()
callback_handler = CallbackHandler()

TICKET_CLASSIFICATION = StrEnum("TICKET_CLASSIFICATION", ["billing", "outage", "QoS", "other"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
db_path = PROJECT_ROOT/"db"/ "agent_checkpoint.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
log.info(db_path)
db_con = sqlite3.connect(db_path, check_same_thread=False)

client = ChatOpenAI(
    model=os.getenv("MODEL"),
    api_key=os.getenv("OPENROUTER_API_KEY"), 
    base_url="https://openrouter.ai/api/v1"
    )


def classify_ticket(state: ChurnDefenseState) -> ChurnDefenseState:
    ticket = state["ticket"]
    log.info(f"Classifying ticket: {ticket.id}")
    desc = ticket.description.lower()

    if re.search(r"billed|billing|invoice|payment", desc):
        state["ticket_classification"] = TICKET_CLASSIFICATION.billing
    elif re.search(r"outage|down|service interruption", desc):
        state["ticket_classification"] = TICKET_CLASSIFICATION.outage
    elif re.search(r"slow|latency",desc):
        state["ticket_classification"] = TICKET_CLASSIFICATION.QoS
    else:
        state["ticket_classification"] = TICKET_CLASSIFICATION.other
    return {"ticket_classification": state["ticket_classification"]}

async def profile_subscriber_risk(state: ChurnDefenseState) -> ChurnDefenseState:
    ticket = state["ticket"]
    for related_party in ticket.relatedParty:
        if related_party.role == "customer":
            customer_id = related_party.party_or_party_role.id
    
    state["subscriber_risk_profile"] = await evaluate_risk_profile(customer_id,[ticket])
    return {**state, "subscriber_risk_profile": state["subscriber_risk_profile"] }


def score_churn_risk(state: ChurnDefenseState) -> ChurnDefenseState:
    profile = state["subscriber_risk_profile"]
    state["risk_score"] = score_risk_profile(profile)
    return {**state, "risk_score": state["risk_score"]}

def prepare_prompt(state: ChurnDefenseState) -> ChurnDefenseState:
    return {"messages": [HumanMessage(
        f"Ticket: {state['ticket'].description}\n"
        f"Classification: {state['ticket_classification']}\n"
        f"Risk profile: {state['subscriber_risk_profile'].model_dump_json()}\n"
        f"Risk score: {state['risk_score'].model_dump_json()}"
    )]}
    

@tool
async def get_offers():
    '''
        retrieve all current catalog offers from which to recommend purchase to customer
    '''
    return await get_sellable_offers()

@tool
def propose_refund(amount: float, reason: str):
    '''
        propose refund to customer if grievance resolution is identified to be refund
    '''
    log.info(f"Proposing refund for churn defense workflow: ${amount} for {reason}")


class LLMResponse(BaseModel):

    recommended_offers: list[str] | None
    recommended_refund: list[float] | None
    recommendation_description: str
    
llm = create_agent(
    model = client,
    tools = [get_offers, propose_refund],
    system_prompt = ("You are a Customer Retention Specialist for a telecom company. "
    "You receive a subscriber's risk profile and churn/value risk score. "
    "Use get_offers to fetch current sellable offers and propose_refund only when a refund is warranted. "
    "The action_tier (standard/moderate/aggressive) sets how far you go. "
    "Return recommended_offers, recommended_refund amounts, and a short recommendation_description. "
    "Recommendations are advisory; monetary actions require human approval."),
    response_format = LLMResponse,
    middleware = [
        ModelCallLimitMiddleware(thread_limit=10, run_limit=5, exit_behavior='end'),
        ToolCallLimitMiddleware(run_limit=4),
        ToolCallLimitMiddleware(tool_name="get_offers", run_limit=2)        
    ],
    checkpointer = SqliteSaver(db_con)
)



async def run_churn_defence_workflow(ticket: TroubleTicket):
    llm_response = None
    try:
        log.info(f"Running Churn Defence Workflow for ticket: {ticket.id}")
        
        workflow = StateGraph(ChurnDefenseState)

        workflow.add_node("classify_ticket", classify_ticket)
        workflow.add_node("score_subscriber_value", profile_subscriber_risk)
        workflow.add_node("score_churn_risk", score_churn_risk)
        workflow.add_node("prepare_prompt", prepare_prompt)
        workflow.add_node("llm", llm)

        workflow.add_edge(START, "classify_ticket")
        workflow.add_edge("classify_ticket","score_subscriber_value")
        workflow.add_edge("score_subscriber_value","score_churn_risk")
        workflow.add_edge("score_churn_risk", "prepare_prompt")
        workflow.add_edge("prepare_prompt", "llm")
        workflow.add_edge("llm", END)

        graph = workflow.compile()
        llm_response = await graph.ainvoke(
            input = {"ticket":ticket},
            config = {"callbacks": [callback_handler]}
            )

        log.info("llm complete response", full_llm_response=llm_response)
    except Exception as e:
        log.exception("Failed in workflow", ticket_id=ticket.id)
    return llm_response
    

class ChurnDefenseState(TypedDict):
    ticket: TroubleTicket 
    ticket_classification: TICKET_CLASSIFICATION
    subscriber_risk_profile: SubscriberRiskProfile
    risk_score: RiskScore
    messages: []
    structured_response : LLMResponse

