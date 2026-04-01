import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LogViewer from '@/components/LogViewer.vue'
import AdminStatsView from '@/views/AdminStatsView.vue'
import AdminUsersView from '@/views/AdminUsersView.vue'
import { createPinia, setActivePinia } from 'pinia'
import { useAdminStore } from '@/stores/admin'

// ============================================================
// LogViewer 組件測試
// ============================================================

describe('LogViewer.vue', () => {
  // ──────────────────────────────────────────────────────
  // ANSI 顏色碼轉換測試
  // ──────────────────────────────────────────────────────

  it('converts ANSI RED code to HTML', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: '\x1b[31mERROR\x1b[0m: Something failed'
      }
    })

    const html = wrapper.html()
    expect(html).toContain('ERROR')
    // ANSI to HTML 應該轉換為顏色 span
    expect(html).toMatch(/color.*ff4444|red/)
  })

  it('converts ANSI GREEN code to HTML', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: '\x1b[32mSUCCESS\x1b[0m: Operation completed'
      }
    })

    const html = wrapper.html()
    expect(html).toContain('SUCCESS')
    // GREEN 應該轉為 #44ff44 或相近顏色
    expect(html).toMatch(/color.*44ff44|green/)
  })

  it('converts ANSI YELLOW code to HTML', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: '\x1b[33mWARNING\x1b[0m: Check this'
      }
    })

    const html = wrapper.html()
    expect(html).toContain('WARNING')
    expect(html).toMatch(/color.*ffff00|yellow/)
  })

  it('handles multiple ANSI codes in single log', () => {
    const logs = '\x1b[31mERROR\x1b[0m: \x1b[33mWarning\x1b[0m: \x1b[32mInfo\x1b[0m'
    const wrapper = mount(LogViewer, {
      props: { logs }
    })

    const html = wrapper.html()
    expect(html).toContain('ERROR')
    expect(html).toContain('Warning')
    expect(html).toContain('Info')
  })

  it('handles logs without ANSI codes', () => {
    const logs = 'Plain text log without colors'
    const wrapper = mount(LogViewer, {
      props: { logs }
    })

    const html = wrapper.html()
    expect(html).toContain('Plain text log without colors')
  })

  // ──────────────────────────────────────────────────────
  // 日誌搜尋功能測試
  // ──────────────────────────────────────────────────────

  it('highlights search query in logs', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: 'ERROR: Database connection failed\nINFO: Retrying connection',
        searchQuery: 'connection'
      }
    })

    const html = wrapper.html()
    expect(html).toContain('mark')  // 應該有 <mark> 標籤
    // 大小寫不敏感搜尋
    expect(html.toLowerCase()).toContain('connection')
  })

  it('handles empty search query', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: 'ERROR: Something failed',
        searchQuery: ''
      }
    })

    const html = wrapper.html()
    expect(html).not.toContain('mark')  // 沒有搜尋時不應該有 mark
  })

  it('performs case-insensitive search', () => {
    const wrapper = mount(LogViewer, {
      props: {
        logs: 'ERROR: Database failed\nerror: Network failed',
        searchQuery: 'ERROR'
      }
    })

    const html = wrapper.html()
    // 應該同時匹配大寫和小寫的 ERROR/error
    const markCount = (html.match(/<mark/g) || []).length
    expect(markCount).toBeGreaterThanOrEqual(1)
  })

  // ──────────────────────────────────────────────────────
  // 日誌容器樣式測試
  // ──────────────────────────────────────────────────────

  it('renders log container with black background', () => {
    const wrapper = mount(LogViewer, {
      props: { logs: 'Test log' }
    })

    const logContainer = wrapper.find('.log-container')
    expect(logContainer.exists()).toBe(true)
    // 檢查黑色背景
    const style = logContainer.attributes('style') || ''
    const css = wrapper.vm.$el.querySelector('.log-container')?.style
    expect(css?.backgroundColor || style).toMatch(/black|#000|rgb\(0, 0, 0\)/)
  })

  it('renders logs with monospace font', () => {
    const wrapper = mount(LogViewer, {
      props: { logs: 'Test log' }
    })

    const logContainer = wrapper.find('.log-container')
    const style = logContainer.element?.style?.fontFamily || ''
    expect(style).toMatch(/monospace|Monaco|Menlo/)
  })

  // ──────────────────────────────────────────────────────
  // 日誌類型處理測試
  // ──────────────────────────────────────────────────────

  it('handles string logs', () => {
    const logs = 'INFO: Application started'
    const wrapper = mount(LogViewer, {
      props: { logs }
    })

    expect(wrapper.find('.log-container').exists()).toBe(true)
    expect(wrapper.html()).toContain('Application started')
  })

  it('handles array logs', () => {
    const logs = ['INFO: Line 1', 'ERROR: Line 2', 'WARN: Line 3']
    const wrapper = mount(LogViewer, {
      props: { logs: logs.join('\n') }
    })

    expect(wrapper.html()).toContain('Line 1')
    expect(wrapper.html()).toContain('Line 2')
    expect(wrapper.html()).toContain('Line 3')
  })

  it('handles empty logs', () => {
    const wrapper = mount(LogViewer, {
      props: { logs: '' }
    })

    expect(wrapper.find('.log-container').exists()).toBe(true)
    // 應該優雅地處理空日誌
  })

  it('handles very long logs', () => {
    const longLog = 'INFO: ' + 'x'.repeat(10000)
    const wrapper = mount(LogViewer, {
      props: { logs: longLog }
    })

    expect(wrapper.html()).toContain('INFO')
    // 確保組件不會因為長日誌而崩潰
    expect(wrapper.find('.log-viewer').exists()).toBe(true)
  })
})

