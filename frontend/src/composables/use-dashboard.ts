import { ref } from 'vue';
import { api } from '@/api';

export interface KpiData {
  messagesToday: number;
  messagesUnreplied: number;
  messagesUnread: number;
  appointmentsToday: number;
  newContactsThisWeek: number;
  totalContacts: number;
}

export interface MessageVolumeItem {
  date: string;
  sent: number;
  received: number;
}

export interface PipelineItem {
  status: string | null;
  _count: { _all: number } | number;
}

export interface SourceItem {
  source: string;
  _count: { _all: number } | number;
}

export interface AppointmentStatusItem {
  status: string;
  _count: { _all: number } | number;
}

export function useDashboard() {
  const kpi = ref<KpiData | null>(null);
  const messageVolume = ref<MessageVolumeItem[]>([]);
  const pipeline = ref<PipelineItem[]>([]);
  const sources = ref<SourceItem[]>([]);
  const appointments = ref<AppointmentStatusItem[]>([]);
  const loading = ref(false);

  async function fetchAll() {
    loading.value = true;
    try {
      const [kpiRes, volRes, pipRes, srcRes, aptRes] = await Promise.all([
        api.get('/dashboard/kpi'),
        api.get('/dashboard/message-volume'),
        api.get('/dashboard/pipeline'),
        api.get('/dashboard/sources'),
        api.get('/dashboard/appointments'),
      ]);
      kpi.value = kpiRes.data;
      messageVolume.value = volRes.data.data || volRes.data;
      // Backend trả { data: [{ status|source, count }] } còn biểu đồ cần mảng có `_count`
      // → bóc lớp `data` và chuẩn hoá tên trường, nếu không 3 biểu đồ luôn "Không có dữ liệu".
      const toChartItems = (res: { data: unknown }) => {
        const body = res.data as { data?: unknown[] } | unknown[];
        const rows = (Array.isArray(body) ? body : body?.data ?? []) as Array<Record<string, unknown>>;
        return rows.map((r) => ({ ...r, _count: (r._count ?? r.count ?? 0) as number }));
      };
      pipeline.value = toChartItems(pipRes) as unknown as PipelineItem[];
      sources.value = toChartItems(srcRes) as unknown as SourceItem[];
      appointments.value = toChartItems(aptRes) as unknown as AppointmentStatusItem[];
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      loading.value = false;
    }
  }

  return {
    kpi, messageVolume, pipeline, sources, appointments,
    loading, fetchAll,
  };
}
