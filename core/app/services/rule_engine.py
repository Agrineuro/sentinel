from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.alert import AlertModel
from app.models.observation import ObservationModel
from app.models.rule import RuleModel

SEVERITY = {"debug": 0, "info": 1, "notice": 1, "warning": 2, "error": 3, "critical": 4}


class RuleEngine:
    def matches(self, rule, observation: ObservationModel) -> bool:
        if rule.observation_type not in ("*", observation.observation_type):
            return False
        if SEVERITY.get(observation.severity.casefold(), 1) < SEVERITY.get(rule.minimum_severity.casefold(), 2):
            return False
        if rule.source_contains and rule.source_contains.casefold() not in (observation.source or "").casefold():
            return False
        if rule.entity_contains and rule.entity_contains.casefold() not in (observation.entity or "").casefold():
            return False
        if rule.summary_contains and rule.summary_contains.casefold() not in (observation.summary or "").casefold():
            return False
        if rule.condition_field:
            value = observation.value
            for part in rule.condition_field.split("."):
                if not isinstance(value, dict) or part not in value:
                    return False
                value = value[part]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            threshold = float(rule.condition_value)
            actual = float(value)
            operator = rule.condition_operator
            if operator == "gt" and not actual > threshold:
                return False
            if operator == "gte" and not actual >= threshold:
                return False
            if operator == "lt" and not actual < threshold:
                return False
            if operator == "lte" and not actual <= threshold:
                return False
        return True

    def evaluate(self, db: Session, observation: ObservationModel) -> list[AlertModel]:
        created = []
        rules = db.query(RuleModel).filter(RuleModel.enabled.is_(True)).all()
        for rule in rules:
            if not self.matches(rule, observation):
                continue
            active = (db.query(AlertModel)
                      .filter(AlertModel.rule_id == rule.id,
                              AlertModel.entity_id == observation.entity_id,
                              AlertModel.status.in_(["open", "acknowledged"]))
                      .first())
            now = datetime.now(timezone.utc)
            if active:
                active.occurrence_count += 1
                active.last_seen_at = now
                active.source_observation_id = observation.id
                active.summary = observation.summary
                active.severity = observation.severity
                if active.status == "acknowledged":
                    active.status = "open"
                    active.acknowledged_at = None
                continue

            alert = AlertModel(
                id=f"alert_{uuid4().hex}", rule_id=rule.id,
                source_observation_id=observation.id, title=rule.name,
                summary=observation.summary, severity=observation.severity,
                entity_id=observation.entity_id, entity=observation.entity,
                status="open", occurrence_count=1, triggered_at=now,
                last_seen_at=now,
            )
            db.add(alert)
            created.append(alert)
        return created


rule_engine = RuleEngine()
