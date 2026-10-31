-- ============================================================================
--  BQG · MÔ PHỎNG "CÔNG TY ẢO ĐANG VẬN HÀNH" ĐỂ XEM DASHBOARD & LUỒNG DỮ LIỆU
--  Tạo: 5 sale + 1 nhóm, 4 nick Zalo, N khách đi qua 8 giai đoạn phễu,
--       hội thoại + tin nhắn 90 ngày, lịch hẹn, ghi chú, bạn bè, chấm điểm,
--       khách đình trệ, tệp khách, thống kê thời gian phản hồi.
--  Mọi dữ liệu ảo đều có nhãn TEST → xoá sạch bằng scripts/bqg-seed-clean.sql.
--  8 giai đoạn pipeline (Mới → Chốt) là CẤU HÌNH THẬT, được giữ lại khi xoá.
--  Chạy:  docker exec -i zalo-crm-db psql -U crmuser -d zalocrm < scripts/bqg-seed-demo.sql
--  Chạy lại nhiều lần được: mỗi lần tự xoá dữ liệu ảo cũ trước khi tạo mới.
-- ============================================================================
\set ON_ERROR_STOP on

-- Dọn dữ liệu ảo cũ (nếu có) — giống hệt scripts/bqg-seed-clean.sql
DELETE FROM zalo_accounts WHERE display_name LIKE 'TEST·%';
DELETE FROM activity_logs WHERE details->>'seed'='TEST_BQG'
   OR entity_id IN (SELECT id FROM contacts WHERE metadata->>'seed'='TEST_BQG')
   OR user_id IN (SELECT id FROM users WHERE email LIKE '%@demo.bqg.test');
DELETE FROM contacts WHERE metadata->>'seed'='TEST_BQG';
DELETE FROM customer_lists WHERE name LIKE 'TEST·%';
DELETE FROM users WHERE email LIKE '%@demo.bqg.test';
DELETE FROM teams WHERE name LIKE 'TEST·%';

