-- ============================================================================
--  BQG · TẠO KHÁCH HÀNG MẪU (ẢO) ĐỂ XEM DASHBOARD / LUỒNG DỮ LIỆU
--  Mọi bản ghi gắn nhãn metadata.seed = 'TEST_BQG' → xoá sạch bằng
--  scripts/bqg-seed-clean.sql, KHÔNG đụng dữ liệu thật.
--  Chạy:  docker exec -i zalo-crm-db psql -U crmuser -d zalocrm < scripts/bqg-seed-demo.sql
-- ============================================================================
DO $$
DECLARE
  v_count    INT := 300;   -- 👉 ĐỔI số này (100..500) nếu muốn nhiều/ít hơn
  v_org      TEXT;
  v_statuses TEXT[];
  v_users    TEXT[];
  v_hos  TEXT[] := ARRAY['Nguyễn','Trần','Lê','Phạm','Hoàng','Vũ','Đặng','Bùi','Đỗ','Hồ','Ngô','Dương','Lý','Phan'];
  v_tens TEXT[] := ARRAY['Hùng','Lan','Tú','Mai','Dũng','Hoa','Nam','Thảo','Sơn','Hạnh','Phúc','Yến','Bình','Nga','Quân','Linh','Tâm','Oanh'];
  v_tinh TEXT[] := ARRAY['Bắc Giang','Hải Dương','Hưng Yên','Thái Bình','Nam Định','Thanh Hóa','Nghệ An','Hà Nam','Vĩnh Phúc','Bắc Ninh','Phú Thọ','Hòa Bình','Ninh Bình','Hà Tĩnh'];
  v_srcs TEXT[] := ARRAY['FB','TT','GT','CN','Google','Zalo','Hotline','Website'];
  v_mach TEXT[] := ARRAY['máy ép cám viên','máy nghiền','máy trộn','máy băm cỏ','máy ép dầu'];
  v_tags TEXT[] := ARRAY['hot-lead','warm-lead','cold-lead','champion','cooling','at-risk','dormant'];
  v_typ  TEXT[] := ARRAY['call','message','meeting','follow_up'];
  i INT; v_name TEXT; v_phone TEXT; v_sid TEXT; v_uid TEXT; v_score INT;
  v_created TIMESTAMP; v_cid TEXT; v_stuck BOOLEAN;
BEGIN
  -- chọn tổ chức (ưu tiên Bình Quân Group / hsholding, nếu không lấy cái đầu)
  SELECT id INTO v_org FROM organizations
    ORDER BY (name='Bình Quân Group') DESC, (name='hsholding') DESC, created_at ASC LIMIT 1;
  IF v_org IS NULL THEN RAISE EXCEPTION 'Không tìm thấy tổ chức nào'; END IF;

  SELECT array_agg(id) INTO v_statuses FROM statuses WHERE org_id = v_org;
  SELECT array_agg(id) INTO v_users    FROM users    WHERE org_id = v_org AND is_active;

  FOR i IN 1..v_count LOOP
    v_name    := v_hos[(1+floor(random()*array_length(v_hos,1)))::int] || ' Văn ' ||
                 v_tens[(1+floor(random()*array_length(v_tens,1)))::int];
    v_phone   := '09' || lpad((floor(random()*100000000))::bigint::text, 8, '0');
    v_score   := floor(random()*101)::int;
    v_created := now() - ((floor(random()*90))::int || ' days')::interval
                       - ((floor(random()*24))::int || ' hours')::interval;
    v_sid     := CASE WHEN v_statuses IS NULL THEN NULL
                      ELSE v_statuses[(1+floor(random()*array_length(v_statuses,1)))::int] END;
    v_uid     := CASE WHEN v_users IS NULL THEN NULL
                      ELSE v_users[(1+floor(random()*array_length(v_users,1)))::int] END;
    v_stuck   := random() < 0.15;
    v_cid     := gen_random_uuid()::text;

    INSERT INTO contacts (
      id, org_id, full_name, crm_name, phone, phone_normalized, source, source_date,
      first_contact_date, status, status_id, lead_score, priority_score, province,
      gender, has_zalo, consent_status, assigned_user_id, last_inbound_at, last_activity,
      stuck_since_aggregate, auto_tags, tags, metadata, created_at, updated_at
    ) VALUES (
      v_cid, v_org, v_name, v_name,
      v_phone, '84' || substr(v_phone,2),
      v_srcs[(1+floor(random()*array_length(v_srcs,1)))::int], v_created,
      v_created, 'new', v_sid, v_score, v_score,
      v_tinh[(1+floor(random()*array_length(v_tinh,1)))::int],
      CASE WHEN random()<0.5 THEN 'male' ELSE 'female' END,
      random()<0.7, 'implicit', v_uid,
      v_created + ((floor(random()*48))::int || ' hours')::interval,
      v_created + ((floor(random()*72))::int || ' hours')::interval,
      CASE WHEN v_stuck THEN v_created - ((floor(random()*20))::int || ' days')::interval ELSE NULL END,
      to_jsonb(ARRAY[ v_tags[(1+floor(random()*array_length(v_tags,1)))::int] ]),
      '[]'::jsonb,
      jsonb_build_object('seed','TEST_BQG','may', v_mach[(1+floor(random()*array_length(v_mach,1)))::int]),
      v_created, v_created
    );

    -- ~35% khách có 1 lịch hẹn (một số trong 24h tới, một số quá hạn)
    IF random() < 0.35 THEN
      INSERT INTO appointments (
        id, org_id, contact_id, assigned_user_id, appointment_date, appointment_time,
        title, duration_min, type, status, source, notes, created_at
      ) VALUES (
        gen_random_uuid()::text, v_org, v_cid, v_uid,
        now() + ((floor(random()*14)-5)::int || ' days')::interval, '09:00',
        'Gọi nhắc KH ' || v_name, 15,
        v_typ[(1+floor(random()*array_length(v_typ,1)))::int],
        'scheduled', 'manual', '[TEST_BQG]', now()
      );
    END IF;
  END LOOP;

  RAISE NOTICE '✅ Đã tạo % khách mẫu (nhãn TEST_BQG) cho tổ chức %', v_count, v_org;
END $$;

-- Tổng kết nhanh
SELECT count(*) AS "Khách mẫu đã tạo" FROM contacts WHERE metadata->>'seed'='TEST_BQG';
