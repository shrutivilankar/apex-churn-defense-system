"""Build a deterministic subscriber risk profile from TMF enrichment APIs.

TMF676 Payment, TMF677 Usage Consumption, TMF635 Product Usage and the local
TMF621 ticket store are read independently. A failing upstream is recorded as a
data gap instead of failing the whole evaluation.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from src.models.trouble_ticket_models import TroubleTicket
from src.payment.payment_client import PaymentClient
from src.payment.payment_models import Money, Payment
from src.payment.payment_service import get_payment_history
from src.product_usage.product_usage_client import ProductUsageClient
from src.product_usage.product_usage_models import ProductUsage
from src.product_usage.product_usage_service import get_usage_history
from src.risk.risk_models import Severity, SubscriberRiskProfile
from src.store import ticket_store
from src.usage.usage_client import UsageConsumptionClient
from src.usage.usage_models import UsageConsumptionReport
from src.usage.usage_service import get_usage_consumption

_PAGE_SIZE = 100
_WINDOW_90D = timedelta(days=90)
_WINDOW_30D = timedelta(days=30)

_PAYMENT = "tmf676_payment"
_USAGE = "tmf677_usage"
_PRODUCT_USAGE = "tmf635_product_usage"
_TICKETS = "tmf621_trouble_ticket"


async def evaluate_risk_profile(
    party_id: str,
    now: Optional[datetime] = None,
    payment_client: Optional[PaymentClient] = None,
    usage_client: Optional[UsageConsumptionClient] = None,
    product_usage_client: Optional[ProductUsageClient] = None,
    tickets: Optional[Iterable[TroubleTicket]] = None,
) -> SubscriberRiskProfile:
    """Assemble one subscriber's risk profile from all available sources."""
    if not party_id:
        raise ValueError("party_id is required")

    evaluated_at = _as_utc(now) or datetime.now(timezone.utc)
    payment_client = payment_client or PaymentClient()
    usage_client = usage_client or UsageConsumptionClient()
    product_usage_client = product_usage_client or ProductUsageClient()
    ticket_list = list(tickets) if tickets is not None else list(ticket_store.values())

    payments_result, usage_result, product_result = await asyncio.gather(
        _all_payments(party_id, payment_client),
        _all_usage_reports(party_id, usage_client),
        _all_product_usage(party_id, product_usage_client),
        return_exceptions=True,
    )

    sources: dict[str, str] = {}
    data_gaps: list[str] = []

    payments = _resolve(payments_result, _PAYMENT, sources, data_gaps, [])
    reports = _resolve(usage_result, _USAGE, sources, data_gaps, [])
    usages = _resolve(product_result, _PRODUCT_USAGE, sources, data_gaps, [])
    sources[_TICKETS] = "ok"

    failed_payments, tenure_months, revenue, avg_revenue, unit = _payment_metrics(
        payments, evaluated_at
    )
    usage_trend, bucket_remaining = _usage_metrics(reports)
    events_30d, events_prev_30d, event_trend, failed_events = _usage_event_metrics(
        usages, evaluated_at
    )
    grievance_count, grievance_severity = _grievance_metrics(
        ticket_list, party_id, evaluated_at
    )

    return SubscriberRiskProfile(
        party_id=party_id,
        evaluated_at=evaluated_at,
        failed_payments_90d=failed_payments,
        tenure_months=tenure_months,
        total_revenue=Money(unit=unit, value=revenue),
        avg_monthly_revenue=Money(unit=unit, value=avg_revenue),
        usage_trend_pct=usage_trend,
        bucket_remaining_pct=bucket_remaining,
        usage_events_30d=events_30d,
        usage_events_prev_30d=events_prev_30d,
        usage_event_trend_pct=event_trend,
        failed_usage_events=failed_events,
        grievance_count_90d=grievance_count,
        grievance_max_severity=grievance_severity,
        sources=sources,
        data_gaps=data_gaps,
    )


async def _all_payments(party_id: str, client: PaymentClient) -> list[Payment]:
    payments: list[Payment] = []
    offset = 0
    while True:
        page = await get_payment_history(
            party_id, offset=offset, limit=_PAGE_SIZE, client=client
        )
        payments.extend(page.items)
        if len(payments) >= page.totalCount or not page.items:
            return payments
        offset += _PAGE_SIZE


async def _all_usage_reports(
    party_id: str, client: UsageConsumptionClient
) -> list[UsageConsumptionReport]:
    reports: list[UsageConsumptionReport] = []
    offset = 0
    while True:
        page = await get_usage_consumption(
            party_id, offset=offset, limit=_PAGE_SIZE, client=client
        )
        reports.extend(page.items)
        if len(reports) >= page.totalCount or not page.items:
            return reports
        offset += _PAGE_SIZE


async def _all_product_usage(
    party_id: str, client: ProductUsageClient
) -> list[ProductUsage]:
    usages: list[ProductUsage] = []
    offset = 0
    while True:
        page = await get_usage_history(
            party_id, offset=offset, limit=_PAGE_SIZE, client=client
        )
        usages.extend(page.items)
        if len(usages) >= page.totalCount or not page.items:
            return usages
        offset += _PAGE_SIZE