DO $$
DECLARE
  v_count INT := 300;   -- 👉 số khách ảo (100..500)
  v_org TEXT; v_team TEXT;
  v_sales TEXT[] := '{}'; v_nicks TEXT[] := '{}'; v_nick_owner TEXT[] := '{}';
  v_sid JSONB := '{}'::jsonb;  -- tên giai đoạn → status_id
  v_stage_names TEXT[] := ARRAY['Mới','Tiếp cận','Hẹn gặp','Nóng','Tiềm năng','Chốt','Mất','Thất Bại'];
  -- mã trạng thái cũ mà Dashboard/phễu chuyển đổi đang đọc (ánh xạ theo status-migration gốc)
  v_legacy      TEXT[] := ARRAY['new','contacted','interested','interested','interested','converted','lost','lost'];
  v_stage_cut   INT[]  := ARRAY[30,52,67,77,85,91,96,100];   -- phân bố % cộng dồn (phễu)
  v_score_lo    INT[]  := ARRAY[0,15,35,60,50,80,0,0];
  v_score_hi    INT[]  := ARRAY[30,45,60,85,75,100,25,20];
  v_hos  TEXT[] := ARRAY['Nguyễn','Trần','Lê','Phạm','Hoàng','Vũ','Đặng','Bùi','Đỗ','Hồ','Ngô','Dương','Lý','Phan'];
  v_dem  TEXT[] := ARRAY['Văn','Thị','Đức','Minh','Hữu','Ngọc','Quang','Thanh'];
  v_tens TEXT[] := ARRAY['Hùng','Lan','Tú','Mai','Dũng','Hoa','Nam','Thảo','Sơn','Hạnh','Phúc','Yến','Bình','Nga','Quân','Linh','Tâm','Oanh'];
  v_tinh TEXT[] := ARRAY['Bắc Giang','Hải Dương','Hưng Yên','Thái Bình','Nam Định','Thanh Hóa','Nghệ An','Hà Nam','Vĩnh Phúc','Bắc Ninh','Phú Thọ','Hòa Bình','Ninh Bình','Hà Tĩnh'];
  v_srcs TEXT[] := ARRAY['FB','FB','FB','TT','TT','Zalo','Zalo','Google','GT','CN','Hotline','Website'];
  v_nuoi TEXT[] := ARRAY['gà 2.000 con','lợn 50 con','cá rô phi 2 ao','vịt 1.500 con','bò 20 con','gà 5.000 con','lợn nái 15 con','ếch 1 ao'];
  v_may  TEXT[] := ARRAY['máy ép cám viên','máy nghiền','máy trộn','máy băm cỏ','máy ép dầu'];
  v_in   TEXT[] := ARRAY['Chào shop, máy ép cám viên giá bao nhiêu ạ?','Máy nghiền 500kg/h có không shop?','Nhà em nuôi %s, dùng máy nào hợp ạ?','Có giao về %s không shop?','Cho em xin video máy chạy thật với ạ','Giá có bớt được không anh?','Bảo hành bao lâu vậy shop?','Ok để em bàn với nhà đã nhé','Thứ 7 em qua xưởng xem máy được không?','Chuyển khoản cọc vào tài khoản nào ạ?','Máy chạy điện 1 pha được không?','Ra viên có đều không anh?'];
  v_out  TEXT[] := ARRAY['Dạ Bình Quân xin chào anh/chị, em tư vấn ngay ạ','Anh/chị đang nuôi con gì, quy mô bao nhiêu ạ?','Dạ %s 300kg/h giá 45 triệu, đã gồm lắp đặt ạ','Em gửi anh video máy chạy thật tại trang trại Hưng Yên ạ','Dạ bên em bảo hành 12 tháng, hỗ trợ kỹ thuật trọn đời ạ','Dạ có giao lắp tận nơi toàn miền Bắc ạ','Em hẹn anh thứ 7 qua xưởng xem máy nhé','Dạ bài toán hoàn vốn: khoảng 8 tháng là hồi vốn ạ','Dạ máy chạy điện 1 pha 220V được ạ'];
  v_note TEXT[] := ARRAY['Khách quan tâm %s, đang so giá với máy Trung Quốc','Đã gửi báo giá + video, hẹn gọi lại cuối tuần','Khách cần bài toán hoàn vốn chi tiết','Vợ khách quyết, cần gọi khi có cả hai vợ chồng','Khách chờ bán lứa gà xong mới cọc','Đã cọc 30%%, hẹn giao lắp tuần sau'];
  i INT; j INT; k INT; r FLOAT; v_stage INT; v_cid TEXT; v_conv TEXT; v_uid TEXT; v_nick TEXT; v_nidx INT;
  v_name TEXT; v_phone TEXT; v_score INT; v_created TIMESTAMP; v_t TIMESTAMP; v_last TIMESTAMP;
  v_nmsg INT; v_in_n INT; v_out_n INT; v_unread INT; v_stuck TIMESTAMP; v_tags JSONB; v_src TEXT; v_tinh_c TEXT; v_nuoi_c TEXT; v_may_c TEXT; v_txt TEXT;
  v_list TEXT; v_ok INT := 0;
