import type { AppInfo, ChatSession, EnabledSiteQuick, SourceSite } from '../types'

export const currentApp: AppInfo = {
  id: 1,
  name: '农药登记评审资料问答',
  app_type: 'rag_chat',
  model_profile_id: 'default_chat',
  kb_name: '农药登记评审资料',
  kb_count: 1,
}

export const categoryLabel: Record<string, string> = {
  registration: '登记',
  evaluation: '评审',
  standard: '标准',
  database: '数据库',
}

export const mockSites: SourceSite[] = [
  {
    site_id: 'us_ppis',
    name: '美国 PPIS',
    region: 'US',
    category: 'registration',
    entry_url: 'http://npirspublic.ceris.purdue.edu/ppis/',
    crawl_mode: 'connector',
    allowed_domains: ['npirspublic.ceris.purdue.edu'],
    status: 'active',
    notes: '美国农药产品检索门户，按有效成分查询登记信息。',
    last_probe_at: '2026-08-10 09:12',
    last_probe_status: '200',
  },
  {
    site_id: 'eu_pesticides_db',
    name: '欧盟农药数据库',
    region: 'EU',
    category: 'registration',
    entry_url:
      'https://ec.europa.eu/food/plant/pesticides/eu-pesticides-database/public/?event=homepage&language=EN',
    crawl_mode: 'connector',
    allowed_domains: ['ec.europa.eu'],
    status: 'active',
    notes: '欧盟官方农药有效成分与制剂数据库。',
    last_probe_at: '2026-08-10 09:12',
    last_probe_status: '200',
  },
  {
    site_id: 'uk_hse_pesticides',
    name: '英国 HSE 农药',
    region: 'UK',
    category: 'registration',
    entry_url: 'https://www.hse.gov.uk/pesticides/',
    crawl_mode: 'list_harvest',
    allowed_domains: ['www.hse.gov.uk', 'hse.gov.uk'],
    status: 'active',
    notes: '',
    last_probe_at: '2026-08-09 18:01',
    last_probe_status: '200',
  },
  {
    site_id: 'au_apvma_reviews',
    name: '澳大利亚 APVMA Reviews',
    region: 'AU',
    category: 'registration',
    entry_url: 'http://www.apvma.gov.au/products/review/a_z_reviews.php',
    crawl_mode: 'list_harvest',
    allowed_domains: ['www.apvma.gov.au', 'apvma.gov.au'],
    status: 'active',
    notes: '注意可能跳转新域名。',
    last_probe_at: '2026-08-09 18:02',
    last_probe_status: '301',
  },
  {
    site_id: 'eu_efsa_publications',
    name: 'EFSA Publications',
    region: 'EU',
    category: 'evaluation',
    entry_url: 'https://www.efsa.europa.eu/en/publications',
    crawl_mode: 'list_harvest',
    allowed_domains: ['www.efsa.europa.eu', 'efsa.europa.eu'],
    status: 'active',
    notes: 'P1 优先列表收获来源。',
    last_probe_at: '2026-08-10 09:15',
    last_probe_status: '200',
  },
  {
    site_id: 'ppdb',
    name: 'PPDB',
    region: 'INT',
    category: 'database',
    entry_url: 'http://sitem.herts.ac.uk/aeru/ppdb/en/index.htm',
    crawl_mode: 'connector',
    allowed_domains: ['sitem.herts.ac.uk'],
    status: 'active',
    notes: '物质页结构相对稳定，适合做连接器样板。',
    last_probe_at: '2026-08-10 09:16',
    last_probe_status: '200',
  },
  {
    site_id: 'cn_pesticide_info',
    name: '中国农药信息网',
    region: 'CN',
    category: 'registration',
    entry_url: '',
    crawl_mode: 'connector',
    allowed_domains: [],
    status: 'pending_url',
    notes: '入口 URL 待业务补全。',
    last_probe_at: null,
    last_probe_status: null,
  },
  {
    site_id: 'cn_std_openstd',
    name: '国家标准全文公开系统',
    region: 'CN',
    category: 'standard',
    entry_url: 'https://openstd.samr.gov.cn/bzgk/std/',
    crawl_mode: 'connector',
    allowed_domains: ['openstd.samr.gov.cn'],
    status: 'active',
    notes: '',
    last_probe_at: '2026-08-08 14:22',
    last_probe_status: '200',
  },
  {
    site_id: 'jp_fsc_env_fate',
    name: '日本 FSC 评价报告（环境归趋）',
    region: 'JP',
    category: 'evaluation',
    entry_url: 'http://www.fsc.go.jp/english/evaluationreports/agrichemicalsl_e1.heml',
    crawl_mode: 'manual',
    allowed_domains: ['www.fsc.go.jp', 'fsc.go.jp'],
    status: 'broken',
    notes: '扩展名疑似笔误 .heml，需确认正确 URL。',
    last_probe_at: '2026-08-08 14:30',
    last_probe_status: '404',
  },
]