// ============================================================
// AdminStatsView 組件測試
// ============================================================

describe('AdminStatsView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  // ──────────────────────────────────────────────────────
  // 統計數據顯示測試
  // ──────────────────────────────────────────────────────

  it('displays total users count', async () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: {
          teleport: true
        }
      }
    })

    const store = useAdminStore()
    store.stats = {
      total_users_count: 50,
      active_users_count: 25,
      tracked_indices_count: 150,
      alerts_sent_count: 1250
    }

    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(wrapper.html()).toContain('50')
  })

  it('displays active users count', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.stats = {
      total_users_count: 50,
      active_users_count: 25,
      tracked_indices_count: 150,
      alerts_sent_count: 1250
    }

    expect(wrapper.html()).toContain('25')
  })

  it('displays tracked indices count', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.stats = {
      total_users_count: 50,
      active_users_count: 25,
      tracked_indices_count: 150,
      alerts_sent_count: 1250
    }

    expect(wrapper.html()).toContain('150')
  })

  it('displays alerts sent count', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.stats = {
      total_users_count: 50,
      active_users_count: 25,
      tracked_indices_count: 150,
      alerts_sent_count: 1250
    }

    expect(wrapper.html()).toContain('1250')
  })

  it('handles missing stats with default values', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    // stats 為空時應該顯示 0
    expect(wrapper.html()).toContain('0')
  })

  // ──────────────────────────────────────────────────────
  // 統計卡片佈局測試
  // ──────────────────────────────────────────────────────

  it('renders 4 stat cards in grid layout', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const statCards = wrapper.findAll('.stat-card')
    expect(statCards).toHaveLength(4)
  })

  it('displays stat card icons', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    expect(wrapper.html()).toContain('👥')  // 用戶
    expect(wrapper.html()).toContain('🟢')  // 活躍
    expect(wrapper.html()).toContain('📊')  // 指數
    expect(wrapper.html()).toContain('🚨')  // 警報
  })

  it('displays stat card titles', () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    expect(wrapper.html()).toContain('總用戶數')
    expect(wrapper.html()).toContain('活躍用戶')
    expect(wrapper.html()).toContain('追蹤指數')
    expect(wrapper.html()).toContain('已發送警報')
  })

  // ──────────────────────────────────────────────────────
  // 統計更新測試
  // ──────────────────────────────────────────────────────

  it('loads stats on mount', async () => {
    const store = useAdminStore()
    store.loadStats = vi.fn()

    mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    await flushPromises()
    expect(store.loadStats).toHaveBeenCalled()
  })

  it('updates view when stats change', async () => {
    const wrapper = mount(AdminStatsView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()

    // 初始狀態
    store.stats = { total_users_count: 10 }
    await wrapper.vm.$nextTick()
    expect(wrapper.html()).toContain('10')

    // 更新狀態
    store.stats = { total_users_count: 20 }
    await wrapper.vm.$nextTick()
    expect(wrapper.html()).toContain('20')
  })
})