BEGIN
  SELECT id INTO v_org FROM organizations
    ORDER BY (name='Bình Quân Group') DESC, (name='hsholding') DESC, created_at ASC LIMIT 1;
  IF v_org IS NULL THEN RAISE EXCEPTION 'Không tìm thấy tổ chức'; END IF;

  -- ── 1. Pipeline 8 giai đoạn (cấu hình THẬT, chỉ tạo nếu chưa có) ──────────
  INSERT INTO statuses (id, org_id, name, "order", color, is_terminal, is_default, created_at, updated_at) VALUES
    (gen_random_uuid()::text, v_org, 'Mất',       1, '#71717A', true,  false, now(), now()),
    (gen_random_uuid()::text, v_org, 'Thất Bại',  2, '#EF4444', true,  false, now(), now()),
    (gen_random_uuid()::text, v_org, 'Mới',       3, '#9CA3AF', false, true,  now(), now()),
    (gen_random_uuid()::text, v_org, 'Tiếp cận',  4, '#3B82F6', false, false, now(), now()),
    (gen_random_uuid()::text, v_org, 'Hẹn gặp',   5, '#06B6D4', false, false, now(), now()),
    (gen_random_uuid()::text, v_org, 'Nóng',      6, '#F97316', false, false, now(), now()),
    (gen_random_uuid()::text, v_org, 'Tiềm năng', 7, '#EAB308', false, false, now(), now()),
    (gen_random_uuid()::text, v_org, 'Chốt',      8, '#22C55E', true,  false, now(), now())
  ON CONFLICT (org_id, name) DO NOTHING;
  SELECT jsonb_object_agg(name, id) INTO v_sid FROM statuses WHERE org_id = v_org;

  -- ── 2. Nhóm + 5 sale ảo (không đăng nhập được) ────────────────────────────
  v_team := gen_random_uuid()::text;
  INSERT INTO teams (id, org_id, name, created_at) VALUES (v_team, v_org, 'TEST·Kinh doanh Miền Bắc', now());
  FOR i IN 1..5 LOOP
    v_uid := gen_random_uuid()::text;
    INSERT INTO users (id, org_id, team_id, email, password_hash, full_name, role, is_active, created_at, updated_at)
    VALUES (v_uid, v_org, v_team, 'sale'||i||'@demo.bqg.test', '!demo-khong-dang-nhap!',
            (ARRAY['TEST·Sale Hùng','TEST·Sale Lan','TEST·Sale Tú','TEST·Sale Mai','TEST·Leader Dũng'])[i],
            CASE WHEN i=5 THEN 'admin' ELSE 'member' END, true, now() - interval '120 days', now());
    v_sales := v_sales || v_uid;
  END LOOP;

  -- ── 3. 4 nick Zalo ảo + quyền xem cho admin thật ──────────────────────────
  FOR i IN 1..4 LOOP
    v_nick := gen_random_uuid()::text;
    INSERT INTO zalo_accounts (id, org_id, owner_user_id, zalo_uid, display_name, phone, status, created_at, last_connected_at)
    VALUES (v_nick, v_org, v_sales[i], 'test-nick-'||i||'-'||substr(v_nick,1,8),
            'TEST·Zalo BQG 0'||i, '09880000'||lpad(i::text,2,'0'), 'disconnected', now() - interval '100 days', now() - interval '1 hour');
    v_nicks := v_nicks || v_nick; v_nick_owner := v_nick_owner || v_sales[i];
    INSERT INTO zalo_account_access (id, zalo_account_id, user_id, permission, created_at)
      SELECT gen_random_uuid()::text, v_nick, u.id, 'admin', now()
      FROM users u WHERE u.org_id = v_org AND (u.role IN ('owner','admin') OR u.id = v_sales[i] OR u.id = v_sales[5])
      ON CONFLICT DO NOTHING;
  END LOOP;

  -- ── 4. Khách + hội thoại + tin nhắn + bạn bè + lịch hẹn + ghi chú ─────────
  FOR i IN 1..v_count LOOP
    r := random()*100;
    v_stage := 1; WHILE r > v_stage_cut[v_stage] LOOP v_stage := v_stage + 1; END LOOP;
    v_score   := v_score_lo[v_stage] + floor(random()*(v_score_hi[v_stage]-v_score_lo[v_stage]+1))::int;
    v_name    := v_hos[1+floor(random()*array_length(v_hos,1))::int] || ' ' || v_dem[1+floor(random()*array_length(v_dem,1))::int] || ' ' || v_tens[1+floor(random()*array_length(v_tens,1))::int];
    v_phone   := '09' || lpad((floor(random()*100000000))::bigint::text, 8, '0');
    -- khách mới dồn về gần đây hơn (giống thực tế đang tăng)
    v_created := now() - ((floor(power(random(),1.6)*90))::int || ' days')::interval - ((floor(random()*12))::int || ' hours')::interval;
    v_nidx    := 1 + floor(random()*4)::int;
    v_nick    := v_nicks[v_nidx]; v_uid := v_nick_owner[v_nidx];
    v_src     := v_srcs[1+floor(random()*array_length(v_srcs,1))::int];
    v_tinh_c  := v_tinh[1+floor(random()*array_length(v_tinh,1))::int];
    v_nuoi_c  := v_nuoi[1+floor(random()*array_length(v_nuoi,1))::int];
    v_may_c   := v_may[1+floor(random()*array_length(v_may,1))::int];
    v_stuck   := CASE WHEN v_stage BETWEEN 2 AND 5 AND random() < 0.22
                      THEN now() - ((5+floor(random()*25))::int || ' days')::interval END;
    v_tags    := to_jsonb(ARRAY[ CASE WHEN v_stuck IS NOT NULL THEN 'at-risk'
                                     WHEN v_score >= 85 THEN 'champion'
                                     WHEN v_score >= 60 THEN 'hot-lead'
                                     WHEN v_score >= 35 THEN 'warm-lead'
                                     WHEN v_stage IN (7,8) THEN 'dormant'
                                     ELSE 'cold-lead' END ]);
    v_cid := gen_random_uuid()::text;

    -- tin nhắn: khách càng đi sâu phễu càng nhiều tin
    v_nmsg := 2 + v_stage + floor(random()*5)::int;
    v_t := v_created; v_in_n := 0; v_out_n := 0; v_last := v_created;
    v_unread := CASE WHEN v_stage <= 5 AND random() < 0.25 THEN 1 + floor(random()*3)::int ELSE 0 END;

    INSERT INTO contacts (id, org_id, full_name, crm_name, phone, phone_normalized, source, source_date,
      first_contact_date, status, status_id, lead_score, priority_score, engagement_score, engagement_pattern,
      province, district, occupation, gender, has_zalo, consent_status, assigned_user_id,
      stuck_since_aggregate, auto_tags, tags, notes, metadata, created_at, updated_at)
    VALUES (v_cid, v_org, v_name, v_name, v_phone, '84'||substr(v_phone,2), v_src, v_created,
      v_created, v_legacy[v_stage], v_sid->>v_stage_names[v_stage], v_score, LEAST(100, v_score + floor(random()*10)::int),
      LEAST(100, 10 + v_stage*9 + floor(random()*15)::int),
      (ARRAY['cold','stable','hot','champion','cooling'])[1+floor(random()*5)::int],
      v_tinh_c, NULL, 'Chăn nuôi: '||v_nuoi_c, CASE WHEN random()<0.75 THEN 'male' ELSE 'female' END,
      true, 'implicit', v_uid, v_stuck, v_tags,
      to_jsonb(ARRAY['quan tâm '||v_may_c]), 'Nuôi '||v_nuoi_c||' · quan tâm '||v_may_c,
      jsonb_build_object('seed','TEST_BQG','may',v_may_c), v_created, now());

    v_conv := gen_random_uuid()::text;
    INSERT INTO conversations (id, org_id, zalo_account_id, contact_id, "threadType", external_thread_id,
      last_message_at, unread_count, is_replied, tab, created_at)
    VALUES (v_conv, v_org, v_nick, v_cid, 'user', 'test-thread-'||substr(v_cid,1,12),
      v_created, v_unread, v_unread = 0, 'main', v_created);

    FOR j IN 1..v_nmsg LOOP
      -- tin cuối cùng của hội thoại có tin chưa đọc phải là của KHÁCH
      IF (j % 2 = 1) OR (j = v_nmsg AND v_unread > 0) THEN
        v_txt := format(v_in[1+floor(random()*array_length(v_in,1))::int], v_nuoi_c);
        IF v_txt LIKE '%không shop?' AND random()<0.5 THEN v_txt := format('Có giao về %s không shop?', v_tinh_c); END IF;
        INSERT INTO messages (id, conversation_id, zalo_msg_id, sender_type, sender_name, content, content_type, sent_at, sent_via, created_at)
        VALUES (gen_random_uuid()::text, v_conv, 'test-'||substr(v_conv,1,8)||'-'||j, 'contact', v_name, v_txt, 'text', v_t, 'user', v_t);
        v_in_n := v_in_n + 1;
      ELSE
        v_txt := format(v_out[1+floor(random()*array_length(v_out,1))::int], v_may_c);
        INSERT INTO messages (id, conversation_id, zalo_msg_id, sender_type, sender_name, content, content_type, sent_at, sent_via, replied_by_user_id, delivered_at, seen_at, created_at)
        VALUES (gen_random_uuid()::text, v_conv, 'test-'||substr(v_conv,1,8)||'-'||j, 'self', 'BQG', v_txt, 'text', v_t, 'user', v_uid, v_t, v_t + interval '3 minutes', v_t);
        v_out_n := v_out_n + 1;
      END IF;
      v_last := v_t;
      -- bước thời gian: phản hồi vài phút → có khi cách vài ngày; không vượt quá hiện tại
      v_t := v_t + CASE WHEN random() < 0.6 THEN ((2+floor(random()*40))::int || ' minutes')::interval
                        ELSE ((1+floor(random()*4))::int || ' days')::interval END;
      EXIT WHEN v_t > now();   -- hội thoại dừng tự nhiên ở thời điểm hiện tại
    END LOOP;

    -- hội thoại "chưa đọc" luôn kết thúc bằng tin của KHÁCH đang chờ trả lời
    IF v_unread > 0 THEN
      v_last := LEAST(now() - interval '3 minutes', v_last + ((5+floor(random()*120))::int || ' minutes')::interval);
      INSERT INTO messages (id, conversation_id, zalo_msg_id, sender_type, sender_name, content, content_type, sent_at, sent_via, created_at)
      VALUES (gen_random_uuid()::text, v_conv, 'test-'||substr(v_conv,1,8)||'-w', 'contact', v_name,
              (ARRAY['Anh ơi tư vấn giúp em với','Shop ơi còn máy không ạ?','Em chờ báo giá nhé','Alo shop?'])[1+floor(random()*4)::int],
              'text', v_last, 'user', v_last);
      v_in_n := v_in_n + 1;
    END IF;

    UPDATE conversations SET last_message_at = v_last WHERE id = v_conv;
    UPDATE contacts SET total_inbound = v_in_n, total_outbound = v_out_n,
      last_inbound_at = v_last, last_outbound_at = v_last - interval '5 minutes', last_activity = v_last,
      last_inbound_preview = 'Tin nhắn mô phỏng', updated_at = v_last
    WHERE id = v_cid;

    INSERT INTO friends (id, org_id, contact_id, zalo_account_id, zalo_uid_in_nick, friendship_status, has_conversation,
      relationship_kind, zalo_display_name, became_friend_at, first_message_at, last_inbound_at, last_outbound_at,
      last_interaction_at, total_inbound, total_outbound, status_id, lead_score, auto_tags, stuck_since, stage_entered_at,
      created_at, updated_at)
    VALUES (gen_random_uuid()::text, v_org, v_cid, v_nick, 'test-uid-'||substr(v_cid,1,12),
      CASE WHEN random()<0.72 THEN 'friend' WHEN random()<0.5 THEN 'pending' ELSE 'none' END, true,
      'customer', v_name, v_created + interval '10 minutes', v_created, v_last, v_last - interval '5 minutes',
      v_last, v_in_n, v_out_n, v_sid->>v_stage_names[v_stage], v_score, v_tags, v_stuck,
      v_created + ((floor(random()*10))::int || ' days')::interval, v_created, now());

    -- lịch hẹn: khách từ "Hẹn gặp" trở lên
    IF v_stage BETWEEN 3 AND 6 OR random() < 0.12 THEN
      FOR k IN 1..(1 + floor(random()*2)::int) LOOP
        v_t := now() + ((floor(random()*20)-12)::int || ' days')::interval + ((floor(random()*9))::int || ' hours')::interval;
        INSERT INTO appointments (id, org_id, contact_id, assigned_user_id, appointment_date, appointment_time, title,
          duration_min, location, type, status, source, notes, created_at)
        VALUES (gen_random_uuid()::text, v_org, v_cid, v_uid, v_t, to_char(v_t,'HH24:MI'),
          (ARRAY['Gọi tư vấn ','Hẹn xem máy tại xưởng · ','Gửi báo giá ','Gọi chốt cọc ','Hẹn giao lắp · '])[1+floor(random()*5)::int] || v_name,
          (ARRAY[15,30,60])[1+floor(random()*3)::int], (ARRAY['Điện thoại','Xưởng Bình Quân','Tại nhà khách','Zalo'])[1+floor(random()*4)::int],
          (ARRAY['call','meeting','message','follow_up'])[1+floor(random()*4)::int],
          CASE WHEN v_t > now() THEN 'scheduled'
               WHEN random() < 0.62 THEN 'completed'
               WHEN random() < 0.5  THEN 'no_show'
               WHEN random() < 0.5  THEN 'cancelled'
               ELSE 'scheduled' END,   -- 'scheduled' trong quá khứ = hẹn quá hạn
          'manual', '[TEST_BQG]', v_created);
      END LOOP;
    END IF;

    -- ghi chú của sale
    IF random() < 0.45 THEN
      INSERT INTO notes (id, org_id, contact_id, author_user_id, body, created_at, updated_at)
      VALUES (gen_random_uuid()::text, v_org, v_cid, v_uid,
        format(v_note[1+floor(random()*array_length(v_note,1))::int], v_may_c), v_last, v_last);
    END IF;

    -- nhịp tương tác theo ngày (heatmap)
    FOR k IN 0..(floor(random()*6))::int LOOP
      INSERT INTO contact_engagement_daily (id, org_id, contact_id, date, inbound_msg_count, outbound_msg_count,
        reaction_count, call_count, quote_reply_count, customer_initiated, daily_intensity, created_at, updated_at)
      VALUES (gen_random_uuid()::text, v_org, v_cid, (v_last - (k*3 || ' days')::interval)::date,
        1+floor(random()*5)::int, 1+floor(random()*4)::int, floor(random()*2)::int, floor(random()*2)::int,
        floor(random()*2)::int, random()<0.5, 20+floor(random()*70)::int, now(), now())
      ON CONFLICT (org_id, contact_id, date) DO NOTHING;
    END LOOP;

    INSERT INTO activity_logs (id, org_id, user_id, actor_type, category, action, entity_type, entity_id, details, created_at)
    VALUES (gen_random_uuid()::text, v_org, v_uid, 'user', 'contact', 'contact.created', 'contact', v_cid,
      jsonb_build_object('seed','TEST_BQG','source',v_src), v_created);
    v_ok := v_ok + 1;
  END LOOP;

  -- ── 5. Thống kê tin nhắn theo ngày / sale / nick (báo cáo thời gian phản hồi) ─
  FOR i IN 1..4 LOOP
    FOR k IN 0..44 LOOP
      INSERT INTO daily_message_stats (id, org_id, user_id, zalo_account_id, stat_date, messages_sent, messages_received,
        messages_unread, messages_unreplied, avg_response_time_seconds)
      SELECT gen_random_uuid()::text, v_org, v_nick_owner[i], v_nicks[i], (now() - (k || ' days')::interval)::date,
        coalesce(sum(CASE WHEN m.sender_type='self' THEN 1 END),0), coalesce(sum(CASE WHEN m.sender_type='contact' THEN 1 END),0),
        floor(random()*4)::int, floor(random()*3)::int,
        -- Sale nick 1 nhanh nhất, nick 4 chậm nhất → thấy khác biệt giữa người
        (60*i + floor(random()*240*i))::int
      FROM messages m JOIN conversations c ON c.id = m.conversation_id
      WHERE c.zalo_account_id = v_nicks[i] AND m.sent_at::date = (now() - (k || ' days')::interval)::date;
    END LOOP;
  END LOOP;

  -- ── 6. Tệp khách hàng (nhập từ hội chợ) ───────────────────────────────────
  v_list := gen_random_uuid()::text;
  INSERT INTO customer_lists (id, org_id, created_by_id, name, icon_emoji, source_type, total_entries, valid_entries,
    invalid_entries, has_zalo_entries, no_zalo_entries, dup_with_contact_entries, status, started_at, ended_at, created_at, updated_at)
  VALUES (v_list, v_org, v_sales[5], 'TEST·Khách hội chợ Nông nghiệp 10/2026', '🌾', 'excel', 60, 56, 4, 41, 15, 6,
    'done', now() - interval '6 days', now() - interval '6 days', now() - interval '6 days', now());
  FOR k IN 1..60 LOOP
    INSERT INTO customer_list_entries (id, customer_list_id, row_index, phone_raw, name_raw, personal_note, phone_e164,
      phone_local, phone_valid, invalid_reason, has_zalo, status, created_at, updated_at)
    VALUES (gen_random_uuid()::text, v_list, k, '098'||lpad(k::text,7,'0'),
      v_hos[1+floor(random()*array_length(v_hos,1))::int]||' '||v_tens[1+floor(random()*array_length(v_tens,1))::int],
      'Gặp ở hội chợ, quan tâm '||v_may[1+floor(random()*array_length(v_may,1))::int],
      '+8498'||lpad(k::text,7,'0'), '098'||lpad(k::text,7,'0'), k > 4, CASE WHEN k <= 4 THEN 'invalid_format' END,
      CASE WHEN k <= 4 THEN NULL WHEN k <= 45 THEN true ELSE false END,
      CASE WHEN k <= 4 THEN 'invalid' ELSE 'enriched' END, now() - interval '6 days', now());
  END LOOP;

  RAISE NOTICE '✅ Đã mô phỏng: % khách · 5 sale · 4 nick Zalo · tin nhắn/lịch hẹn/ghi chú/bạn bè/tệp khách', v_ok;