export const enabledSitesQuick: EnabledSiteQuick[] = [
  {
    id: 'ppdb',
    name: 'PPDB',
    logo: 'PP',
    url: 'http://sitem.herts.ac.uk/aeru/ppdb/en/index.htm',
  },
  {
    id: 'efsa',
    name: 'EFSA Publications',
    logo: 'EF',
    url: 'https://www.efsa.europa.eu/en/publications',
  },
  {
    id: 'gb',
    name: '国家标准公开系统',
    logo: 'GB',
    url: 'https://openstd.samr.gov.cn/bzgk/std/',
  },
]

export const mockSessions: ChatSession[] = [
  {
    id: 's1',
    title: '草甘膦 欧盟登记资料',
    time_label: '10:24',
    messages: [
      {
        id: 'm1',
        role: 'user',
        content: '草甘膦在欧盟的登记评审资料有哪些？',
        time: '10:24',
      },
      {
        id: 'm2',
        role: 'assistant',
        content: `根据当前知识库检索结果，与「草甘膦（glyphosate）」相关的欧盟登记/评审资料线索如下：

**评审报告**
- EFSA 出版物库中可检索 glyphosate 相关 scientific opinions / conclusions
- 关注再评审（renewal）与风险评估结论类文档

**科学支持文件**
- 欧盟农药数据库中的有效成分条目（批准状态、截止日期等需核对官网）
- 相关 peer review 与公开咨询材料（如有入库）

**使用建议**
- 以下引用仅反映库内片段，正式登记结论请打开原文核对
- 若需最新状态，建议同时访问欧盟农药数据库与 EFSA Publications`,
        time: '10:24',
        citations: [
          {
            index: 1,
            title: 'Glyphosate — peer review of the pesticide risk assessment',
            site_name: 'EFSA Publications',
            url: 'https://www.efsa.europa.eu/en/publications',
            snippet:
              '…the peer review of the pesticide risk assessment of the active substance glyphosate…',
          },
          {
            index: 2,
            title: 'EU Pesticides Database — active substance search',
            site_name: '欧盟农药数据库',
            url: 'https://ec.europa.eu/food/plant/pesticides/eu-pesticides-database/public/?event=homepage&language=EN',
            snippet: '…search active substances and check approval status in the EU…',
          },
        ],
      },
    ],
  },
  {
    id: 's2',
    title: 'PPDB 物质查询',
    time_label: '昨天',
    messages: [
      {
        id: 'm3',
        role: 'user',
        content: 'PPDB 上怎么查有效成分的环境归趋数据？',
        time: '昨天 16:02',
      },
      {
        id: 'm4',
        role: 'assistant',
        content:
          'PPDB（Pesticide Properties DataBase）可按物质英文通用名检索。库内如有该物质页摘要，我会给出引用；否则请直接打开右侧快捷站点进入 PPDB 查询。',
        time: '昨天 16:02',
        citations: [
          {
            index: 1,
            title: 'PPDB Homepage',
            site_name: 'PPDB',
            url: 'http://sitem.herts.ac.uk/aeru/ppdb/en/index.htm',
            snippet: '…search by active ingredient common name…',
          },
        ],
      },
    ],
  },
  {
    id: 's3',
    title: '国标检索入口',
    time_label: '5/19',
    messages: [
      {
        id: 'm5',
        role: 'user',
        content: 'GB/T 相关农药标准在国标平台上的检索入口是什么？',
        time: '5/19 11:08',
      },
      {
        id: 'm6',
        role: 'assistant',
        content:
          '可使用「国家标准全文公开系统」作为入口。当前站点清单中已启用该站，请从右侧快捷访问打开后按标准号检索。回答仅供辅助参考。',
        time: '5/19 11:08',
        citations: [
          {
            index: 1,
            title: '国家标准全文公开系统',
            site_name: 'openstd.samr.gov.cn',
            url: 'https://openstd.samr.gov.cn/bzgk/std/',
            snippet: '…标准检索与全文公开阅读入口…',
          },
        ],
      },
    ],
  },
]
