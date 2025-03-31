
CREATE OR REPLACE FUNCTION fix_issue_50482()
RETURNS void AS $$
DECLARE
    test_key text := 'bibliographicIssueDate';
BEGIN
    RAISE NOTICE 'start: %', timeofday();
    UPDATE records_metadata
    SET json = jsonb_set(
        json,
        '{bibliographicIssueDate}',
        to_jsonb(regexp_replace(json->>'bibliographicIssueDate', '^\[(\d{4})\]$', '\1', 'g'))
    )
    WHERE json->>'bibliographicIssueDate' ~ '^\[\d{4}\]$';
    RAISE NOTICE 'end: %', timeofday();
END;
$$ LANGUAGE plpgsql;