def _resolve(result, source, sources, data_gaps, empty):
    if isinstance(result, Exception):
        sources[source] = "unavailable"
        data_gaps.append(source)
        return empty
    sources[source] = "ok"
    return result


def _payment_metrics(
    payments: list[Payment], now: datetime
) -> tuple[int, int, float, float, str]:
    window_start = now - _WINDOW_90D
    failed = 0
    revenue = 0.0
    unit = "CAD"
    unit_set = False
    captured_dates: list[datetime] = []

    for payment in payments:
        paid_at = _as_utc(payment.paymentDate)
        status = (payment.status or "").lower()

        if status in {"failed", "denied"} and paid_at and paid_at >= window_start:
            failed += 1

        if status in {"captured", "done"}:
            amount = payment.totalAmount or payment.amount
            if amount is not None:
                revenue += amount.value
                if not unit_set:
                    unit = amount.unit
                    unit_set = True
            if paid_at is not None:
                captured_dates.append(paid_at)

    tenure_months = (
        _months_between(min(captured_dates), now) if captured_dates else 0
    )
    avg_revenue = revenue / max(tenure_months, 1)
    return failed, tenure_months, round(revenue, 2), round(avg_revenue, 2), unit


def _usage_metrics(
    reports: list[UsageConsumptionReport],
) -> tuple[Optional[float], Optional[float]]:
    if not reports:
        return None, None

    newest = reports[0]
    dominant = _dominant_type(newest)
    used_new = _used_by_type(newest)
    new_used = used_new.get(dominant, 0.0) if dominant else 0.0
    if not dominant or new_used <= 0:
        return None, None

    trend = None
    if len(reports) > 1:
        old_used = _used_by_type(reports[1]).get(dominant)
        if old_used and old_used > 0:
            trend = (new_used - old_used) / old_used

    remaining = _remaining_for_type(newest, dominant)
    bucket_pct = None
    if remaining is not None and (remaining + new_used) > 0:
        bucket_pct = max(0.0, min(1.0, remaining / (remaining + new_used)))

    return trend, bucket_pct


def _usage_event_metrics(
    usages: list[ProductUsage], now: datetime
) -> tuple[int, int, Optional[float], int]:
    start_30 = now - _WINDOW_30D
    start_60 = now - 2 * _WINDOW_30D
    start_90 = now - _WINDOW_90D
    last_30 = 0
    prev_30 = 0
    failed = 0

    for usage in usages:
        created = _as_utc(usage.creationDate)
        status = (usage.status or "").lower()

        if status in {"failed", "unrated"} and created and created >= start_90:
            failed += 1

        if created is None:
            continue
        if created >= start_30:
            last_30 += 1
        elif start_60 <= created < start_30:
            prev_30 += 1

    trend = None
    if prev_30 > 0:
        trend = (last_30 - prev_30) / prev_30

    return last_30, prev_30, trend, failed


def _grievance_metrics(
    tickets: list[TroubleTicket], party_id: str, now: datetime
) -> tuple[int, Optional[Severity]]:
    window_start = now - _WINDOW_90D
    count = 0
    severities: list[Severity] = []

    for ticket in tickets:
        if not _ticket_for_party(ticket, party_id):
            continue
        created = _as_utc(ticket.creationDate)
        if created is None or created < window_start:
            continue

        count += 1
        severity = _normalize_severity(ticket.severity)
        if severity is not None:
            severities.append(severity)

    max_severity = None
    if severities:
        order = {"critical": 3, "major": 2, "minor": 1}
        max_severity = max(severities, key=order.get)

    return count, max_severity


def _ticket_for_party(ticket: TroubleTicket, party_id: str) -> bool:
    for related in ticket.relatedParty:
        ref = related.party_or_party_role
        if ref is not None and ref.id == party_id:
            return True
    return False


def _normalize_severity(value: Optional[str]) -> Optional[Severity]:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in {"critical", "high", "severe"}:
        return "critical"
    if normalized in {"major", "medium", "moderate"}:
        return "major"
    if normalized in {"minor", "low"}:
        return "minor"
    return None


def _used_by_type(report: UsageConsumptionReport) -> dict[str, float]:
    used: dict[str, float] = {}
    for bucket in report.bucket:
        key = (bucket.usageType or "unknown").lower()
        for counter in bucket.bucketCounter:
            if counter.value is not None and counter.value.amount is not None:
                used[key] = used.get(key, 0.0) + counter.value.amount
    return used


def _dominant_type(report: UsageConsumptionReport) -> Optional[str]:
    for bucket in report.bucket:
        if (bucket.usageType or "").lower() == "data":
            return "data"
    for bucket in report.bucket:
        if bucket.usageType:
            return bucket.usageType.lower()
    return None


def _remaining_for_type(
    report: UsageConsumptionReport, usage_type: str
) -> Optional[float]:
    total = None
    for bucket in report.bucket:
        if (bucket.usageType or "").lower() != usage_type:
            continue
        if bucket.remainingValue is not None:
            total = (total or 0.0) + bucket.remainingValue.amount
    return total


def _months_between(start: datetime, end: datetime) -> int:
    if end <= start:
        return 0
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(months, 0)


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
