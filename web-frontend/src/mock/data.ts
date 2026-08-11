import type { AppInfo, ChatSession, EnabledSiteQuick } from '../types'

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
    title_locked: false,
    pinned: true,
    updated_at: '2026-08-11T10:24:00+08:00',
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
    title_locked: false,
    pinned: false,
    updated_at: '2026-08-10T16:02:00+08:00',
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
    title_locked: true,
    pinned: false,
    updated_at: '2026-05-19T11:08:00+08:00',
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