END $$;

-- ── Tổng kết ───────────────────────────────────────────────────────────────
SELECT 'Khách hàng' AS "Dữ liệu ảo", count(*) AS "Số lượng" FROM contacts WHERE metadata->>'seed'='TEST_BQG'
UNION ALL SELECT 'Hội thoại', count(*) FROM conversations c JOIN zalo_accounts z ON z.id=c.zalo_account_id WHERE z.display_name LIKE 'TEST·%'
UNION ALL SELECT 'Tin nhắn', count(*) FROM messages m JOIN conversations c ON c.id=m.conversation_id JOIN zalo_accounts z ON z.id=c.zalo_account_id WHERE z.display_name LIKE 'TEST·%'
UNION ALL SELECT 'Lịch hẹn', count(*) FROM appointments WHERE notes='[TEST_BQG]'
UNION ALL SELECT 'Ghi chú', count(*) FROM notes n JOIN contacts ct ON ct.id=n.contact_id WHERE ct.metadata->>'seed'='TEST_BQG'
UNION ALL SELECT 'Nick Zalo ảo', count(*) FROM zalo_accounts WHERE display_name LIKE 'TEST·%'
UNION ALL SELECT 'Sale ảo', count(*) FROM users WHERE email LIKE '%@demo.bqg.test';
