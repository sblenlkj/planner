analytics/
  domain/
    entities/
      analytics_observation.py
      analytics_insight.py

    value_objects/
      analytics_observation_id.py
      analytics_insight_id.py
      analytics_description.py
      analytics_evidence_note.py
      analytics_score.py
      analytics_tags.py

    enums/
      analytics_scope.py
      analytics_stability.py
      analytics_record_status.py
      analytics_observation_source.py

    repositories/
      analytics_observation_repository.py
      analytics_insight_repository.py

    services/
      analytics_record_lifecycle.py

    exceptions.py
    __init__.py

  application/
    commands/
      record_observation_command.py
      create_insight_command.py
      reject_observation_command.py
      reject_insight_command.py
      supersede_insight_command.py
      expire_analytics_record_command.py

    queries/
      build_analytics_context_query.py
      search_analytics_records_query.py

    dto/
      analytics_observation_dto.py
      analytics_insight_dto.py
      analytics_context_dto.py

    ports/
      analytics_retrieval_port.py
      analytics_embedding_port.py

    use_cases/
      record_observation.py
      create_insight.py
      reject_observation.py
      reject_insight.py
      supersede_insight.py
      expire_analytics_record.py
      build_analytics_context.py
      search_analytics_records.py

    services/
      analytics_context_builder.py
      analytics_relevance_ranker.py

    __init__.py