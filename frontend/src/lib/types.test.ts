/**
 * Minimal type validation test - ensures types construct correctly
 */
import { describe, it, expect } from 'vitest';
import type {
  TelegramStatusRead,
  ChannelRead,
  SubscriptionRead,
  MediaItemRead,
  DownloadJobRead,
  SettingRead,
  EventRead,
  PluginRead,
} from './types';

describe('Types compilation', () => {
  it('constructs TelegramStatusRead', () => {
    const status: TelegramStatusRead = {
      status: 'connected',
      username: '@testuser',
      display_name: 'Test User',
      phone: '+1*****1234',
    };
    expect(status.status).toBe('connected');
  });

  it('constructs ChannelRead', () => {
    const channel: ChannelRead = {
      id: 1,
      tg_id: 123456789,
      title: 'Test Channel',
      username: '@testchannel',
      is_forum: false,
      photo_b64: 'base64data',
    };
    expect(channel.tg_id).toBe(123456789);
  });

  it('constructs SubscriptionRead', () => {
    const sub: SubscriptionRead = {
      id: 1,
      channel_id: 1,
      topic_id: undefined,
      enabled: true,
      mode: 'immediate',
      schedule_days: null,
      filter_regex: null,
      filter_mode: 'include',
      min_size_mb: null,
      max_size_mb: null,
      storage_path: '/data/videos',
      rename_template: '{title}',
      season_detection: true,
      retention_days: 30,
      retention_disk_pct: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(sub.mode).toBe('immediate');
  });

  it('constructs MediaItemRead', () => {
    const media: MediaItemRead = {
      id: 1,
      channel_id: 1,
      topic_id: null,
      subscription_id: 1,
      tg_msg_id: 999,
      caption: 'Test caption',
      file_name: 'video.mp4',
      mime: 'video/mp4',
      size_bytes: 1024000,
      duration_sec: 120,
      date_posted: '2024-01-01T10:00:00Z',
      thumb_b64: null,
      status: 'downloaded',
      local_path: '/local/video.mp4',
      downloaded_at: '2024-01-01T10:30:00Z',
      reactions: { '👍': 5 },
      comments_count: 2,
      created_at: '2024-01-01T10:00:00Z',
      updated_at: '2024-01-01T10:30:00Z',
    };
    expect(media.status).toBe('downloaded');
  });

  it('constructs DownloadJobRead', () => {
    const job: DownloadJobRead = {
      id: 1,
      media_id: 1,
      status: 'downloading',
      progress: 0.5,
      speed_bps: 1000000,
      eta_sec: 60,
      bytes_done: 500000,
      bytes_total: 1000000,
      attempt: 1,
      error: null,
      started_at: '2024-01-01T10:00:00Z',
      finished_at: null,
    };
    expect(job.progress).toBe(0.5);
  });

  it('constructs SettingRead', () => {
    const setting: SettingRead = {
      key: 'theme',
      value: '"dark"',
    };
    expect(setting.key).toBe('theme');
  });

  it('constructs EventRead', () => {
    const event: EventRead = {
      id: 1,
      level: 'info',
      kind: 'download_started',
      subscription_id: 1,
      media_id: 1,
      message: 'Download started',
      created_at: '2024-01-01T10:00:00Z',
    };
    expect(event.level).toBe('info');
  });

  it('constructs PluginRead', () => {
    const plugin: PluginRead = {
      id: 1,
      name: 'test-plugin',
      version: '1.0.0',
      enabled: true,
      config: { debug: true },
      installed_at: '2024-01-01T00:00:00Z',
    };
    expect(plugin.enabled).toBe(true);
  });
});
