-- ============================================================================
--  BQG · XOÁ SẠCH KHÁCH HÀNG MẪU (ẢO)
--  Chỉ xoá bản ghi gắn nhãn metadata.seed = 'TEST_BQG'. Lịch hẹn của các khách
--  này tự xoá theo (ràng buộc cascade). KHÔNG đụng dữ liệu thật.
--  Chạy:  docker exec -i zalo-crm-db psql -U crmuser -d zalocrm < scripts/bqg-seed-clean.sql
-- ============================================================================
SELECT count(*) AS "Sắp xoá" FROM contacts WHERE metadata->>'seed'='TEST_BQG';

DELETE FROM contacts WHERE metadata->>'seed'='TEST_BQG';

SELECT count(*) AS "Còn lại (phải = 0)" FROM contacts WHERE metadata->>'seed'='TEST_BQG';