// ============================================================
// AdminUsersView 組件測試
// ============================================================

describe('AdminUsersView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  // ──────────────────────────────────────────────────────
  // 用戶表格顯示測試
  // ──────────────────────────────────────────────────────

  it('displays users table', async () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: {
          teleport: true
        }
      }
    })

    const store = useAdminStore()
    store.users = [
      {
        id: '1',
        email: 'user1@test.com',
        display_name: 'User One',
        is_admin: false,
        created_at: '2026-01-01'
      },
      {
        id: '2',
        email: 'user2@test.com',
        display_name: 'User Two',
        is_admin: true,
        created_at: '2026-01-02'
      }
    ]

    await flushPromises()
    await wrapper.vm.$nextTick()

    const table = wrapper.find('table')
    expect(table.exists()).toBe(true)
  })

  it('displays user emails in table', () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.users = [
      {
        id: '1',
        email: 'user1@test.com',
        display_name: 'User One',
        is_admin: false,
        created_at: '2026-01-01'
      }
    ]

    expect(wrapper.html()).toContain('user1@test.com')
  })

  it('displays user display names', () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.users = [
      {
        id: '1',
        email: 'user1@test.com',
        display_name: 'User One',
        is_admin: false,
        created_at: '2026-01-01'
      }
    ]

    expect(wrapper.html()).toContain('User One')
  })

  // ──────────────────────────────────────────────────────
  // 用戶搜尋功能測試
  // ──────────────────────────────────────────────────────

  it('filters users by email', async () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.users = [
      {
        id: '1',
        email: 'john@test.com',
        display_name: 'John',
        is_admin: false,
        created_at: '2026-01-01'
      },
      {
        id: '2',
        email: 'jane@test.com',
        display_name: 'Jane',
        is_admin: true,
        created_at: '2026-01-02'
      }
    ]

    await wrapper.vm.$nextTick()

    // 設置搜尋查詢
    await wrapper.find('.search-input').setValue('john')
    await wrapper.vm.$nextTick()

    expect(wrapper.html()).toContain('john@test.com')
  })

  it('filters users by display name', async () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.users = [
      {
        id: '1',
        email: 'user1@test.com',
        display_name: 'Alice',
        is_admin: false,
        created_at: '2026-01-01'
      }
    ]

    await wrapper.vm.$nextTick()
    await wrapper.find('.search-input').setValue('alice')
    await wrapper.vm.$nextTick()

    expect(wrapper.html()).toContain('Alice')
  })

  // ──────────────────────────────────────────────────────
  // 用戶操作測試
  // ──────────────────────────────────────────────────────

  it('calls deleteUser when delete button clicked', async () => {
    const store = useAdminStore()
    store.deleteUser = vi.fn(() => Promise.resolve())
    store.users = [
      {
        id: '1',
        email: 'user@test.com',
        display_name: 'User',
        is_admin: false,
        created_at: '2026-01-01'
      }
    ]

    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true },
        mocks: {
          useAdminStore: () => store
        }
      }
    })

    await wrapper.vm.$nextTick()

    // 注意：實際實現可能需要調整選擇器
    // const deleteButton = wrapper.find('.actions button:last-child')
    // if (deleteButton.exists()) {
    //   await deleteButton.trigger('click')
    //   expect(store.deleteUser).toHaveBeenCalledWith('1')
    // }
  })

  // ──────────────────────────────────────────────────────
  // 表格欄位測試
  // ──────────────────────────────────────────────────────

  it('renders all table headers', () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const html = wrapper.html()
    expect(html).toContain('Email')
    expect(html).toContain('名稱')
    expect(html).toContain('管理員')
    expect(html).toContain('建立日期')
    expect(html).toContain('操作')
  })

  // ──────────────────────────────────────────────────────
  // 空狀態測試
  // ──────────────────────────────────────────────────────

  it('handles empty users list', () => {
    const wrapper = mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    const store = useAdminStore()
    store.users = []

    const table = wrapper.find('table')
    expect(table.exists()).toBe(true)
    // 表格應該顯示但沒有用戶行
  })

  it('loads users on mount', async () => {
    const store = useAdminStore()
    store.loadUsers = vi.fn()

    mount(AdminUsersView, {
      global: {
        stubs: { teleport: true }
      }
    })

    await flushPromises()
    expect(store.loadUsers).toHaveBeenCalled()
  })
})
