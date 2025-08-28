 SELECT m.id,
    m.user_id,
    u.email,
    m.title,
    m.processing_status,
    m.duration_seconds,
    m.transcription_confidence,
    m.model_used,
    m.created_at,
    m.processing_completed_at
   FROM meetings m
     JOIN users u ON m.user_id = u.id;