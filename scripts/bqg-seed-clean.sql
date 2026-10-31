-- ============================================================================
--  BQG · XOÁ SẠCH DỮ LIỆU MÔ PHỎNG
--  Chỉ xoá dữ liệu có nhãn TEST (khách metadata.seed='TEST_BQG', nick/nhóm/tệp
--  tên bắt đầu "TEST·", sale email @demo.bqg.test). Hội thoại, tin nhắn, lịch
--  hẹn, ghi chú, bạn bè, thống kê đi kèm tự xoá theo. KHÔNG đụng dữ liệu thật.
--  8 giai đoạn pipeline (Mới → Chốt) được GIỮ LẠI vì là cấu hình dùng thật.
--  Chạy:  docker exec -i zalo-crm-db psql -U crmuser -d zalocrm < scripts/bqg-seed-clean.sql
-- ============================================================================
\set ON_ERROR_STOP on
SELECT count(*) AS "Khách ảo sắp xoá" FROM contacts WHERE metadata->>'seed'='TEST_BQG';

-- 1. Nick Zalo ảo → kéo theo hội thoại, tin nhắn, thống kê, bạn bè, quyền xem
DELETE FROM zalo_accounts WHERE display_name LIKE 'TEST·%';
-- 2. Nhật ký thao tác liên quan dữ liệu ảo
DELETE FROM activity_logs WHERE details->>'seed'='TEST_BQG'
   OR entity_id IN (SELECT id FROM contacts WHERE metadata->>'seed'='TEST_BQG')
   OR user_id IN (SELECT id FROM users WHERE email LIKE '%@demo.bqg.test');
-- 3. Khách ảo → kéo theo lịch hẹn, ghi chú, nhịp tương tác
DELETE FROM contacts WHERE metadata->>'seed'='TEST_BQG';
-- 4. Tệp khách ảo
DELETE FROM customer_lists WHERE name LIKE 'TEST·%';
-- 5. Sale ảo + nhóm ảo
DELETE FROM users WHERE email LIKE '%@demo.bqg.test';
DELETE FROM teams WHERE name LIKE 'TEST·%';

SELECT
  (SELECT count(*) FROM contacts WHERE metadata->>'seed'='TEST_BQG')   AS "Khách ảo còn (phải = 0)",
  (SELECT count(*) FROM zalo_accounts WHERE display_name LIKE 'TEST·%') AS "Nick ảo còn (phải = 0)",
  (SELECT count(*) FROM users WHERE email LIKE '%@demo.bqg.test')       AS "Sale ảo còn (phải = 0)";
